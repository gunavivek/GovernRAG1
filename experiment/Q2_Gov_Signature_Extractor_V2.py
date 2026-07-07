import json
import os
import re
from typing import Dict, Any, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# PhD Strategy: Small model (Gemma) proves that governance-bounded 
# tasks do not require massive LLMs, optimizing for efficiency.
MODEL_ID = "gemini-3.5-flash"

INPUT_FILE = "output/Q1_intent_gate.jsonl"
OUTPUT_FILE = "output/Q2_signatures.jsonl"

class GovernedSignatureExtractorV2:
    def __init__(self):
        # Noise filter for concept distillation (Interrogative cleaning)
        self.interrogative_noise = {"what", "which", "who", "how", "where", "when", "the", "this"}
        self.attribute_targets_by_intent = {
              "Quantity": ["amount", "price", "cost", "value", "total", "number"],
              "Temporal": ["date", "time", "year", "start", "end"],
              "Spatial": ["location", "place", "city", "country", "headquarters"],
              "Identity": ["name", "founder", "author", "creator"],
              "General_Relation": ["name", "description"]
        }
        # --- Option B: graph-grounded anchor linking (design-A scoped) ---
        # Enabled iff the scoped-vocab artifact is present; else frozen behavior.
        self.scoped_vocab = None
        _sv = os.path.join("output", "serve_scoped_vocab.json")
        if os.path.exists(_sv):
            with open(_sv, encoding="utf-8") as _f:
                self.scoped_vocab = json.load(_f)   # {record_id: [node_name, ...]}
            print(f"[Q2] Anchor linking ON: scoped node vocab for {len(self.scoped_vocab)} questions")
    def _distill_concepts(self, text: str, active_domains: List[str], record_id: str = None) -> List[str]:
        """
        PRESERVED V1 LOGIC: Pattern-Aware Concept Distillation.
        Extracts entities, quoted strings, and numbers as Graph Search Anchors.
        """
        concepts = []

        # 1. QUOTE EXTRACTION (Specific entities)
        quoted_titles = re.findall(r'"([^"]*)"', text)
        concepts.extend(quoted_titles)

        # 2. CLEANING & SPLITTING
        clean_text = re.sub(r'[^\w\s]', '', text)
        words = clean_text.split()

        # 3. NOISE-AWARE TITLE CASE CHECK (Entity Identification)
        for i, word in enumerate(words):
            if word[0].isupper() or any(char.isdigit() for char in word):
                if i == 0 and word.lower() in self.interrogative_noise:
                    continue
                concepts.append(word)
        
        # 3b. GRAPH-GROUNDED ANCHOR LINKING (design-A scoped) -- additive; fallback-safe.
        if self.scoped_vocab is not None and record_id is not None:
            q_lower = text.lower()
            for name in self.scoped_vocab.get(str(record_id), []):
                nl = str(name).lower().strip()
                if len(nl) >= 4 and re.search(r"\b" + re.escape(nl) + r"\b", q_lower):
                    if name not in concepts:
                        concepts.append(name)

        # 4. DOMAIN ANCHORING
        for domain in active_domains:
            if domain not in concepts:
                concepts.append(domain)
        
        seen = set()
        return [x for x in concepts if not (x in seen or seen.add(x))]

    def _map_predicates_dynamically(self, question: str, functional_intent: str, authorized_predicates: List[str]) -> List[str]:
        """
        NEURO-SYMBOLIC COMPONENT: Governed Ontological Mapping.
        Forces the LLM to stay within the 'Closed World' of authorized predicates.
        """
        if not authorized_predicates:
            return []

        mapping_prompt = f"""
        Act as a Business Architecture Ontologist.
        User Question: "{question}"
        Functional Intent: {functional_intent}
        Authorized Predicates (extracted from document manifest): {authorized_predicates}

        Identify which 'Authorized Predicates' are semantically required to find the answer to the {functional_intent} aspect of this question.
        
        Rules:
        1. Only select strings from the 'Authorized Predicates' list above.
        2. If no clear match exists, return an empty list [].
        3. Return ONLY a valid JSON list of strings. No conversation.
        """

        import time as _time
        last_err = None
        for _attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=mapping_prompt,
                    config=types.GenerateContentConfig(temperature=0.0)  # Zero temp for DSR reproducibility
                )
                clean_res = (response.text or "").strip().replace("```json", "").replace("```", "").strip()
                try:
                    val = json.loads(clean_res)
                except json.JSONDecodeError:
                    m = re.search(r"\[.*\]", clean_res, re.DOTALL)  # salvage a JSON array if wrapped/truncated
                    if not m:
                        raise
                    val = json.loads(m.group(0))
                return val if isinstance(val, list) else []
            except Exception as e:
                last_err = e
                _time.sleep(2 * (_attempt + 1))
        print(f"[Q2][WARN] predicate mapping degraded to [] (Rule 2) after 3 tries: {last_err}")
        return []

    def process(self):
        print("--- Q2 V2: Governed Signature Extractor (Frozen State) ---")
        if not os.path.exists(INPUT_FILE):
            print(f"[FATAL] Missing input: {INPUT_FILE}")
            raise SystemExit(1)

        count = 0
        with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
             open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
            
            for line in f_in:
                if not line.strip(): continue
                record = json.loads(line)
                
                # Retrieve Governance Context from Q1 (Using unified record_id)
                gov_context = record.get("governed_context", {})
                laws = gov_context.get("primary_laws", {})
                active_domains = gov_context.get("active_domains", [])
                functional_intent = gov_context.get("functional_intent", "General_Relation")
                
                relational_predicates = laws.get("relational_predicates", [])

                # Execute Dynamic Mapping
                mapped_predicates = self._map_predicates_dynamically(
                    record["question"], 
                    functional_intent, 
                    relational_predicates
                )

                # Execute Concept Distillation
                target_nodes = self._distill_concepts(
                    record["question"], active_domains, record_id=record.get("record_id"))

                # Assemble the Enhanced Signature (The Search Warrant)
                signature = {
                    "primary_anchor": active_domains[0] if active_domains else "General",
                    "target_nodes": target_nodes,
                    "required_predicates": mapped_predicates, 
                    "attribute_targets": self.attribute_targets_by_intent.get(functional_intent, ["name", "description"]),
                    "complexity_constraints": record.get("traversal_parameters", {})
                }
                
                # Update the record and write to file
                record["q_signature"] = signature
                f_out.write(json.dumps(record, ensure_ascii=False) + '\n')
                count += 1
                
        print(f"--- SUCCESS: {count} Concept-Mapped Signatures generated ---")

if __name__ == "__main__":
    GovernedSignatureExtractorV2().process()