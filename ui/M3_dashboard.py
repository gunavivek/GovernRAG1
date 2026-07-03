# --------------------------------------------------------------------------
# UI MODULE 3: Knowledge Graph Visualization
# Displays the constructed NetworkX graph using the streamlit-agraph component.
# --------------------------------------------------------------------------
import streamlit as st
import networkx as nx
import os
import json
import pandas as pd  # <-- THIS IS THE REQUIRED FIX
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(layout="wide", page_title="Module 3: Knowledge Graph")
st.title("🕸️ Module 3: Core Knowledge Graph Visualization")
st.header("The Foundational Index for Concept-Enhanced RAG")

# --- Define file path ---
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
GRAPH_FILE_PATH = os.path.join(ROOT_DIR, 'output', 'M3_Knowledge_Graph.gml')
EDGES_FILE_PATH = os.path.join(ROOT_DIR, 'output', 'M3_Graph_Edges.csv') # To show tabular data

# --- Data Loading and Caching ---
@st.cache_data
def load_graph():
    """Loads the NetworkX graph from the GML file."""
    try:
        # 1. Load the NetworkX Graph
        G = nx.read_gml(GRAPH_FILE_PATH)
        return G
    except FileNotFoundError:
        st.error(f"[ERROR] Graph file not found: {GRAPH_FILE_PATH}. Please run M3_graph_construction.py first.")
        return None
    except Exception as e:
        st.error(f"Error loading graph: {e}")
        return None

G = load_graph()

# --- Graph Rendering Function ---
def render_graph(G):
    """Converts NetworkX graph to agraph nodes/edges and renders it."""
    
    nodes = []
    edges = []
    
    # 1. Convert NetworkX Nodes
    for node_id in G.nodes():
        # Use node_id as both id and label for clarity
        nodes.append(Node(
            id=node_id, 
            label=node_id, 
            size=15, 
            title=f"Concept: {node_id}"
        ))
        
    # 2. Convert NetworkX Edges
    for u, v, data in G.edges(data=True):
        predicate = data.get('relationship', 'CONNECTS')
        source_chunk = data.get('source_chunk_id', 'N/A')
        
        edges.append(Edge(
            source=u, 
            target=v, 
            label=predicate, 
            title=f"Relationship: {predicate} (Source Chunk: {source_chunk})",
            # Style the edges for better visibility
            arrows="to",
            color="grey"
        ))

    # 3. Configure the Visualization
    config = Config(
        width=1000, 
        height=700,
        directed=True, 
        physics=True, 
        # Add solver to keep large graphs stable
        solver='barnesHut',
        hierarchical=False,
        # Customize the interaction
        maxZoom=1, 
        minZoom=0.1
    )

    # 4. Render the graph
    return agraph(nodes=nodes, edges=edges, config=config)

# --- Main Layout ---
if G:
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        st.metric(label="Total Nodes (Unique Concepts)", value=G.number_of_nodes())
    with col2:
        st.metric(label="Total Edges (Relationships)", value=G.number_of_edges())
    with col3:
        st.metric(label="Connectivity (Edges/Nodes)", value=f"{G.number_of_edges() / G.number_of_nodes():.2f}")
        
    st.markdown("---")
    
    st.subheader("Interactive Knowledge Graph")
    st.info("Drag nodes to rearrange. Hover over nodes/edges for more details.")
    
    # Render the graph visualization
    render_graph(G)
    
    st.markdown("---")
    
    st.subheader("Graph Edge List (Source Data)")
    # Optional: Display the raw edge data table
    try:
        # This line now works because pandas is imported as pd
        df_edges = pd.read_csv(EDGES_FILE_PATH)
        st.dataframe(df_edges, use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Edge CSV not found at: {EDGES_FILE_PATH}")
        
else:
    st.info("The graph could not be loaded. Please check the terminal output for M3_graph_construction.py.")