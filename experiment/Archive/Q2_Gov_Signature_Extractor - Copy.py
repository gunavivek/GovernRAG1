import json
import os
import re  # Added for Pattern Matching
from typing import Dict, Any, List

# --- Project Paths ---
INPUT_FILE = "output/Q1_intent_gate.jsonl"
OUTPUT_FILE = "output/Q2_signatures.jsonl"

class GovernedSignatureExtractor:
    def __init__(self):
        # NEW: Filter list to prevent "Question Words" from becoming "Nodes"
        self.interrogative_noise = {"what", "which", "who", "how", "where", "when", "the", "this"}

    def process(self):
        print("--- Q2: Governed Signature Extractor (Adaptive BA Mode) ---")
        if not os.path.exists(INPUT_FILE):
            print(f"[FATAL] Missing input: {INPUT_FILE}")
            return

        count = 0
        with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                if not line.strip(): continue
                record = json.loads(line)
                
                gov_context = record.get("governed_context", {})
                laws = gov_context.get("primary_laws", {})
                active_domains = gov_context.get("active_domains", [])

                onboarded_attributes = laws.get("governed_attributes", ["name", "description"])
                relational_predicates = laws.get("relational_predicates", [])

                question_text = record["question"]
                target_nodes = self._distill_concepts(question_text, active_domains)

                signature = {
                    "primary_anchor": active_domains[0] if active_domains else "Enterprise",
                    "target_nodes": target_nodes,
                    "required_predicates": [
                        p for p in relational_predicates 
                        if p.lower() in question_text.lower()
                    ],
                    "attribute_targets": onboarded_attributes,
                    "complexity_constraints": record.get("traversal_parameters", {})
                }
                
                record["q_signature"] = signature
                f_out.write(json.dumps(record, ensure_ascii=False) + '\n')
                count += 1
                
        print(f"--- SUCCESS: {count} Adaptive BA Signatures generated ---")

    def _distill_concepts(self, text: str, active_domains: List[str]) -> List[str]:
        """
        Improved PhD Logic: Pattern-Aware Concept Distillation.
        """
        concepts = []

        # 1. NEW: QUOTE EXTRACTION (Highest Priority)
        # Finds everything inside " " and treats it as one node.
        quoted_titles = re.findall(r'"([^"]*)"', text)
        concepts.extend(quoted_titles)

        # 2. IMPROVED: CLEANING & SPLITTING
        # Remove punctuation without destroying the sentence structure
        clean_text = re.sub(r'[^\w\s]', '', text)
        words = clean_text.split()

        # 3. IMPROVED: NOISE-AWARE TITLE CASE CHECK
        for i, word in enumerate(words):
            if word[0].isupper() or any(char.isdigit() for char in word):
                # Only add if it's NOT a leading noise word (What/Which/etc)
                if i == 0 and word.lower() in self.interrogative_noise:
                    continue
                concepts.append(word)
        
        # 4. DOMAIN ANCHORING (Preserved from your original)
        for domain in active_domains:
            if domain not in concepts:
                concepts.append(domain)
        
        # Deduplicate while preserving order
        seen = set()
        return [x for x in concepts if not (x in seen or seen.add(x))]

if __name__ == "__main__":
    GovernedSignatureExtractor().process()