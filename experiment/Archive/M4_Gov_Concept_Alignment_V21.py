# --------------------------------------------------------------------------
# MODULE 4: Business Architecture Enhancement (M4_V2.1)
# STRATEGY: Atomic Ingestion & Namespace Isolation
# GOAL: Resolve CH-001 (Metadata Vacuum) by enforcing Attribute Inheritance.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time 

print("--- Starting Module 4: Atomic Governed Alignment (V2.1) ---")

# --- 0. Setup ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL_NAME = "gemini-2.0-flash-lite"
RATE_LIMIT_DELAY = 1.5 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_DOC_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3.3_Gov_Augmented_Graph.gml')
INPUT_REF_ONTOLOGY = os.path.join(PROJECT_ROOT, 'output', 'R_Reference_Ontology_Governance.gml')
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Gov_Hybrid_Graph.gml')

# --- 1. Load Data ---
G_doc = nx.read_gml(INPUT_DOC_GRAPH)
G_ref = nx.read_gml(INPUT_REF_ONTOLOGY)

# Prepare BIZBOK context for LLM
BIZBOK_LIST = "\n".join([f"- {n}: {d.get('definition')}" for n, d in G_ref.nodes(data=True)])

SYSTEM_INSTRUCTION = f"""
You are a Business Architecture Mapping Agent. Align 'Document Concepts' to the 'R_Reference_Ontology'.
REFERENCE CONCEPTS:
{BIZBOK_LIST}

RULES:
1. Match: Use if concept is a direct instance of the Reference.
2. Adaptive: Use for novel terms, map to closest Reference parent.
3. Unmapped: Use if confidence < 40 or no bridge exists.
"""

OUTPUT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "status": types.Schema(type=types.Type.STRING, enum=["Match", "Adaptive", "Unmapped"]),
        "reference_concept": types.Schema(type=types.Type.STRING),
        "mapping_reason": types.Schema(type=types.Type.STRING),
    },
    required=["status", "reference_concept", "mapping_reason"],
)

def align_to_standard(concept_name, definition, client):
    user_prompt = f"Align Concept: '{concept_name}'\nDefinition: '{definition}'"
    try:
        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=OUTPUT_SCHEMA,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except:
        return {"status": "Unmapped", "reference_concept": "N/A", "mapping_reason": "API_ERROR"}

# --- 2. Main Execution (Atomic Injection) ---
if __name__ == "__main__":
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Start with the Reference Layer as the immutable base
    G_hybrid = G_ref.copy()
    nx.set_node_attributes(G_hybrid, "ReferenceConcept", "node_type")

    doc_nodes = list(G_doc.nodes(data=True))
    print(f"Injecting {len(doc_nodes)} nodes into Governed Architecture...")

    for i, (node_name, node_data) in enumerate(doc_nodes):
        # Step A: Enforce Namespace Isolation
        record_id = node_data.get('source_chunk_id', 'Global').split('_')[0]
        atomic_id = f"{record_id}:{node_name}"
        
        # Step B: LLM Alignment
        mapping = align_to_standard(node_name, node_data.get('generated_definition'), client)
        status = mapping.get("status")
        ref_target = mapping.get("reference_concept")

        # Step C: Metadata-Rich Injection (Fixes CH-001)
        G_hybrid.add_node(atomic_id, **node_data) # Preserves all source attributes
        G_hybrid.nodes[atomic_id]['node_type'] = f"{status}Concept" if status != "Match" else "DocumentConcept"
        G_hybrid.nodes[atomic_id]['original_label'] = node_name

        # Step D: Governance Bridge
        if status in ["Match", "Adaptive"] and ref_target in G_ref:
            rel = "IS_ALIGNED_WITH" if status == "Match" else "ADAPTED_FROM"
            G_hybrid.add_edge(atomic_id, ref_target, relationship=rel, mapping_status=status)
            print(f"[{i+1}] {atomic_id} -> {rel} -> {ref_target}")
        
        time.sleep(RATE_LIMIT_DELAY)

    nx.write_gml(G_hybrid, OUTPUT_GRAPH)
    print(f"\n[PHD SUCCESS] M4_V2.1 Complete. Unique records preserved.")