# --------------------------------------------------------------------------
# MODULE 6: Graph Analysis Dashboard (Community Detection)
# FINAL FIX: Corrects UnhashableParamError by using the _G convention in caching.
# Plus: fixes matplotlib.colors, community filter, and edges_agraph init.
# --------------------------------------------------------------------------
import streamlit as st
import networkx as nx
import os
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import rgb2hex  # ✅ color utility
import numpy as np
import random


st.set_page_config(layout="wide", page_title="M6: Community Detection")
st.title("🧩 Module 6: Concept Community Analysis")
st.header("Thematic Partitioning for Retrieval Routing")

# --- 1. Define file paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

GRAPH_FILE_PATH = os.path.join(PROJECT_ROOT, 'output', 'M6_Clustered_Graph.gml')
CHUNKS_FILE_PATH = os.path.join(PROJECT_ROOT, 'output', 'M1_Text_Chunks.csv')


# --- 2. Data Loading and Graph Processing ---
@st.cache_resource
def load_and_process_graph():
    """Loads the M6 Clustered Graph and prepares dataframes."""
    try:
        G = nx.read_gml(GRAPH_FILE_PATH)
        df_chunks = pd.read_csv(CHUNKS_FILE_PATH)
    except FileNotFoundError as e:
        st.error(f"[ERROR] Required file not found: {e}. Please run M1 and M6 first.")
        return None, None, None, None

    # Prepare node dataframe with community attributes
    node_df_list = []
    for node_id, data in G.nodes(data=True):
        community_id_str = str(data.get('community_id', 'N/A'))

        try:
            # Ensure community_id is numeric before string formatting
            community_id_str = f"COMMUNITY_{int(float(community_id_str))}"
        except ValueError:
            # If it's not numeric, keep whatever was in the graph
            community_id_str = community_id_str

        node_df_list.append({
            'Node ID': node_id,
            'Type': data.get('node_type', 'UnmappedConcept'),
            'Community ID': community_id_str,  # Use string format for filtering
            'Base Concept': data.get('base_concept_name', node_id),
            'Document ID': 'DOC_1'  # ASSIGN DOC ID (for single document prototype)
        })

    # Prepare edge dataframe (for context triples lookup)
    edge_df_list = []
    for u, v, data in G.edges(data=True):
        edge_df_list.append({
            'Source': u,
            'Target': v,
            'relationship': data.get('relationship', 'PREDICATE'),
            'source_chunk_id': data.get('source_chunk_id', 'N/A')
        })

    node_df = pd.DataFrame(node_df_list)
    edge_df = pd.DataFrame(edge_df_list)

    # FIX: Force integer type consistency for chunk ID lookup
    edge_df['source_chunk_id'] = pd.to_numeric(edge_df['source_chunk_id'], errors='coerce').fillna(-1).astype(int)
    df_chunks['chunk_id'] = df_chunks['chunk_id'].astype(int)

    return G, node_df, edge_df, df_chunks


G, node_df, edge_df, df_chunks = load_and_process_graph()

if G is None:
    st.stop()


# --- 3. Sidebar Filtering and Setup ---
st.sidebar.header("Filter by Scope 🔎")

# 3.1 Document Filter (Placeholder for RAGBENCH)
document_list = sorted(node_df['Document ID'].unique().tolist())
selected_document = st.sidebar.selectbox(
    "1. Document Filter (Layer 1)",
    document_list
)

# Calculate unique communities for the filter
community_list = sorted([c for c in node_df['Community ID'].astype(str).unique() if c != 'N/A'])
selected_community = st.sidebar.selectbox(
    "2. Thematic Community (Layer 4)",
    ['All Communities'] + community_list
)

# We need a stable list of all nodes to build the focus filter
all_nodes_list = node_df['Node ID'].tolist()
selected_focus_node = st.sidebar.selectbox("3. Node for Lineage Trace", all_nodes_list, index=0)


# --- 4. Graph Rendering and Filtering ---
# FIX 1: Add underscore to G and pass selected_document explicitly
@st.cache_resource
def get_subgraph_and_color_map(selected_community, selected_document, _G, _node_df, _edge_df):
    """
    Filters the graph by document/community and prepares nodes color-coded by chunk_id.
    """

    # 4.1 FILTER NODES: Filter by Document and Community
    filtered_df = _node_df[
        (_node_df['Type'].isin(['DocumentConcept', 'AdaptiveConcept'])) &
        (_node_df['Document ID'] == selected_document)
    ]

    if selected_community != 'All Communities':
        # Community IDs are stored as strings like "COMMUNITY_0"
        filtered_df = filtered_df[filtered_df['Community ID'].astype(str) == selected_community]

    # Include Reference Concepts linked to the filtered Document/Adaptive Nodes
    linked_ref_nodes = _edge_df[
        (_edge_df['Source'].isin(filtered_df['Node ID'])) |
        (_edge_df['Target'].isin(filtered_df['Node ID']))
    ]['Target'].unique().tolist()

    # Combine filtered Document/Adaptive nodes with their Reference Anchors
    final_nodes = filtered_df['Node ID'].tolist() + linked_ref_nodes
    subgraph = _G.subgraph(final_nodes)

    # 4.2 COLOR MAPPING (Color by CHUNK ID - Stable Hex Colors)
    # Get all unique chunk IDs present in the filtered nodes' edges
    unique_chunk_ids = _edge_df[_edge_df['Source'].isin(final_nodes)]['source_chunk_id'].unique()
    unique_chunk_ids = [cid for cid in unique_chunk_ids if cid != -1]

    chunk_to_color = {}
    if len(unique_chunk_ids) > 0:
        # At least 5 distinct colors, or as many as chunk IDs
        cmap = plt.cm.get_cmap('Spectral', max(len(unique_chunk_ids), 5))
        # Avoid divide-by-zero; spread indices across [0,1]
        denom = max(len(unique_chunk_ids) - 1, 1)
        chunk_to_color = {
            cid: rgb2hex(cmap(i / denom))
            for i, cid in enumerate(unique_chunk_ids)
        }

    nodes_agraph = []
    edges_agraph = []  # ✅ ensure this is defined before we append

    for node_id, data in subgraph.nodes(data=True):
        node_type = data.get('node_type', 'DocumentConcept')
        size = 25 if node_type == "ReferenceConcept" else 12

        # Determine the color: Use the *first* chunk ID linked to this node
        is_source_node_edge = _edge_df[_edge_df['Source'] == node_id]
        color = '#1f77b4'       # Default color for Reference/Non-sourced nodes (Blue)
        color_source_id = 'N/A' # For display in title

        if not is_source_node_edge.empty:
            color_source_id = int(is_source_node_edge.iloc[0]['source_chunk_id'])
            color = chunk_to_color.get(color_source_id, '#7f7f7f')

        nodes_agraph.append(Node(
            id=node_id,
            label=data.get('base_concept_name', node_id),  # prefer graph attribute if present
            size=size,
            title=f"Community: {data.get('community_id', 'N/A')} | Chunk Source: {color_source_id}",
            color=color,
        ))

    for u, v, data in subgraph.edges(data=True):
        edges_agraph.append(Edge(source=u, target=v, color="#555555", width=1.0, arrows="to"))

    return nodes_agraph, edges_agraph, chunk_to_color


# FIX 2: Call the function with the underscore arguments + selected_document
nodes_agraph, edges_agraph, chunk_to_color = get_subgraph_and_color_map(
    selected_community,
    selected_document,
    G,
    node_df,
    edge_df
)

# --- 5. Main Display and Traceability Panel ---
st.markdown("---")
col_graph, col_lineage = st.columns([3, 1])

with col_graph:
    st.subheader(f"1. Community Graph View ({selected_community})")
    st.info(f"Visualizing {len(nodes_agraph)} concepts in filtered view. Nodes are stable (Physics Disabled).")

    # Render the community-filtered subgraph
    config = Config(width=1000, height=600, directed=True, physics=False, maxZoom=1.5)
    agraph(nodes=nodes_agraph, edges=edges_agraph, config=config)

    # Legend for Chunk Colors
    st.markdown("**Chunk Color Legend (Traceability Layer 2)**")
    if chunk_to_color:
        legend_items = [
            f"<span style='color: {hex_code}'>⬤</span> Chunk ID {cid}"
            for cid, hex_code in chunk_to_color.items()
        ]
        st.markdown(" | ".join(legend_items), unsafe_allow_html=True)
    else:
        st.caption("No chunk-based color mapping available for this selection.")

# --- Lineage Panel (Document -> Chunk -> Concept Trace) ---
with col_lineage:
    st.subheader("2. Full Traceability Lineage 📜")
    st.info("Lineage Flow: Document → Chunk → Concept → Community")

    # 5.1 Trace: Concept -> Community ID
    focus_data = node_df[node_df['Node ID'] == selected_focus_node]

    if not focus_data.empty:
        focus_data_row = focus_data.iloc[0]
        focus_comm_id = focus_data_row['Community ID']

        st.markdown(f"**Node:** `{selected_focus_node}`")
        # focus_comm_id is already like "COMMUNITY_0"
        st.markdown(f"**Community (Layer 4):** `{focus_comm_id}`")
        st.markdown(f"**Document (Layer 1):** `{selected_document}`")

        # 5.2 Trace: Concept -> Chunk ID -> Document Text
        source_triples = edge_df[
            (edge_df['Source'] == selected_focus_node) |
            (edge_df['Target'] == selected_focus_node)
        ]
        valid_chunk_ids = source_triples['source_chunk_id'].unique()
        valid_chunk_ids = valid_chunk_ids[valid_chunk_ids != -1]

        if len(valid_chunk_ids) >= 1:
            st.markdown("---")
            st.caption(f"**Chunk Evidence Found ({len(valid_chunk_ids)} Chunks):**")

            lineage_chunks = df_chunks[df_chunks['chunk_id'].isin(valid_chunk_ids)].sort_values(by='chunk_id')

            for index, row in lineage_chunks.iterrows():
                with st.expander(f"Chunk ID {row['chunk_id']} (Source)", expanded=False):
                    st.code(row['chunk_text'])
        else:
            st.warning(f"No raw chunk source found for this concept (Node Type: {focus_data_row['Type']}).")
    else:
        st.warning("Please select a valid node ID to trace.")
