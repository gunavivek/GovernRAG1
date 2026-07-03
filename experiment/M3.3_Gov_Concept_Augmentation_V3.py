# --------------------------------------------------------------------------
# MODULE 3.3: M3_3_Gov_Definition_Augmenter_V3.py
# ARCHITECTURE: Weighted Concept Synthesis for Multi-Graphs
# DISSERTATION GOAL: Generate Definitions based on Epistemic Authority (Weights)
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
import time 
import re
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-3-flash-preview" 
RATE_LIMIT_DELAY = 1.0 

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# INPUT: The GraphML file from M3_V3
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_Knowledge_Graph.graphml') 
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_3_Augmented_Graph.graphml') 

# --- 1. Robust Parsing Logic ---
def extract_json_object(resp_text):
    try:
        clean_text = re.sub(r'```json\s*|```', '', resp_text).strip()
        data = json.loads(clean_text)
        if isinstance(data, list) and len(data) > 0: data = data[0]
        return data if isinstance(data, dict) else None
    except:
        return None

# --- 2. Weighted Synthesis Function ---
def generate_weighted_definition(node_name: str, context_triples: list):
    """
    Uses the LLM to synthesize a definition, prioritizing high-weight facts.
    """
    if not context_triples:
        return {"definition": "Context too sparse.", "confidence": 0}

    # We embed the weights into the prompt so the LLM knows what to trust.
    context_str = "\n".join(context_triples)

    system_instruction = f"""
    You are a Semantic Graph Auditor.
    TASK: Synthesize a single-sentence definition for the concept '{node_name}'.
    
    INPUT DATA: A list of facts (Edges) with 'Weights' (0.0-1.0).
    
    CRITICAL RULE: 
    - Give HIGH PRIORITY to facts with High Weights (>0.4).
    - Give LOW PRIORITY to facts with Low Weights (<0.2).
    - If facts conflict, the High Weight fact is the Truth.
    
    OUTPUT JSON: {{"definition": "The synthesized text...", "confidence": 0-100}}
    """
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[f"Weighted Facts for '{node_name}':\n{context_str}"],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        result = extract_json_object(response.text)
        if not result:
            raise ValueError(f"Invalid definition payload for node: {node_name}")
        return result
    except Exception as e:
        raise RuntimeError(f"M3.3 definition generation failed for node '{node_name}': {e}") from e

# --- 3. Main Execution ---
def run_m3_3_weighted_augmentation():
    if not os.path.exists(INPUT_GRAPH):
        sys.exit(f"[CRITICAL] Input Graph missing: {INPUT_GRAPH}")

    if os.path.exists(OUTPUT_GRAPH):
        os.remove(OUTPUT_GRAPH)

    print("M3.3_V3.0: Loading Multi-Graph for Weighted Augmentation...")
    # Load GraphML (MultiDiGraph)
    G = nx.read_graphml(INPUT_GRAPH)
    print(f"-> Loaded {G.number_of_nodes()} Nodes and {G.number_of_edges()} Edges.")

    augmented_count = 0
    start_time = time.time()

    # Iterate over all nodes
    for i, node in enumerate(list(G.nodes)):
        # 1. Gather Weighted Context (Handling MultiDiGraph)
        context_triples = []
        
        # Outgoing Edges
        for u, v, key, data in G.edges(node, keys=True, data=True):
            w = data.get('weight', 0.1)
            dom = data.get('domain', 'Gen')
            rel = data.get('predicate', 'related')
            context_triples.append(f"-> connects to '{v}' via '{rel}' [Domain: {dom} | Weight: {w}]")

        # Incoming Edges
        for u, v, key, data in G.in_edges(node, keys=True, data=True):
            w = data.get('weight', 0.1)
            dom = data.get('domain', 'Gen')
            rel = data.get('predicate', 'related')
            context_triples.append(f"<- is connected from '{u}' via '{rel}' [Domain: {dom} | Weight: {w}]")

        # 2. Skip if isolated
        if not context_triples: continue

        # 3. Generate Definition
        result = generate_weighted_definition(node, context_triples)
        
        # 4. Staple to Node
        G.nodes[node]['definition'] = result.get('definition', 'Synthesis Failed')
        G.nodes[node]['confidence'] = int(result.get('confidence', 0))
        augmented_count += 1
            
            # Concise Log
        if i % 10 == 0:
            print(f"[{i}/{G.number_of_nodes()}] Defined '{node}' (Conf: {result.get('confidence')})")
        
        # Rate Limit
        time.sleep(RATE_LIMIT_DELAY)

    # 5. Save Artifact
    nx.write_graphml(G, OUTPUT_GRAPH)
    
    print("\n" + "="*50)
    print(f"M3.3_V3.0 COMPLETE. Augmented {augmented_count} Nodes.")
    print(f"Artifact: {OUTPUT_GRAPH}")
    print("="*50)

if __name__ == "__main__":
    run_m3_3_weighted_augmentation()


# VERIFY GRAPH NODE COUNTS
#import networkx as nx
#g = nx.read_graphml(r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG\output\M3_3_Augmented_Graph.graphml")
#print("Nodes:", g.number_of_nodes())
#print("Edges:", g.number_of_edges())
#
#
# VERIFY NODE ATTRIBUTES
#sample_nodes = list(g.nodes(data=True))[:10]
#for name, attrs in sample_nodes:
#    print(name, "=>", {
#        "definition": attrs.get("definition"),
#        "confidence": attrs.get("confidence")
#    })
#
# VERIFY MISSING DEFINITIONS
# import networkx as nx
# g = nx.read_graphml(r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG\output\M3_3_Augmented_Graph.graphml")
# missing_defs = [n for n, a in g.nodes(data=True) if not a.get("definition")]
# print("Nodes missing definition:", len(missing_defs))
# print(missing_defs[:20])