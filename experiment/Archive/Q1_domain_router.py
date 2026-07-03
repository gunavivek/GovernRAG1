import json
import os
from typing import Dict, Any

# --- Configuration & File Paths ---
CONFIG_PATH = 'config/ragbench_subset_to_domain.json'
# Input from the D1 program (must exist in the 'output' folder)
INPUT_FILE = 'data/D1_Test_file.jsonl' 
# Output file for the single processed record
OUTPUT_FILE = 'output/Q1_domain_router.jsonl' 

# --- Core Logic Functions ---

def load_domain_mapping(config_path: str) -> Dict[str, str]:
    """Loads the static dataset-to-domain mapping from a JSON configuration file."""
    try:
        # Assuming the config file is stored relative to the project root
        config_full_path = os.path.join(os.getcwd(), config_path)
        with open(config_full_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config at {config_path}: {e}")
        return {}

def route_question_domain(question_data: Dict[str, Any], domain_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Assigns a business domain based on the 'dataset_name' field, handling 
    concatenated formats (e.g., 'subset_split').
    """
    
    dataset_name_raw = question_data.get("dataset_name", "NA") 
    
    # CRITICAL FIX: Extract the core subset name (e.g., 'cuad_train' -> 'cuad')
    subset_name = dataset_name_raw.lower().split('_')[0]
    
    lookup_key = subset_name
    
    # Core Logic: Lookup the domain or use the 'General' default
    # Fallback ensures 'NA' key is used if possible, or 'General' as a final resort.
    primary_domain = domain_map.get(lookup_key, domain_map.get("na", "General")) 
    
    # Determine confidence based on successful lookup
    confidence = 0.95 if lookup_key in domain_map else 0.50
    routing_notes = (
        f"Domain derived from extracted subset='{subset_name}' via configuration mapping." 
        if confidence == 0.95 else 
        f"Extracted subset '{subset_name}' not found; defaulted to '{primary_domain}'."
    )
    
    # Augment the input data with the routing information, retaining all original fields
    question_data["primary_domain"] = primary_domain
    question_data["domains"] = [{ "name": primary_domain, "confidence": confidence }]
    question_data["routing_notes"] = routing_notes
    
    return question_data

# --- Main Execution Script ---

def main():
    """Reads one record, routes it, and prints the summary."""
    
    print("--- Q1: Domain Router (Single Record Test Mode) ---")
    
    # 1. Load Configuration
    domain_mapping = load_domain_mapping(CONFIG_PATH)
    if not domain_mapping:
        print("Fatal: Domain mapping is empty or failed to load. Exiting.")
        return

    processed_record = None
    
    # 2. Process Input File (Read only the FIRST line)
    try:
        # Input file is assumed to be in the project 'output' folder
        input_full_path = os.path.join(os.getcwd(), INPUT_FILE)
        
        with open(input_full_path, 'r') as infile:
            first_line = infile.readline().strip()
            
            if not first_line:
                print(f"Input file {INPUT_FILE} is empty or not found.")
                return
            
            # Deserialize the first JSON object
            question_data = json.loads(first_line)
            
            # Route the single record
            processed_record = route_question_domain(question_data, domain_mapping)
            
            # Write the full processed record to the output file
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            output_full_path = os.path.join(os.getcwd(), OUTPUT_FILE)
            with open(output_full_path, 'w') as outfile:
                 outfile.write(json.dumps(processed_record) + '\n')
            
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE}.")
        print("ACTION REQUIRED: Ensure D1 program has created this file.")
        return
    except json.JSONDecodeError:
        print(f"Error: Malformed JSON found in the first line of {INPUT_FILE}.")
        return
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return

    # 3. Print the Final Summary Output
    if processed_record:
        print("\n--- Processed Output Summary ---")
        print(f"Question: {processed_record.get('question', 'N/A')}")
        print(f"Domain: {processed_record.get('primary_domain', 'N/A')}")
        print("Record Count: 1")
        print("----------------------------------")
        print(f"Full record saved to: {OUTPUT_FILE}")
    else:
        print("No records were successfully processed.")

if __name__ == "__main__":
    main()