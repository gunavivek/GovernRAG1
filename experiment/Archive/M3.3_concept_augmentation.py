# --------------------------------------------------------------------------
# MODULE 3.3: Concept Definition Augmentation
# Goal: Augment Document Concept nodes in M3 graph with LLM-generated 
#       definitions and confidence scores for semantic parity.
# FIX: Renamed to M3.3. Added final summary print.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
import time 
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Configuration for Rate Limiting ---
RATE_LIMIT_DELAY = 7  # Seconds: (60 seconds / 10 requests per minute) + safety buffer

print("--- Starting Module 3.3: Concept Definition Augmentation ---")

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite")

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# CHANGE 1: Input is M3 output.
INPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_Knowledge_Graph.gml') 
# CHANGE 2: Output is the new M3.3 Augmented Graph.
OUTPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_3_Augmented_Graph.gml') 


# --- 1. Define LLM Prompt and Output Schema for Definition Generation ---
SYSTEM_INSTRUCTION = """
You are a Knowledge Graph Concept Auditor. Your task is to generate a concise, synthesized definition for a central concept based ONLY on the list of facts (triples) connected to it. 
After generating the definition, provide a numerical confidence score (0-100) reflecting how well the provided facts allow for a clear, complete definition.

Output MUST be valid JSON.
"""

OUTPUT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "generated_definition": types.Schema(type=types.Type.STRING, description="The synthesized, single-sentence definition for the central concept."),
        "confidence_score": types.Schema(type=types.Type.INTEGER, description="Confidence score from 0 to 100."),
    },
    required=["generated_definition", "confidence_score"],
)

# --- 2. Core Augmentation Function ---
def augment_concept_definition(G: nx.DiGraph, concept_name: str, client: genai.Client):
    """Retrieves local context and uses the LLM to generate a definition and confidence score."""
    
    # 2.1 Retrieve Local Context (Connected Triples)
    context_triples = []
    
    # NOTE: NetworkX methods are robust and operate on the current state of G.
    for u, v, data in G.edges(concept_name, data=True): # Outgoing edges (where node_name is source)
        context_triples.append(f"({u}) {data.get('relationship', 'CONNECTS')} ({v})")
        
    for u, v, data in G.in_edges(concept_name, data=True): # Incoming edges (where node_name is target)
        context_triples.append(f"({u}) {data.get('relationship', 'CONNECTS')} ({v})")
        
    if not context_triples:
        return {"generated_definition": "Context too sparse for definition.", "confidence_score": 10}

    # 2.2 Construct Prompt
    context_text = "\n".join(context_triples)
    user_prompt = f"""
    Concept to define: {concept_name}
    Facts (Triples):
    {context_text}
    """
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=OUTPUT_SCHEMA,
    )
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=[user_prompt],
            config=config,
        )
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        print(f"  [ERROR] LLM Definition generation failed for {concept_name}. Error: {e}")
        return {"generated_definition": "LLM failure or JSON parsing error.", "confidence_score": 0}


# --- 3. Main Execution Logic ---
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("\n[SETUP ERROR] GEMINI_API_KEY not found.")
        exit()
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Load the M3 Knowledge Graph (unaugmented)
    try:
        G = nx.read_gml(INPUT_GRAPH_FILE)
    except FileNotFoundError:
        print(f"\n[ERROR] Input graph not found: {INPUT_GRAPH_FILE}. Please run M3_graph_construction.py first.")
        exit()
    
    print(f"Loaded M3 Graph: {G.number_of_nodes()} nodes.")
    
    nodes_to_augment = list(G.nodes)
    augmented_count = 0
    
    for i, node_name in enumerate(nodes_to_augment):
        
        # Check if the node already has a definition (e.g., from M3.5)
        # Since M3 has no definition attribute, this is primarily for future robustness
        if G.nodes[node_name].get('definition', 'N/A') == 'N/A':
            print(f"Augmenting Concept {i+1}/{len(nodes_to_augment)}: '{node_name}'")
            
            # Call the augmentation function
            augmentation_data = augment_concept_definition(G, node_name, client)
            
            # Store the new attributes back into the graph node
            G.nodes[node_name]['generated_definition'] = augmentation_data['generated_definition']
            G.nodes[node_name]['confidence_score'] = augmentation_data['confidence_score']
            
            print(f"  -> Score: {augmentation_data['confidence_score']}. Definition: {augmentation_data['generated_definition'][:50]}...")

            augmented_count += 1
            
            # --- RATE LIMITER INJECTION ---
            print(f"  [RATE LIMITER] Pausing for {RATE_LIMIT_DELAY} seconds...")
            time.sleep(RATE_LIMIT_DELAY) 
            # --- END RATE LIMITER ---

    # --- Save the Augmented Graph ---
    try:
        output_dir = os.path.join(PROJECT_ROOT, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        nx.write_gml(G, OUTPUT_GRAPH_FILE)
        print(f"\n[SUCCESS] Module 3.3 successfully completed!")
        print(f"Total concepts augmented: {augmented_count} out of {G.number_of_nodes()} nodes.")
        print(f"Augmented Graph saved to: {OUTPUT_GRAPH_FILE}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save graph. Reason: {e}")