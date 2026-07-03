import json
import os
import re
from typing import List, Dict, Any, Optional
from tqdm import tqdm

# --- Configuration ---
# INPUTS: As per E2.0 Specification
Q5_RETRIEVAL_PATH = "output/Q5_retrieval_plan.jsonl"  # Final routing decisions (Q3/Q4/M6 data assumed merged here)
E1_INPUT_PATH = "eval/E1_2_type_aware_accuracy.jsonl" # Source of IDs to process
E2_OUTPUT_PATH = "eval/E2_0_path_variables.jsonl" # Causal Variables Output

# --- Utility: Load JSONL to Map ---

def load_jsonl_to_map(path: str, key_field: str = 'id') -> Dict[str, dict]:
    """Loads a JSONL file into a dictionary keyed by ID."""
    data_map = {}
    if not os.path.exists(path):
        print(f"Warning: Input file not found at {path}. Returning empty map.")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if key_field in record:
                        data_map[record[key_field]] = record
                except json.JSONDecodeError:
                    continue # Skip corrupted lines
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return {}
    return data_map

# --- Core E2.0 Calculation Functions ---

def analyze_concept_utilization(
    retrieval_contexts: List[Dict[str, Any]], 
    m6_node_types: Dict[str, str] # Map from Node ID to NodeType (M4/M6 Lookup)
) -> Dict[str, int]:
    """
    Quantifies GraphRAG utilization by counting the usage of M4-classified node types.
    [cite_start]This proves the utilization of the BIZBOK semantic layer[cite: 66].
    """
    used_adaptive_concepts = 0
    used_reference_concepts = 0
    used_document_concepts = 0

    # Collect all unique concept nodes retrieved across all chunks
    retrieved_concept_ids = set()
    for context in retrieval_contexts:
        # Assumes 'concept_nodes' holds the IDs of concepts linked to the chunk
        for concept_id in context.get('concept_nodes', []):
            if concept_id:
                retrieved_concept_ids.add(concept_id)

    # Check the type for each retrieved concept ID
    for concept_id in retrieved_concept_ids:
        # Look up the node_type from the M6 graph metadata
        node_type = m6_node_types.get(concept_id, 'UnmappedConcept')

        if node_type == "AdaptiveConcept":
            used_adaptive_concepts += 1
        elif node_type == "ReferenceConcept":
            used_reference_concepts += 1
        elif node_type == "DocumentConcept":
            used_document_concepts += 1
            
    return {
        [cite_start]"used_adaptive_concepts": used_adaptive_concepts, # Thesis Proof: Quantifies novel, high-confidence concepts [cite: 67]
        [cite_start]"used_reference_concepts": used_reference_concepts, # Governance Proof: Quantifies authoritative BIZBOK standards [cite: 67]
        [cite_start]"used_document_concepts": used_document_concepts, # Quantifies generic concepts that failed alignment [cite: 67]
    }

def check_concept_alignment(q_layer_concept: str, seed_nodes: List[Dict[str, Any]]) -> int:
    """
    Checks if the question's structured concept (Q3 signature) aligns with the primary 
    [cite_start]seed nodes chosen by the Q4 router[cite: 70].
    """
    if not q_layer_concept or not seed_nodes:
        return 0

    # Normalize Q3 concept for case-insensitive and safe matching
    q_concept_normalized = re.sub(r'[^a-z0-9]', '', q_layer_concept.lower())
    
    # Check if the normalized Q3 concept appears in any seed node ID
    for seed in seed_nodes:
        seed_id = seed.get('node_id', '')
        seed_id_normalized = re.sub(r'[^a-z0-9]', '', seed_id.lower())
        
        if q_concept_normalized and q_concept_normalized in seed_id_normalized:
            return 1 # Success
            
    return 0 # Failure

# --- Main E2.0 Runner ---

def run_e2_0_variable_generation(e1_path: str, q5_path: str):
    """
    Loads necessary pipeline data, calculates the Causal Variables (E2.0 metrics), 
    [cite_start]and saves the enriched output[cite: 73].
    """
    # Load E1.2 data (to get the list of IDs to process)
    e1_data = load_jsonl_to_map(e1_path)
    
    # Load Q5 data (contains the retrieval outputs)
    q5_data = load_jsonl_to_map(q5_path)

    # --- SIMULATION: M6 Node Types Lookup ---
    # This dictionary simulates the lookup table extracted from the M6_Clustered_Graph.gml file,
    # [cite_start]which holds the node_type assigned during M4: Concept Alignment[cite: 62].
    m6_node_types_lookup = {
        "Apollo Architecture": "AdaptiveConcept",
        "cloud-native architecture": "DocumentConcept",
        "Digital Transformation": "AdaptiveConcept",
        "Platform 2.0": "ReferenceConcept",
        "Legal Regulation": "ReferenceConcept",
        "Supplier Contract": "DocumentConcept",
        "procurement process": "DocumentConcept",
        "Customer Feedback": "DocumentConcept",
        "Product Catalog": "ReferenceConcept",
        # Example concepts (Ensure all concepts used in Q5 dummy data are covered)
    }
    
    if not e1_data or not q5_data:
        print("Error: Could not load required E1 or Q5 data. Exiting E2.0.")
        return

    os.makedirs(os.path.dirname(E2_OUTPUT_PATH), exist_ok=True)
    evaluation_results = []
    
    print(f"Starting E2.0 Variable Generation for {len(e1_data)} records...")
    
    for record_id, e1_record in tqdm(e1_data.items(), desc="Generating Causal Variables"):
        q5_record = q5_data.get(record_id)
        
        if not q5_record:
            continue
            
        # --- INPUT EXTRACTION (Assumes merging has occurred) ---
        q_layer = q5_record.get('Q_layer', {})
        q_layer_concept = q_layer.get('concept', '')

        retrieval_contexts = q5_record.get('retrieval_contexts', [])
        seed_nodes = q5_record.get('seed_nodes', [])
        
        # --- 1. CONCEPT UTILIZATION (M4 Validation) ---
        utilization_metrics = analyze_concept_utilization(retrieval_contexts, m6_node_types_lookup)

        # --- 2. ROUTING ALIGNMENT (Q3/Q4 Validation) ---
        alignment_flag = check_concept_alignment(q_layer_concept, seed_nodes)
        
        # [cite_start]Quantify GraphRAG component (clustering) [cite: 68, 70]
        num_communities_used = len(q5_record.get('candidate_communities', []))
        num_seeds_used = len(seed_nodes)

        # --- STORE CAUSAL VARIABLES ---
        
        result_record = {
            "id": record_id,
            "used_adaptive_concepts": utilization_metrics['used_adaptive_concepts'],
            "used_reference_concepts": utilization_metrics['used_reference_concepts'],
            "used_document_concepts": utilization_metrics['used_document_concepts'], # Added for full traceability
            "seeds_aligned_to_q3_concept": alignment_flag,
            "num_communities_used": num_communities_used,
            "num_seeds_used": num_seeds_used,
            "q_layer_concept": q_layer_concept, 
        }
        
        evaluation_results.append(result_record)

    # [cite_start]Save the output (Input for E2.1 Correlation Analysis) [cite: 74]
    print(f"Saving Causal Variables to {E2_OUTPUT_PATH}...")
    with open(E2_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for record in evaluation_results:
            f.write(json.dumps(record) + '\n')
            
    print("E2.0 Path Variable Generation Complete.")


# --- Execution Example ---
if __name__ == "__main__":
    
    # 1. Setup Dummy Files for Testing
    os.makedirs('output', exist_ok=True)
    os.makedirs('eval', exist_ok=True)

    # Example record simulating the Q5 output from the 'Apollo' scenario
    q5_dummy_data = [
        # Record 1: SUCCESS (Uses Adaptive Concept, Reference Concept, and aligns concept)
        {"id": "test_id_1", 
         "Q_layer": {"concept": "cloud-native architecture"},
         "retrieval_contexts": [
             {"concept_nodes": ["Apollo Architecture", "Platform 2.0", "cloud-native architecture"]},
             {"concept_nodes": ["Legal Regulation", "Supplier Contract"]},
         ],
         "seed_nodes": [{"node_id": "cloud-native architecture"}],
         "candidate_communities": [{"community_id": "COMMUNITY_A"}]},
         
        # Record 2: PARTIAL SUCCESS (Misaligned concept, uses only Document Concept/Reference)
        {"id": "test_id_2", 
         "Q_layer": {"concept": "Customer Feedback"},
         "retrieval_contexts": [
             {"concept_nodes": ["Customer Feedback", "Product Catalog"]},
             {"concept_nodes": ["Supplier Contract"]},
         ],
         "seed_nodes": [{"node_id": "product catalog"}], # Intentional Mismatch to Q_layer concept
         "candidate_communities": [{"community_id": "COMMUNITY_B"}, {"community_id": "COMMUNITY_C"}],
         },
    ]
    with open(Q5_RETRIEVAL_PATH, 'w', encoding='utf-8') as f:
        for record in q5_dummy_data:
            f.write(json.dumps(record) + '\n')

    # 2. Simulate E1.2 Input (Just needs IDs for the loop)
    e1_dummy_data = [{"id": "test_id_1", "response": "Apollo"}, {"id": "test_id_2", "response": "15%"}]
    with open(E1_INPUT_PATH, 'w', encoding='utf-8') as f:
        for record in e1_dummy_data:
            f.write(json.dumps(record) + '\n')

    # Run E2.0
    print("--- Running E2.0 Path Variable Generation ---")
    run_e2_0_variable_generation(E1_INPUT_PATH, Q5_RETRIEVAL_PATH)
    
    print("\n--- E2.0 Simulation Results Check ---")
    print("Expected: ID 1 should show high Adaptive/Reference counts and seeds_aligned=0 or 1.")
    print("Expected: ID 2 should show high Document/Reference counts and seeds_aligned=0.")
    print(f"Check the contents of {E2_OUTPUT_PATH} for the generated Causal Variables.")