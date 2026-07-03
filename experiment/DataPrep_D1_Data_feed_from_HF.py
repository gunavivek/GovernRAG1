import os
import json
from datasets import load_dataset

# --- Configuration ---
DATASET_NAME = "galileo-ai/ragbench"
CONFIG_NAME = "cuad"  
SPLIT = "train" 

# *** NEW: Define the limit for testing ***
RECORD_LIMIT = 10 

# Define the output directory and file path
OUTPUT_DIR = "output"
D1_OUTPUT_FILE_NAME = "D1_OUTPUT_FILE_10_RECORDS.jsonl" # Renamed output for clarity
D1_OUTPUT_PATH = os.path.join(OUTPUT_DIR, D1_OUTPUT_FILE_NAME)

def run_data_feed_module_d1():
    """
    Streams the specified HF dataset, extracts data, and stops after RECORD_LIMIT.
    """
    
    # 1. Create Output Directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory '{OUTPUT_DIR}' ensured.")
    
    print(f"Loading dataset '{DATASET_NAME}' config '{CONFIG_NAME}' in streaming mode...")
    try:
        dataset_stream = load_dataset(DATASET_NAME, CONFIG_NAME, split=SPLIT, streaming=True)
    except Exception as e:
        print(f"Error loading dataset. Check CONFIG_NAME and internet connection: {e}")
        return

    record_count = 0
    with open(D1_OUTPUT_PATH, 'w') as f_out: 
        print(f"Starting data feed and writing up to {RECORD_LIMIT} records to: {D1_OUTPUT_PATH}")
        
        # --- The Data Feed Loop ---
        for i, record in enumerate(dataset_stream):
            
            # *** CRITICAL: Check the limit at the start of the loop ***
            if record_count >= RECORD_LIMIT:
                print(f"\nLimit of {RECORD_LIMIT} records reached. Stopping stream.")
                break 
            # -------------------------------------------------------------
            
            if 'id' not in record:
                print(f"Skipping record {i}. Missing 'id'.")
                continue
            
            record_id = record['id']
            
            try:
                # Extract only the required columns
                d2_input_data = {
                    "id": record_id,
                    "question": record['question'],
                    "documents": record['documents'],
                    "response": record['response'],
                    "dataset_name": record['dataset_name']                }
                
                # Write the extracted data to the JSON Lines file (persistence)
                f_out.write(json.dumps(d2_input_data) + '\n')
                f_out.flush() 
                record_count += 1

            except KeyError as e:
                print(f"[ID: {record_id}] Missing required column {e}. Skipping record.")
                continue
            except Exception as e:
                print(f"[ID: {record_id}] An unknown error occurred: {e}")
                continue 

    print("\n--- D1 Data Feed Complete ---")
    print(f"Total records processed: {record_count}")

if __name__ == "__main__":
    run_data_feed_module_d1()