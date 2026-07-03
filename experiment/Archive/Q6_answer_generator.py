# --------------------------------------------------------------------------
# MODULE Q6: Graph-Guided Answer Generator
#
# Purpose:
#   - Take Q5 retrieval plans (graph-scoped contexts)
#   - Generate a final answer + reasoning trace as structured JSON
#   - DO NOT use ground-truth 'response' during answering
#
# Inputs:
#   - output/Q5_retrieval_plan.jsonl
#
# Outputs:
#   - output/Q6_answers.jsonl
#
# Dependencies:
#   - OPENAI_API_KEY in .env
#   - pip install openai python-dotenv
# --------------------------------------------------------------------------

import os
import json
from typing import Dict, Any, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

Q5_INPUT_FILE = "output/Q5_retrieval_plan.jsonl"
Q6_OUTPUT_FILE = "output/Q6_answers.jsonl"

# How many contexts to use per question (top-K by score)
TOP_K_CONTEXTS = 2

# JSON schema for LLM output (as text for the prompt)
ANSWER_JSON_SCHEMA = """
{
  "answer": "The answer string or empty string if unanswerable.",
  "answer_type": "extractive | abstractive | unanswerable",
  "answer_confidence": 0.0,
  "used_context_ids": ["ctx_1", "ctx_2"],
  "supporting_concepts": ["list of concept node names used for reasoning"],
  "supporting_edges": ["list of edge summaries used for reasoning"],
  "supporting_snippets": ["short text snippets copied from the provided chunk_text fields"],
  "unanswerable_flag": false,
  "hallucination_risk_flag": false,
  "explanation": "short natural language explanation of how you arrived at the answer"
}
"""


# --------------------------------------------------------------------------
# 1. Data loading
# --------------------------------------------------------------------------

def load_q5_plans(path: str) -> List[Dict[str, Any]]:
    """Load all Q5 retrieval plan records from JSONL."""
    records: List[Dict[str, Any]] = []
    try:
        full_path = os.path.join(os.getcwd(), path)
        with open(full_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        print(f"[Q6][DEBUG] Loaded {len(records)} Q5 records from {path}")
    except FileNotFoundError:
        print(f"[Q6][ERROR] Q5 retrieval plan file not found at {path}")
    except json.JSONDecodeError as e:
        print(f"[Q6][ERROR] JSON parsing error in {path}: {e}")
    return records


# --------------------------------------------------------------------------
# 2. Context selection
# --------------------------------------------------------------------------

def select_top_contexts(q5_record: Dict[str, Any], top_k: int = TOP_K_CONTEXTS) -> List[Dict[str, Any]]:
    """Select top-K retrieval contexts for a question, sorted by score."""
    contexts = q5_record.get("retrieval_contexts", []) or []
    if not contexts:
        return []

    # Sort by score descending (default 0.0 if missing)
    contexts_sorted = sorted(
        contexts,
        key=lambda c: float(c.get("score", 0.0)),
        reverse=True
    )
    return contexts_sorted[:top_k]


def truncate_text(text: str, max_chars: int = 2000) -> str:
    """Truncate long text for prompt safety, with marker."""
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + " ... [TRUNCATED]"


# --------------------------------------------------------------------------
# 3. Prompt construction
# --------------------------------------------------------------------------

def build_q6_prompt(
    record: Dict[str, Any],
    contexts: List[Dict[str, Any]]
) -> str:
    """
    Build the user prompt for the LLM:
    - includes question + Q-layer
    - includes top-K retrieval contexts (concept nodes, edges, chunk_text)
    - instructs the model to use only provided information
    """
    question_text = record.get("question_text") or record.get("question") or ""
    primary_domain = record.get("primary_domain", "General")
    intent = record.get("intent", "Extractive")
    q_layer = record.get("Q_layer", {}) or {}

    concept = q_layer.get("concept")
    attribute = q_layer.get("attribute")
    value = q_layer.get("value")

    # Build a descriptive signature string (for the prompt only)
    q_signature_desc = (
        f"Concept = {concept!r}, Attribute = {attribute!r}, Value = {value!r}"
    )

    # Compose context descriptions
    ctx_blocks: List[str] = []
    for ctx in contexts:
        ctx_id = ctx.get("context_id", "ctx_unknown")
        ctx_score = ctx.get("score", 0.0)
        concept_nodes = ctx.get("concept_nodes", []) or []
        edge_summaries = ctx.get("edge_summaries", []) or []
        chunk_text = ctx.get("chunk_text", "") or ""

        ctx_block = [
            f"- CONTEXT_ID: {ctx_id}",
            f"  SCORE: {ctx_score}",
            f"  CONCEPT_NODES: {', '.join(concept_nodes) if concept_nodes else '[none]'}",
            f"  EDGE_SUMMARIES:",
        ]
        if edge_summaries:
            for e in edge_summaries:
                ctx_block.append(f"    - {e}")
        else:
            ctx_block.append("    - [none]")

        ctx_block.append("  CHUNK_TEXT:")
        ctx_block.append(truncate_text(chunk_text, max_chars=2000))
        ctx_blocks.append("\n".join(ctx_block))

    contexts_text = "\n\n".join(ctx_blocks) if ctx_blocks else "[NO CONTEXTS AVAILABLE]"

    prompt = (
        "You are a Graph-RAG answer generator. You must answer strictly from the "
        "provided contexts, which were selected via a graph-based retrieval pipeline. "
        "You are NOT allowed to use external knowledge or guess.\n\n"
        f"DOMAIN: {primary_domain}\n"
        f"QUESTION INTENT: {intent}\n"
        f"QUESTION SIGNATURE (Q-layer): {q_signature_desc}\n\n"
        f"QUESTION:\n{question_text}\n\n"
        "RETRIEVAL CONTEXTS:\n"
        f"{contexts_text}\n\n"
        "TASK:\n"
        "1. If the answer is explicitly supported by the contexts, return it.\n"
        "2. If the contexts suggest an answer but it is not fully explicit, you may return an "
        "abstractive answer, but still ground it in the given text.\n"
        "3. If you cannot answer from the contexts, mark the answer as unanswerable.\n"
        "4. Always indicate which context_ids, concepts, edges, and snippets you used.\n\n"
        "Return ONLY a single valid JSON object with the following structure:\n"
        f"{ANSWER_JSON_SCHEMA}\n\n"
        "Remember:\n"
        "- Do not hallucinate facts that are not in the contexts.\n"
        "- Do not use outside knowledge.\n"
        "- If unsure, prefer 'unanswerable'.\n"
    )

    return prompt


# --------------------------------------------------------------------------
# 4. LLM call & JSON parsing
# --------------------------------------------------------------------------

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client; relies on OPENAI_API_KEY in environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set in environment/.env for Q6_answer_generator."
        )
    return OpenAI()


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """
    Parse JSON from the model output.
    - Strips common ```json fences if present.
    - Attempts to locate the first '{' and last '}' for robustness.
    """
    text = raw_text.strip()

    # Remove common Markdown fences
    if text.startswith("```"):
        # strip ``` and possible language tag
        text = text.lstrip("`")
        # after stripping leading backticks, we might still have 'json\n{...}'
        # just find the first '{'
    if text.endswith("```"):
        text = text.rstrip("`")

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try bracket-range extraction
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not parse JSON from LLM output: {raw_text[:200]}...")


def call_llm_for_answer(prompt: str, client: OpenAI) -> Dict[str, Any]:
    """
    Call the LLM and return the parsed answer JSON.
    On failure, return a conservative unanswerable structure.
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a graph-based retrieval answerer. "
                        "You MUST return a single valid JSON object and nothing else."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        content = resp.choices[0].message.content or ""
        content = content.strip()
        answer_json = parse_llm_json(content)

        # Ensure required keys with sensible defaults
        answer_json.setdefault("answer", "")
        answer_json.setdefault("answer_type", "unanswerable")
        answer_json.setdefault("answer_confidence", 0.0)
        answer_json.setdefault("used_context_ids", [])
        answer_json.setdefault("supporting_concepts", [])
        answer_json.setdefault("supporting_edges", [])
        answer_json.setdefault("supporting_snippets", [])
        answer_json.setdefault("unanswerable_flag", False)
        answer_json.setdefault("hallucination_risk_flag", False)
        answer_json.setdefault("explanation", "")

        return answer_json

    except Exception as e:
        print(f"[Q6][ERROR] LLM or JSON parsing error: {e}")
        # Conservative fallback: unanswerable
        return {
            "answer": "",
            "answer_type": "unanswerable",
            "answer_confidence": 0.0,
            "used_context_ids": [],
            "supporting_concepts": [],
            "supporting_edges": [],
            "supporting_snippets": [],
            "unanswerable_flag": True,
            "hallucination_risk_flag": True,
            "explanation": "Failed to generate or parse answer JSON. Marked as unanswerable.",
        }


# --------------------------------------------------------------------------
# 5. Main driver
# --------------------------------------------------------------------------

def run_q6(
    q5_path: str = Q5_INPUT_FILE,
    q6_out_path: str = Q6_OUTPUT_FILE,
) -> None:
    print("[Q6] Starting Q6 Answer Generator...")

    plans = load_q5_plans(q5_path)
    if not plans:
        print("[Q6][ERROR] No Q5 records found. Aborting Q6.")
        return

    os.makedirs(os.path.dirname(q6_out_path), exist_ok=True)
    if os.path.exists(q6_out_path):
        os.remove(q6_out_path)

    client = get_openai_client()

    count = 0
    with open(q6_out_path, "w", encoding="utf-8") as outfile:
        for rec in plans:
            qid = rec.get("id", rec.get("question_id", f"Q{count+1}"))
            contexts = select_top_contexts(rec, TOP_K_CONTEXTS)

            if not contexts:
                # No contexts – mark as unanswerable without LLM call
                print(f"[Q6][WARN] No retrieval contexts for QID {qid}. Marking unanswerable.")
                answer_json = {
                    "answer": "",
                    "answer_type": "unanswerable",
                    "answer_confidence": 0.0,
                    "used_context_ids": [],
                    "supporting_concepts": [],
                    "supporting_edges": [],
                    "supporting_snippets": [],
                    "unanswerable_flag": True,
                    "hallucination_risk_flag": False,
                    "explanation": "No retrieval contexts available; cannot answer.",
                }
            else:
                prompt = build_q6_prompt(rec, contexts)
                answer_json = call_llm_for_answer(prompt, client)

            out_rec = rec.copy()
            out_rec["generated_answer"] = answer_json.get("answer", "")
            out_rec["answer_type"] = answer_json.get("answer_type", "unanswerable")
            out_rec["answer_confidence"] = answer_json.get("answer_confidence", 0.0)
            out_rec["used_context_ids"] = answer_json.get("used_context_ids", [])
            out_rec["supporting_concepts"] = answer_json.get("supporting_concepts", [])
            out_rec["supporting_edges"] = answer_json.get("supporting_edges", [])
            out_rec["supporting_snippets"] = answer_json.get("supporting_snippets", [])
            out_rec["unanswerable_flag"] = answer_json.get("unanswerable_flag", False)
            out_rec["hallucination_risk_flag"] = answer_json.get("hallucination_risk_flag", False)
            out_rec["answer_explanation"] = answer_json.get("explanation", "")
            out_rec["q6_notes"] = (
                "Answer generated from graph-scoped retrieval contexts using Q6 answer generator."
            )

            outfile.write(json.dumps(out_rec) + "\n")
            count += 1

            if count % 10 == 0:
                print(f"[Q6][INFO] Processed {count} questions...")

    print(f"[Q6] Completed. Wrote {count} records to: {q6_out_path}")


if __name__ == "__main__":
    run_q6()