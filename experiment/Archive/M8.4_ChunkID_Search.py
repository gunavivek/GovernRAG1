# --------------------------------------------------------------------------
# MODULE: M8.4_ChunkID_Search_V2.py
# ROLE: Targeted Forensic Audit
# DISSERTATION GOAL: Verify "Traceability" for a specific Source Record.
# --------------------------------------------------------------------------

import networkx as nx
import os
import sys

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M5_FILE = os.path.join(PROJECT_ROOT, "output", "M5_Embedded_Graph.graphml")

# The Target Record ID (The "Nets" Document)
TARGET_RECORD_ID = "5a83093c55429966c78a6b01"

def run_targeted_audit():
    print("================================================================")
    print(f"🕵️ M8.4 V2: TARGETED PROVENANCE SEARCH")
    print(f"   Target Record: {TARGET_RECORD_ID}")
    print(f"   Source Graph:  {M5_FILE}")
    print("================================================================\n")

    if not os.path.exists(M5_FILE):
        print("❌ Graph file not found. Run M5 first.")
        return

    print("Loading GraphML... (Please wait)")
    try:
        G = nx.read_graphml(M5_FILE)
    except Exception as e:
        print(f"Error reading graph: {e}")
        return

    print(f"-> Scanning {G.number_of_edges()} edges for provenance matches...\n")

    # Metrics
    match_count = 0
    unique_chunks = set()
    missing_chunk_id_count = 0

    # Scan Edges
    for u, v, k, data in G.edges(keys=True, data=True):
        # 1. Check if this edge belongs to our Target Record
        # We convert to string to ensure "5abe..." matches even if stored oddly
        current_rid = str(data.get('record_id', 'N/A'))
        
        if current_rid == TARGET_RECORD_ID:
            match_count += 1
            
            # 2. Extract the Chunk ID (Check both keys for safety)
            cid = data.get('chunk_id') or data.get('source_chunk_id')
            
            if cid:
                unique_chunks.add(cid)
                print(f"✅ FOUND | Edge: '{u}' -> '{v}'")
                print(f"         | Predicate: {data.get('predicate')}")
                print(f"         | Chunk ID:  {cid}")
                print("-" * 60)
            else:
                missing_chunk_id_count += 1
                print(f"⚠️  MATCH | Edge: '{u}' -> '{v}'")
                print(f"         | [WARNING] Record ID matches, but Chunk ID is missing.")
                print("-" * 60)

    # Summary Report
    print("\n================================================================")
    print("   📊 AUDIT SUMMARY FOR TARGET RECORD")
    print("================================================================")
    print(f"   Total Evidence Edges Found:   {match_count}")
    print(f"   Unique Chunk IDs Recovered:   {len(unique_chunks)}")
    print(f"   Edges with Missing IDs:       {missing_chunk_id_count}")
    print("----------------------------------------------------------------")
    
    if len(unique_chunks) > 0:
        print("   recovered_chunk_ids = [")
        for c in sorted(list(unique_chunks)):
            print(f"      '{c}',")
        print("   ]")
    else:
        print("   ❌ No Chunk IDs found for this Record.")
    
    print("================================================================")

if __name__ == "__main__":
    run_targeted_audit()