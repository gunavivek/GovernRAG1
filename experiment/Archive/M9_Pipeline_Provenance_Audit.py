# --------------------------------------------------------------------------
# PHD MODULE 9: End-to-End Causal Integrity Auditor (V2.4)
# FIX: Resolved NameError by promoting CHAIN to Global Scope.
# --------------------------------------------------------------------------
import os
import time
import networkx as nx
import pandas as pd
import json
import argparse
from datetime import datetime

# --- 0. Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
REPORT_PATH = os.path.join(OUTPUT_DIR, 'M9_E2E_Audit_Report.txt')

# Define the Global Chain of Causality
CHAIN_CONFIG = [
    {"id": "M1", "path": os.path.join(OUTPUT_DIR, 'M1_Governed_Chunks.csv'), "type": "csv"},
    {"id": "M2", "path": os.path.join(OUTPUT_DIR, 'M2_Extracted_Triples.json'), "type": "json"},
    {"id": "M3", "path": os.path.join(OUTPUT_DIR, 'M3_Gov_Knowledge_Graph.gml'), "type": "gml"},
    {"id": "M3.3", "path": os.path.join(OUTPUT_DIR, 'M3.3_Gov_Augmented_Graph.gml'), "type": "gml"},
    {"id": "M4", "path": os.path.join(OUTPUT_DIR, 'M4_Gov_Hybrid_Graph.gml'), "type": "gml"},
    {"id": "M5", "path": os.path.join(OUTPUT_DIR, 'M5_Gov_Embedded_Graph.gml'), "type": "gml"},
    {"id": "M6", "path": os.path.join(OUTPUT_DIR, 'M6_Gov_Clustered_Graph.gml'), "type": "gml"}
]

def audit_e2e_pipeline(active_chain):
    print(f"\n--- Starting M9 Audit: {active_chain[0]['id']} to {active_chain[-1]['id']} ---")
    
    results = []
    prev_mtime = 0
    prev_stage_name = "N/A"

    for i, stage in enumerate(active_chain):
        if not os.path.exists(stage["path"]):
            results.append({"Stage": stage["id"], "Status": "MISSING", "Time": "N/A", "Sequence": "N/A", "Retention_%": 0, "Records": 0})
            continue
        
        # 1. Temporal Check
        mtime = os.path.getmtime(stage["path"])
        readable_time = time.strftime('%H:%M:%S', time.localtime(mtime))
        is_sequence_valid = True if i == 0 or mtime >= (prev_mtime - 1) else False
        
        # 2. Semantic Integrity Check
        unique_records = set()
        total_items = 0
        items_with_source = 0

        if stage["type"] == "csv":
            df = pd.read_csv(stage["path"])
            total_items = len(df)
            if 'record_id' in df.columns:
                unique_records = set(df['record_id'].unique())
                items_with_source = total_items

        elif stage["type"] == "json":
            with open(stage["path"], 'r') as f:
                data = json.load(f)
                total_items = len(data)
                for item in data:
                    rid = item.get('record_id') or item.get('source_chunk_id', '').split('_')[0]
                    if rid:
                        unique_records.add(rid)
                        items_with_source += 1

        elif stage["type"] == "gml":
            G = nx.read_gml(stage["path"])
            total_items = G.number_of_nodes()
            for n, d in G.nodes(data=True):
                sid = d.get('source_chunk_id')
                if sid:
                    items_with_source += 1
                    unique_records.add(str(sid).split('_')[0])

        retention_score = round((items_with_source / total_items) * 100, 2) if total_items > 0 else 0
        
        status = "PASS"
        if not is_sequence_valid: status = "BACKDATED"
        if retention_score < 100: status = "LEAK"

        results.append({
            "Stage": stage["id"],
            "Time": readable_time,
            "Sequence": "OK" if is_sequence_valid else f"ERR: < {prev_stage_name}",
            "Retention_%": retention_score,
            "Records": len(unique_records),
            "Status": status
        })

        prev_mtime = mtime
        prev_stage_name = stage["id"]

    return pd.DataFrame(results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="M9 Causal Auditor Gatekeeper")
    parser.add_argument("--until", type=str, choices=["M1", "M2", "M3", "M3.3", "M4", "M5", "M6"],
                        help="The last stage you want to audit.")
    args = parser.parse_args()

    # Determine which stages to audit
    active_chain = CHAIN_CONFIG
    if args.until:
        limit_idx = next(i for i, s in enumerate(CHAIN_CONFIG) if s["id"] == args.until)
        active_chain = CHAIN_CONFIG[:limit_idx + 1]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_audit = audit_e2e_pipeline(active_chain)

    # Log results
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        def log(msg):
            print(msg); f.write(msg + "\n")

        log("="*95)
        log(f"PHD E2E CAUSAL AUDIT | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"SCOPE: {active_chain[0]['id']} -> {active_chain[-1]['id']}")
        log("="*95)
        log(df_audit.to_string(index=False))
        log("="*95)

    print(f"\nAudit Report: {REPORT_PATH}")