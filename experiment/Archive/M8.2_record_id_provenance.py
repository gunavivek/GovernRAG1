import os
import networkx as nx

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# The Pipeline Stages to Audit
STAGES = [
    ("M3", "M3_Knowledge_Graph.graphml"),
    ("M3.3", "M3_3_Augmented_Graph.graphml"),
    ("M4", "M4_Hybrid_Graph.graphml"),
    ("M5", "M5_Embedded_Graph.graphml")
]

def analyze_provenance():
    print("--- 🕵️‍♂️ STARTING PROVENANCE FORENSICS ---")
    
    for stage_name, filename in STAGES:
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        print(f"\n[{stage_name}] Checking: {filename}...")
        
        if not os.path.exists(filepath):
            print(f"  ❌ File not found!")
            continue
            
        try:
            # Load Graph
            G = nx.read_graphml(filepath)
            
            # Count Edges
            total_edges = G.number_of_edges()
            edges_with_rid = 0
            sample_rid = "None"
            
            # Iterate edges to find 'record_id'
            # Note: GraphML keys are string attributes
            for u, v, data in G.edges(data=True):
                # Check for direct key or 'provenance' context
                if 'record_id' in data:
                    edges_with_rid += 1
                    sample_rid = data['record_id']
                # Sometimes it might be nested if JSON serialization went wrong
                elif 'source_chunk_id' in data: # Fallback check
                    edges_with_rid += 1
                    sample_rid = data['source_chunk_id']

            # Calculate Health
            health = 0
            if total_edges > 0:
                health = (edges_with_rid / total_edges) * 100
            
            print(f"  -> Total Edges: {total_edges}")
            print(f"  -> Edges with 'record_id': {edges_with_rid}")
            print(f"  -> Provenance Health: {health:.1f}%")
            print(f"  -> Sample ID: {sample_rid}")
            
            # Diagnostic Logic
            if health == 0:
                print("  🚨 CRITICAL FAILURE: Provenance completely wiped.")
            elif health < 50 and stage_name in ["M4", "M5"]:
                print("  ⚠️ NOTE: Drop expected in M4/M5 (Governance edges don't have IDs).")
            else:
                print("  ✅ HEALTHY.")
                
        except Exception as e:
            print(f"  ❌ Error reading graph: {e}")

if __name__ == "__main__":
    analyze_provenance()