import json
import os
import argparse

def extract_record(input_filepath: str, output_filepath: str, target_numeric_id: int, flag: str):
    """
    Universal Data Extractor for GraphRAG Pipeline.
    Reads either standard JSON or JSON Lines format, extracts a specific ID, 
    and formats it for D-Pipeline ingestion.
    """
    # 1. Map the Flag to the Schema
    flag = flag.upper()
    if flag == 'P':
        dataset_label = "RGB_Positive"
        context_key = "positive"
        output_id = f"rgb_{target_numeric_id}_P"
    elif flag == 'N':
        dataset_label = "RGB_Negative"
        context_key = "negative"
        output_id = f"rgb_{target_numeric_id}_N"
    else:
        raise ValueError(f"Invalid flag '{flag}'. Must be 'P' or 'N'.")

    # 2. Open the File and Search for the ID
    if not os.path.exists(input_filepath):
        raise FileNotFoundError(f"Input file not found at {input_filepath}")

    print(f"Loading dataset from {os.path.basename(input_filepath)}...")
    target_record = None

    with open(input_filepath, 'r', encoding='utf-8') as f:
        # Check if it's a standard JSON array or JSON Lines
        first_char = f.read(1)
        f.seek(0) # Reset cursor to beginning

        if first_char == '[':
            # It's a standard JSON array
            master_data = json.load(f)
            target_record = next((item for item in master_data if item.get("id") == target_numeric_id), None)
        else:
            # It's a JSON Lines file (like en_refine.json)
            for line in f:
                if not line.strip(): continue
                record = json.loads(line)
                if record.get("id") == target_numeric_id:
                    target_record = record
                    break
    
    if not target_record:
        raise ValueError(f"Record with id '{target_numeric_id}' not found in the dataset.")
    
    selected_context = target_record.get(context_key)

    if selected_context is None:
        raise ValueError(f"Context key '{context_key}' missing for id '{target_numeric_id}'.")

    if isinstance(selected_context, list) and len(selected_context) == 0:
        raise ValueError(f"Context key '{context_key}' is empty for id '{target_numeric_id}'.")

    # 3. Package into D-Pipeline JSONL Schema
    output_record = {
        "id": output_id, 
        "dataset": dataset_label,
        "question": target_record.get("query", ""),
        "context": selected_context
    }
    print(f"Selected record_id: {output_id}")
    print(f"Selected context_key: {context_key}")
    print_context_preview(selected_context)

    # 4. Save the output
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, 'w', encoding='utf-8') as f_out:
        f_out.write(json.dumps(output_record, ensure_ascii=False) + "\n")
        
    print(f"SUCCESS: Extracted Record {target_numeric_id} [{dataset_label}] to {os.path.basename(output_filepath)}")
    print(f"Question: {output_record['question']}")

def reset_pipeline_caches():
    """Wipes the D3 and D4 memory so new experiments start clean."""
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    d3_cache = os.path.join(PROJECT_ROOT, "..", "output", "D3_Domain_Discovery.json")
    d4_cache = os.path.join(PROJECT_ROOT, "..", "output", "D4_Registry_Discovered.json")
    mapping = os.path.join(PROJECT_ROOT, "..", "output", "D2_D3_Record_Domain_Mapping.jsonl")

    # Wipe D3 and D4 with empty JSON brackets
    for cache_file in [d3_cache, d4_cache]:
        if os.path.exists(cache_file):
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write("{}")
    
    # Empty the D2 mapping file completely
    if os.path.exists(mapping):
        with open(mapping, 'w', encoding='utf-8') as f:
            f.write("")
            
    print("--- Pipeline Caches Successfully Reset ---")

def print_context_preview(context, max_items: int = 3, max_chars: int = 500):
    """
    Prints a short preview of the selected context/document for manual verification.
    Safe for both list and string payloads.
    """
    print("\n--- D00 CONTEXT PREVIEW ---")

    if isinstance(context, list):
        print(f"Context type: list | Items: {len(context)}")
        for i, item in enumerate(context[:max_items], start=1):
            if isinstance(item, dict):
                preview = json.dumps(item, ensure_ascii=False)
            else:
                preview = str(item)

            preview = preview.replace("\n", " ").strip()
            if len(preview) > max_chars:
                preview = preview[:max_chars] + " ..."
            print(f"[{i}] {preview}")

    else:
        preview = str(context).replace("\n", " ").strip()
        if len(preview) > max_chars:
            preview = preview[:max_chars] + " ..."
        print(f"Context type: {type(context).__name__}")
        print(preview)

    print("--- END D00 CONTEXT PREVIEW ---\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract one RGB record for D-pipeline ingestion.")
    parser.add_argument("--numeric-id", type=int, required=True, help="Numeric source record ID, e.g. 12")
    parser.add_argument("--flag", choices=["P", "N"], required=True, help="P for positive, N for negative")
    parser.add_argument("--reset-caches", action="store_true", help="Reset D3/D4/D2 caches before extraction")
    args = parser.parse_args()

    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    INPUT_FILE = os.path.join(PROJECT_ROOT, "..", "data", "en_refine_scored.jsonl")
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "..", "data", "RGB_Single_Record.jsonl")

    if args.reset_caches:
        reset_pipeline_caches()

    extract_record(INPUT_FILE, OUTPUT_FILE, args.numeric_id, args.flag)