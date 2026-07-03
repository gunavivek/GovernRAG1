# --------------------------------------------------------------------------
# MODULE 3.3: Governed Concept Definition Augmentation (M3.3_V2.1)
# STRATEGY: Attribute Promotion & Provenance Stapling
# GOAL: Resolve CH-001 by migrating source_chunk_id from Edges to Nodes.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
import time 
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup and Configuration ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
LLM_MODEL = "gemini-2.0-flash-lite" 
RATE_LIMIT_DELAY = 1.5 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_Gov_Knowledge_Graph.gml') 
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3.3_Gov_Augmented_Graph.gml') 

# --- 1. Robust Parsing Logic ---
def extract_json_object(resp_text):
    """Robustly extracts a dictionary even if wrapped in markdown."""
    try:
        clean_text = re.sub(r'```json\s*|```', '', resp_text).strip()
        data = json.loads(clean_text)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else None
    except:
        return None

# --- 2. Governed Synthesis Function ---
def get_governed_definition(node_name, context_triples, domain, glossary, predicates):
    if not context_triples:
        return {"generated_definition": "Context too sparse.", "confidence_score": 10}

    system_instruction = f"""
    You are a Business Architecture Auditor for the {domain} domain.
    Synthesize a single-sentence definition for '{node_name}' based on its graph context.
    Constraints: Predicates: {predicates}; Glossary: {glossary}.
    Output ONLY JSON: {{"generated_definition": "...", "confidence_score": 0-100}}
    """
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[f"Triples for {node_name}:\n" + "\n".join(context_triples)],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return extract_json_object(response.text)
    except:
        return None

# --- 3. Main Execution (With Attribute Promotion) ---
if __name__ == "__main__":
    if not os.path.exists(INPUT_GRAPH):
        exit(f"[CRITICAL ERROR] Graph missing: {INPUT_GRAPH}")

    G = nx.read_gml(INPUT_GRAPH)
    print(f"--- Starting M3.3_V2.1: Augmenting {G.number_of_nodes()} Nodes ---")

    for node in list(G.nodes):
        # A. Collect all edges to gather context and metadata
        in_edges = list(G.in_edges(node, data=True))
        out_edges = list(G.edges(node, data=True))
        all_edges = in_edges + out_edges

        # B. PROVENANCE RECOVERY: Extract source_chunk_id from edges
        # This is where we recover the 'Golden Thread'
        source_ids = set()
        context_triples = []
        domain, glossary, predicates = "General", "{}", "[]"

        for u, v, data in all_edges:
            # 1. Capture Provenance
            sid = data.get('source_chunk_id')
            if sid: source_ids.add(sid)
            
            # 2. Capture Governance Context
            domain = data.get('domain', domain)
            glossary = data.get('glossary', glossary)
            predicates = data.get('predicates', predicates)
            
            # 3. Build context for LLM
            context_triples.append(f"({u}) --[{data.get('relationship')}]--> ({v})")

        print(f"Augmenting: {node} (Sources: {len(source_ids)})")
        
        # C. LLM SYNTHESIS
        result = get_governed_definition(node, context_triples, domain, glossary, predicates)
        
        # D. GOVERNED STAPLING: Promote edge metadata to node level
        if result:
            G.nodes[node]['generated_definition'] = result.get('generated_definition', 'Synthesis failed.')
            G.nodes[node]['confidence_score'] = int(result.get('confidence_score', 0))
        else:
            G.nodes[node]['generated_definition'] = "Data Synthesis Error."
            G.nodes[node]['confidence_score'] = 0

        # CRITICAL FIX: Explicitly persist source_chunk_id to the node
        if source_ids:
            # Join multiple sources if it's a cross-chunk concept, otherwise take the one
            G.nodes[node]['source_chunk_id'] = "; ".join(list(source_ids))
        
        G.nodes[node]['augmentation_source'] = "M3.3_V2.1_GOV_DISAMBIGUATION"
        G.nodes[node]['node_type'] = "DocumentConcept"
        
        time.sleep(RATE_LIMIT_DELAY)

    # Final Persistence
    nx.write_gml(G, OUTPUT_GRAPH)
    print(f"\n[PHD SUCCESS] M3.3_V2.1 Complete. Node attributes promoted for M9 Audit.")