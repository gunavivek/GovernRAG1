# --------------------------------------------------------------------------
# MODULE 2: Entity and Relationship Extraction
# Goal: Use Gemini to extract Knowledge Triples (S-P-O) from M1 chunks
#       and save the resulting triples to M2_Extracted_Triples.json.
# --------------------------------------------------------------------------
import os
import pandas as pd
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup and Configuration ---
# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash-lite") # Fallback model
# We use the existing OPENAI_API_KEY environment variable
#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
# We use a reliable OpenAI model that is already configured elsewhere in the pipeline (Q3/Q6)
#LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4.1-mini")

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, '../output', 'M1_Text_Chunks.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, '../output', 'M2_Extracted_Triples.json')

# --- 1. Define the LLM Prompt and Output Schema ---

# A robust system instruction ensures the LLM behaves predictably and outputs a clean format.
SYSTEM_INSTRUCTION = """
You are an expert Knowledge Graph Extraction Agent. Your task is to analyze a given text chunk and extract all possible and relevant Subject-Predicate-Object (S-P-O) triples.

Rules for Extraction:
1. Subject and Object should be specific entities (people, concepts, technologies, dates, plans).
2. The Predicate (Relationship) must clearly describe the connection between the Subject and Object.
3. Consolidate entities. For example, use 'Apollo Architecture' instead of 'Apollo'.
4. Do NOT hallucinate; only use information explicitly present in the text.
5. The output MUST be a valid JSON array of objects, where each object has three keys: "subject", "predicate", and "object".

Example Output Format:
[
  {"subject": "Digital Transformation", "predicate": "mandates", "object": "retirement of Platform 2.0"},
  {"subject": "Apollo Architecture", "predicate": "is crucial for", "object": "scalability"}
]
"""

# Define the expected output structure using the Pydantic-like schema for reliable JSON output
OUTPUT_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    description="A list of knowledge triples extracted from the text.",
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "subject": types.Schema(type=types.Type.STRING, description="The subject entity of the fact."),
            "predicate": types.Schema(type=types.Type.STRING, description="The relationship connecting the subject and object."),
            "object": types.Schema(type=types.Type.STRING, description="The object entity of the fact."),
        },
        required=["subject", "predicate", "object"],
    )
)


# --- 2. Core Extraction Function ---
def extract_triples(text_chunk, client):
    """Calls the Gemini API to extract S-P-O triples from a single chunk."""
    
    # Configure the request to use the System Instruction and the structured JSON output
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=OUTPUT_SCHEMA,
    )
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=[text_chunk],
            config=config,
        )
        # The response.text will be a valid JSON string conforming to OUTPUT_SCHEMA
        return json.loads(response.text)
    except Exception as e:
        print(f"  [ERROR] Gemini API call failed for chunk. Error: {e}")
        return []

# --- 3. Main Execution Logic ---
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("\n[SETUP ERROR] GEMINI_API_KEY not found. Please create a .env file and add your key.")
        exit()

    # Initialize Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Load chunks from Module 1
    try:
        df_chunks = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"\n[ERROR] Input artifact not found: {INPUT_FILE}. Please run M1_chunking.py first.")
        exit()
    
    all_triples = []
    
    print(f"\n--- Starting Extraction for {len(df_chunks)} Chunks using {LLM_MODEL_NAME} ---")
    
    for index, row in df_chunks.iterrows():
        chunk_id = row['chunk_id']
        chunk_text = row['chunk_text']
        
        print(f"Processing Chunk ID: {chunk_id}...")
        
        # Call the extraction function
        triples = extract_triples(chunk_text, client)
        
        # Tag each extracted triple with its originating chunk_id for traceability
        for triple in triples:
            triple['source_chunk_id'] = chunk_id
            all_triples.append(triple)
        
    if all_triples:
        # Save all extracted triples to the output JSON file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_triples, f, indent=2)
            
        print(f"\n[SUCCESS] Module 2 successfully completed!")
        print(f"Total Triples Extracted: {len(all_triples)}")
        print(f"Intermediate artifact saved to: {OUTPUT_FILE}")
    else:
        print("\n[WARNING] No triples were extracted. Check your API key and input file.")