# --------------------------------------------------------------------------
# MODULE 1: Text Chunking (GraphRAG 3.1.2 - Hybrid Two-Pass LLM Split)
# Goal: Cost-effective semantic chunking: Local split first, LLM for size-enforcement only.
# --------------------------------------------------------------------------
import pandas as pd
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
from typing import List

print("--- Starting Module 1: Hybrid Two-Pass LLM Chunking ---")

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use gemini-2.5-flash-lite for cost efficiency on this high-volume task
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite")
RATE_LIMIT_DELAY = 1 # Small delay to prevent burst rate limit errors

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.abspath(os.path.join(BASE_DIR, '../data', 'ragbench_documents.txt'))
OUTPUT_FILE = os.path.abspath(os.path.join(BASE_DIR, '../output', 'M1_Text_Chunks.csv'))

# --- Configuration for LLM Splitting ---
MAX_CHUNK_SIZE = 512 
CHUNK_OVERLAP = 100 # Not used in LLM split logic but kept for documentation

SYSTEM_INSTRUCTION = f"""
You are a text chunking engine. Your task is to take a single large block of text and rewrite it as a list of smaller, non-overlapping, sequential chunks.

Rules:
1. Each resulting chunk MUST NOT exceed {MAX_CHUNK_SIZE} characters in length.
2. Each chunk must be a semantically coherent, self-contained unit (e.g., a sentence or group of related sentences).
3. The output MUST be a valid JSON array of strings. Do not include any other text or explanation.
"""

OUTPUT_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    description="A list of self-contained text chunks.",
    items=types.Schema(type=types.Type.STRING)
)

# --- Core LLM Chunking Function ---
def llm_chunking(text_block: str, client: genai.Client) -> List[str]:
    """Uses the LLM to break a large, unbroken block into smaller semantic chunks."""
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=OUTPUT_SCHEMA,
    )
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=[text_block],
            config=config,
        )
        
        chunks = json.loads(response.text)
        
        # Validation: ensure no chunk exceeds the max size 
        valid_chunks = [c.strip() for c in chunks if isinstance(c, str) and len(c.strip()) <= MAX_CHUNK_SIZE]
             
        return valid_chunks
        
    except Exception as e:
        print(f"  [ERROR] LLM chunking call failed for block. Error: {e}")
        return []

# --- EXECUTION ---
if __name__ == "__main__":
    
    if not GEMINI_API_KEY:
        print("\n[SETUP ERROR] GEMINI_API_KEY not found. LLM-Based Chunking requires an active key.")
        exit(1)

    client = genai.Client(api_key=GEMINI_API_KEY)

    output_dir = os.path.abspath(os.path.join(BASE_DIR, '../output'))
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except FileNotFoundError:
        print(f"\n[ERROR] Input file not found: {INPUT_FILE}")
        exit(1)
        
    # 1. PASS 1: Local/Cost-Effective Macro-Split (Paragraphs)
    paragraph_blocks = [block.strip() for block in full_text.split("\n\n") if block.strip()]
    
    all_chunks = []
    
    print(f"--- Processing {len(paragraph_blocks)} Macro-Blocks ---")
    
    for i, block in enumerate(paragraph_blocks):
        
        if len(block) <= MAX_CHUNK_SIZE:
            # Block fits size limit, use the local chunk
            all_chunks.append(block)
        else:
            # 2. PASS 2: LLM-Guided Micro-Split (Only for oversized blocks)
            print(f"  [LLM SPLIT] Processing oversized block {i+1}/{len(paragraph_blocks)} ({len(block)} chars)...")
            llm_split_chunks = llm_chunking(block, client)
            all_chunks.extend(llm_split_chunks)
            time.sleep(RATE_LIMIT_DELAY) # Respect rate limits

    # 3. Final Assembly and Traceability Tagging
    chunk_data = []
    for i, unit_text in enumerate(all_chunks):
        if unit_text:
            chunk_data.append({
                'chunk_id': i, 
                'chunk_text': unit_text
            })
            
    if chunk_data:
        df_chunks = pd.DataFrame(chunk_data)
        df_chunks.to_csv(OUTPUT_FILE, index=False)
        
        print(f"\n[SUCCESS] Module 1 successfully completed with HYBRID TWO-PASS LLM CHUNKING.")
        print(f"Total semantic chunks created: {len(df_chunks)}")
        print(f"Intermediate artifact saved to: {OUTPUT_FILE}")
    else:
        print("\n[WARNING] No chunks were created. Check API key and input file content.")
        exit(1)