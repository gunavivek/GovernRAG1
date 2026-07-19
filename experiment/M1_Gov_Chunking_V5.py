# --------------------------------------------------------------------------
# MODULE 1: M1_Gov_Chunking_V5_1.py
# ARCHITECTURE: Poly-Ontological Coverage + Negative Constraint Governance
# DISSERTATION VALUE: Proves Structural Relativity (Focus Mode)
# --------------------------------------------------------------------------
import pandas as pd
import json
import os
import re
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key: sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=120_000))  # 120s/call ceiling (approved 2026-07-19)
LLM_MODEL = "gemini-3.1-flash-lite"  # repointed 2026-07-19 twice: 3-flash-preview degraded (504), then 2.5-flash-lite withdrawn (404); 3.1-flash-lite = GA pin, probe OK 4.4s; approved, .bakM

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MANIFEST = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")

# --- CONFIGURATION ---
PHYSICAL_WINDOW_CHARS = 30000
ORPHAN_WINDOW_CHARS = 6000
MAX_ORPHAN_CHUNKS_PER_SLICE = 24
MAX_JSON_ATTEMPTS = 3
JSON_RETRY_DELAY_SECONDS = 2

def parse_partitioner_json(resp_text: str) -> list:
    """
    Parse LLM JSON defensively.
    Handles markdown fences, raw control characters, and trailing junk.
    """
    clean = re.sub(r"```json\s*|```", "", resp_text).strip()

    candidates = [
        clean,
        re.sub(r"[\x00-\x1F]+", " ", clean),
    ]

    decoder = json.JSONDecoder()
    last_error = None

    for candidate in candidates:
        try:
            obj = json.loads(candidate)
            if isinstance(obj, list):
                return obj
            raise ValueError(f"Expected JSON array, got {type(obj).__name__}")
        except Exception as e:
            last_error = e
            try:
                obj, _ = decoder.raw_decode(candidate)
                if isinstance(obj, list):
                    return obj
                raise ValueError(f"Expected JSON array, got {type(obj).__name__}")
            except Exception as e2:
                last_error = e2

    raise ValueError(f"Malformed JSON payload: {last_error}")

def resolution_based_partitioner(text_segment: str, domain_profile: dict, z_score: float) -> list:
    """
    Partitions text using 'Focus Mode'.
    Applies Negative Constraints to prevent splitting irrelevant text.
    """
    domain_name = domain_profile['domain']
    rules = domain_profile['rules']
    
    # --- GOVERNANCE MAPPING ---
    target_depth = rules.get("search_exit_depth", 4)
    predicates = rules.get("relational_predicates", [])
    disambiguation = rules.get("disambiguation_keys", {})

    # --- THE V5.1 FIX: EXCLUSIONARY LOGIC ---
    if target_depth >= 4:
        # High Complexity: We want detail, but ONLY for this domain.
        res_mode = "ATOMIC FOCUS (Exclusionary)"
        instruction = f"""
        1. SCAN the text for concepts strictly related to '{domain_name}' and these actions: {predicates}.
        2. POSITIVE CONSTRAINT (Relevant Text): If a sentence IS related to {domain_name}, SPLIT IT aggressively. Isolate specific facts.
        3. NEGATIVE CONSTRAINT (Irrelevant Text): If a section is NOT related to {domain_name}, DO NOT SPLIT IT. Merge it into a single summary block.
        """
    elif target_depth == 3:
        res_mode = "STANDARD RESOLUTION"
        instruction = f"Split naturally. Group related sentences, but split when the sub-topic shifts based on {predicates}."
    else:
        # Low Complexity: Broad strokes only.
        res_mode = "THEMATIC RESOLUTION"
        instruction = "Group text broadly. Only split when the major theme changes completely."

    discovery_mode = "EXPLORATORY" if z_score >= 2.5 else "STRICT"
    max_chunks_for_slice = MAX_ORPHAN_CHUNKS_PER_SLICE if z_score >= 2.5 else 999

    prompt = f"""
    You are a Domain-Aware Text Chunking Architect working within the {domain_name} business domain.
    
    CONFIGURATION:
    - MODE: {discovery_mode}
    - STRATEGY: {res_mode}
    
    TASK: Partition the text into 'Knowledge Pockets' using ONLY the lens of {domain_name}.
    
    CRITICAL GOVERNANCE LAWS:
    {instruction}
    
    VOCABULARY DEFENSE:
    Use these definitions to resolve ambiguity: {disambiguation}.
    
    OUTPUT FORMAT:
    - Return a valid JSON Array of strings.
    - Content must be RAW text from the source (no summarizing, just grouping).
    - For this single input slice, return AT MOST {max_chunks_for_slice} strings.
    - Merge adjacent same-theme sentences rather than creating excessive micro-chunks.
    
    <TEXT>
    {text_segment}
    </TEXT>
    """
    
    last_error = None

    for attempt in range(1, MAX_JSON_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                ),
            )

            result = parse_partitioner_json(response.text)

            clean_chunks = [str(x).strip() for x in result if str(x).strip()]
            if z_score >= 2.5 and len(clean_chunks) > MAX_ORPHAN_CHUNKS_PER_SLICE:
                raise ValueError(
                    f"Oversized orphan output for {domain_name}: "
                    f"{len(clean_chunks)} chunks > {MAX_ORPHAN_CHUNKS_PER_SLICE}"
                )

            if not clean_chunks:
                raise ValueError(f"Empty chunk list returned for {domain_name}.")

            return clean_chunks

        except Exception as e:
            last_error = e
            if attempt == MAX_JSON_ATTEMPTS:
                raise RuntimeError(f"Chunking failed for {domain_name}: {e}") from e
            time.sleep(JSON_RETRY_DELAY_SECONDS)

def run_m1_v5_1_focus_mode():
    if not os.path.exists(INPUT_MANIFEST): 
        sys.exit("Manifest missing.")
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    final_chunks = []
    print(f"M1_V5.1: Initializing Poly-Ontological Ingestion (Focus Mode)...")

    with open(INPUT_MANIFEST, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            contract = json.loads(line)
            rid = contract["record_id"]
            z_score = contract.get("z_score", 0.0)
            
            # 1. Forensic Stripping
            text = contract["source_text"]
            evidence = text.split(" | Document: ", 1)[1] if " | Document: " in text else text
            evidence = re.sub(r"\s+", " ", evidence).strip()
            
            # 2. Total Coverage Loop: Iterate ALL domains
            all_domains = sorted(contract["governance_profile"], key=lambda x: x['affinity_weight'], reverse=True)
            
            for view in all_domains:
                domain_name = view['domain']
                
                # 3. Physical Safety Slicing
                window_chars = ORPHAN_WINDOW_CHARS if z_score >= 2.5 else PHYSICAL_WINDOW_CHARS
                text_len = len(evidence)
                physical_slices = [evidence[k:k+window_chars] for k in range(0, text_len, window_chars)]
                
                view_chunks = []
                for si, p_slice in enumerate(physical_slices):
                    c = resolution_based_partitioner(p_slice, view, z_score)
                    view_chunks.extend(c)
                    print(f"  [slice {si+1}/{len(physical_slices)}] {domain_name}: {len(view_chunks)} chunks", flush=True)
                
                # 4. Stapling & ID Generation
                for j, pocket_text in enumerate(view_chunks):
                    # Create View-Specific ID
                    safe_dom = domain_name.upper().replace(" ", "_").replace("&", "AND")[:15]
                    
                    final_chunks.append({
                        "record_id": rid,
                        "chunk_id": f"CHNK_{rid[-4:]}_{safe_dom}_{j:02d}",
                        "viewpoint_domain": domain_name,
                        "chunk_text": pocket_text,
                        "wa_score": view['affinity_weight'],
                        "granularity_level": view["rules"].get("search_exit_depth", 4),
                        "z_score": z_score,
                        "predicates": json.dumps(view["rules"].get("relational_predicates", [])),
                        "disambiguation": json.dumps(view["rules"].get("disambiguation_keys", {}))
                    })
                
                print(f"Record {rid} | View: {domain_name} (Wa:{view['affinity_weight']:.4f}) | Chunks: {len(view_chunks)}")

    # Export
    pd.DataFrame(final_chunks).to_csv(OUTPUT_FILE, index=False)
    print(f"\nM1_V5.1 COMPLETE. Focus Mode Artifact: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_m1_v5_1_focus_mode()