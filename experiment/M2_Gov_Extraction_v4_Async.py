import os
import pandas as pd
import json
import time
import re
import asyncio
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-2.5-flash-lite"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Extracted_Triples.json")
DISCOVERY_FILE = os.path.join(PROJECT_ROOT, "output", "M2_Discovery_Registry.json")

# CONCURRENCY CONFIG: Adjust based on your API tier
# CONCURRENCY CONFIG: Freeze-safe bounded parallelism
CONCURRENT_LIMIT = 5
REQUEST_TIMEOUT_SECONDS = 300
MAX_TRANSPORT_ATTEMPTS = 2
semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

telemetry = {
    "api_calls": 0,
    "total_prompt_tokens": 0,
    "total_comp_tokens": 0,
    "total_time": 0.0 # Cumulative Network Latency
}

# --- 1. Schema Definition ---
OUTPUT_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    description="List of semantic triples.",
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "subject": types.Schema(type=types.Type.STRING),
            "predicate": types.Schema(type=types.Type.STRING),
            "object": types.Schema(type=types.Type.STRING),
        },
        required=["subject", "predicate", "object"],
    )
)

# --- 2. Dynamic Heuristic Interceptor ---
def heuristic_entity_rescue(text, record_id, domain, existing_triples):
    """Scavenges for Quoted Entities missed by LLM and maps them to the domain."""
    new_triples = []
    patterns = [r'"([^"]+)"', r"'([^']+)'"]
    
    for pat in patterns:
        matches = re.findall(pat, text)
        for entity in matches:
            if len(entity) < 3 or len(entity) > 75: continue
            if not any(char.isupper() for char in entity): continue

            # Deduplication
            if any(t['subject'] == entity or t['object'] == entity for t in existing_triples):
                continue

            clean_domain = domain.replace(" ", "_")
            new_triples.append({
                "subject": entity, "predicate": "is_type_of", 
                "object": f"{clean_domain}_Artifact", "extraction_mode": "HEURISTIC" 
            })
            new_triples.append({
                "subject": entity, "predicate": "belongs_to_domain", 
                "object": domain, "extraction_mode": "GOVERNANCE"
            })
    return existing_triples + new_triples

# --- 3. Async Extraction Wrapper ---
async def call_extraction_async(
        text: str, 
        domain: str, 
        predicates: list, 
        definitions: dict, 
        mode: str,
        record_id: str,
        chunk_id: str,
        ) -> list:
    if mode == "STRICT":
        constraint = f"STRICTLY usage ONLY these verbs: {predicates}."
    else:
        constraint = "DISCOVERY MODE: Vocabulary failed. Extract using natural language verbs."

    prompt = f"Engineer for {domain}. Context: {constraint}. Definitions: {definitions}. Task: Extract triples.\n\n<TEXT>\n{text}\n</TEXT>"

    async with semaphore:
        last_error = None
        for attempt in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
            try:
                start_time = time.time()
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=LLM_MODEL,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=OUTPUT_SCHEMA,
                            temperature=0.0
                        )
                    ),
                    timeout=REQUEST_TIMEOUT_SECONDS
                )

                telemetry['api_calls'] += 1
                telemetry['total_time'] += (time.time() - start_time)
                if response.usage_metadata:
                    telemetry['total_prompt_tokens'] += (
                        getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    )
                    telemetry['total_comp_tokens'] += (
                        getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                    )

                triples = json.loads(response.text)
                if not isinstance(triples, list):
                    raise ValueError("Expected JSON array of triples.")

                for t in triples:
                    if isinstance(t, dict):
                        t["extraction_mode"] = mode

                return triples

            except Exception as e:
                last_error = e
                if attempt == MAX_TRANSPORT_ATTEMPTS:
                    raise RuntimeError(
                        f"M2 extraction failed | mode={mode} | record={record_id} "
                        f"| chunk={chunk_id} | domain={domain} | attempt={attempt} | error={e}"
                    ) from e
                await asyncio.sleep(2)

# --- 4. Logic Gate for Single Chunk ---
async def process_chunk(idx, row):
    try:
        preds = json.loads(row['predicates']) if isinstance(row['predicates'], str) else []
        defs = json.loads(row['disambiguation']) if isinstance(row['disambiguation'], str) else {}
    except Exception as e:
        raise RuntimeError(
            f"M2 metadata parse failed | record={row['record_id']} "
            f"| chunk={row['chunk_id']} | error={e}"
        ) from e

    # Tier 1: STRICT
    triples = await call_extraction_async(
        row['chunk_text'], 
        row['viewpoint_domain'], 
        preds, 
        defs, 
        "STRICT",
        row['record_id'],
        row['chunk_id']
    )
    mode = "STRICT"
    
    # Tier 2: HYBRID/DISCOVERY
    if (not triples or len(triples) < 2) and row['wa_score'] > 0.35: 
        discovery = await call_extraction_async(
            row['chunk_text'], 
            row['viewpoint_domain'], 
            preds, 
            defs, 
            "DISCOVERY",
            row['record_id'],
            row['chunk_id'],
        )
        if discovery:
            triples.extend(discovery)
            mode = "HYBRID" 

    # Tier 3: HEURISTIC
    triples = heuristic_entity_rescue(row['chunk_text'], row['record_id'], row['viewpoint_domain'], triples)

    # Metadata Stapling & Discovery Registry Collection
    chunk_discovery_log = []
    for t in triples:
        t.update({
            'record_id': row['record_id'], 'chunk_id': row['chunk_id'],
            'domain': row['viewpoint_domain'], 'weight': row['wa_score'],
            'extraction_mode': t.get('extraction_mode', mode),
            'granularity': row['granularity_level']
        })
        if t.get('extraction_mode') == "DISCOVERY":
            chunk_discovery_log.append({
                "domain": row['viewpoint_domain'],
                "found_predicate": t['predicate'],
                "context_snippet": row['chunk_text'][:100]
            })

    return idx, triples, mode, chunk_discovery_log

# --- 5. Main Execution ---
async def run_m2_async():
    wall_start = time.time()
    print("M2_V4.0_Async: Initializing Controlled Parallel Extraction...")
    
    if not os.path.exists(INPUT_FILE):
        sys.exit(f"Missing: {INPUT_FILE}")
    
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    if os.path.exists(DISCOVERY_FILE):
        os.remove(DISCOVERY_FILE)

    df = pd.read_csv(INPUT_FILE)
    total_chunks = len(df)
    completed_count, all_triples, discovery_registry = 0, [], []
    run_stats = {"STRICT": 0, "HYBRID": 0}

    #tasks = [process_chunk(row) for _, row in df.iterrows()]
    
    tasks = [
        asyncio.create_task(process_chunk(idx, row))
        for idx, (_, row) in enumerate(df.iterrows())
    ]
    ordered_results = [None] * total_chunks

    try:
        for task in asyncio.as_completed(tasks):
            idx, chunk_triples, mode, disc_logs = await task
            ordered_results[idx] = (chunk_triples, mode, disc_logs)

            completed_count += 1
            run_stats[mode] += 1
            percent = (completed_count / total_chunks) * 100
            print(f"[{completed_count:03d}/{total_chunks}] {percent:4.1f}% | Mode: {mode:7} | Triples: {len(chunk_triples):2}")

    except Exception:
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    for result in ordered_results:
        chunk_triples, mode, disc_logs = result
        all_triples.extend(chunk_triples)
        discovery_registry.extend(disc_logs)

    # Persistence
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f: json.dump(all_triples, f, indent=2)
    with open(DISCOVERY_FILE, 'w', encoding='utf-8') as f: json.dump(discovery_registry, f, indent=2)
    
    wall_time = time.time() - wall_start

    # Persist M2 telemetry for paper-grade cost reporting
    telemetry_file = os.path.join(PROJECT_ROOT, "output", "M2_telemetry.json")
    with open(telemetry_file, 'w', encoding='utf-8') as f_t:
        json.dump({
            "wall_time_seconds": round(wall_time, 3),
            "api_calls": telemetry["api_calls"],
            "total_prompt_tokens": telemetry["total_prompt_tokens"],
            "total_completion_tokens": telemetry["total_comp_tokens"],
            "cumulative_api_seconds": round(telemetry["total_time"], 3),
            "concurrency_gain": round(telemetry["total_time"] / wall_time, 2) if wall_time > 0 else 0,
            "concurrency_limit": CONCURRENT_LIMIT,
            "strict_runs": run_stats.get("STRICT", 0),
            "hybrid_runs": run_stats.get("HYBRID", 0),
            "total_chunks_processed": total_chunks
        }, f_t, indent=2)

    print(
    f"\n{'='*50}\nDONE. Wall Time: {wall_time:.2f}s | "
    f"Gain: {(telemetry['total_time']/wall_time):.2f}x\n"
    f"Telemetry persisted: {telemetry_file}\n{'='*50}"
    )

if __name__ == "__main__":
    asyncio.run(run_m2_async())