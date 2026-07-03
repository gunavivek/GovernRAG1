# --------------------------------------------------------------------------
# MODULE 1: Domain-Governed Partitioning with Dissertation Metrics (M1_V4)
# Goal: Partition text semantically and capture processing telemetry.
# --------------------------------------------------------------------------
import pandas as pd
import json
import os
import sys
import time
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup and Instrumentation ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
LLM_MODEL = "gemini-2.0-flash-lite"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_MANIFEST = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")

# Metrics Registry for Dissertation Evaluation 
metrics = {
    "total_records": 0,
    "total_chunks": 0,
    "llm_calls": 0,
    "start_time": 0,
    "end_time": 0,
    "record_latencies": []
}

def domain_partitioner(text: str, domain: str, predicates: list, glossary: dict) -> List[str]:
    """Uses Domain Knowledge to find semantic boundaries (M1_V4 Logic)."""
    metrics["llm_calls"] += 1
    
    prompt = f"""
    You are a Business Architecture Analyst. Partition the following text into semantically distinct 'Knowledge Pockets' 
    based on the domain: {domain}.
    
    Constraints:
    1. Every pocket must be centered around a specific concept or relationship valid in {domain}.
    2. Use the provided Predicates to identify relationship boundaries: {predicates}.
    3. Refer to the Glossary for domain-specific definitions: {glossary}.
    4. Output ONLY a valid JSON array of strings.
    """
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[prompt, text],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1),
        )
        return json.loads(response.text)
    except Exception:
        return [text]

def run_m1_v4_instrumented():
    if not os.path.exists(INPUT_MANIFEST):
        sys.exit("[CRITICAL ERROR] D5 Manifest missing.")

    metrics["start_time"] = time.time()
    final_chunks = []

    with open(INPUT_MANIFEST, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            rec_start = time.time()
            contract = json.loads(line)
            metrics["total_records"] += 1
            
            pockets = domain_partitioner(
                contract["source_text"], 
                contract["domain"], 
                contract["governance_constraints"]["predicates"],
                contract["governance_constraints"]["glossary"]
            )
            
            for j, pocket_text in enumerate(pockets):
                final_chunks.append({
                    "record_id": contract["record_id"],
                    "chunk_id": f"CHNK_{i:04d}_{j:02d}",
                    "domain": contract["domain"],
                    "chunk_text": pocket_text,
                    "predicates": json.dumps(contract["governance_constraints"]["predicates"]),
                    "glossary": json.dumps(contract["governance_constraints"]["glossary"]),
                    "depth_limit": contract["governance_constraints"]["depth"]
                })
            
            metrics["record_latencies"].append(time.time() - rec_start)
            time.sleep(0.5) # Rate limit mitigation

    metrics["end_time"] = time.time()
    metrics["total_chunks"] = len(final_chunks)
    
    # Export Artifact
    pd.DataFrame(final_chunks).to_csv(OUTPUT_FILE, index=False)
    
    # --- DISSERTATION METRICS PRINTOUT ---
    total_duration = metrics["end_time"] - metrics["start_time"]
    avg_latency = sum(metrics["record_latencies"]) / metrics["total_records"]
    expansion_ratio = metrics["total_chunks"] / metrics["total_records"]

    print("\n" + "="*50)
    print("M1_V4: GOVERNED PARTITIONING METRICS")
    print("="*50)
    print(f"Total Processing Time:     {total_duration:.2f} seconds")
    print(f"Total Records Ingested:    {metrics['total_records']}")
    print(f"Total LLM Calls Made:      {metrics['llm_calls']}")
    print(f"Total Semantic Chunks:     {metrics['total_chunks']}")
    print(f"Mean Latency per Record:   {avg_latency:.2f} seconds")
    print(f"Chunk Expansion Ratio:     {expansion_ratio:.2f}x")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_m1_v4_instrumented()