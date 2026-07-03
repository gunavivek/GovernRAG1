# --------------------------------------------------------------------------
# MODULE 3: Knowledge Graph Construction
# Goal: Load M2 triples and construct the core Knowledge Graph structure
#       using NetworkX, saving it as M3_Knowledge_Graph.gml.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
import networkx as nx

print("--- Starting Module 3: Knowledge Graph Construction ---")

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, '../output', 'M2_Extracted_Triples.json')
OUTPUT_FILE = os.path.join(BASE_DIR, '../output', 'M3_Knowledge_Graph.gml')
OUTPUT_EDGES_CSV = os.path.join(BASE_DIR, '../output', 'M3_Graph_Edges.csv')


# --- Core Graph Construction Function ---
def build_and_save_graph():
    """Loads triples, constructs a NetworkX graph, and saves the graph and its edge list."""
    
    # 1. Load Extracted Triples from M2
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            triples_list = json.load(f)
    except FileNotFoundError:
        print(f"\n[ERROR] Input artifact not found: {INPUT_FILE}. Please run M2_extraction.py first.")
        return False
    except json.JSONDecodeError:
        print(f"\n[ERROR] Error decoding {INPUT_FILE}. Check the file for valid JSON format.")
        return False

    # 2. Initialize the Graph (Directed Graph - DiGraph)
    G = nx.DiGraph()
    
    # List to store edge data for saving as CSV
    edge_data_list = []

    # 3. Populate the Graph with Nodes and Edges
    for i, triple in enumerate(triples_list):
        subject = triple['subject']
        predicate = triple['predicate']
        object_ = triple['object']
        source_chunk_id = triple.get('source_chunk_id', 'N/A')
        
        # ADDED FIX: Pass subject and object_ as positional arguments (u and v)
        G.add_edge(
            subject,  # u_of_edge (Source)
            object_,  # v_of_edge (Target)
            key=i, # Unique identifier for this edge
            relationship=predicate, 
            source_chunk_id=source_chunk_id
        )
        
        # Collect edge data for CSV output
        edge_data_list.append({
            'source': subject,
            'target': object_,
            'relationship': predicate,
            'source_chunk_id': source_chunk_id
        })
        
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    # 4. Save the Graph (GML Format)
    nx.write_gml(G, OUTPUT_FILE)
    print(f"Knowledge Graph structure saved to: {OUTPUT_FILE}")

    # 5. Save the Edge List (CSV Format for easy inspection)
    df_edges = pd.DataFrame(edge_data_list)
    df_edges.to_csv(OUTPUT_EDGES_CSV, index=False)
    print(f"Graph Edge list saved to: {OUTPUT_EDGES_CSV}")
    
    return True

# --- EXECUTION ---
if __name__ == "__main__":
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.join(BASE_DIR, '../output')
    os.makedirs(output_dir, exist_ok=True)
    
    if build_and_save_graph():
        print("\n[SUCCESS] Module 3 successfully completed: Core Knowledge Graph is built.")