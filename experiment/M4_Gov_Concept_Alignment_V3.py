# --------------------------------------------------------------------------
# MODULE 4 (PARALLEL): same alignment DECISION LOGIC as the hardened V3
# (identical prompt, system instruction, conf<40 gate, edge rules, temp=0.0),
# but LLM calls run concurrently. Graph mutations happen ONLY in the main
# thread, so the resulting graph is identical to the serial version.
# Also writes per-node results to output/M4_alignment_results.jsonl for the
# equivalence check against the serial run's log.
#
# OUTPUT-NEUTRAL by construction: concurrency changes *when* calls happen,
# never *what* each call sends or *how* results are applied.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
import re
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

print("--- Starting M4_V3.1 (PARALLEL): Poly-Ontological Alignment ---")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-3-flash-preview"
REQUEST_TIMEOUT_SECONDS = 300
MAX_TRANSPORT_ATTEMPTS = 5
CHECKPOINT_EVERY = 250
MAX_WORKERS = 10          # concurrent LLM calls; well under Tier-1 RPM. raise if stable.

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DATA_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_3_Augmented_Graph.graphml')
INPUT_REF_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'R_Embedded_Reference_Ontology.graphml')
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.graphml')
RESULTS_LOG = os.path.join(PROJECT_ROOT, 'output', 'M4_alignment_results.jsonl')

TRANSIENT = ("503", "unavailable", "429", "resource_exhausted", "500",
             "internal", "deadline", "timeout", "high demand")

def _is_transient(e):
    return any(t in str(e).lower() for t in TRANSIENT)

# ---- IDENTICAL to hardened V3 (verbatim) ----
SYSTEM_INSTRUCTION = """
You are a Business Architecture Mapper.
TASK: Align the 'Document Concept' to the best matching 'Reference Concept'.

RULES:
1. Match: Direct semantic equivalent (e.g., 'Nets' -> 'Organization').
2. Adaptive: Specific instance (e.g., 'Jason Collins' -> 'Person').
3. Unmapped: No logical connection or weak definition.

OUTPUT JSON: {"status": "Match|Adaptive|Unmapped", "target": "RefNodeName", "reason": "..."}
"""

def extract_json_object(resp_text):
    try:
        clean_text = re.sub(r'```json\s*|```', '', resp_text).strip()
        data = json.loads(clean_text)
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else None
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None

def align_concept(doc_node, definition, ref_nodes_text):
    prompt = f"""
    Document Concept: '{doc_node}'
    Definition: '{definition}'

    Available Reference Concepts:
    {ref_nodes_text}
    """
    for attempt in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                client.models.generate_content,
                model=LLM_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            response = future.result(timeout=REQUEST_TIMEOUT_SECONDS)
            result = extract_json_object(response.text)
            if not result:
                raise ValueError(f"Invalid alignment payload for node: {doc_node}")
            return result
        except Exception as e:
            if attempt < MAX_TRANSPORT_ATTEMPTS:
                wait = (min(60, 2 ** attempt) + random.uniform(0, 2)) if _is_transient(e) else 2
                time.sleep(wait)
                continue
            raise RuntimeError(f"M4 alignment failed for '{doc_node}' after {attempt} attempts: {e}") from e

def align_safe(node, defn, ref_list):
    """Never raises: returns (node, result_dict, error_or_None). Runs in a worker thread."""
    try:
        return node, align_concept(node, defn, ref_list), None
    except Exception as e:
        return node, {"status": "Unmapped (Error)", "target": ""}, str(e)[:80]

def run_m4_alignment():
    if not os.path.exists(INPUT_DATA_GRAPH):
        sys.exit(f"[CRITICAL] Data Graph missing: {INPUT_DATA_GRAPH}")
    if not os.path.exists(INPUT_REF_GRAPH):
        sys.exit(f"[CRITICAL] Reference Ontology missing: {INPUT_REF_GRAPH}")

    print("Loading Data Graph...")
    G_doc = nx.read_graphml(INPUT_DATA_GRAPH)
    print(f"-> Loaded Data Graph: {G_doc.number_of_nodes()} nodes")

    print(f"Loading Reference Ontology: {INPUT_REF_GRAPH}...")
    G_ref = nx.read_graphml(INPUT_REF_GRAPH)
    if not isinstance(G_ref, nx.MultiDiGraph):
        G_ref = nx.MultiDiGraph(G_ref)
    print(f"-> Loaded Reference Ontology: {G_ref.number_of_nodes()} nodes")

    ref_list = "\n".join([f"- {n}" for n in G_ref.nodes])
    ref_candidates_seen = G_ref.number_of_nodes()
    ref_node_set = set(G_ref.nodes)
    print(f"-> M4 alignment vocabulary: {ref_candidates_seen} BIZBOK concepts visible to LLM")

    if os.path.exists(OUTPUT_GRAPH):
        print(f"-> Resuming from partial hybrid {OUTPUT_GRAPH}")
        G_hybrid = nx.read_graphml(OUTPUT_GRAPH)
        if not isinstance(G_hybrid, nx.MultiDiGraph):
            G_hybrid = nx.MultiDiGraph(G_hybrid)
    else:
        G_hybrid = nx.compose(G_doc, G_ref)

    doc_nodes = [n for n in G_doc.nodes if n not in ref_node_set]

    # partition: resume-skip / low-conf (no LLM) / to_align
    to_align = []
    low_conf = 0
    for node in doc_nodes:
        if str(G_hybrid.nodes[node].get('alignment_status', '')).strip():
            continue  # already done (resume)
        defn = G_hybrid.nodes[node].get('definition', '')
        try:
            conf = int(float(G_hybrid.nodes[node].get('confidence', 0)))
        except Exception:
            conf = 0
        if conf < 40:
            G_hybrid.nodes[node]['alignment_status'] = "Unmapped (Low Conf)"
            G_hybrid.nodes[node]['alignment_candidates_seen'] = ref_candidates_seen
            low_conf += 1
            continue
        to_align.append((node, defn))

    print(f"Aligning {len(to_align)} concepts concurrently ({MAX_WORKERS} workers); "
          f"{low_conf} low-conf skipped without LLM.")

    results_fp = open(RESULTS_LOG, "a", encoding="utf-8")
    aligned_count = failed_count = processed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(align_safe, node, defn, ref_list) for node, defn in to_align]
        for fut in as_completed(futures):
            node, result, err = fut.result()          # completes in MAIN thread
            status = result.get('status', 'Unmapped')
            target = result.get('target', '')

            # ----- graph mutation: MAIN THREAD ONLY (same logic as serial) -----
            if err:
                G_hybrid.nodes[node]['alignment_status'] = "Unmapped (Error)"
                failed_count += 1
            elif status in ["Match", "Adaptive"] and target in ref_node_set:
                G_hybrid.add_edge(node, target, key=f"Align_{node}_{target}",
                                  predicate="IS_ALIGNED_WITH", type="Governance", weight=1.0)
                G_hybrid.nodes[node]['alignment_status'] = status
                aligned_count += 1
            else:
                G_hybrid.nodes[node]['alignment_status'] = "Unmapped"
            G_hybrid.nodes[node]['alignment_candidates_seen'] = ref_candidates_seen

            results_fp.write(json.dumps({"node": node, "status": status, "target": target}) + "\n")
            processed += 1
            if processed % 10 == 0 or err:
                print(f"[{processed}/{len(to_align)}] Evaluated '{node}': {status} -> {target}"
                      + (f"  [SKIP:{err}]" if err else ""))
            if processed % CHECKPOINT_EVERY == 0:
                results_fp.flush()
                nx.write_graphml(G_hybrid, OUTPUT_GRAPH)
                print(f"      [checkpoint] {processed} processed")

    results_fp.close()
    nx.write_graphml(G_hybrid, OUTPUT_GRAPH)
    print("\n" + "=" * 50)
    print(f"M4 PARALLEL COMPLETE. Aligned: {aligned_count} | Unmapped-error: {failed_count} | low-conf: {low_conf}")
    print(f"Graph:   {OUTPUT_GRAPH}")
    print(f"Results: {RESULTS_LOG}")
    print("=" * 50)

if __name__ == "__main__":
    run_m4_alignment()
