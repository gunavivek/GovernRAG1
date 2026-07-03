import os
import json
import time 
import networkx as nx 
import spacy
import numpy as np # NEW IMPORT for vectors
from sklearn.metrics.pairwise import cosine_similarity # NEW IMPORT for search
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from google import genai 
from google.genai import types 
from dotenv import load_dotenv 

# --- CONFIGURATION AND SETUP ---
load_dotenv() 
LLM_CLIENT_MODEL = "gpt-3.5-turbo" 
EMBEDDING_MODEL = 'text-embedding-004' # Same model used in M5
EMBEDDING_DIM = 768
M4_HYBRID_GRAPH_PATH = "output/M4_Hybrid_Graph.gml" 
RATE_LIMIT_DELAY = 1
# THRESHOLD: Define a threshold for high-confidence match vs adaptive match
HIGH_CONFIDENCE_THRESHOLD = 0.90 


# Initialize Global NLP Resources
try:
    NLP = spacy.load("en_core_web_sm") 
except OSError:
    print("Error: spaCy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'.")
    exit()

# --- Utility Functions for LLM Communication and Vector Loading ---

def get_llm_client() -> Optional[OpenAI]:
    """Initializes and returns the OpenAI client (used only for query expansion)."""
    try:
        client = OpenAI() 
        return client
    except Exception:
        return None
        
def load_graph_data(gml_path: str = M4_HYBRID_GRAPH_PATH) -> Tuple[List[str], np.ndarray]:
    """Loads ALL M4 node IDs and their embeddings for vector search."""
    if not os.path.exists(gml_path):
        return [], np.array([])
    try:
        G = nx.read_gml(gml_path)
        node_ids = []
        vectors = []
        
        for node_id, data in G.nodes(data=True):
             if 'embedding' in data and data['embedding']:
                node_ids.append(node_id)
                # Convert embedding list back to numpy array
                vectors.append(np.array(data['embedding']))
                
        return node_ids, np.array(vectors)
    except Exception as e:
        print(f"Error loading M4 Graph GML for vectors: {e}. Cannot perform mapping.")
        return [], np.array([])

def get_embedding_vector(text: str) -> np.ndarray:
    """Uses the M5 embedding model directly to vectorize the query concept."""
    if not text.strip():
        return np.zeros(EMBEDDING_DIM, dtype=np.float32) 
        
    try:
        # Note: We must re-initialize the client here if not passed in, as embedding is separate from chat
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # FINAL CRITICAL FIX: Use 'model' and 'content' for standard modern API syntax
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, 
            content=[text]
        )
        # Access the vector using attribute indexing
        vector = response.embedding.values
        return np.array(vector, dtype=np.float32)
        
    except Exception as e:
        # print(f"  [CRITICAL API FAILURE] Embedding failed for query: {text[:30]}... Error: {e}")
        return np.zeros(EMBEDDING_DIM, dtype=np.float32) 


# --- CORE FUNCTION: VECTOR-BASED ADAPTIVE MAPPING (Step 3) ---
def map_concepts_to_graph_nodes_vector(concepts: List[str], graph_node_ids: List[str], X_vectors: np.ndarray) -> List[Dict[str, str]]:
    """
    Step 3: Maps extracted linguistic concepts to the closest Node ID in the M4 Graph using Cosine Similarity.
    """
    if not graph_node_ids or X_vectors.size == 0:
        return []

    mapped_concepts = []
    
    for raw_concept in concepts:
        
        # 1. Embed the raw concept
        query_vector = get_embedding_vector(raw_concept)
        
        # Skip if embedding failed (returns zero vector)
        if np.all(query_vector == 0):
            continue 
            
        # 2. Calculate similarity to all M4 nodes
        similarity_scores = cosine_similarity(query_vector.reshape(1, -1), X_vectors)[0]
        
        # Find the best match
        closest_node_index = similarity_scores.argmax()
        max_similarity = similarity_scores[closest_node_index]
        closest_node_id = graph_node_ids[closest_node_index]
        
        # 3. Determine mapping status based on threshold (Adaptive Logic)
        if max_similarity >= HIGH_CONFIDENCE_THRESHOLD:
            mapping_status = "IS_ALIGNED_WITH" # Direct, high-confidence match
        else:
            mapping_status = "ADAPTED_FROM" # Fuzzy match, uses closest node as adaptive ancestor

        # Add result to the signature list
        mapped_concepts.append({
            "raw_concept": raw_concept,
            "mapped_node_id": closest_node_id,
            "mapping_status": mapping_status,
            "similarity_score": float(f"{max_similarity:.4f}") # For debugging/logging
        })
        
    return mapped_concepts


# --- Main M7.2 Logic ---

def extract_signature(
    m7_1_output: Dict[str, Any], 
    llm_client: Optional[OpenAI],
    graph_node_ids: List[str], # All M4 graph nodes
    X_vectors: np.ndarray # All M4 embeddings
) -> Dict[str, Any]:
    """
    M7.2 Core Function: Transforms M7.1 output into the final M4-enhanced search signature.
    """
    q_text = m7_1_output["question_text"]
    history = m7_1_output.get("history", []) 
    intents = m7_1_output.get("predicted_intents", [])
    
    primary_intent = intents[0]['intent'] if intents else "Extractive"
    
    # 1. Query Rewriting for Context
    rewritten_query = rewrite_query_for_context_llm(llm_client, q_text, history)
    
    # 2. Linguistic Processing (Extract raw concepts to be mapped)
    doc = NLP(rewritten_query)
    concepts_to_map = set()
    
    # Extract key nouns and proper nouns for M4 graph mapping
    search_targets = {"NOUN", "PROPN"}
    for token in doc:
        if token.pos_ in search_targets and not token.is_stop and len(token.text) > 2:
            concepts_to_map.add(token.lemma_.lower()) 

    # 3. M4 Graph-Mediated Concept Mapping (CORE NEW VECTOR STEP)
    # The output is a list of structured mappings
    mapped_concepts = map_concepts_to_graph_nodes_vector(list(concepts_to_map), graph_node_ids, X_vectors)
    
    # 4. Query Expansion
    expanded_queries = generate_expanded_queries_llm(llm_client, rewritten_query)

    # 5. Intent-Based Refinement (Hardcoded Corrections for better retrieval)
    is_numerical_query = any(k in q_text.lower() for k in ["year", "quarter", "percent", "cost", "number", "time", "reduction"])
    if is_numerical_query and primary_intent != "Quantitative":
        primary_intent = "Quantitative" 

    # 6. Final Signature Assembly
    return {
        "question_id": m7_1_output["question_id"],
        "question_text": q_text,
        "primary_intent": primary_intent,
        "rewritten_query": rewritten_query,
        "search_signature": {
            "mapped_concepts": mapped_concepts, # The final list of structured mappings
            "raw_concepts": list(concepts_to_map)
        },
        "expanded_queries": expanded_queries
    }

# --- Driver Execution ---

def run_m7_2_extractor(input_file: str = "output/M7_1_intents.jsonl", output_file: str = "output/M7_2_signatures.jsonl"):
    """Main function to load M7.1 output, process signatures, and save results."""
    
    # 1. Initialize LLM client and load M4 Graph Nodes (All Concepts)
    llm_client = get_llm_client() 
    graph_node_ids, X_vectors = load_graph_concepts() 
    
    if not graph_node_ids:
        print("CRITICAL WARNING: M4 Graph not found or empty. Cannot perform standardization.")
        return
        
    # 2. Load M7.1 output
    try:
        m7_1_results = load_m7_1_output(input_file)
    except FileNotFoundError as e:
        print(e)
        return
    
    # Create output directory and clear old output file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    if os.path.exists(output_file):
        os.remove(output_file)

    print(f"--- Running M7.2: Adaptive Graph Signature Extractor on {len(m7_1_results)} questions ---")
    
    all_signatures = []
    
    for m7_1_item in m7_1_results:
        # Process the question into a signature
        signature = extract_signature(m7_1_item, llm_client, graph_node_ids, X_vectors)
        all_signatures.append(signature)
        
        # Write results immediately to the JSONL file
        with open(output_file, 'a', encoding='utf-8') as outfile:
            outfile.write(json.dumps(signature) + '\n')
            
        print(f"Processed {signature['question_id']} | Primary: {signature['primary_intent']}")
        print(f"  Nodes Mapped: {len(signature['search_signature']['mapped_concepts'])}")
        
    print(f"\nSuccessfully generated {len(all_signatures)} search signatures. Results saved to {output_file}")
    
if __name__ == '__main__':
    # NOTE: You will need to manually create a dummy M7_1_intents.jsonl file 
    #       for this script to run successfully for testing.
    run_m7_2_extractor()