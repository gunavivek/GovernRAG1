import os
import re
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# PhD Strategy: Gemma-3 is used here as a "Governed Narrator." 
# It is structurally forbidden from hallucinating outside the Tiered Evidence.
MODEL_ID = "gemma-3-4b-it"

# CRITICAL UPDATE: Q6 now reads the legally routed packet from Q5
INPUT_FILE = "output/Q5_routed_context.jsonl"
OUTPUT_FILE = "output/Q6_final_answers.jsonl"

def generate_governed_answer(record: dict) -> dict:
    """
    PHD RESEARCH COMPONENT: Q6 - Federated Synthesis (Concept Governance V2)
    Executes the final synthesis using ONLY the Q5-audited payload.
    """
    record_id = record.get('record_id', 'Unknown') 
    question = record.get('question', '')
    
    # Tier 1-2 Evidence Extraction (Already Filtered by Q5)
    triplets = record.get('symbolic_triplets', [])
    text_chunk = record.get('semantic_chunk', '')
    residual_chunks = record.get('residual_context', []) 
    
    # Retrieval of Governance Design Intent
    q2_sig = record.get('q_signature', {})
    authorized_predicates = q2_sig.get('required_predicates', [])
    justification = record.get('justification', {})
    functional_intent = justification.get('target_functional_intent', 'General')
    attribute_targets = q2_sig.get('attribute_targets', [])

    # --- GOVERNANCE GATE 1: EMPIRICAL EXISTENCE CHECK ---
    # If Q5 stripped EVERYTHING because it was invalid, we must block generation.
    if not triplets and not residual_chunks:
        return {
            "record_id": record_id,
            "question": question,
            "final_prompt": None,
            "mode": "BLOCKED_BY_Q5_AUDIT",
            "generated_answer": "Governance Boundary: All retrieved evidence violated D5 authorized predicates. Response blocked.",
            "status": "REJECTED"
        }

    # Format symbolic data for prompt injection
    triplet_string = "\n".join([f"- {t['s']} [{t['p']}] -> {t['o']}" for t in triplets])
    
    # Format residual chunks cleanly for citation
    if isinstance(residual_chunks, list) and residual_chunks:
        residual_string = "\n".join([f"[RESIDUAL_{i}] {chunk}" for i, chunk in enumerate(residual_chunks)])
    else:
        residual_string = "No supplementary residuals approved."

    # --- CONSTRUCT FEDERATED PROMPT (Tiered Authority) ---
    prompt = f"""
    You are a PhD Research Agent executing 'Governed Synthesis'.
    Objective: Answer the question ONLY using the tiered evidence below.
    
    --- TIER 0: GOVERNANCE SIGNATURE ---
    Functional Intent: {functional_intent}
    Authorized Predicates: {authorized_predicates}
    Attribute Targets: {attribute_targets}

    --- TIER 1: ARCHITECTURAL TRUTH (SYMBOLIC TRIPLETS) ---
    {triplet_string}

    --- TIER 1: DESCRIPTIVE CONTEXT ---
    [CHNK_PRIMARY] {text_chunk}

    --- TIER 2: SUPPLEMENTARY RESIDUALS (AUDITED) ---
    {residual_string}

    --- MANDATORY RULES ---
    1. Provide a direct, concise answer first.
    2. You MUST cite sources using [CHNK_PRIMARY] or [RESIDUAL_X].
    3. TIER 1 (Symbolic Triplets) represents verified architectural facts. Prioritize this.
    4. If the info is missing from the provided tiers, state: "Governance Boundary: Evidence insufficient."
    5. Do not use internal knowledge.
    6. Prioritize evidence that matches the Attribute Targets when selecting the answer span.

    QUESTION: {question}
    """
       
    print("\n" + "="*30 + " Q6 FINAL LLM PROMPT " + "="*30)
    print(prompt)
    print("="*80 + "\n")

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0) # Absolute determinism
        )
       
        answer_text = response.text.strip()
        
        # Provenance Check
        if not re.search(r"\[(?:CHNK_[^\]]+|RESIDUAL_[^\]]+)\]", answer_text):
            print(f"[WARNING] Generated answer missing required provenance citation for {record_id}")
            
        return {
            "record_id": record_id,
            "question": question,
            "final_prompt": prompt,
            "generated_answer": answer_text,
            "mode": "SUCCESS_GENERATED",
            "metadata": {
                "triplet_count": len(triplets),
                "chunks_used": len(residual_chunks) if isinstance(residual_chunks, list) else 0,
                "domains": justification.get("domain_focus", [])
            }
        }
    
    except Exception as e:
        raise RuntimeError(f"Q6 synthesis failed for record_id={record_id}: {e}") from e

def run_q6_synthesis():
    print("--- Q6 V2: Governed Synthesis (Final DSR State) ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[FATAL] Input missing: {INPUT_FILE}. Ensure Q5 has run.")
        raise SystemExit(1)

    results = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            record = json.loads(line)
            ans_packet = generate_governed_answer(record)
            results.append(ans_packet)
            print(f"[Q6] Synthesized Answer for: {record['record_id']}")
            
            print(f"\n[Q6] Synthesized Answer for: {record['record_id']}")
            print("-" * 80)
            print(ans_packet.get("generated_answer", "No answer generated."))
            print("-" * 80 + "\n")
            
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for res in results:
            f_out.write(json.dumps(res, ensure_ascii=False) + '\n')
    
    print(f"--- SUCCESS: {len(results)} Final Answers Generated ---")

if __name__ == "__main__":
    run_q6_synthesis()