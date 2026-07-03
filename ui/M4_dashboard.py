# --------------------------------------------------------------------------
# UI MODULE 4: Hybrid Knowledge Graph Visualization
# FIX: Document Fact Concept filter now includes Unmapped Concepts for debugging.
# --------------------------------------------------------------------------
import streamlit as st
import networkx as nx
import os
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config

# --- 1. Configuration and Setup ---
st.set_page_config(layout="wide", page_title="M4: Hybrid Graph Dashboard")
st.title("🔗 Module 4: Hybrid Knowledge Graph Dashboard")
st.header("Semantic Triangulation: Document Facts Anchored to BIZBOK")

is_default_focus = False  # Flag to check if default focus is used

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
GRAPH_FILE_PATH = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.gml')
CHUNKS_FILE_PATH = os.path.join(PROJECT_ROOT, 'output', 'M1_Text_Chunks.csv')


# --- 2. Data Loading and Graph Processing ---
@st.cache_resource
def load_and_process_graph():
    """Loads the M4 Hybrid Graph and prepares all dataframes and lists."""
    try:
        G = nx.read_gml(GRAPH_FILE_PATH)
        df_chunks = pd.read_csv(CHUNKS_FILE_PATH)
    except FileNotFoundError as e:
        st.error(f"[ERROR] Required file not found: {e}. Ensure M1 and M4 were run successfully.")
        return None, None, None, None # Return Nones on failure

    # Prepare dataframes and lists
    node_df_list = []
    edge_df_list = []

    for node_id, data in G.nodes(data=True):
        node_df_list.append({'Node ID': node_id, 'Type': data.get('node_type', 'UnmappedConcept'), 'Domain': data.get('industry_domain'), 'Base Concept': data.get('base_concept_name', node_id)})
        
    for u, v, data in G.edges(data=True):
        edge_df_list.append({'Source': u, 'Target': v, 'relationship': data.get('relationship', 'PREDICATE'), 'mapping_status': data.get('mapping_status', 'N/A'), 'source_chunk_id': data.get('source_chunk_id', 'N/A')})

    node_df = pd.DataFrame(node_df_list)
    edge_df = pd.DataFrame(edge_df_list)

    # FIX: Force integer type consistency across both DataFrames for reliable filtering
    edge_df['source_chunk_id'] = pd.to_numeric(edge_df['source_chunk_id'], errors='coerce').fillna(-1).astype(int)
    df_chunks['chunk_id'] = df_chunks['chunk_id'].astype(int)

    return G, node_df, edge_df, df_chunks 

G, node_df, edge_df, df_chunks = load_and_process_graph()

# --- Stop if data load failed ---
if G is None:
    st.stop()


# --- 3. Sidebar Filtering (Targeted Filters) ---
st.sidebar.header("Select Focus Node ID 🔎")

# Define lists of IDs for each filter
ref_concepts = node_df[node_df['Type'] == 'ReferenceConcept']['Node ID'].sort_values().tolist()
adaptive_concepts = node_df[node_df['Type'] == 'AdaptiveConcept']['Node ID'].sort_values().tolist()

# FIX: Include both DocumentConcept and UnmappedConcept in the bottom layer filter list
doc_and_unmapped_concepts = node_df[node_df['Type'].isin(['DocumentConcept', 'UnmappedConcept'])]['Node ID'].sort_values().tolist()


# 3.1. Filter 1: Reference Concept (Top Layer Anchor)
selected_ref = st.sidebar.selectbox(
    "1. Top Layer: BIZBOK Reference Concept (Blue)", 
    ['Select a Reference Concept'] + ref_concepts
)

# 3.2. Filter 2: Adaptive Concept (Middle Layer Bridge)
selected_adaptive = st.sidebar.selectbox(
    "2. Middle Layer: Adaptive Concept (Red)", 
    ['Select an Adaptive Concept'] + adaptive_concepts
)

# 3.3. Filter 3: Document Concept (Bottom Layer Fact & Unmapped)
selected_doc = st.sidebar.selectbox(
    "3. Bottom Layer: Document Fact Concept (Green/Gray)", # Updated display text
    ['Select a Document Concept'] + doc_and_unmapped_concepts
)

# 3.4. Determine the primary node for visualization
if selected_ref != 'Select a Reference Concept':
    selected_focus_node = selected_ref
elif selected_adaptive != 'Select an Adaptive Concept':
    selected_focus_node = selected_adaptive
elif selected_doc != 'Select a Document Concept':
    selected_focus_node = selected_doc
else:
    selected_focus_node = ref_concepts[0] if ref_concepts else (doc_and_unmapped_concepts[0] if doc_and_unmapped_concepts else 'N/A')
    is_default_focus = True if selected_ref == 'Select a Reference Concept' and selected_adaptive == 'Select an Adaptive Concept' and selected_doc == 'Select a Document Concept' else False


# --- 4. Subgraph Creation Based on Filter ---

@st.cache_data 
def create_subgraph_for_visualization(_G, focus_node):
    """Creates a subgraph showing the 2-step neighborhood of the focus node."""
    
    subgraph_nodes = nx.single_source_shortest_path_length(_G, focus_node, cutoff=2).keys()
    subgraph = _G.subgraph(subgraph_nodes).copy()
    
    isolated = list(nx.isolates(subgraph))
    subgraph.remove_nodes_from(isolated)

    return subgraph

subgraph = create_subgraph_for_visualization(G, selected_focus_node)


# --- 5. Graph Rendering Function (Hierarchy Logic) ---

def render_subgraph(subgraph):
    """Converts NetworkX graph to agraph nodes/edges and renders it with hierarchy."""
    nodes_agraph = []
    edges_agraph = [] 

    COLOR_MAP = {
        "ReferenceConcept": "#1f77b4",  # Blue (Anchor)
        "AdaptiveConcept": "#d62728",   # Red (Novel/Resilience)
        "DocumentConcept": "#2ca02c",   # Green (Document Fact)
        "UnmappedConcept": "#7f7f7f"    # Gray (Unlinked/Ignored)
    }
    
    LEVEL_MAP = {
        "ReferenceConcept": 1, # Top Layer
        "AdaptiveConcept": 2,  # Middle Layer
        "DocumentConcept": 3,  # Bottom Layer
        "UnmappedConcept": 3   
    }
    
    # Process Nodes
    for node_id, data in subgraph.nodes(data=True):
        node_type = data.get('node_type', 'UnmappedConcept')
        label = data.get('base_concept_name', node_id)
        size = 25 if node_type == "ReferenceConcept" else 15

        nodes_agraph.append(Node(
            id=node_id, 
            label=label,
            size=size,
            title=f"Type: {node_type} | ID: {node_id}",
            color=COLOR_MAP.get(node_type, '#000000'),
            level=LEVEL_MAP.get(node_type, 3)
        ))
        
    # Process Edges
    for u, v, data in subgraph.edges(data=True):
        relationship = data.get('relationship', 'PREDICATE')
        
        if relationship in ["IS_ALIGNED_WITH", "ADAPTED_FROM"]:
            color = "#ff7f0e"  # Orange (Triangulation Link)
            width = 2
        elif relationship == "RELATED_TO":
            color = "#17becf"  # Cyan (BIZBOK Standard Link)
            width = 1.5
        else:
            color = "#7f7f7f"  # Gray (Original Document Predicate)
            width = 1
        
        edges_agraph.append(Edge(
            source=u, 
            target=v, 
            label=relationship, 
            color=color,
            width=width,
            arrows="to"
        ))

    # Configure the visualization parameters (ENABLE HIERARCHY)
    config = Config(
        width=1200, 
        height=850, 
        directed=True, 
        physics=False, 
        hierarchical=True, 
        direction='UD', 
        sortMethod='directed',
        layout={
            'hierarchical': {
                'levelSeparation': 150, 
                'nodeSpacing': 250,     
                'treeSpacing': 200      
            }
        },
        maxZoom=1, 
        minZoom=0.1
    )

    agraph(nodes=nodes_agraph, edges=edges_agraph, config=config)


# --- 6. Main Display (Layer Headers/Swimlanes Added) ---

st.markdown("---")
col_graph, col_lineage = st.columns([3, 1])

with col_graph:
    st.subheader("Conceptual Traversal Path")
    st.caption(f"Currently centered on: **{selected_focus_node}**. Use sidebar filters to isolate specific paths.")
    
    # --- VISUAL INDEX (Legend) SECTION ---
    st.markdown("---")
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown("**Node Role (Bubble Color/Size)**")
        st.markdown("- <span style='color:#1f77b4; font-size: large;'>⬤</span> **Layer 1: Reference Concept** (Anchor)", unsafe_allow_html=True)
        st.markdown("- <span style='color:#d62728; font-size: medium;'>⬤</span> **Layer 2: Adaptive Concept** (Bridge)", unsafe_allow_html=True)
        st.markdown("- <span style='color:#2ca02c; font-size: small;'>⬤</span> **Layer 3: Document Concept** (Raw Fact)", unsafe_allow_html=True)
        st.markdown("- <span style='color:#7f7f7f; font-size: small;'>⬤</span> **Unmapped Concept**", unsafe_allow_html=True)

    with col_v2:
        st.markdown("**Edge Relationship (Line Color/Thickness)**")
        st.markdown("- <span style='color:#ff7f0e; font-weight: normal;'>— Thin Orange:</span> **Triangulation Links** (IS\_ALIGNED\_WITH / ADAPTED\_FROM)", unsafe_allow_html=True)
        st.markdown("- <span style='color:#17becf; font-weight: normal;'>— Thin Cyan:</span> **BIZBOK Structure** (RELATED\_TO)", unsafe_allow_html=True)
        st.markdown("- <span style='color:#7f7f7f; font-weight: normal;'>— Thin Gray:</span> **Document Predicate** (Original M2 Fact)", unsafe_allow_html=True)
        st.markdown("**Note:** Layering is enforced using fixed vertical positions (Swimlanes).", unsafe_allow_html=True)

    render_subgraph(subgraph)

# --- Lineage Panel ---
with col_lineage:
    st.subheader("Source Chunk Lineage 📜")
    st.info("The lineage refreshes for the node currently selected in the sidebar filters.")
    
    if is_default_focus:
        display_concept = "Select a concept in the sidebar to trace its source."
    else:
        display_concept = selected_focus_node
        
    st.markdown(f"**Focus Concept:** `{display_concept}`") 
    
    focus_type = node_df[node_df['Node ID'] == selected_focus_node]['Type'].iloc[0]
    
    source_triples = edge_df[(edge_df['Source'] == selected_focus_node) | (edge_df['Target'] == selected_focus_node)]
    
    if focus_type not in ['ReferenceConcept', 'UnmappedConcept']:
        
        chunk_ids = source_triples['source_chunk_id'].unique()
        valid_chunk_ids = chunk_ids[chunk_ids != -1]
        
        if len(valid_chunk_ids) >= 1:
            st.success(f"Concept derived from {len(valid_chunk_ids)} unique chunk(s) (M1).")
            
            lineage_chunks = df_chunks[df_chunks['chunk_id'].isin(valid_chunk_ids)].sort_values(by='chunk_id')
            
            st.markdown("**Original Chunk Text (M1 Artifact):**")
            for index, row in lineage_chunks.iterrows():
                with st.expander(f"Chunk ID {row['chunk_id']}", expanded=False): 
                    st.code(row['chunk_text']) 

        else:
            st.warning("Could not trace this concept back to a source chunk. The linked chunk ID was invalid or missing.")

    else:
        st.info("This is a BIZBOK Anchor concept. Lineage is defined by the Information Map CSV (M3.5).")

st.markdown("---")

st.subheader("Raw Data Check: Linking Edges")
linking_df = edge_df[edge_df['relationship'].isin(["IS_ALIGNED_WITH", "ADAPTED_FROM"])]
st.dataframe(linking_df.head(10), use_container_width=True)