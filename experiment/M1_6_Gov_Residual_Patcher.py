# --------------------------------------------------------------------------
# MODULE: M1_6_Gov_Residual_Patcher.py
# ROLE: The "Tier 2" Knowledge Creator
# STRATEGY: "Tiered Governance" - Creates fallback chunks with Shadow Domains
# INPUT: M1_5_Audit_Report.jsonl (Gaps) + M1_Governed_Chunks.csv (Existing)
# OUTPUT: M1_6_Residual_Chunks.csv (A separate Tier 2 Registry)
# --------------------------------------------------------------------------

import pandas as pd
import json
import os
import csv
from dotenv import load_dotenv
from google import genai

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_REPORT = os.path.join(PROJECT_ROOT, "output", "M1_5_Audit_Report.jsonl")
M1_INPUT_PATH = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
D5_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")

# NEW OUTPUT FILE (Separate Tier 2 Registry)
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "output", "M1_6_Residual_Chunks.csv")

# Load API for "Shadow Domain" Identification
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
LLM_MODEL = "gemini-3-flash-preview"

class GovResidualPatcher:
    def __init__(self):
        self.d5_map = {} 
        self.patched_count = 0

    def _load_source_text(self):
        """Loads full source text to recover the complete missing segments."""
        if not os.path.exists(D5_PATH): return
        with open(D5_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                rec = json.loads(line)
                text = rec["source_text"]
                # Clean metadata exactly like M1.5 V3 did to ensure alignment
                if "| Document:" in text:
                    text = text.split("| Document:", 1)[1].strip()
                self.d5_map[rec["record_id"]] = text

    def _get_full_residual_text(self, record_id, m1_chunks):
        """Re-calculates the FULL missing text."""
        if record_id not in self.d5_map: return ""
        full_source = self.d5_map[record_id]
        
        # Normalize existing chunks for comparison
        combined_chunks = " ".join([str(c) for c in m1_chunks])
        
        import re
        sentences = re.split(r'(?<=[.!?])\s+', full_source)
        residual_parts = []
        for sent in sentences:
            # Threshold: Ignore tiny noise (< 20 chars) and text already in M1
            if len(sent) > 20 and sent not in combined_chunks:
                residual_parts.append(sent)
                
        return " ... ".join(residual_parts)

    def _identify_shadow_domain(self, text):
        """
        Asks LLM to identify the 'Real' domain for metadata purposes.
        """
        prompt = f"""
        Classify this text into a specific Industry or Topic.
        Text: "{text[:300]}..."
        Return ONLY the Category Name (e.g., 'Legal Services', 'Cinema', 'Sports History').
        """
        try:
            response = client.models.generate_content(model=LLM_MODEL, contents=[prompt])
            return response.text.strip().replace("\n", "")
        except:
            return "Unclassified_Context"

    def run_patching(self):
        print("================================================================")
        print(" M1.6: RESIDUAL CONTEXT PATCHER (SEPARATE FILE OUTPUT)")
        print(f"   Input Audit:  {os.path.basename(AUDIT_REPORT)}")
        print(f"   Output File:  {os.path.basename(OUTPUT_PATH)}")
        print("================================================================")

        if not os.path.exists(AUDIT_REPORT):
            print("XX Audit report missing. Run M1.5 first.")
            return

        self._load_source_text()
        
        # Load existing chunks from M1 just to verify what to exclude
        try:
            m1_df = pd.read_csv(M1_INPUT_PATH)
            m1_df['chunk_text'] = m1_df['chunk_text'].fillna("").astype(str)
        except:
            print("XX Could not read M1 Input CSV.")
            return

        patches = []
        
        # Process Audit Report
        with open(AUDIT_REPORT, 'r', encoding='utf-8') as f:
            for line in f:
                audit = json.loads(line)
                
                # ONLY patch if there is a detected gap
                if audit["status"] == "FAIL_GAP_DETECTED":
                    rid = audit["record_id"]
                    
                    # 1. Recover the text (Diffing Source vs Existing M1 Chunks)
                    existing_chunks = m1_df[m1_df['record_id'] == rid]['chunk_text'].tolist()
                    residual_text = self._get_full_residual_text(rid, existing_chunks)
                    
                    if len(residual_text) < 15: 
                        print(f"   WARNING! Skipping {rid[:8]} (Gap too small/noise)")
                        continue 

                    # 2. Identify the "Shadow Domain" (The LLM Call)
                    real_topic = self._identify_shadow_domain(residual_text)

                    # 3. Create the Safe Chunk (Matches M1 Schema)
                    patch = {
                        "record_id": rid,
                        "chunk_id": f"CHNK_{rid[-4:]}_RESIDUAL_00",
                        "viewpoint_domain": "General_Context",
                        "chunk_text": residual_text,
                        "wa_score": 0.05, # Low Authority (Tier 2)
                        "granularity_level": 0,
                        "z_score": 0.0,
                        "predicates": json.dumps(["fallback_context"]), 
                        "disambiguation": json.dumps({"shadow_domain": real_topic}) 
                    }
                    patches.append(patch)
                    print(f"   -> Generating Patch for {rid[:8]} | Topic: '{real_topic}'")

        # Save to NEW CSV File
        if patches:
            print(f"\n Saving {len(patches)} Residual Chunks to {OUTPUT_PATH}...")
            
            patch_df = pd.DataFrame(patches)
            
            # Ensure column order matches M1 schema for consistency
            cols = ["record_id", "chunk_id", "viewpoint_domain", "chunk_text", 
                    "wa_score", "granularity_level", "z_score", 
                    "predicates", "disambiguation"]
            
            patch_df = patch_df[cols]
            
            # Write to NEW file with Header (since it's a standalone file)
            patch_df.to_csv(OUTPUT_PATH, mode='w', header=True, index=False, quoting=csv.QUOTE_ALL)
            
            print(f" SUCCESS: File created successfully.")
        else:
            print(" No significant gaps found. No residual file created.")

        print("================================================================")

if __name__ == "__main__":
    patcher = GovResidualPatcher()
    patcher.run_patching()