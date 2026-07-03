# --------------------------------------------------------------------------
# MODULE: Q3_Unit_Test_Record_Isolation.py
# PURPOSE: Debugging - Force Q3 to search ONLY inside one specific document.
# --------------------------------------------------------------------------

import os
import json
import networkx as nx
import numpy as np
from dotenv import load_dotenv
from google import genai
from sklearn.metrics.pairwise import cosine_similarity

# --- CONFIGURATION ---
TARGET_RECORD_ID = "5a83093c55429966c78a6b01"
TEST_QUESTION = "Were both Léopold Eyharts and Ulrich Walter a General in the French Air Force?"

# Setup
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
M5_GRAPH = "output/M5_Embedded_Graph.graphml"
EMBEDDING_MODEL = "text-embedding-004"

def get_embedding(text):
    try:
        resp = client.models.embed_content(model=EMBEDDING_MODEL, contents=[text])
        return resp.embeddings[0].values
    except: return None

def run_unit_test():
    print(f"--- 🧪 Q3 UNIT TEST: ISOLATING RECORD {TARGET_RECORD_ID} ---")
    
    # 1. Load the Full Graph
    if not os.path.exists(M5_GRAPH):
        print("❌ M5 Graph missing.")
        return
    G = nx.read_graphml(M5_GRAPH)
    
    # 2. ISOLATE THE SUBGRAPH (The "Filter")
    print(f"Filtering graph for Record ID: {TARGET_RECORD_ID}...")
    
    relevant_edges = []
    for u, v, k, data in G.edges(keys=True, data=True):
        # Check if edge belongs to this record
        rid = data.get('record_id') or data.get('source_chunk_id') or ""
        
        # Loose string matching to be safe
        if TARGET_RECORD_ID in str(rid):
            relevant_edges.append((u, v, k, data))

    if not relevant_edges:
        print("❌ NO EDGES FOUND for this Record ID. Check M8.4 Audit again.")
        print("   (Did M5 actually ingest the Space Exploration chunks?)")
        return

    print(f"✅ Found {len(relevant_edges)} edges belonging to this record.")

    # 3. RUN VECTOR SEARCH ON SUBGRAPH
    print(f"\n🔎 Searching for: '{TEST_QUESTION}'")
    q_vec = get_embedding(TEST_QUESTION)
    
    hits = []
    for u, v, k, data in relevant_edges:
        if 'embedding' not in data: continue
        
        try:
            edge_vec = json.loads(data['embedding'])
            sim = cosine_similarity([q_vec], [edge_vec])[0][0]
            
            # We lower the threshold for debugging to see even weak matches
            if sim > 0.25: 
                hits.append({
                    "source": u, "target": v, 
                    "predicate": data.get('predicate'),
                    "chunk_id": data.get('chunk_id'),
                    "score": sim,
                    "provenance": data.get('provenance', 'N/A')
                })
        except: continue

    # 4. REPORT RESULTS
    hits.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n--- 🎯 RESULTS: Top Chunks for this Question ---")
    if not hits:
        print("No semantic matches found in this record.")
    
    found_eyharts = False
    found_walter = False

    for i, hit in enumerate(hits[:10]):
        print(f"[{i+1}] Score: {hit['score']:.4f} | Chunk: {hit['chunk_id']}")
        print(f"    Fact: ({hit['source']}) --[{hit['predicate']}]--> ({hit['target']})")
        
        # Check if we found our specific targets
        if "Eyharts" in hit['source'] or "Eyharts" in hit['target']: found_eyharts = True
        if "Walter" in hit['source'] or "Walter" in hit['target']: found_walter = True

    print("\n--- 🕵️ FORENSIC DIAGNOSIS ---")
    if found_eyharts and found_walter:
        print("✅ SUCCESS: The system found BOTH entities in the graph edges.")
    elif not found_eyharts and not found_walter:
        print("❌ FAILURE: The system found NEITHER entity.")
        print("   REASON: The 'Space Exploration' chunks (Chunk 00 & 01) are missing from M5.")
        print("   FIX: Re-run M3 (Graph Builder) ensuring it ingests ALL chunks from M1.")
    else:
        print("⚠️ PARTIAL: Found one but not the other.")

if __name__ == "__main__":
    run_unit_test()