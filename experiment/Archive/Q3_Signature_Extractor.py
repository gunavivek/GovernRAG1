import json
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Configuration & File Paths ---
Q1_INPUT_FILE = "output/Q1_domain_router.jsonl"
Q2_INPUT_FILE = "output/Q2_intents.jsonl"
OUTPUT_FILE = "output/Q3_signatures.jsonl"
DOMAIN_CATALOG_PATH = "config/domain_catalog.json"  # reserved for future external config

# --- Default Structures ---
DEFAULT_SIGNATURE = {
    "Q_layer": {"concept": None, "attribute": None, "value": None},
    "constraints": {
        "time_horizon": None,
        "segment": None,
        "channel": None,
        "geography": None,
    },
    "metric_hints": [],
}

# JSON SCHEMA: example structure we show to the LLM
JSON_OUTPUT_SCHEMA = """
{
  "concept": "[The main subject or entity of the question, using domain terminology]",
  "attribute": "[The specific property or action being asked about]",
  "value": "[Any explicit numeric/date/target value mentioned in the QUESTION TEXT itself, or null if not explicitly stated]",
  "constraints": {
    "time_horizon": "[e.g., Q4 2023, Fiscal Year 2024, or null]",
    "segment": "[e.g., Retail, Commercial Banking, or null]",
    "channel": "[e.g., Online, Branch, or null]",
    "geography": "[e.g., US, Europe, or null]"
  },
  "metric_hints": ["list", "of", "metric-like", "keywords"]
}
"""

# Domain Catalog (internal for now)
DOMAIN_CATALOG: Dict[str, Any] = {
    "Operations": {
        "description": "Systems, platforms, processes, technical debt, operational risk and efficiency.",
        "typical_concepts": [
            "platform retirement",
            "incident management",
            "operational risk",
            "technical debt",
        ],
    },
    "Finance": {
        "description": "Financial products, pricing, statements, balances, cash flows.",
        "typical_concepts": [
            "interest rate",
            "principal",
            "transactional cost",
            "portfolio value",
        ],
    },
    "Legal": {
        "description": "Contracts, clauses, obligations, regulatory requirements, compliance.",
        "typical_concepts": [
            "supplier contract",
            "legal regulation",
            "obligation",
            "termination clause",
        ],
    },
    "General Knowledge": {
        "description": "Broad topics, history, public figures, general definitions.",
        "typical_concepts": [
            "historical event",
            "person name",
            "country capital",
            "definition",
        ],
    },
}

# --- 1. Data Loading and Joining ---


def load_jsonl_to_dict(file_path: str, stage_name: str) -> Dict[str, Dict[str, Any]]:
    """Loads all records from a JSONL file into a dict keyed by question_id/id."""
    data: Dict[str, Dict[str, Any]] = {}
    try:
        full_path = os.path.join(os.getcwd(), file_path)
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                qid = record.get("id", record.get("question_id"))
                if qid:
                    data[qid] = record
        print(f"[Q3][DEBUG] {stage_name} loaded {len(data)} records from {file_path}")
    except FileNotFoundError:
        print(f"[Q3][ERROR] {stage_name} input file not found at {file_path}")
    except json.JSONDecodeError as e:
        print(f"[Q3][ERROR] {stage_name} JSON parsing failed: {e}")
    return data


def join_q1_q2_data(
    q1_data: Dict[str, Any], q2_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Joins Q1 and Q2 data on question_id/id for records present in both inputs."""
    joined_list: List[Dict[str, Any]] = []

    for qid, q1_record in q1_data.items():
        q2_record = q2_data.get(qid)

        if q2_record:
            merged_record = q1_record.copy()
            # merge all fields from q2 into q1 (intent, explanation, etc.)
            merged_record.update(q2_record)

            # Normalise question text field
            if merged_record.get("question_text") or merged_record.get("question"):
                merged_record["question_text"] = merged_record.get(
                    "question_text", merged_record.get("question")
                )
                joined_list.append(merged_record)
            else:
                print(f"[Q3][WARN] Skipping QID {qid}: Missing question text.")
        else:
            print(
                f"[Q3][WARN] Skipping QID {qid}: Missing Q2 intent data. Check Q2 file."
            )

    print(f"[Q3][DEBUG] Join complete. Total matched records: {len(joined_list)}")
    return joined_list


# --- 2. Prompt Construction ---


def create_q3_prompt(data: Dict[str, Any], catalog: Dict[str, Any]) -> str:
    """
    Builds the domain-aware LLM prompt for signature extraction.
    Uses:
      - primary_domain (from Q1)
      - intent (from Q2)
      - question_text
      - DOMAIN_CATALOG
      - JSON_OUTPUT_SCHEMA
    """
    domain_name = data.get("primary_domain", "General Knowledge")
    intent = data.get("intent", "Extractive")
    question_text = data.get("question_text", "")

    domain_info = catalog.get(domain_name, catalog["General Knowledge"])
    domain_desc = domain_info.get("description", "")
    typical_concepts = ", ".join(domain_info.get("typical_concepts", []))

    prompt = (
        f"You are a hyper-specialized Signature Extractor operating on questions "
        f"within the '{domain_name}' domain.\n\n"
        f"DOMAIN FOCUS: {domain_desc}\n"
        f"TYPICAL CONCEPTS (Hints): {typical_concepts}\n"
        f"QUESTION INTENT: {intent} "
        "(Inferential questions often imply impact/relationship between concepts).\n\n"
        "TASK:\n"
        "Analyze the QUESTION TEXT below and, conditioning your interpretation on the "
        "DOMAIN FOCUS, extract the following fields:\n"
        "- concept: main subject or entity of the question (use domain terminology where possible).\n"
        "- attribute: specific property / action / relationship being asked about.\n"
        "- value: any explicit numeric/date/target value mentioned in the QUESTION TEXT itself, "
        "or null if no such value is explicitly stated. Do NOT infer the answer or pull it from any document. "
        "If the answer is not explicitly written in the QUESTION TEXT, set value to null.\n"
        "- constraints: time_horizon, segment, channel, geography (or null for each if not present).\n"
        "- metric_hints: metric-like phrases (e.g., 'resolution time', 'transactional cost').\n\n"
        "Return ONLY a single valid JSON object with this structure (all fields must be present):\n"
        f"{JSON_OUTPUT_SCHEMA}\n\n"
        f'QUESTION TEXT: "{question_text}"\n'
        "Respond with JSON only, no explanation."
    )
    return prompt


# --- 3. LLM Call ---


def _postprocess_value_for_intent(value: Any, intent: str) -> Any:
    """
    Heuristic cleanup:
    - For Extractive questions, if `value` is a short generic word like 'new', 'this', 'that', etc.,
      treat it as not a real value and set to None.
    """
    if value is None:
        return None

    if not isinstance(value, str):
        return value

    v = value.strip().lower()

    # Only apply this for Extractive intent
    if intent.lower() == "extractive":
        generic_tokens = {"new", "this", "that", "it", "they"}
        # if it's exactly one of these generic words, or extremely short and non-numeric
        if v in generic_tokens:
            return None
        if len(v.split()) <= 2 and not any(ch.isdigit() for ch in v):
            # conservative: could still be legit, but if you want stricter, keep this
            return value  # keep as-is for now, only knock out obvious generics

    return value


def call_llm_for_signature(prompt: str, intent: str) -> Dict[str, Any]:
    """Calls the LLM once and parses the JSON response into a signature dict."""
    client = OpenAI()  # simple: instantiate per call

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract JSON signatures for questions. "
                        "Always return a single valid JSON object, with no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        content = resp.choices[0].message.content.strip()
        sig = json.loads(content)

        # Ensure required keys exist with defaults
        sig.setdefault("concept", None)
        sig.setdefault("attribute", None)
        sig.setdefault("value", None)
        sig.setdefault("constraints", {})
        sig["constraints"].setdefault("time_horizon", None)
        sig["constraints"].setdefault("segment", None)
        sig["constraints"].setdefault("channel", None)
        sig["constraints"].setdefault("geography", None)
        sig.setdefault("metric_hints", [])

        # --- Post-processing rule for value ---
        sig["value"] = _postprocess_value_for_intent(sig["value"], intent)

        return sig

    except Exception as e:
        print(f"[Q3][ERROR] LLM error: {e}")
        # Fall back to default empty signature
        return {
            "concept": None,
            "attribute": None,
            "value": None,
            "constraints": {
                "time_horizon": None,
                "segment": None,
                "channel": None,
                "geography": None,
            },
            "metric_hints": [],
        }


# --- 4. Main Driver ---


def run_q3(
    q1_path: str = Q1_INPUT_FILE,
    q2_path: str = Q2_INPUT_FILE,
    out_path: str = OUTPUT_FILE,
) -> None:
    """Main driver for Q3 Signature Extractor."""
    print("[Q3] Starting Q3 Signature Extractor...")

    q1_data = load_jsonl_to_dict(q1_path, "Q1")
    q2_data = load_jsonl_to_dict(q2_path, "Q2")

    if not q1_data or not q2_data:
        print("[Q3][ERROR] Missing Q1 or Q2 data. Aborting Q3.")
        return

    joined_records = join_q1_q2_data(q1_data, q2_data)
    if not joined_records:
        print("[Q3][ERROR] No joined records to process. Aborting Q3.")
        return

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)

    count = 0
    with open(out_path, "w", encoding="utf-8") as outfile:
        for rec in joined_records:
            prompt = create_q3_prompt(rec, DOMAIN_CATALOG)
            intent = rec.get("intent", "Extractive")
            sig = call_llm_for_signature(prompt, intent)

            out_rec = rec.copy()

            out_rec["Q_layer"] = {
                "concept": sig["concept"],
                "attribute": sig["attribute"],
                "value": sig["value"],
            }
            out_rec["constraints"] = sig["constraints"]
            out_rec["metric_hints"] = sig["metric_hints"]
            out_rec["q3_notes"] = (
                "Domain-aware signature extracted via single LLM call (value constrained to question text)."
            )

            outfile.write(json.dumps(out_rec) + "\n")
            count += 1

            if count % 10 == 0:
                print(f"[Q3][INFO] Processed {count} questions...")

    print(f"[Q3] Completed. Wrote {count} records to: {out_path}")


if __name__ == "__main__":
    run_q3()