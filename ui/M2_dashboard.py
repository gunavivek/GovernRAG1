# --------------------------------------------------------------------------
# UI MODULE 2: Entity & Relationship Extraction Visualization
# Displays M1 chunks and the resulting M2_Extracted_Triples.json artifact.
# --------------------------------------------------------------------------
import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(layout="wide", page_title="Module 2: Triple Extraction")
st.title("🔗 Module 2: Entity & Relationship Extraction Review")
st.header("Concept-Enhanced RAG Framework")

# --- Define file paths ---
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CHUNK_FILE_PATH = os.path.join(ROOT_DIR, 'output', 'M1_Text_Chunks.csv')
TRIPLE_FILE_PATH = os.path.join(ROOT_DIR, 'output', 'M2_Extracted_Triples.json')

# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    """Loads the chunk DataFrame and the extracted Triples JSON."""
    
    # 1. Load Chunks (Input)
    try:
        df_chunks = pd.read_csv(CHUNK_FILE_PATH)
        df_chunks['chunk_id'] = df_chunks['chunk_id'].astype(int)
    except FileNotFoundError:
        df_chunks = pd.DataFrame()
        st.error(f"[ERROR] Chunk file not found: {CHUNK_FILE_PATH}")

    # 2. Load Triples (Output)
    try:
        with open(TRIPLE_FILE_PATH, 'r', encoding='utf-8') as f:
            triples_list = json.load(f)
        df_triples = pd.DataFrame(triples_list)
    except FileNotFoundError:
        df_triples = pd.DataFrame()
        st.warning("Artifact not found: Please run 'python experiment/M2_extraction.py' first.")
    except json.JSONDecodeError:
        df_triples = pd.DataFrame()
        st.error("Error decoding M2_Extracted_Triples.json. Check the file for valid JSON format.")
        
    return df_chunks, df_triples

df_chunks, df_triples = load_data()

st.markdown("---")

# --- Layout and Visualization ---

# Column layout for metrics
col1, col2 = st.columns(2)

with col1:
    st.metric(label="Total Chunks (M1 Input)", value=len(df_chunks))
with col2:
    st.metric(label="Total Triples Extracted (M2 Output)", value=len(df_triples))

st.markdown("---")

st.subheader("1. Detailed Chunk and Triple Review")

if not df_chunks.empty:
    # Iterate through chunks and show the extracted triples for each
    for index, chunk_row in df_chunks.iterrows():
        chunk_id = chunk_row['chunk_id']
        chunk_text = chunk_row['chunk_text']
        
        # Filter triples for the current chunk
        chunk_triples = df_triples[df_triples['source_chunk_id'] == chunk_id]
        
        # Use an expander to keep the main view clean
        with st.expander(f"Chunk ID {chunk_id} ({len(chunk_triples)} Triples Extracted)"):
            st.markdown("**Source Text:**")
            st.code(chunk_text, language='text')
            
            if not chunk_triples.empty:
                st.markdown("**Extracted Knowledge Triples (Subject-Predicate-Object):**")
                # Drop the source_chunk_id for cleaner display
                display_df = chunk_triples.drop(columns=['source_chunk_id'], errors='ignore')
                st.dataframe(display_df, use_container_width=True, height=200)
            else:
                st.info("No triples were extracted from this chunk.")
else:
    st.error("Cannot proceed: M1_Text_Chunks.csv is missing or empty.")

st.markdown("---")

st.subheader("2. Full Extracted Triples Table")
if not df_triples.empty:
    st.dataframe(df_triples, use_container_width=True)
else:
    st.info("No data in M2_Extracted_Triples.json.")