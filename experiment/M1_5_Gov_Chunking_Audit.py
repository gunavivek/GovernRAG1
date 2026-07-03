# --------------------------------------------------------------------------
# MODULE: M1_5_Gov_Chunking_Audit.py (V3: Cleaned Source Logic)
# ROLE: Data Lineage Integrity Auditor
# FIX: Strips 'Question:' metadata to prevent False Positives on Drop %
# --------------------------------------------------------------------------

import pandas as pd
import json
import os
import re
from datetime import datetime

# --- Configuration & Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D5_PATH = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
M1_PATH = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")
AUDIT_REPORT_PATH = os.path.join(PROJECT_ROOT, "output", "M1_5_Audit_Report.jsonl")

class GovChunkingAudit:
    def __init__(self):
        self.total_records = 0
        self.failed_records = 0

    def _clean_source_text(self, raw_text):
        """
        Forensic Cleaning: Removes the 'Question' metadata from the source.
        We only want to audit the 'Document' part (the actual knowledge).
        """
        # Pattern: Look for "Question: ... | Document:" and discard it.
        # This keeps ONLY the text after "| Document:"
        if "| Document:" in raw_text:
            return raw_text.split("| Document:", 1)[1].strip()
        return raw_text

    def _find_text_gaps(self, source, chunks):
        """
        Identifies missing text using Normalized Containment.
        """
        clean_source = " ".join(source.split())
        combined_chunks = " ".join([" ".join(str(c).split()) for c in chunks])
        sentences = re.split(r'(?<=[.!?])\s+', clean_source)
        
        gaps = []
        for sent in sentences:
            if len(sent) < 20: continue 
            if sent not in combined_chunks:
                gaps.append(sent)
        return gaps

    def run_audit(self):
        print("================================================================")
        print(" M1.5 V3: DATA LINEAGE AUDIT (METADATA STRIPPED)")
        print("   Comparing Cleaned Source (D5) vs. Extracted Registry (M1)")
        print("================================================================")
        
        if not os.path.exists(D5_PATH) or not os.path.exists(M1_PATH):
            print("X Input files missing.")
            return

        print("Loading M1 Chunks...")
        try:
            m1_df = pd.read_csv(M1_PATH)
            m1_df['chunk_text'] = m1_df['chunk_text'].fillna("").astype(str)
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return

        print("Loading D5 Source...")
        d5_records = []
        with open(D5_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                d5_records.append(json.loads(line))

        reports = []
        
        for record in d5_records:
            self.total_records += 1
            rid = record["record_id"]
            
            # --- THE FIX: CLEAN THE SOURCE ---
            full_text = self._clean_source_text(record["source_text"])
            
            chunks = m1_df[m1_df['record_id'] == rid]['chunk_text'].tolist()
            
            if not chunks:
                coverage_pct = 0.0
                missing_segments = ["ENTIRE DOCUMENT MISSING"]
            else:
                missing_segments = self._find_text_gaps(full_text, chunks)
                total_chars = len(full_text)
                missing_chars = sum(len(s) for s in missing_segments)
                coverage_pct = 100 - ((missing_chars / total_chars) * 100) if total_chars > 0 else 0

            status = "PASS" if coverage_pct > 95.0 else "FAIL_GAP_DETECTED"
            if status == "FAIL_GAP_DETECTED": self.failed_records += 1

            audit_entry = {
                "record_id": rid,
                "timestamp": datetime.now().isoformat(),
                "existing_m1_chunks": len(chunks),
                "coverage_score": round(coverage_pct, 2),
                "dropped_text_pct": round(100 - coverage_pct, 2),
                "potential_residual_chunks": 1 if len(missing_segments) > 0 else 0,
                "omitted_segments_count": len(missing_segments),
                "status": status,
                "omitted_text_samples": missing_segments[:5]
            }
            
            reports.append(audit_entry)
            
            icon = "SUCCESS" if status == "PASS" else "FAILURE"
            print(f"{icon} [{rid[:8]}] Cov: {coverage_pct:.1f}% | Drop: {audit_entry['dropped_text_pct']}% | Gaps: {len(missing_segments)}")

        with open(AUDIT_REPORT_PATH, 'w', encoding='utf-8') as f:
            for r in reports:
                f.write(json.dumps(r) + '\n')

        print("================================================================")
        print(f" AUDIT COMPLETE")
        print(f"   Total Records: {self.total_records}")
        print(f"   Failed Records: {self.failed_records}")
        print("================================================================")

if __name__ == "__main__":
    auditor = GovChunkingAudit()
    auditor.run_audit()