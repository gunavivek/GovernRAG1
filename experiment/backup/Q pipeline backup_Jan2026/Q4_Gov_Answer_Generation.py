import os
import json
import time
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2026 PHD STANDARD: Utilizing the Preview model for advanced reasoning
MODEL_ID = "gemini-3-flash-preview"

INPUT_FILE = "output/Q3_retrieved_evidence.jsonl"
OUTPUT_FILE = "output/Q4_final_answers.jsonl"

def generate_neuro_symbolic_answer(record: dict) -> dict:
    """
    Synthesizes the final answer aligned with the Dissertation Proposal (v3).
    Includes Research Audit Prints for Grounding and Traceability.
    """
    record_id = record.get('record_id', 'Unknown') 
    question = record.get('question', '')
    triplets = record.get('symbolic_triplets', [])
    text_chunk = record.get('semantic_chunk', '')
    contributing_chunks = record.get('contributing_chunks', [])

    # --- GOVERNANCE GATE: CLOSED-WORLD ENFORCEMENT ---
    if not triplets or len(triplets) == 0:
        return {
            "record_id": record_id,
            "question": question,
            "generated_answer": "Governance Boundary: Insufficient governed evidence to support a response.",
            "mode": "BLOCKED_BY_GOVERNANCE",
            "triplet_count": 0
        }

    # Format symbolic data for prompt injection
    triplet_string = "\n".join([f"- {t['s']} [{t['p']}] -> {t['o']}" for t in triplets])

    # --- CONSTRUCT AGNOSTIC NEURO-SYMBOLIC PROMPT (V4.4 - GOLD STANDARD) ---
    prompt = f"""
    You are a PhD Research Agent executing the 'Synthesis' phase of a Design Science Research project. 
    Your objective is to generate a 'Governed Synthesis' that adheres to strict Business Architecture constraints.

    --- ARCHITECTURAL TRUTH: SYMBOLIC TRIPLETS ---
    {triplet_string}

    --- DESCRIPTIVE CONTEXT: SEMANTIC CHUNKS ---
    {text_chunk}

    --- MANDATORY GOVERNANCE RULES (ZERO-DEVIATION POLICY) ---
    1. PRECISE ANSWER FIRST: Start the response with a direct, one-sentence answer to the user's question.
    2. AUTHORITY HIERARCHY: SYMBOLIC TRIPLETS are the primary truth. If a semantic chunk contradicts a triplet, you MUST prioritize the triplet and explicitly note the discrepancy.
    3. DESCRIPTIVE ENRICHMENT: Use SEMANTIC CHUNKS only to provide human-readable attributes (names, dates, descriptions) for entities already identified in the TRIPLETS.
    4. FRAGMENT-LEVEL PROVENANCE: Every factual claim MUST be followed by its specific source [CHNK_ID].
    5. UNVERIFIED CONTEXT HANDLING: If a fact exists in a SEMANTIC CHUNK but has no corresponding SYMBOLIC TRIPLET, you must label it as "Descriptive context (unverified by architecture)."
    6. CLOSED-WORLD ASSUMPTION: Use NO external knowledge or training data. If the provided context is insufficient, state: "Governance Boundary: Symbolic evidence missing for [Entity]."
    7. TRACEABILITY: Cite the parent Record ID [{record_id}] at the very end.

    USER QUESTION: {question}

    --- GOVERNED SYNTHESIS WITH ARCHITECTURAL GROUNDING ---
    [Provide the direct answer here first, then follow with a "Justification and Governance" section.]
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.MEDIUM 
                )
            )
        )
        
        generated_text = response.text.strip() if response.text else "Error: Empty response."

        # --- RESEARCH AUDIT LOG: VISIBILITY FOR DISSERTATION EVALUATION ---
        print("\n" + "!" * 30 + " GOVERNED RESEARCH AUDIT " +"-Q4"+ "!" * 30)
        print(f"RECORD ID   : {record_id}")
        print(f"QUESTION    : {question}")
        print("-" * 85)
        print(f"FINAL ANSWER:\n{generated_text}")
        print("-" * 85)
        print("SOURCE CHUNK CONTEXT (The Grounding Evidence):")
        # text_chunk contains the [CHNK_ID] and the raw document text retrieved in Q3
        print(text_chunk if text_chunk else "[No Semantic Context Provided]")
        print("!" * 85 + "\n")
        # ------------------------------------------------------------------

        return {
            "record_id": record_id,
            "question": question,
            "generated_answer": generated_text,
            "mode": "GENERATED",
            "triplet_count": len(triplets),
            "text_length": len(text_chunk),
            "cited_chunks": contributing_chunks
        }
    except Exception as e:
        return {
            "record_id": record_id, 
            "mode": "ERROR", 
            "error": f"Synthesis Failure: {str(e)}"
        }

def run_q4_synthesis():
    """Batch synthesis mode for dissertation pipeline execution"""
    print("--- Starting Q4 V4.3: Concept-Enhanced Research Synthesis ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[FATAL] Q3 evidence file not found at {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            record = json.loads(line)
            rid = record.get('record_id', 'Unknown')
            
            result = generate_neuro_symbolic_answer(record)
            outfile.write(json.dumps(result, ensure_ascii=False) + '\n')
            
            time.sleep(0.5) 

    print(f"--- SUCCESS: Final Governed Answers saved to {OUTPUT_FILE} ---")

if __name__ == "__main__":
    run_q4_synthesis()