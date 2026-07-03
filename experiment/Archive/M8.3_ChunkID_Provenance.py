# --------------------------------------------------------------------------
# MODULE: M8.3_ChunkID_Provenance_V3.py
# ROLE: Forensic Analysis & Reporting
# DISSERTATION OUTPUT: 
#    1. Prints detailed audit to Terminal (Immediate Feedback)
#    2. Saves 'output/M8.3_Provenance_Report.csv' (Dissertation Artifact)
# --------------------------------------------------------------------------

import os
import json
import networkx as nx
import pandas as pd
import csv
from datetime import datetime

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
REPORT_FILE = os.path.join(OUTPUT_DIR, 'M8.3_Provenance_Report.csv')

PIPELINE_STAGES = [
    ("M1",   "Ingestion",      "M1_Governed_Chunks.csv",       "csv"),
    ("M2",   "Extraction",     "M2_Extracted_Triples.json",    "json"),
    ("M3",   "Graph Const.",   "M3_Knowledge_Graph.graphml",   "graphml"),
    ("M5",   "Vectorization",  "M5_Embedded_Graph.graphml",    "graphml")
]

def analyze_stage(filepath, ftype):
    """Returns a tuple: (Set of Chunk IDs, Set of Record IDs, Sample ID)"""
    chunk_ids = set()
    record_ids = set()
    sample_id = "None"
    
    if not os.path.exists(filepath):
        return (set(), set(), "File Missing")

    try:
        if ftype == 'csv':
            df = pd.read_csv(filepath)
            if 'chunk_id' in df.columns: chunk_ids.update(df['chunk_id'].astype(str))
            if 'record_id' in df.columns: record_ids.update(df['record_id'].astype(str))
            
        elif ftype == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data if isinstance(data, list) else []
                for item in items:
                    if 'chunk_id' in item: chunk_ids.add(str(item['chunk_id']))
                    if 'record_id' in item: record_ids.add(str(item['record_id']))
                    if 'triples' in item:
                        for t in item['triples']:
                            if 'chunk_id' in t: chunk_ids.add(str(t['chunk_id']))

        elif ftype == 'graphml':
            G = nx.read_graphml(filepath)
            for u, v, k, data in G.edges(keys=True, data=True):
                # Check all provenance keys
                if 'chunk_id' in data: chunk_ids.add(str(data['chunk_id']))
                if 'source_chunk_id' in data: chunk_ids.add(str(data['source_chunk_id']))
                if 'record_id' in data: record_ids.add(str(data['record_id']))

    except Exception as e:
        print(f"  [Error] {e}")

    # Capture a sample ID for validation
    if len(chunk_ids) > 0:
        sample_id = list(chunk_ids)[0]
        
    return chunk_ids, record_ids, sample_id

def run_audit_and_report():
    print("================================================================")
    print("       🧬 M8.3 V3: PROVENANCE REPORT GENERATION 🧬       ")
    print(f"       Saving to: {REPORT_FILE}")
    print("================================================================")
    
    report_rows = []
    
    # Track M1 baseline for survival calculation
    m1_chunk_count = 0
    m1_chunk_ids = set()
    
    for stage, name, filename, ftype in PIPELINE_STAGES:
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # --- 1. Analyze ---
        c_ids, r_ids, sample = analyze_stage(filepath, ftype)
        
        # --- 2. Calculate Statistics ---
        if stage == "M1":
            m1_chunk_count = len(c_ids)
            m1_chunk_ids = c_ids
            survival_rate = 100.0
            attrition = 0
        else:
            # Calculate how many of the ORIGINAL M1 chunks are still here
            surviving = len(c_ids.intersection(m1_chunk_ids))
            survival_rate = (surviving / m1_chunk_count * 100) if m1_chunk_count > 0 else 0.0
            attrition = m1_chunk_count - surviving

        # --- 3. Print to Terminal (Immediate Feedback) ---
        print(f"\n[{stage}] Checking {name}...")
        print(f"  -> 📦 Physical Chunks found: {len(c_ids)}")
        print(f"  -> 📄 Logical Records found: {len(r_ids)}")
        print(f"  -> 🛡️  Global Survival Rate:  {survival_rate:.1f}%")
        if len(c_ids) > 0:
            print(f"     (Sample Chunk ID: {sample})")
        
        # --- 4. Build CSV Row ---
        row = {
            "Stage": stage,
            "Module Name": name,
            "Filename": filename,
            "Physical_Chunks_Found": len(c_ids),
            "Logical_Records_Found": len(r_ids),
            "Global_Survival_Rate_pct": f"{survival_rate:.1f}%",
            "Attrition_Count": attrition,
            "Sample_ID": sample,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        report_rows.append(row)

    # --- 5. Write CSV File ---
    keys = ["Stage", "Module Name", "Filename", "Physical_Chunks_Found", 
            "Logical_Records_Found", "Global_Survival_Rate_pct", 
            "Attrition_Count", "Sample_ID", "Timestamp"]
            
    with open(REPORT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(report_rows)

    print("\n" + "="*64)
    print(f"✅ Report Generated: {REPORT_FILE}")
    print("="*64)

if __name__ == "__main__":
    run_audit_and_report()