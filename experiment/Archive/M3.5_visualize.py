# --------------------------------------------------------------------------
# MODULE 3.5 VISUALIZATION: Graph Plot Generation
# Goal: Load the M3.5 Reference Ontology (GML) and save a static PNG
#       visualization for display in the Streamlit dashboard.
# --------------------------------------------------------------------------
import networkx as nx
import matplotlib.pyplot as plt
import os
import random
import pandas as pd
from matplotlib import cm

print("--- Starting M3.5 Visualization Generation ---")

# --- Define file paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

GML_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_5_Reference_Ontology.gml')
OUTPUT_IMAGE_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_5_Reference_Ontology_Viz.png')


# --- Core Visualization Logic ---
def generate_ontology_plot():
    try:
        # Load the graph built in M3.5
        G = nx.read_gml(GML_FILE)
    except FileNotFoundError:
        print(f"[ERROR] Required graph file not found: {GML_FILE}. Please run M3.5_ontology_construction.py first.")
        return

    print(f"Graph loaded with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    # --- 1. Data Preparation ---
    domains = nx.get_node_attributes(G, 'industry_domain')
    unique_domains = sorted(list(set(domains.values())))

    # Select a representative subgraph for visualization (2-step radius from a 'Common' node)
    start_node = next((n for n, domain in domains.items() if domain == 'Common' and ':' in n), None)

    if start_node:
        subgraph_nodes = nx.single_source_shortest_path_length(G, start_node, cutoff=2).keys()
        
        # Create a mutable copy of the subgraph
        subgraph = G.subgraph(subgraph_nodes).copy()
        
        # Prune isolated nodes for clarity
        isolated = list(nx.isolates(subgraph))
        subgraph.remove_nodes_from(isolated)
        
        print(f"Visualizing a subgraph with {subgraph.number_of_nodes()} nodes.")
    else:
        # Fallback visualization
        nodes_to_sample = min(40, G.number_of_nodes()) 
        subgraph_nodes = random.sample(G.nodes, nodes_to_sample)
        subgraph = G.subgraph(subgraph_nodes).copy()
        print(f"Visualizing a random subgraph with {subgraph.number_of_nodes()} nodes.")

    # --- 2. Prepare Drawing Attributes ---
    node_colors = []
    cmap = cm.get_cmap('tab20', len(unique_domains)) 
    domain_to_color = {domain: cmap(i) for i, domain in enumerate(unique_domains)}

    for node in subgraph.nodes:
        domain = G.nodes[node].get('industry_domain', 'Unknown')
        node_colors.append(domain_to_color.get(domain, 'gray'))

    labels = {node: G.nodes[node].get('base_concept_name', node) for node in subgraph.nodes}

    # --- 3. Draw and Save ---
    plt.figure(figsize=(18, 14))
    pos = nx.spring_layout(subgraph, k=0.15, iterations=50, seed=42)

    nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, node_size=1500, alpha=0.9)
    nx.draw_networkx_edges(subgraph, pos, edgelist=subgraph.edges, arrowstyle='->', arrowsize=25, edge_color='dimgray', width=1.5)
    nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=10, font_weight='bold', clip_on=False)

    legend_handles = [plt.Line2D([0], [0], marker='o', color='w', label=domain, markerfacecolor=domain_to_color[domain], markersize=12) 
                      for domain in unique_domains if domain in domain_to_color]

    plt.legend(handles=legend_handles, title="Industry Domains", loc='upper left', fontsize=12, title_fontsize=14)
    plt.title("M3.5 Reference Ontology Subgraph (Domain-Qualified Concepts)", fontsize=16)
    plt.axis('off')
    plt.tight_layout()

    # Save the plot file
    plt.savefig(OUTPUT_IMAGE_FILE)
    print(f"[SUCCESS] Visualization file successfully saved to: {OUTPUT_IMAGE_FILE}")


if __name__ == "__main__":
    # Ensure matplotlib is available
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[SETUP ERROR] Matplotlib not found. Please install it: pip install matplotlib")
        exit()
        
    generate_ontology_plot()