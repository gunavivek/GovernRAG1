# --------------------------------------------------------------------------
# MODULE 8.1: M8.1_Gov_E2E_Auditor_V3.py
# ARCHITECTURE: Causal Integrity & Hypothesis Verification
# DISSERTATION GOAL: Audits the "Golden Thread" of Provenance & Weights
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
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
REPORT_PATH = os.path.join(OUTPUT_DIR, 'M9_Audit_Report.txt')

# The Validated Pipeline Chain (Note: M6 is excluded as it was retired)
CHAIN_CONFIG = [
    {"id": "M1", "path": os.path.join(OUTPUT_DIR, 'M1_Governed_Chunks.csv'), "type": "csv"},
    {"id": "M2", "path": os.path.join(OUTPUT_DIR, 'M2_Extracted_Triples.json'), "type": "json"},
    {"id": "M3", "path": os.path.join(OUTPUT_DIR, 'M3_Knowledge_Graph.graphml'), "type": "graphml"},
    {"id": "M3.3", "path": os.path.join(OUTPUT_DIR, 'M3_3_Augmented_Graph.graphml'), "type": "graphml"},
    {"id": "M4", "path": os.path.join(OUTPUT_DIR, 'M4_Hybrid_Graph.graphml'), "type": "graphml"},
    {"id": "M5", "path": os.path.join(OUTPUT_DIR, 'M5_Embedded_Graph.graphml'), "type": "graphml"}
]

def analyze_graphml_stage(stage_id, filepath):
    """Deep inspection of GraphML artifacts for PhD Hypotheses attributes."""
    try:
        # Robust Reader
        G = nx.read_graphml(filepath)
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()
        
        # PhD Hypothesis Checks
        has_weights = False
        has_definitions = False
        has_alignment = False
        has_vectors = False
        
        # Check Edge Weights (H3 Interoperability)
        if edge_count > 0:
            sample_edge = list(G.edges(data=True))[0][2]
            if 'weight' in sample_edge: has_weights = True
            
        # Check Node Attributes (H2 Extensibility)
        if node_count > 0:
            sample_node = list(G.nodes(data=True))[0][1]
            # Check for definitions (M3.3)
            if 'definition' in sample_node or 'generated_definition' in sample_node: has_definitions = True
            # Check for alignment (M4)
            if 'alignment_status' in sample_node: has_alignment = True
            # Check for vectors (M5)
            if 'embedding' in sample_node: has_vectors = True

        return {
            "Nodes": node_count,
            "Edges": edge_count,
            "Weighted_Edges": "YES" if has_weights else "NO",
            "Defined_Nodes": "YES" if has_definitions else "NO",
            "Aligned_Nodes": "YES" if has_alignment else "NO",
            "Vectorized": "YES" if has_vectors else "NO"
        }
    except Exception as e:
        return {"Error": str(e)}

def audit_e2e_pipeline():
    print(f"\n--- Starting M9_V3.0 Audit: Causal Integrity Check ---")
    
    audit_log = []
    prev_mtime = 0
    
    for stage in CHAIN_CONFIG:
        entry = {"Stage": stage["id"], "File": os.path.basename(stage["path"])}
        
        # 1. Existence Check
        if not os.path.exists(stage["path"]):
            entry["Status"] = "MISSING"
            audit_log.append(entry)
            continue
            
        # 2. Temporal Check
        mtime = os.path.getmtime(stage["path"])
        entry["Time"] = time.strftime('%H:%M:%S', time.localtime(mtime))
        entry["Sequence"] = "OK" if mtime >= (prev_mtime - 5) else "STALE/BACKDATED" # 5s buffer
        prev_mtime = mtime

        # 3. Content Logic Check
        if stage["type"] == "csv":
            df = pd.read_csv(stage["path"])
            entry["Count"] = f"{len(df)} Chunks"
            # M1 Check: Are domains present?
            if 'viewpoint_domain' in df.columns: entry["Validation"] = "Poly-Ontological"
            
        elif stage["type"] == "json":
            with open(stage["path"], 'r') as f:
                data = json.load(f)
            entry["Count"] = f"{len(data)} Triples"
            # M2 Check: Are weights present?
            if len(data) > 0 and 'weight' in data[0]: entry["Validation"] = "Weighted Edges"
            
        elif stage["type"] == "graphml":
            stats = analyze_graphml_stage(stage["id"], stage["path"])
            entry["Count"] = f"{stats.get('Nodes', 0)} N / {stats.get('Edges', 0)} E"
            
            # Specific Hypothesis Checks per stage
            if stage["id"] == "M3":
                entry["Validation"] = f"Topology: {stats.get('Weighted_Edges')} Weights"
            elif stage["id"] == "M3.3":
                entry["Validation"] = f"Semantics: {stats.get('Defined_Nodes')} Definitions"
            elif stage["id"] == "M4":
                entry["Validation"] = f"Governance: {stats.get('Aligned_Nodes')} Alignment"
            elif stage["id"] == "M5":
                entry["Validation"] = f"Vectors: {stats.get('Vectorized')} Embeddings"

        entry["Status"] = "PASS"
        audit_log.append(entry)

    # Output formatting
    df_results = pd.DataFrame(audit_log)
    
    # Console Output
    print("\n" + "="*90)
    print(f"PHD PIPELINE AUDIT REPORT | {datetime.now().strftime('%Y-%m-%d')}")
    print("="*90)
    print(df_results.to_string(index=False))
    print("="*90)
    
    # File Output
    with open(REPORT_PATH, 'w') as f:
        f.write("M9_V3.0 GOVERNED PIPELINE AUDIT REPORT\n")
        f.write(df_results.to_string(index=False))
        
    print(f"\nAudit saved to: {REPORT_PATH}")

if __name__ == "__main__":
    audit_e2e_pipeline()