# --------------------------------------------------------------------------
# MODULE 5.5: Embedding Validation Dashboard (FINAL FIX)
# FIX: Corrects KeyErrors by using the proper column names ('Link Type' and 'Source_Reference_Similarity').
# --------------------------------------------------------------------------
import streamlit as st
import pandas as pd
import os
import numpy as np

st.set_page_config(layout="wide", page_title="M5.5: Traceability Validation")
st.title("📊 Module 5.5: Concept Embedding Validation")
st.header("Quantitative Proof of Semantic Grounding")

# --- Define file paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

INPUT_APCS_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_5_APCS_Matrix.csv')
INPUT_TRACE_MATRIX_FILE = os.path.join(PROJECT_ROOT, 'output', 'M5_5_Full_Trace_Matrix.csv')

# --- 1. Load Data ---
@st.cache_data
def load_validation_data():
    """Loads the pre-calculated APCS Matrix and Traceability Scores."""
    try:
        df_apcs = pd.read_csv(INPUT_APCS_FILE, index_col=0)
        df_trace = pd.read_csv(INPUT_TRACE_MATRIX_FILE)
        return df_apcs, df_trace
    
    except FileNotFoundError as e:
        st.error(f"[ERROR] Required score file not found: {e}. Please run M5.5_embedding_validation.py first.")
        return None, None
    except Exception as e:
        st.error(f"[ERROR] Data loading error: {e}")
        return None, None

df_apcs_matrix, df_full_trace_matrix = load_validation_data()

if df_apcs_matrix is None:
    st.stop()


# --- 2. Display Tables ---
st.subheader("1. Concept Coherence and Traceability Results")

col_apcs, col_trace = st.columns(2)

# --- Column 1: APCS Matrix (Abstract Coherence) ---
with col_apcs:
    st.markdown("**A. Average Pairwise Cosine Similarity (APCS) Matrix**")
    st.caption("Verifies the abstract consistency of concept groups (Reference vs. Adaptive).")
    
    # Highlight highest scores for visual validation
    st.dataframe(df_apcs_matrix.style.highlight_max(axis=0, color='lightgreen', subset=pd.IndexSlice[['Reference', 'Adaptive', 'Document'], :]), 
                 use_container_width=True)
    st.markdown("""
        **Quantitative Proof:** High similarity in the **Reference ↔ Reference** cell proves the BIZBOK layer is semantically consistent.
    """)


# --- Column 2: Full Traceability Matrix (Individual Grounding Proof) ---
with col_trace:
    st.markdown("**B. Individual Concept Traceability Score Matrix**")
    st.caption("Verifies the grounding score for every M4 link (Source Concept <=> Reference Anchor).")
    
    # RENAME FIX: The calculation outputted 'Alignment Link Type', but for clean display,
    # we rename it here if the longer name exists.
    if 'Alignment Link Type' in df_full_trace_matrix.columns:
        df_full_trace_matrix.rename(columns={'Alignment Link Type': 'Link Type'}, inplace=True)
    
    # RENAME FIX: Rename Source_Anchor_Similarity for display clarity
    if 'Source_Anchor_Similarity' in df_full_trace_matrix.columns:
        df_full_trace_matrix.rename(columns={'Source_Anchor_Similarity': 'Source_Reference_Similarity'}, inplace=True)
    
    st.dataframe(df_full_trace_matrix, use_container_width=True)
    
    # Calculate key statistics (only if the necessary columns exist)
    if 'Source_Reference_Similarity' in df_full_trace_matrix.columns and 'Link Type' in df_full_trace_matrix.columns:
        
        # FIX: Use the final, correct column names 'Link Type' and 'Source_Reference_Similarity' for filtering
        ref_score_mean = df_full_trace_matrix[df_full_trace_matrix['Link Type'] == 'IS_ALIGNED_WITH']['Source_Reference_Similarity'].astype(float).mean()
        adapt_score_mean = df_full_trace_matrix[df_full_trace_matrix['Link Type'] == 'ADAPTED_FROM']['Source_Reference_Similarity'].astype(float).mean()

        st.markdown("---")
        col_stat1, col_stat2 = st.columns(2)

        with col_stat1:
            if not pd.isna(ref_score_mean):
                st.metric("Avg. Alignment Score (IS_ALIGNED_WITH)", f"{ref_score_mean:.4f}")
        with col_stat2:
            if not pd.isna(adapt_score_mean):
                st.metric("Avg. Grounding Score (ADAPTED_FROM)", f"{adapt_score_mean:.4f}")