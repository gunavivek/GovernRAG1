import json
import os
import spacy
from spacy.matcher import Matcher
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client (Flash 2.0 recommended for speed/gatekeeping)
client = genai.Client(api_key=GEMINI_API_KEY)

# Load spaCy model for structural Logic Gates
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# File Paths (Aligned with Q1_v2 output)
INPUT_FILE = 'output/Q1_domain_router.jsonl'
OUTPUT_FILE = 'output/Q2_intents.jsonl'

# --- 1. Symbolic Logic Gate (spaCy Rule Engine) ---

def apply_symbolic_gates(text: str) -> Optional[str]:
    """
    Detects structural patterns that force specific GraphRAG behaviors.
    H3 Trigger: 'Comparison' mandates triangulation between multiple nodes.
    """
    matcher = Matcher(nlp.vocab)
    doc = nlp(text)

    # Comparison Gate: 'both', 'difference', 'versus', 'compared to'
    matcher.add("Comparison", [[{"LOWER": {"IN": ["compare", "versus", "vs", "difference", "than", "both", "between"]}}]])
    
    # Trend/Temporal Gate: 'history', 'evolution', 'changes over time'
    matcher.add("Trend", [[{"LOWER": {"IN": ["trend", "history", "monthly", "yearly", "growth", "evolution"]}}]])
    
    # Navigational Gate: Direct retrieval commands
    matcher.add("Navigational", [[{"LOWER": {"IN": ["find", "show", "get", "locate"]}}, {"POS": "PROPN"}]])

    matches = matcher(doc)
    if matches:
        match_id, start, end = matches[0]
        return nlp.vocab.strings[match_id]
    return None

# --- 2. Semantic Logic Gate (Gemini Integration) ---

def call_llm_intent(question: str, domain: str) -> Dict[str, Any]:
    """
    PhD Governance Layer: Disambiguates 'Inferential' vs 'Extractive' 
    to set the search budget for Q45.
    """
    intent_definitions = """
    - Extractive: Simple factual lookup (1-hop).
    - Summarization: Synthesis of multiple nodes.
    - Quantitative: Numerical aggregation or counting.
    - Inferential: Analyzing impact or relationships between concepts (Multi-hop).
    - Complex: Requires multi-community traversal.
    - Temporal: Specific date/sequence ordering.
    - Unknown: Ambiguous or out-of-governance scope.
    """

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "intent": {"type": "STRING", "enum": ["Extractive", "Summarization", "Quantitative", "Inferential", "Complex", "Temporal", "Unknown"]},
            "explanation": {"type": "STRING"}
        },
        "required": ["intent", "explanation"]
    }

    prompt = f"""
**SYSTEM:** You are a Governed Query Agent. Classify the intent for a GraphRAG system.
{intent_definitions}

**CONTEXT:**
DOMAIN: {domain}
QUESTION: "{question}"

**OUTPUT:** Return JSON only.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=response_schema,
                temperature=0.0 
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[Q2_v2][ERROR] LLM Gate Failure: {e}")
        return {"intent": "Unknown", "explanation": "Fallback due to API error."}

# --- 3. Main Execution Driver ---

def run_q2_v2_intent_detector():
    print("--- Q2_v2: Hybrid Intent Detector (Logic Gate Trigger Mode) ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Q1_v2 input not found at {INPUT_FILE}")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            record = json.loads(line)
            text = record.get('question', '')
            domain = record.get('primary_domain', 'General')
            
            # PHASE 1: Symbolic Check (Fast/Pattern-based)
            intent = apply_symbolic_gates(text)
            explanation = "Structural pattern detected by spaCy."
            
            # PHASE 2: Semantic Check (LLM-based)
            if not intent:
                llm_res = call_llm_intent(text, domain)
                intent = llm_res['intent']
                explanation = llm_res['explanation']
            
            # PHASE 3: Update and Passthrough
            # CRITICAL: Preserve record_id, z_score, and governance_status for Q45
            record.update({
                "intent": intent,
                "intent_explanation": explanation,
                "q2_v2_status": "Logic Gate Triggered"
            })
            
            outfile.write(json.dumps(record, ensure_ascii=False) + '\n')
            count += 1
            print(f"[Q2_v2] ID: {record.get('id')} -> Intent: {intent}")

    print(f"--- SUCCESS: {count} Records Processed to {OUTPUT_FILE} ---")

if __name__ == "__main__":
    run_q2_v2_intent_detector()