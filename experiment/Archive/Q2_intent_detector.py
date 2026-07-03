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
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")

# Initialize real GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Load spaCy model for symbolic rules
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Configuration & File Paths
INPUT_FILE = 'output/Q1_domain_router.jsonl'
OUTPUT_FILE = 'output/Q2_intents.jsonl' 

# Combined Taxonomy: spaCy + Gemini labels
INTENT_LABELS = [
    "Extractive", "Summarization", "Quantitative", "Inferential", 
    "Complex", "Unknown", "Comparison", "Trend", "Navigational"
]

# --- 1. Hybrid intent layer 1: spaCy Rule Engine (Structural) ---

def apply_spacy_rules(text: str) -> Optional[str]:
    """Uses spaCy's Matcher for deterministic intent detection."""
    matcher = Matcher(nlp.vocab)
    doc = nlp(text)

    # Comparison Pattern: Detects versus, vs, compare, etc.
    matcher.add("Comparison", [[{"LOWER": {"IN": ["compare", "versus", "vs", "difference", "than", "better", "worse"]}}]])
    
    # Trend Pattern: Detects time-series intent
    matcher.add("Trend", [[{"LOWER": {"IN": ["trend", "history", "monthly", "yearly", "growth", "increase", "decrease"]}}]])
    
    # Navigational Pattern: Detects direct commands followed by proper nouns
    matcher.add("Navigational", [[{"LOWER": {"IN": ["find", "show", "open", "get"]}}, {"POS": "PROPN"}]])

    matches = matcher(doc)
    if matches:
        match_id, start, end = matches[0]
        return nlp.vocab.strings[match_id]
    return None

# --- 2. Hybrid intent layer 2: Gemini Integration (Semantic) ---

def call_llm_api(prompt: str) -> Optional[Dict[str, Any]]:
    """Calls Gemini 2.5 Flash for high-level semantic classification."""
    try:
        # Define response schema to enforce JSON structure
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "intent": {"type": "STRING", "enum": ["Summarization", "Inferential", "Complex", "Unknown", "Extractive", "Quantitative"]},
                "explanation": {"type": "STRING"},
                "nuance_detected": {"type": "BOOLEAN"}
            },
            "required": ["intent", "explanation", "nuance_detected"]
        }

        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=response_schema,
                temperature=0.1 
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"[Q2][ERROR] LLM failure: {e}")
        return None

# --- 3. Prompt Construction ---

def create_q2_prompt(question_text: str, primary_domain: str) -> str:
    """Builds the prompt focused on semantic/complex reasoning."""
    intent_definitions = """
    1. Summarization: Seeks a synthesis or high-level overview.
    2. Inferential: Seeks analysis of impact, reasons, or relationships.
    3. Complex: Query requires multi-step logic or crosses multiple communities.
    4. Unknown: Query is out-of-scope, ambiguous, or lacks conceptual grounding.
    5. Extractive/Quantitative: Simple factual retrieval or single numbers.
    """
    return f"""
**SYSTEM INSTRUCTION:** You are a Query Gatekeeper. Classify the semantic intent:
{intent_definitions}

**INPUT:**
DOMAIN: {primary_domain}
QUESTION: "{question_text}"

**OUTPUT FORMAT:** Return JSON: {{"intent": "...", "explanation": "...", "nuance_detected": bool}}
""".strip()

# --- 4. Main Driver ---

def run_q2_intent_module():
    print("--- Q2: Hybrid spaCy + Gemini Intent Detector Started ---")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            q1_data = json.loads(line)
            text = q1_data.get('question', '')
            
            # Step 1: Deterministic check via spaCy
            spacy_intent = apply_spacy_rules(text)
            
            if spacy_intent:
                out_record = {
                    **q1_data, 
                    "intent": spacy_intent, 
                    "intent_explanation": "Detected by spaCy rule-based matcher.",
                    "nuance_detected": False,
                    "q2_notes": "Rule-based match."
                }
            else:
                # Step 2: Semantic fallback via Gemini
                prompt = create_q2_prompt(text, q1_data.get('primary_domain', 'General'))
                llm_result = call_llm_api(prompt)
                
                # Merge and handle fallback
                out_record = {**q1_data}
                if llm_result:
                    out_record.update(llm_result)
                else:
                    out_record.update({"intent": "Unknown", "explanation": "LLM failed."})
                out_record["q2_notes"] = "Classified by Gemini."
            
            outfile.write(json.dumps(out_record) + '\n')

    print(f"--- Q2: Completed. Output: {OUTPUT_FILE} ---")

if __name__ == "__main__":
    run_q2_intent_module()