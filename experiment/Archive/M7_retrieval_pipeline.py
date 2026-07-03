# --------------------------------------------------------------------------
# MODULE 7: Hybrid Retrieval Pipeline
# Goal: Implement the core retrieval function (retrieve_hybrid_rag) 
#       that uses Semantic Triangulation and Graph Traversal.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
from typing import List, Tuple, Any

print("--- Starting Module 7: Hybrid Retrieval Pipeline Setup ---")

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = 'text-embedding-004' 
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
RATE_LIMIT_DELAY = 1 # Minimal delay for faster operation (assuming Pro Plan/API stability)

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

INPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M6_Clustered_Graph.gml')
INPUT_CHUNKS_FILE = os.path.join(PROJECT_ROOT, 'output', 'M1_Text_Chunks.csv')


# --- 1. Load Final Indexed Artifacts ---
# This function prepares the vector matrix (X) and metadata (df_meta) for searching.
# NOTE: Streamlit Caching is removed here as M7 is designed to run in the console/M8 test harness.
def load_artifacts() -> Tuple[Any, pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Loads the clustered graph, chunks, and prepares the vector index for search."""
    try:
        G = nx.read_gml(INPUT_GRAPH_FILE)
        df_chunks = pd.read_csv(INPUT_CHUNKS_FILE)
    except FileNotFoundError as e:
        print(f"[ERROR] Required input file not found: {e}.")
        exit()

    # Extract vectors and node metadata from the graph for vector search
    node_metadata = []
    vector_list = []
    
    for node_id, data in G.nodes(data=True):
        # Only nodes with non-zero embeddings are included in the search index
        if 'embedding' in data and data['embedding']:
            node_metadata.append({
                'id': node_id,
                'community_id': data.get('community_id', 'N/A'),
                'type': data.get('node_type', 'DocumentConcept')
            })
            # Convert embedding list back to numpy array
            vector_list.append(np.array(data['embedding']))
            
    # X is the vector matrix for all embedded nodes
    X = np.array(vector_list)
    df_meta = pd.DataFrame(node_metadata)

    return G, df_chunks, df_meta, X

G_indexed, df_chunks, df_meta, X_vectors = load_artifacts()

client = genai.Client(api_key=GEMINI_API_KEY)


# --- 2. Query Concept Extraction (LLM-Guided Filtering) ---
def extract_query_concept(query: str, client: genai.Client) -> str:
    """Uses LLM to extract the core query concept (QC) from the question (Stage 1 Processing)."""
    
    SYSTEM_INSTRUCTION = "You are a Question Parser for a Business Architecture RAG system. Extract only the single most important Information Concept (e.g., 'Policy', 'Agreement', 'Customer Feedback') from the question. Respond only with the concept name."
    
    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    
    try:
        time.sleep(RATE_LIMIT_DELAY) # Rate limit protection
        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=[query],
            config=config,
        )
        return response.text.strip()
    except Exception as e:
        print(f"  [ERROR] LLM Query extraction failed: {e}")
        return "Unknown Concept"


# --- 3. Core Hybrid Retrieval Function ---
def retrieve_hybrid_rag(query: str, client: genai.Client, G: nx.DiGraph, df_chunks: pd.DataFrame, df_meta: pd.DataFrame, X: np.ndarray) -> (List[str], str):
    """
    Implements the M7 Hybrid Retrieval: Vector Similarity + Graph Triangulation.
    Returns the top context chunks and the conceptual path.
    """
    
    # --- Step A: Query Concept Extraction (Stage 1 Processing) ---
    query_concept_name = extract_query_concept(query, client)
    
    if query_concept_name == "Unknown Concept" or not query_concept_name:
        return ["Error: Could not extract primary concept from query. RAG search aborted."], "Extraction Failed"

    # --- Step B: Vector Search (Stage 2 Processing: Alignment) ---
    
    # Embed the extracted Query Concept to find its vector space location
    try:
        # FIX: Correct API usage for embedding the single query concept
        query_embedding = client.models.embed_content(model=EMBEDDING_MODEL, content=[query_concept_name]).embedding
        query_vector = np.array(query_embedding)
    except Exception as e:
        return [f"Error: Embedding failed for query concept. {e}"], "Embedding Failed"
    
    # Calculate similarity to ALL indexed nodes
    similarity = cosine_similarity(query_vector.reshape(1, -1), X)[0]
    
    # Find the index of the closest node (The semantic starting point)
    closest_node_index = similarity.argmax()
    closest_node_id = df_meta.iloc[closest_node_index]['id']
    
    # Identify the relevant Community ID (for filtering)
    target_community_id = df_meta.iloc[closest_node_index]['community_id']
    
    print(f"Found Query Concept: '{query_concept_name}'")
    print(f"Starting Node: {closest_node_id} (Community: {target_community_id})")

    # --- Step C: Graph Traversal (Triangulation and Path Collection) ---
    
    concept_path = []
    chunk_ids_to_retrieve = set()
    
    # Use Breadth-First Search (BFS) to traverse outward from the closest node
    nodes_to_visit = {closest_node_id}
    visited_nodes = set()
    
    # Hop limited to 3 for efficiency in the prototype
    for hop in range(3): 
        next_nodes = set()
        
        for u in nodes_to_visit:
            if u in visited_nodes: continue
            visited_nodes.add(u)
            
            # Check for Triangulation and BIZBOK Reference Edges
            for _, v, data in G.edges(u, data=True):
                relationship = data.get('relationship')
                
                # Prioritize M4 links (Triangulation) and M3.5 links (BIZBOK Structure)
                if relationship in ['IS_ALIGNED_WITH', 'ADAPTED_FROM', 'RELATED_TO']:
                    concept_path.append(f"({u}) --[{relationship}]--> ({v})")
                    
                    # Collect chunk ID from the edge (M2 data)
                    chunk_id = data.get('source_chunk_id', -1)
                    if chunk_id != -1:
                        chunk_ids_to_retrieve.add(chunk_id)

                    # Apply Community Filtering: Only traverse within the target community 
                    # OR if it's a Reference Concept (since BIZBOK links cross community bounds)
                    if v in G.nodes: # Ensure node exists in the indexed graph
                        v_meta = df_meta[df_meta['id'] == v]
                        
                        if not v_meta.empty:
                            v_meta = v_meta.iloc[0]
                            is_ref_concept = v_meta['type'] == 'ReferenceConcept'
                            is_in_target_community = v_meta['community_id'] == target_community_id
                            
                            if is_ref_concept or is_in_target_community:
                                next_nodes.add(v)
        
        nodes_to_visit = next_nodes
        if not nodes_to_visit: break # Stop if no more valid paths found

    # --- Step D: Context Assembly (Retrieve Raw Chunks) ---
    
    if not chunk_ids_to_retrieve:
        return [f"No chunk evidence found during traversal."], "\n".join(concept_path)

    # Retrieve the unique chunk text using the collected IDs
    context_chunks = df_chunks[df_chunks['chunk_id'].isin(chunk_ids_to_retrieve)]
    
    # Final context is the union of all found chunk texts, sorted for coherence
    final_context = context_chunks.sort_values(by='chunk_id')['chunk_text'].tolist()

    return final_context, "\n".join(concept_path)


# --- Example Execution Block (For Testing) ---
if __name__ == "__main__":
    
    # The input question is defined here
    test_query = "What are the rules for retiring Platform 2.0?"
    
    print("\n--- Testing Hybrid RAG Retrieval (M7) ---")
    
    # Pass all loaded artifacts to the function
    context, path = retrieve_hybrid_rag(test_query, client, G_indexed, df_chunks, df_meta, X_vectors)

    print(f"\nQUERY: {test_query}")
    print("\n--- CONCEPTUAL PATH (Evidence Chain) ---")
    if path:
        print(path)
    else:
        print("No graph path found.")

    print("\n--- RETRIEVED CONTEXT CHUNKS ---")
    for i, chunk in enumerate(context):
        print(f"Chunk {i+1}: {chunk[:100]}...")
    
    print("\nNote: Module 8 will take this context and generate the final answer.")