import json
import os

def extract_rgb_record(input_filepath: str, output_filepath: str, target_id: str, flag: str):
    """
    Extracts a specific Positive or Negative record from the master RGB JSON file 
    and formats it into a JSONL schema for the GraphRAG pipeline.
    
    Parameters:
    - target_id: The ID string (e.g., "rgb_10")
    - flag: "P" for Positive context, "N" for Negative context
    """
    # 1. Parse the integer ID from the string (e.g., "rgb_10" -> 10)
    try:
        numeric_id = int(target_id.split('_')[1])
    except (IndexError, ValueError):
        print(f"CRITICAL ERROR: Invalid ID format '{target_id}'. Expected format: 'rgb_10'")
        return

    # 2. Determine the target schema based on the flag
    if flag.upper() == 'P':
        dataset_label = "RGB_Positive"
        context_key = "positive"
    elif flag.upper() == 'N':
        dataset_label = "RGB_Negative"
        context_key = "negative"
    else:
        print(f"CRITICAL ERROR: Invalid flag '{flag}'. Use 'P' or 'N'.")
        return

    # 3. Load the master JSON array
    if not os.path.exists(input_filepath):
        print(f"CRITICAL ERROR: Could not find input file at {input_filepath}")
        return

    with open(input_filepath, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    # 4. Search for the specific record
    target_record = next((item for item in master_data if item.get("id") == numeric_id), None)
    
    if not target_record:
        print(f"ERROR: Record with numeric ID {numeric_id} not found in the dataset.")
        return

    # 5. Package the data into the D-Pipeline JSONL schema
    output_record = {
        "id": target_id,
        "dataset": dataset_label,
        "question": target_record.get("query", ""),
        "context": target_record.get(context_key, [])
    }

    # 6. Save as a single-line JSONL file
    with open(output_filepath, 'w', encoding='utf-8') as f_out:
        f_out.write(json.dumps(output_record, ensure_ascii=False) + "\n")
        
    print(f"SUCCESS: Extracted {target_id} [{dataset_label}] to {output_filepath}")


if __name__ == "__main__":
    # --- Configuration ---
    # Assuming the files are in your 'data' folder
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    # Adjust this path if your script is inside the 'experiment' folder
    INPUT_FILE = os.path.join(PROJECT_ROOT, "..", "data", "RGB_Positive_Negative_10Records.json")
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "..", "data", "RGB_Single_Record.jsonl")

    # --- Execution ---
    # To extract rgb_10 Positive:
    extract_rgb_record(
        input_filepath=INPUT_FILE, 
        output_filepath=OUTPUT_FILE, 
        target_id="rgb_10", 
        flag="P"
    )