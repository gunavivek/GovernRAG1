# --------------------------------------------------------------------------
# UI MODULE 1: Text Chunking Visualization
# Displays the input text and the resulting M1_Text_Chunks.csv artifact.
# --------------------------------------------------------------------------
import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Module 1: Text Chunking")
st.title("🧱 Module 1: Text Chunking & Artifact Review")
st.header("Concept-Enhanced RAG Framework")

# --- Define file paths ---
# Get the root directory by navigating up one level from 'ui'
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
INPUT_FILE_PATH = os.path.join(ROOT_DIR, 'data', 'ragbench_documents.txt')
OUTPUT_FILE_PATH = os.path.join(ROOT_DIR, 'output', 'M1_Text_Chunks.csv')

# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    """Loads the input document and the output CSV artifact."""
    
    # 1. Load Original Document
    try:
        with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as f:
            original_text = f.read()
    except FileNotFoundError:
        original_text = "[ERROR] Input file 'ragbench_documents.txt' not found in /data folder."

    # 2. Load Chunk Output
    try:
        df_chunks = pd.read_csv(OUTPUT_FILE_PATH)
    except FileNotFoundError:
        df_chunks = pd.DataFrame()
        st.warning("Artifact not found: Please run 'python experiment/M1_chunking.py' first.")

    return df_chunks, original_text

df_chunks, original_text = load_data()

# --- Layout and Visualization ---

st.markdown("---")
st.subheader("1. Input Document (`data/ragbench_documents.txt`)")
st.code(f"Total Characters: {len(original_text)}", language='text')
st.text_area("Original Corpus Text", original_text, height=350, disabled=True)

st.markdown("---")
st.subheader(f"2. Output Artifact (`output/M1_Text_Chunks.csv`)")

if not df_chunks.empty:
    st.success(f"Successfully loaded {len(df_chunks)} chunks.")
    
    # Display the chunks dataframe
    st.dataframe(df_chunks, use_container_width=True)
    
    st.subheader("Preview: First 5 Chunks")
    
    # Simple table to preview chunks
    preview_data = df_chunks[['chunk_id', 'chunk_text']].head(5).to_dict('records')
    
    for item in preview_data:
        st.markdown(f"**Chunk ID: {item['chunk_id']}**")
        st.code(item['chunk_text'], language='text')
else:
    st.error("The output artifact M1_Text_Chunks.csv is empty or was not found. Please run the core script.")