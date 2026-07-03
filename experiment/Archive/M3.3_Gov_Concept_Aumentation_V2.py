# --------------------------------------------------------------------------
# MODULE 3.3: Governed Concept Definition Augmentation (M3.3_V2 - FINAL)
# Goal: Achieve Semantic Parity via Governed Disambiguation.
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
RATE_LIMIT_DELAY = 2  

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_Gov_Knowledge_Graph.gml') 
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3.3_Gov_Augmented_Graph.gml') 

metrics = {"augmented_count": 0, "start_time": time.time(), "confidence_scores": []}

# --- 1. Robust Parsing Logic ---
def extract_json_object(resp_text):
    """PHD RIGOR: Robustly extracts a dictionary even if wrapped in lists or markdown."""
    try:
        # 1. Clean Markdown
        clean_text = re.sub(r'```json\s*|```', '', resp_text).strip()
        data = json.loads(clean_text)
        
        # 2. Unpack if list
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
            
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None

# --- 2. Governed Synthesis Function ---
def get_governed_definition(G, node_name, domain, glossary, predicates):
    context_triples = []
    for u, v, data in G.edges(node_name, data=True):
        context_triples.append(f"({u}) --[{data.get('relationship')}]--> ({v})")
    for u, v, data in G.in_edges(node_name, data=True):
        context_triples.append(f"({u}) --[{data.get('relationship')}]--> ({v})")

    if not context_triples:
        return {"generated_definition": "Context too sparse.", "confidence_score": 10}

    system_instruction = f"""
    You are a Business Architecture Auditor for the {domain} domain.
    Synthesize a single-sentence definition for '{node_name}'.
    Constraints: Relational Predicates: {predicates}; Disambiguation Glossary: {glossary}.
    Output ONLY a valid JSON object: {{"generated_definition": "...", "confidence_score": 0-100}}
    """
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[f"Facts for {node_name}:\n" + "\n".join(context_triples)],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return extract_json_object(response.text)
    except:
        return None

# --- 3. Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(INPUT_GRAPH):
        exit(f"[CRITICAL ERROR] Graph missing: {INPUT_GRAPH}")

    G = nx.read_gml(INPUT_GRAPH)
    print(f"--- Starting M3.3_V2: Augmenting {G.number_of_nodes()} Nodes ---")

    for node in list(G.nodes):
        connected_edges = list(G.edges(node, data=True)) + list(G.in_edges(node, data=True))
        
        # Ingest Governance Packet [cite: 4, 6]
        domain, glossary, predicates = "General", "{}", "[]"
        if connected_edges:
            edge_data = connected_edges[0][2]
            domain = edge_data.get('domain', domain)
            glossary = edge_data.get('glossary', glossary)
            predicates = edge_data.get('predicates', predicates)

        print(f"Augmenting: {node}")
        result = get_governed_definition(G, node, domain, glossary, predicates)
        
        # Staple Attributes 
        if result:
            G.nodes[node]['generated_definition'] = result.get('generated_definition', 'Synthesis failed.')
            G.nodes[node]['confidence_score'] = int(result.get('confidence_score', 0))
        else:
            G.nodes[node]['generated_definition'] = "Data Synthesis Error."
            G.nodes[node]['confidence_score'] = 0

        G.nodes[node]['augmentation_source'] = "M3.3_V2_GOV_DISAMBIGUATION"
        G.nodes[node]['node_type'] = "DocumentConcept"
        
        metrics["augmented_count"] += 1
        metrics["confidence_scores"].append(G.nodes[node]['confidence_score'])
        time.sleep(RATE_LIMIT_DELAY)

    nx.write_gml(G, OUTPUT_GRAPH)
    
    duration = time.time() - metrics["start_time"]
    avg_score = sum(metrics["confidence_scores"]) / len(metrics["confidence_scores"])
    
    print("\n" + "="*50)
    print(f"M3.3_V2: SUCCESS | Mean Score: {avg_score:.2f}/100 | Time: {duration:.2f}s")
    print("="*50 + "\n")