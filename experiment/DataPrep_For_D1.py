import json
import csv
import os

# Define Paths
input_file = os.path.join("data", "RGB_Negative_Rejection_Candidates.json")
output_file = os.path.join("data", "RGB_Dataset_Negative_Rej.csv")

# 1. Exact columns from your RAGBench dataset description.csv
columns = [
    "Dataset Name", 
    "Domain", 
    "Dataset Description", 
    "Document Source", 
    "Question Source"
]

# 2. Load the 10 raw RGB records
with open(input_file, 'r', encoding='utf-8') as f:
    rgb_data = json.load(f)

os.makedirs(os.path.dirname(output_file), exist_ok=True)

# 3. Transform the JSON array into the RAGBench CSV format
with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=columns)
    writer.writeheader()
    
    for i, record in enumerate(rgb_data):
        # Flatten the negative array into a single text block
        negative_context = " ".join(record.get("negative", []))
        
        # Map your 10 records into the RAGBench columns
        row_data = {
            "Dataset Name": f"RGB_Neg_{record.get('id', i)}",  # Unique name per record (e.g. RGB_Neg_10)
            "Domain": "General Knowledge",                     # Hardcoded domain as requested
            "Dataset Description": negative_context,           # The Negative Document Text
            "Document Source": "RGB_Negative_Rejection",
            "Question Source": record.get("query", "")         # The Query Text
        }
        writer.writerow(row_data)

print(f"Success! Processed {len(rgb_data)} records into {output_file}")