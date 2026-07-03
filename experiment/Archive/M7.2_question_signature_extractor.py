import os
import json
import time 
import networkx as nx 
import spacy
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from google import genai 
from google.genai import types 
from dotenv import load_dotenv 

# --- CONFIGURATION AND SETUP ---
load_dotenv() 
# Define LLM/API settings
LLM_CLIENT_MODEL = "gpt-3.5-turbo" 
M4_HYBRID_GRAPH_PATH = "output/M4_Hybrid_Graph.gml" # CRITICAL INPUT: M4 graph for all nodes
RATE_LIMIT_DELAY = 1

# Initialize Global NLP Resources
try:
    NLP = spacy.load("en_core_web_sm") 
except OSError:
    print("Error: spaCy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'.")
    exit()

# --- Utility Functions for LLM Communication ---

def get_llm_client() -> Optional[OpenAI]:
    """Initializes and returns the OpenAI client."""
    try:
        client = OpenAI() 
        return client
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client for M7.2 LLM features: {e}. ")
        return None

def load_graph_concepts(gml_path: str = M4_HYBRID_GRAPH_PATH) -> List[str]:
    """Loads ALL unique concepts (Node IDs) from the M4 Hybrid Graph for mapping."""
    if not os.path.exists(gml_path):
        print(f"CRITICAL WARNING: M4 Hybrid Graph not found at {gml_path}. Standardization will be skipped.")
        return []
    try:
        G = nx.read_gml(gml_path)
        # Return the list of ALL node IDs (Reference, Document, Adaptive)
        return list(G.nodes)
    except Exception as e:
        print(f"Error loading M4 Graph GML: {e}. Skipping mapping.")
        return []


def rewrite_query_for_context_llm(client: Optional[OpenAI], question: str, history: Optional[List[str]]) -> str:
    """Step 1: Rewrites a conversational question into a standalone query."""
    if not history:
        return question

    if any(word in question.lower().split() for word in ["it", "they", "its"]):
        return f"Context from previous query: '{history[-1]}'. Question: {question}"
    return question


def generate_expanded_queries_llm(client: Optional[OpenAI], query: str) -> List[str]:
    """Step 4: Generates synonyms and paraphrases using the LLM."""
    if not client:
        return [query]

    system_prompt = (
        "You are an expert search query generator. Given a user query, generate 3 "
        "semantically equivalent search queries using different synonyms and phrasing. "
        "Respond ONLY with a JSON array of strings. Example: [\"query 1\", \"query 2\", \"query 3\"]"
    )

    try:
        # Rate limit protection
        time.sleep(RATE_LIMIT_DELAY) 
        
        response = client.chat.completions.create(
            model=LLM_CLIENT_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Original Query: {query}"}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        # Robust parsing logic remains for JSON safety
        raw_parsed = json.loads(response.choices[0].message.content)
        raw_list = []
        if isinstance(raw_parsed, list): raw_list = raw_parsed
        elif isinstance(raw_parsed, dict):
            for key in raw_parsed.values():
                if isinstance(key, list): raw_list = key; break
        
        final_expanded_queries = [q for q in raw_list if isinstance(q, str)]
        expanded_list = list(set([query] + final_expanded_queries))
        return expanded_list
    
    except Exception as e:
        # print(f"LLM expansion failed ({e}). Returning original query only.")
        return [query]


# --- CORE FUNCTION: ADAPTIVE CONCEPT MAPPING (Step 3) ---
def map_concepts_to_graph_nodes(client: Optional[OpenAI], concepts: List[str], graph_nodes: List[str]) -> List[Dict[str, str]]:
    """
    Step 3: Maps extracted linguistic concepts to the closest Node ID in the M4 Graph 
    (Reference, Document, or Adaptive) and determines the mapping status.
    """
    if not client or not graph_nodes or not concepts:
        return [{"raw_concept": c, "mapped_node_id": "UNMAPPED_GENERIC", "mapping_status": "NONE"}]

    # Use a large, representative sample of nodes (first 500) to guide the LLM's mapping choice
    prompt_nodes = graph_nodes[:500] 

    system_prompt = (
        "You are an expert Semantic Mapper. Your goal is to standardize user concepts against the provided Graph Node List. "
        "Your final decision must include a semantic status: 'IS_ALIGNED_WITH' (direct match) or 'ADAPTED_FROM' (fuzzy/novel match)."
    )
    
    user_prompt = (
        f"M4 Graph Node List:\n{prompt_nodes}\n\n"
        f"Concepts to Map: {', '.join(concepts)}. "
        "For each concept, output the closest Node ID from the list and its status ('IS_ALIGNED_WITH' or 'ADAPTED_FROM'). "
        "If a match cannot be found, use 'UNMAPPED_NO_MATCH'."
        "Output ONLY a JSON array of objects with keys: 'raw_concept', 'mapped_node_id', 'mapping_status'."
    )
    
    try:
        # Rate limit protection for the mapping call
        time.sleep(RATE_LIMIT_DELAY) 
        
        response = client.chat.completions.create(
            model=LLM_CLIENT_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        mapping_result = json.loads(response.choices[0].message.content)
        
        # Robust parsing to handle array or dictionary wrapper
        final_list = []
        if isinstance(mapping_result, dict) and mapping_result.get('mapped_concepts'): 
            mapping_result = mapping_result['mapped_concepts']
        
        if isinstance(mapping_result, list):
             for item in mapping_result:
                if isinstance(item, dict) and item.get('mapped_node_id'):
                    final_list.append(item)
        
        return final_list
        
    except Exception as e:
        # print(f"LLM M4 mapping failed ({e}). Defaulting to generic concepts.")
        return [{"raw_concept": c, "mapped_node_id": "UNMAPPED_NO_MATCH", "mapping_status": "NONE"} for c in concepts]


# --- Input Handling ---

def load_m7_1_output(file_path: str = "output/M7_1_intents.jsonl") -> List[Dict[str, Any]]:
    """Reads and loads all classified questions from the M7.1 JSONL output file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"M7.1 output file not found at: {file_path}")
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try: questions.append(json.loads(line))
                except json.JSONDecodeError: print(f"Skipping malformed JSON line: {line.strip()}")
    return questions

# --- Main M7.2 Logic ---

def extract_signature(
    m7_1_output: Dict[str, Any], 
    llm_client: Optional[OpenAI],
    graph_nodes: List[str] # INPUT: ALL M4 graph nodes
) -> Dict[str, Any]:
    """
    M7.2 Core Function: Transforms M7.1 output into the final M4-enhanced search signature.
    """
    q_text = m7_1_output["question_text"]
    history = m7_1_output.get("history", []) 
    intents = m7_1_output.get("predicted_intents", [])
    
    primary_intent = intents[0]['intent'] if intents else "Extractive"
    
    # 1. Query Rewriting for Context
    rewritten_query = rewrite_query_for_context_llm(llm_client, q_text, history)
    
    # 2. Linguistic Processing (Extract raw concepts to be mapped)
    doc = NLP(rewritten_query)
    concepts_to_map = set()
    
    search_targets = {"NOUN", "PROPN"}
    for token in doc:
        if token.pos_ in search_targets and not token.is_stop and len(token.text) > 2:
            concepts_to_map.add(token.lemma_.lower()) 

    # 3. M4 Graph-Mediated Concept Mapping (CORE NEW STEP)
    # The output is a list of structured mappings
    mapped_concepts = map_concepts_to_graph_nodes(llm_client, list(concepts_to_map), graph_nodes)
    
    # 4. Query Expansion
    expanded_queries = generate_expanded_queries_llm(llm_client, rewritten_query)

    # 5. Intent-Based Refinement (Hardcoded Corrections for better retrieval)
    is_numerical_query = any(k in q_text.lower() for k in ["year", "quarter", "percent", "cost", "number", "time", "reduction"])
    if is_numerical_query and primary_intent != "Quantitative":
        primary_intent = "Quantitative" 

    # 6. Final Signature Assembly
    return {
        "question_id": m7_1_output["question_id"],
        "question_text": q_text,
        "primary_intent": primary_intent,
        "rewritten_query": rewritten_query,
        "search_signature": {
            "mapped_concepts": mapped_concepts, # The final list of structured mappings
            "raw_concepts": list(concepts_to_map)
        },
        "expanded_queries": expanded_queries
    }

# --- Driver Execution ---

def run_m7_2_extractor(input_file: str = "output/M7_1_intents.jsonl", output_file: str = "output/M7_2_signatures.jsonl"):
    """Main function to load M7.1 output, process signatures, and save results."""
    
    # 1. Initialize LLM client and load M4 Graph Nodes (All Concepts)
    llm_client = get_llm_client() 
    graph_nodes = load_graph_concepts() # Loads all nodes from M4 GML
    
    if not graph_nodes:
        print("CRITICAL WARNING: M4 Graph not found. Standardization will be skipped.")
        
    # 2. Load M7.1 output
    try:
        m7_1_results = load_m7_1_output(input_file)
    except FileNotFoundError as e:
        print(e)
        return
    
    # Create output directory and clear old output file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    if os.path.exists(output_file):
        os.remove(output_file)

    print(f"--- Running M7.2: Adaptive Graph Signature Extractor on {len(m7_1_results)} questions ---")
    
    all_signatures = []
    
    for m7_1_item in m7_1_results:
        # Process the question into a signature
        signature = extract_signature(m7_1_item, llm_client, graph_nodes)
        all_signatures.append(signature)
        
        # Write results immediately to the JSONL file
        with open(output_file, 'a', encoding='utf-8') as outfile:
            outfile.write(json.dumps(signature) + '\n')
            
        print(f"Processed {signature['question_id']} | Primary: {signature['primary_intent']}")
        print(f"  Nodes Mapped: {len(signature['search_signature']['mapped_concepts'])}")
        
    print(f"\nSuccessfully generated {len(all_signatures)} search signatures. Results saved to {output_file}")
    
if __name__ == '__main__':
    # NOTE: You will need to manually create a dummy M7_1_intents.jsonl file 
    #       for this script to run successfully for testing.
    run_m7_2_extractor()