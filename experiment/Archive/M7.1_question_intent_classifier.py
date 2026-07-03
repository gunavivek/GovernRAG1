import os
import json
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from pydantic import BaseModel, ValidationError, Field
from time import sleep
from dotenv import load_dotenv 

# Load environment variables from the .env file immediately
load_dotenv() 

# --- Pydantic Schemas for Multi-Intent LLM Output ---

class IntentScore(BaseModel):
    """Schema for a single predicted intent and its confidence."""
    intent: str = Field(description="One of the primary intent types (Extractive, Summarization, Quantitative, Inferential).")
    confidence: float = Field(description="The confidence score (0.0 to 1.0) for this intent.")
    explanation: str = Field(description="A short reason for this classification.")

class LLMIntentOutput(BaseModel):
    """The root schema for the LLM's multi-intent JSON response."""
    predictions: List[IntentScore]

# --- Configuration Loading ---

def load_config(config_path: str = "config/m7_1_intent_config.json") -> Dict:
    """Loads and validates the configuration file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            required_keys = ["model_name", "api_provider", "output_file", "input_files", "label_definitions"]
            if not all(k in config for k in required_keys):
                raise KeyError("Missing required keys in config file.")
            
            # ADDITION: Define the confidence threshold
            config["confidence_threshold"] = config.get("confidence_threshold", 0.70)
            
            return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}. Please create it.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {config_path}.")
        exit(1)
    except KeyError as e:
        print(f"Error: Configuration file is incomplete: {e}")
        exit(1)

# --- Core LLM Classification Logic ---

def build_system_prompt(label_definitions: Dict[str, str]) -> str:
    """Constructs the detailed system message for the multi-intent LLM call."""
    
    definitions_str = "\n".join([f"- {k}: {v}" for k, v in label_definitions.items()])
    valid_intents = "|".join(label_definitions.keys())
    
    prompt = f"""
You are an expert in question classification for a Business Architecture RAG system.

Analyze the user's question and determine all relevant intents. Assign a confidence score (0.0 to 1.0) to each. The intent definitions are:
{definitions_str}

Return a list of predictions, sorted by confidence, including all intents that apply (up to 4). Ensure the 'intent' value is one of the types listed above.

Respond ONLY with a JSON object containing a 'predictions' array:
{{"predictions": [{{"intent": "<{valid_intents}>", "confidence": 0.95, "explanation": "<short reason>"}}]}}
"""
    return prompt

def classify_question_llm(
    client: OpenAI, 
    question_text: str, 
    config: Dict
) -> Tuple[Optional[List[Dict]], str]:
    """
    Calls the LLM client for multi-intent classification and applies a confidence threshold.
    Returns (List of Confident Intents or None, raw_response_text).
    """
    system_prompt = build_system_prompt(config["label_definitions"])
    model_name = config["model_name"]
    max_retries = 3
    threshold = config["confidence_threshold"]
    
    for attempt in range(max_retries):
        raw_response_text = ""
        try:
            # Use structured output request for reliable JSON generation
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: \"{question_text}\""}
                ],
                response_format={"type": "json_object"},
                temperature=0.1 # Slightly higher temp to encourage multiple ideas
            )
            
            raw_response_text = response.choices[0].message.content
            
            # Pydantic validation handles parsing and basic field structure validation
            json_data = json.loads(raw_response_text)
            validated_output = LLMIntentOutput(**json_data)
            
            # Filter and validate against defined intents and confidence threshold
            confident_intents = []
            valid_intents = set(config["label_definitions"].keys())
            
            for item in validated_output.predictions:
                if item.intent in valid_intents and item.confidence >= threshold:
                    confident_intents.append({
                        "intent": item.intent,
                        "confidence": item.confidence,
                        "explanation": item.explanation
                    })
            
            # Ensure at least one intent is returned if successful, otherwise None
            if confident_intents:
                return confident_intents, raw_response_text
            
            return None, raw_response_text # LLM succeeded but no intent met the threshold

        except (json.JSONDecodeError, ValidationError, ValueError, KeyError) as e:
            print(f"  [Error] Failed to parse LLM output (Attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return None, raw_response_text
            sleep(1) 
        
        except Exception as e:
            print(f"  [API Error] LLM API call failed (Attempt {attempt + 1}): {e}.")
            if attempt == max_retries - 1:
                return None, f"API_FAIL: {str(e)}"
            sleep(2 ** attempt) 

    return None, "" 

# --- Fallback Classifier (Hardcoded Heuristic for Single Intent) ---
# Note: Fallback must return a list of dictionaries to match the new output format.

def fallback_classifier(question_text: str) -> List[Dict[str, Any]]:
    """
    Implements a simple rule-based heuristic as a single-intent fallback.
    """
    question_lower = question_text.lower()
    
    if any(q_word in question_lower for q_word in ["summarize", "describe", "objective", "main goal", "overall purpose"]):
        intent = "Summarization"
    elif any(q_word in question_lower for q_word in ["how many", "what percent", "cost", "date", "when", "by what quarter", "figure", "number"]):
        intent = "Quantitative"
    elif any(q_word in question_lower for q_word in ["why", "how does", "impact", "implication", "conclusion", "reason", "probabl"]):
        intent = "Inferential" 
    else:
        intent = "Extractive"
        
    return [{
        "intent": intent,
        "confidence": 1.0, # Set to 1.0 since it's a forced classification
        "explanation": "Fallback heuristic used due to LLM failure or parsing error."
    }]

# --- Main Execution Loop ---

def run_m7_1_classifier():
    """Main function to orchestrate file reading, classification, and writing."""
    config = load_config()
    
    # 1. Initialize the LLM client
    if config["api_provider"].lower() == "openai":
        try:
            # The client will automatically find the OPENAI_API_KEY loaded by load_dotenv()
            client = OpenAI() 
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}. ")
            print("Please ensure your .env file is present and contains OPENAI_API_KEY.")
            return
    else:
        print("Error: Only 'openai' provider is currently supported in this module.")
        return

    # Create output directory and clear old output file
    os.makedirs(os.path.dirname(config["output_file"]), exist_ok=True)
    if os.path.exists(config["output_file"]):
        os.remove(config["output_file"])
    
    print(f"Starting M7.1 Intent Classification using {config['model_name']}...")
    print(f"Confidence Threshold set at: {config['confidence_threshold'] * 100:.0f}%")
    question_counter = 0

    for file_path in config["input_files"]:
        if not os.path.exists(file_path):
            print(f"Skipping missing input file: {file_path}")
            continue

        file_name = os.path.basename(file_path).split('.txt')[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Could not read {file_path}: {e}")
            continue

        print(f"\nProcessing {len(questions)} questions from {file_name}...")

        for i, question in enumerate(questions):
            question_counter += 1
            question_id = f"{file_name}_{i+1:04d}"
            
            # Attempt LLM Classification (returns list of confident intents)
            confident_intents, raw_llm_response = classify_question_llm(client, question, config)
            
            if confident_intents:
                # Success: At least one intent met the threshold
                final_intents = confident_intents
                raw_response_log = raw_llm_response
            else:
                # Fallback to Heuristic (returns a single-item list)
                final_intents = fallback_classifier(question)
                raw_response_log = f"FALLBACK_USED | Raw: {raw_llm_response}"
            
            # Format the intents for logging
            intent_summary = ", ".join([
                f"{item['intent']} ({item['confidence']:.2f})" for item in final_intents
            ])

            result = {
                "question_id": question_id,
                "question_text": question,
                "predicted_intents": final_intents, # List of objects
                "raw_llm_response": raw_response_log
            }
            
            # Write results immediately to the JSONL file
            with open(config["output_file"], 'a', encoding='utf-8') as outfile:
                outfile.write(json.dumps(result) + '\n')
            
            print(f"  [{intent_summary}] {question_id}: {question[:60]}...")

    print(f"\nFinished classifying {question_counter} questions. Results saved to {config['output_file']}")

if __name__ == '__main__':
    run_m7_1_classifier()