import streamlit as st
import networkx as nx
import os
import pandas as pd

# --- 1. Configuration and Setup ---
st.set_page_config(layout="wide", page_title="M3.5 Reference Ontology Dashboard")

# Define file paths using robust path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT is one level up from BASE_DIR ('experiment')
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Define paths to the generated files
GML_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_5_Reference_Ontology.gml')
VIZ_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_5_Reference_Ontology_Viz.png')


# --- 2. Load Data ---
@st.cache_data
def load_graph_data():
    """Loads the Reference Ontology graph from GML and prepares DataFrames."""
    try:
        # Load the graph built with the Composite Key
        G = nx.read_gml(GML_FILE)
        
        # Prepare Node DataFrames
        node_data = []
        for node, data in G.nodes(data=True):
            data['Node ID'] = node
            # Extract the concept name without the domain prefix for a clean column
            data['Base Concept'] = data.get('base_concept_name', node.split(':')[-1]) 
            node_data.append(data)
        
        node_df = pd.DataFrame(node_data)
        
        # Prepare Edge DataFrames
        edge_data = []
        for source, target, data in G.edges(data=True):
            edge_data.append({
                'Source': source,
                'Target': target,
                'Relationship': data.get('relationship', 'RELATED_TO'),
                'Source Domain': data.get('source_domain', source.split(':')[0]),
                'Target Domain': data.get('target_domain', target.split(':')[0])
            })
        
        edge_df = pd.DataFrame(edge_data)
        
        return G, node_df, edge_df
    
    except FileNotFoundError:
        st.error(f"Error: Graph file not found. Ensure M3.5 was run successfully. Missing: {GML_FILE}")
        return None, None, None
    except Exception as e:
        st.error(f"Error loading graph: {e}")
        return None, None, None

G, node_df, edge_df = load_graph_data()

# --- 3. Streamlit Display ---
st.title("🏛️ M3.5 Reference Ontology Dashboard")
st.markdown("This dashboard validates the construction of the domain-qualified BIZBOK Reference Ontology using the composite key approach.")
st.markdown("---")

if G is None:
    st.stop()


# --- Sidebar Filtering Logic ---
st.sidebar.header("Filter & Analysis Options")
domains_list = ['All'] + sorted(node_df['industry_domain'].unique().tolist())
selected_domain = st.sidebar.selectbox("Filter Metrics by Domain", domains_list)

if selected_domain != 'All':
    filtered_nodes = node_df[node_df['industry_domain'] == selected_domain]
    
    # Calculate filtered edge count
    filtered_edges = edge_df[
        (edge_df['Source Domain'] == selected_domain) | 
        (edge_df['Target Domain'] == selected_domain)
    ]
    
    node_count = len(filtered_nodes)
    edge_count = len(filtered_edges)
    concept_count = filtered_nodes['Base Concept'].nunique()
    domain_count = 1
else:
    filtered_nodes = node_df
    node_count = G.number_of_nodes()
    edge_count = G.number_of_edges()
    concept_count = node_df['Base Concept'].nunique()
    domain_count = len(domains_list) - 1


# --- Metrics Display ---
st.header(f"Reference Ontology Metrics ({'All Domains' if selected_domain == 'All' else selected_domain})")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Domain-Qualified Concepts", f"{node_count:,}")
with col2:
    st.metric("Total Authoritative Relationships", f"{edge_count:,}")
with col3:
    st.metric("Unique Base Concept Names", f"{concept_count:,}")
with col4:
    st.metric("Industry Domains Captured", f"{domain_count:,}")

st.markdown("---")

# --- Visualization Display (Fix applied here) ---
st.header("Graph Structure Visualization (Semantic Partitioning)")

try:
    if os.path.exists(VIZ_FILE):
        # FIX: Using use_container_width=True to resolve deprecation warning and improve rendering
        st.image(VIZ_FILE, use_container_width=True, 
                 caption=f"Subgraph Visualization showing Domain:Concept Nodes and RELATED_TO Edges.")
        st.markdown("""
            The visualization confirms that the **composite key structure** successfully partitioned concepts by domain, maintaining semantic rigor.
        """)
    else:
        st.warning(f"Static visualization image not found at the expected path: {VIZ_FILE}. Please ensure the graph visualization code was run successfully to generate the PNG file first.")
        
except Exception as e:
    st.error(f"Failed to display image due to internal error: {e}")

st.markdown("---")

# [Lines 1 through 100+ of existing M3_5_dashboard.py code are unchanged:
# Setup, Load Data, Metrics Display, Sidebar Logic are all the same]

# --- Visualization and Data Tables ---
st.header("Graph Inspection and Visualization")

# --- Tabs Implementation ---
# Change here: Define three tabs instead of two
tab1, tab2, tab3 = st.tabs(["Reference Concept Nodes", "RELATED_TO Edges", "Graph Visualization"])

with tab1:
    st.subheader("Reference Concept Nodes (Filtered)")
    st.dataframe(filtered_nodes[['Node ID', 'Base Concept', 'industry_domain', 'definition', 'types']].head(15), 
                 height=300, use_container_width=True)
    st.caption("Node ID uses the required composite key structure: `Domain:Concept`.")

with tab2:
    st.subheader("RELATED_TO Edges (Sample)")
    st.dataframe(edge_df.sample(min(30, len(edge_df)), random_state=42), height=300, use_container_width=True)
    st.caption("These edges define the authoritative BIZBOK relationships used for retrieval traversal.")

with tab3:
    st.subheader("Reference Ontology Subgraph Visualization")
    
    try:
        if os.path.exists(VIZ_FILE):
            # Display the static PNG generated in the previous step's console execution
            st.image(VIZ_FILE, use_container_width=True, 
                     caption=f"Subgraph Visualization showing Domain:Concept Nodes and RELATED_TO Edges.")
            st.markdown("""
                The node colors and distinct node labels confirm the **composite key structure** is working, ensuring semantic rigor by partitioning concepts by domain.
            """)
        else:
            st.warning(f"""
                **File Missing Error:** Static visualization image not found at the expected path: `{VIZ_FILE}`. 
                
                **To resolve this:** Please execute the last visualization code block (the one that uses `plt.savefig`) in your console one more time to ensure the image file is successfully created and saved in your `output` folder.
            """)
            
    except Exception as e:
        st.error(f"Failed to display image due to internal error: {e}")

# End of M3_5_dashboard.py