# --------------------------------------------------------------------------
# MODULE 4: M4_Gov_Ontology_Alignment_V3.py
# ARCHITECTURE: Hybrid Graph Construction with Robust JSON Parsing
# FIX: Handles LLM returning lists instead of dicts.
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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

print("--- Starting M4_V3.1: Poly-Ontological Alignment ---")

# --- 0. Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    sys.exit("[CRITICAL] API Key missing.")

client = genai.Client(api_key=api_key)
LLM_MODEL = "gemini-3-flash-preview"
RATE_LIMIT_DELAY = 1.0
REQUEST_TIMEOUT_SECONDS = 300
MAX_TRANSPORT_ATTEMPTS = 3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# INPUT 1: The Data Graph (from M3.3)
INPUT_DATA_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3_3_Augmented_Graph.graphml')
# INPUT 2: The Reference Ontology 
INPUT_REF_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'R_Embedded_Reference_Ontology.graphml')
# OUTPUT: The Hybrid Graph
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.graphml')

# --- 1. Alignment Logic ---
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
    """
    Robustly extracts a dictionary even if wrapped in lists or markdown.
    """
    try:
        # 1. Strip Markdown
        clean_text = re.sub(r'```json\s*|```', '', resp_text).strip()
        
        # 2. Parse
        data = json.loads(clean_text)
        
        # 3. FIX: Handle List Wrapper
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]
            else:
                return None
                
        # 4. Return Dict
        if isinstance(data, dict):
            return data
            
    except Exception as e:
        # print(f"JSON Parse Error: {e}")
        pass
    return None

def align_concept(doc_node, definition, ref_nodes_text, client):
    prompt = f"""
    Document Concept: '{doc_node}'
    Definition: '{definition}'
    
    Available Reference Concepts:
    {ref_nodes_text}
    """
    last_error = None
    for attempt in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
        try:
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                client.models.generate_content,
                model=LLM_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            try:
                response = future.result(timeout=REQUEST_TIMEOUT_SECONDS)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

            result = extract_json_object(response.text)
            if not result:
                raise ValueError(f"Invalid alignment payload for node: {doc_node}")
            return result

        except FuturesTimeoutError as e:
            last_error = TimeoutError(
                f"Alignment request timed out after {REQUEST_TIMEOUT_SECONDS}s"
            )
            if attempt == MAX_TRANSPORT_ATTEMPTS:
                raise RuntimeError(
                    f"M4 alignment failed for node '{doc_node}' "
                    f"after {attempt} attempts: {last_error}"
                ) from e
            time.sleep(2)

        except Exception as e:
            last_error = e
            if attempt == MAX_TRANSPORT_ATTEMPTS:
                raise RuntimeError(
                    f"M4 alignment failed for node '{doc_node}' "
                    f"after {attempt} attempts: {e}"
                ) from e
            time.sleep(2)

# --- 2. Main Execution ---
def run_m4_alignment():
    # 1. Validation
    if not os.path.exists(INPUT_DATA_GRAPH):
        sys.exit(f"[CRITICAL] Data Graph missing: {INPUT_DATA_GRAPH}")
    if not os.path.exists(INPUT_REF_GRAPH):
        sys.exit(f"[CRITICAL] Reference Ontology missing: {INPUT_REF_GRAPH}")

    if os.path.exists(OUTPUT_GRAPH):
        os.remove(OUTPUT_GRAPH)
    
    # 2. Load Graphs (Robust Format Handling)
    print("Loading Data Graph...")
    try:
        G_doc = nx.read_graphml(INPUT_DATA_GRAPH)
        print(f"-> Loaded Data Graph: {G_doc.number_of_nodes()} nodes")
    except Exception as e:
        sys.exit(f"[CRITICAL] Failed to load Data Graph: {e}")

    # Load Reference Graph
    if os.path.exists(INPUT_REF_GRAPH):
        print(f"Loading Reference Ontology: {INPUT_REF_GRAPH}...")
        try:
            if INPUT_REF_GRAPH.endswith('.gml'):
                G_ref = nx.read_gml(INPUT_REF_GRAPH)
            elif INPUT_REF_GRAPH.endswith('.graphml'):
                G_ref = nx.read_graphml(INPUT_REF_GRAPH)
            else:
                # Fallback check
                try:
                    G_ref = nx.read_gml(INPUT_REF_GRAPH)
                except:
                    G_ref = nx.read_graphml(INPUT_REF_GRAPH)
            
            # Ensure Topology Match (MultiDiGraph)
            if not isinstance(G_ref, nx.MultiDiGraph):
                G_ref = nx.MultiDiGraph(G_ref)
                
            print(f"-> Loaded Reference Ontology: {G_ref.number_of_nodes()} nodes")
            
        except Exception as e:
            sys.exit(f"[CRITICAL] Could not parse Reference Ontology: {e}")
    
    # Prepare Context (List of Ref Nodes for LLM)
    ref_list = "\n".join([f"- {n}" for n in G_ref.nodes]) 

    # 3. Hybrid Merge
    G_hybrid = nx.compose(G_doc, G_ref)
    
    aligned_count = 0
    
    # 4. Alignment Loop
    # Filter only Document Concepts (concepts not originally in G_ref)
    ref_node_set = set(G_ref.nodes)
    doc_nodes = [n for n in G_doc.nodes if n not in ref_node_set]
    
    print(f"Aligning {len(doc_nodes)} Document Concepts...")

    for i, node in enumerate(doc_nodes):
        # Retrieve M3.3 Attributes
        defn = G_hybrid.nodes[node].get('definition', '')
        conf = 0
        try:
            # Handle string/int conversion safely
            raw_conf = G_hybrid.nodes[node].get('confidence', 0)
            conf = int(float(raw_conf))
        except:
            conf = 0
        
        # GOVERNANCE GATE: Only align confident definitions
        if conf < 40:
            G_hybrid.nodes[node]['alignment_status'] = "Unmapped (Low Conf)"
            continue

        # Call LLM
        result = align_concept(node, defn, ref_list, client)
        
        status = result.get('status', 'Unmapped')
        target = result.get('target', '')
        
        print(f"[{i+1}/{len(doc_nodes)}] Evaluated '{node}': {status} -> {target}")

        # Create Alignment Edge
        if status in ["Match", "Adaptive"] and target in ref_node_set:
            G_hybrid.add_edge(
                node, 
                target, 
                key=f"Align_{node}_{target}",
                predicate="IS_ALIGNED_WITH", 
                type="Governance", 
                weight=1.0 # Max Authority
            )
            G_hybrid.nodes[node]['alignment_status'] = status
            aligned_count += 1
            if i % 10 == 0: print(f"[{i}] Aligned '{node}' -> '{target}' ({status})")
        else:
            G_hybrid.nodes[node]['alignment_status'] = "Unmapped"
            
        time.sleep(RATE_LIMIT_DELAY)

    # 5. Persistence
    nx.write_graphml(G_hybrid, OUTPUT_GRAPH)
    print("\n" + "="*50)
    print(f"M4_V3.1 COMPLETE. Hybrid Graph Created.")
    print(f"Total Aligned Nodes: {aligned_count}")
    print(f"Artifact: {OUTPUT_GRAPH}")
    print("="*50)

if __name__ == "__main__":
    run_m4_alignment()