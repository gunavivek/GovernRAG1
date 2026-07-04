# --------------------------------------------------------------------------
# MODULE 3.3 (HARDENED): retry/backoff on transient 503/429, per-node skip,
# and incremental checkpointing so a crash RESUMES instead of restarting.
# Behaviour is otherwise identical to V3 (same model, prompt, temperature=0.0),
# so it is OUTPUT-NEUTRAL — no effect on results or comparability.
#
# Drop-in replacement for experiment/M3.3_Gov_Concept_Augmentation_V3.py
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
import time
import re
import sys
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-3-flash-preview"
RATE_LIMIT_DELAY = 1.0

MAX_RETRIES = 6            # attempts per node before skipping it
CHECKPOINT_EVERY = 200     # save partial graph every N augmented nodes

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_Knowledge_Graph.graphml')
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_3_Augmented_Graph.graphml')

TRANSIENT = ("503", "unavailable", "429", "resource_exhausted", "500",
             "internal", "deadline", "timeout", "high demand")


def _is_transient(e) -> bool:
    s = str(e).lower()
    return any(t in s for t in TRANSIENT)


def extract_json_object(resp_text):
    try:
        clean_text = re.sub(r'```json\s*|```', '', resp_text).strip()
        data = json.loads(clean_text)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def generate_weighted_definition(node_name: str, context_triples: list):
    """Same synthesis as V3, but retries transient server errors with backoff."""
    if not context_triples:
        return {"definition": "Context too sparse.", "confidence": 0}

    context_str = "\n".join(context_triples)
    system_instruction = f"""
    You are a Semantic Graph Auditor.
    TASK: Synthesize a single-sentence definition for the concept '{node_name}'.

    INPUT DATA: A list of facts (Edges) with 'Weights' (0.0-1.0).

    CRITICAL RULE:
    - Give HIGH PRIORITY to facts with High Weights (>0.4).
    - Give LOW PRIORITY to facts with Low Weights (<0.2).
    - If facts conflict, the High Weight fact is the Truth.

    OUTPUT JSON: {{"definition": "The synthesized text...", "confidence": 0-100}}
    """

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=[f"Weighted Facts for '{node_name}':\n{context_str}"],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            result = extract_json_object(response.text)
            if not result:
                raise ValueError(f"Invalid definition payload for node: {node_name}")
            return result
        except Exception as e:
            last_err = e
            if _is_transient(e) and attempt < MAX_RETRIES:
                wait = min(90, 2 ** attempt) + random.uniform(0, 2)
                print(f"      [retry {attempt}/{MAX_RETRIES}] '{node_name}': transient "
                      f"({str(e)[:60]}...) waiting {wait:.0f}s")
                time.sleep(wait)
                continue
            raise RuntimeError(f"M3.3 definition failed for node '{node_name}': {e}") from e
    raise RuntimeError(f"M3.3 exhausted retries for '{node_name}': {last_err}")


def run_m3_3_weighted_augmentation():
    if not os.path.exists(INPUT_GRAPH):
        sys.exit(f"[CRITICAL] Input Graph missing: {INPUT_GRAPH}")

    # RESUME: if a partial output exists, continue from it; else start from M3 output.
    if os.path.exists(OUTPUT_GRAPH):
        print(f"M3.3 (HARDENED): resuming from partial output {OUTPUT_GRAPH}")
        G = nx.read_graphml(OUTPUT_GRAPH)
    else:
        print("M3.3 (HARDENED): fresh start from M3 graph")
        G = nx.read_graphml(INPUT_GRAPH)
    print(f"-> Loaded {G.number_of_nodes()} Nodes and {G.number_of_edges()} Edges.")

    augmented_count = 0
    skipped_failed = 0
    already_done = 0

    for i, node in enumerate(list(G.nodes)):
        # skip nodes already defined in a previous (resumed) run
        if str(G.nodes[node].get('definition', '')).strip():
            already_done += 1
            continue

        context_triples = []
        for u, v, key, data in G.edges(node, keys=True, data=True):
            context_triples.append(f"-> connects to '{v}' via '{data.get('predicate','related')}' "
                                   f"[Domain: {data.get('domain','Gen')} | Weight: {data.get('weight',0.1)}]")
        for u, v, key, data in G.in_edges(node, keys=True, data=True):
            context_triples.append(f"<- is connected from '{u}' via '{data.get('predicate','related')}' "
                                   f"[Domain: {data.get('domain','Gen')} | Weight: {data.get('weight',0.1)}]")

        if not context_triples:
            continue

        try:
            result = generate_weighted_definition(node, context_triples)
        except Exception as e:
            # after all retries, DON'T kill the stage — log, placeholder, continue
            print(f"      [SKIP] '{node}' failed after {MAX_RETRIES} retries: {str(e)[:80]}")
            result = {"definition": "Synthesis unavailable (transient API error)", "confidence": 0}
            skipped_failed += 1

        G.nodes[node]['definition'] = result.get('definition', 'Synthesis Failed')
        G.nodes[node]['confidence'] = int(result.get('confidence', 0))
        augmented_count += 1

        if i % 10 == 0:
            print(f"[{i}/{G.number_of_nodes()}] Defined '{node}' (Conf: {result.get('confidence')})")

        # incremental checkpoint so a crash resumes here, not from zero
        if augmented_count % CHECKPOINT_EVERY == 0:
            nx.write_graphml(G, OUTPUT_GRAPH)
            print(f"      [checkpoint] saved after {augmented_count} new nodes")

        time.sleep(RATE_LIMIT_DELAY)

    nx.write_graphml(G, OUTPUT_GRAPH)
    print("\n" + "=" * 50)
    print(f"M3.3 COMPLETE. New: {augmented_count} | resumed-skip: {already_done} | failed-skip: {skipped_failed}")
    print(f"Artifact: {OUTPUT_GRAPH}")
    print("=" * 50)


if __name__ == "__main__":
    run_m3_3_weighted_augmentation()
