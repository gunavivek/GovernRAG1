import os
import sys
import networkx as nx
from pyvis.network import Network
import json

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_Embedded_Graph.graphml')

def diagnose_graph_ids(G):
    """Prints a summary of IDs found in the graph to help the user."""
    found_ids = set()
    for _, _, data in G.edges(data=True):
        rid = data.get('record_id') or data.get('chunk_id') or data.get('source_chunk_id')
        if rid: found_ids.add(str(rid))
    
    if not found_ids:
        print("\n[🚨 CRITICAL] No Record IDs found in any edge attributes!")
        print("Your M5 vectorization script likely failed to persist the 'record_id'.")
    else:
        print(f"\n[📊 INFO] Found {len(found_ids)} unique Record IDs in the graph.")
        print(f"Sample IDs available: {list(found_ids)[:3]}")

def visualize_graph():
    if not os.path.exists(INPUT_FILE):
        print(f"\n[CRITICAL] Input file missing: {INPUT_FILE}")
        return

    print("Loading GraphML from disk... (Large files may take a moment)")
    Full_G = nx.read_graphml(INPUT_FILE)
    diagnose_graph_ids(Full_G)

    # CLI or Interactive ID selection
    target_id = sys.argv[1] if len(sys.argv) > 1 else input("\nEnter Record ID or 'global': ").strip()

    if target_id.lower() in ["global", "1", "all"]:
        G = Full_G
        OUTPUT_HTML = os.path.join(PROJECT_ROOT, 'output', 'M5.5_Global_Graph.html')
    else:
        # Filter Logic
        relevant_edges = []
        for u, v, k, data in Full_G.edges(keys=True, data=True):
            rid = data.get('record_id') or data.get('chunk_id') or data.get('source_chunk_id')
            # Use 'in' for fuzzy matching if the user provides a short ID
            if rid and (str(target_id) in str(rid)):
                relevant_edges.append((u, v, k))
        
        if not relevant_edges:
            print(f"❌ ERROR: No matches for ID '{target_id}'")
            return
        
        G = Full_G.edge_subgraph(relevant_edges).copy()
        OUTPUT_HTML = os.path.join(PROJECT_ROOT, 'output', f'M5.5_Record_{target_id[:8]}.html')

    # Setup PyVis with Dissertation-Ready Dark Theme
    net = Network(height="95vh", width="100%", bgcolor="#1a1a1a", font_color="white", heading="Governed Knowledge Extraction")
    
    # Node/Edge Styling Logic
    for node, data in G.nodes(data=True):
        # Color coding by Node Type
        n_type = data.get('type', 'Concept')
        color_map = {"Organization": "#ff7675", "Person": "#55efc4", "Location": "#74b9ff", "Event": "#a29bfe"}
        node_color = color_map.get(n_type, "#dfe6e9")
        
        net.add_node(node, label=node, color=node_color, size=25, title=f"Type: {n_type}")

    for u, v, data in G.edges(data=True):
        net.add_edge(u, v, label=data.get('predicate', 'related'), color="#636e72", arrows="to")

    net.save_graph(OUTPUT_HTML)
    print(f"✅ Visualization saved to: {OUTPUT_HTML}")

if __name__ == "__main__":
    visualize_graph()