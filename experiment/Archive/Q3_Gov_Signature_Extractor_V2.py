import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup & Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# DISSERTATION FILE PATHS
INPUT_FILE = "output/Q2_intents.jsonl"
OUTPUT_FILE = "output/Q3_signatures.jsonl"
D4_REGISTRY_PATH = "output/D4_Registry_Discovered.json"

def load_governed_glossary(domain: str) -> str:
    """
    DYNAMIC HANDSHAKE: Loads terms from D4 to anchor Signature (H1).
    Ensures data is a dictionary to prevent TypeError: string indices must be integers.
    """
    if not os.path.exists(D4_REGISTRY_PATH):
        print(f"[Q3][WARN] D4 Registry missing at {D4_REGISTRY_PATH}")
        return ""
    
    try:
        with open(D4_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            # DESERIALIZATION: json.load(f) returns a dictionary
            registry = json.load(f)
        
        # Access domain laws specifically engineered in the D-Pipeline
        laws = registry.get(domain, {})
        
        # TYPE CHECK: Ensure 'laws' is a dict before attempting list comprehension
        if isinstance(laws, dict):
            packet = laws.get('governance_packet', [])
            # Extract governed predicates for Logic Gate 3 (Epistemic Proof)
            predicates = [p['predicate'] for p in packet if isinstance(p, dict) and 'predicate' in p]
            return ", ".join(predicates)
        
        return ""
    except Exception as e:
        print(f"[Q3][ERROR] Glossary handshake failed for {domain}: {e}")
        return ""

def call_llm_signature(record: Dict[str, Any], glossary: str) -> Dict[str, Any]:
    """
    Logic Gate 3: Extract Q-Layer using ONLY Governed Vocabulary (H3).
    Gold Answer Invisibility: The 'response' field is kept INVISIBLE.
    """
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "concept": {"type": "STRING"},
            "attribute": {"type": "STRING"},
            "value": {"type": "STRING", "nullable": True},
            "constraints": {
                "type": "OBJECT",
                "properties": {
                    "time_horizon": {"type": "STRING", "nullable": True},
                    "segment": {"type": "STRING", "nullable": True},
                    "geography": {"type": "STRING", "nullable": True}
                }
            },
            "metric_hints": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["concept", "attribute", "value", "constraints", "metric_hints"]
    }

    # CONDITIONING: Mandating use of BIZBOK-aligned vocabulary
    prompt = f"""
**SYSTEM:** Extract a GraphRAG Signature (Q-Layer).
**DOMAIN:** {record.get('primary_domain')}
**GOVERNED VOCABULARY:** {glossary}

**QUESTION:** "{record.get('question')}"

**TASK:** Extract Concept/Attribute/Value using the Governed Vocabulary where possible.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=response_schema,
            temperature=0.0 
        )
    )
    return json.loads(response.text)

def main():
    print("--- Q3_v2: Governed Signature Extractor (Processing All Records) ---")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input {INPUT_FILE} not found.")
        return

    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        
        # STREAMING: Fixes the 'one record' issue by iterating through all lines
        for line in infile:
            line = line.strip()
            if not line: continue
            
            try:
                record = json.loads(line)
                
                # Dynamic Handshake with D4 Registry (H1 Anchor)
                glossary = load_governed_glossary(record.get('primary_domain', 'General'))
                
                # Build the Q-Layer Signature (H3 Triangulation)
                signature = call_llm_signature(record, glossary)
                
                # Maintain Golden Thread and passthrough metadata
                record["Q_layer"] = signature
                record["q3_notes"] = f"Governed signature extracted for: {record.get('primary_domain')}"
                
                outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
                print(f"Processed Record {count}: {record.get('id', 'N/A')}")
            except Exception as e:
                print(f"[Q3_v2][ERROR] Failed processing record: {e}")

    print(f"--- SUCCESS: Wrote {count} signatures to {OUTPUT_FILE} ---")

if __name__ == "__main__":
    main()