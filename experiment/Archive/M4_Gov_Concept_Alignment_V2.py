# --------------------------------------------------------------------------
# MODULE 4: Business Architecture Enhancement (M4_V2)
# STRATEGY: Top-Down Ontological Alignment (Architecture-First Ingestion)
# GOAL: Semantic Triangulation between M3.3 Governed Graph and R-Ontology.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time 

print("--- Starting Module 4: Governed Concept Alignment (M4_V2) ---")

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL_NAME = "gemini-2.0-flash-lite" # Optimized for speed/cost
RATE_LIMIT_DELAY = 2 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Input Artifacts
INPUT_DOC_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M3.3_Gov_Augmented_Graph.gml')
INPUT_REF_ONTOLOGY = os.path.join(PROJECT_ROOT, 'output', 'R_Reference_Ontology_Governance.gml')

# Output Artifact (Final Hybrid Graph)
OUTPUT_GRAPH = os.path.join(PROJECT_ROOT, 'output', 'M4_Gov_Hybrid_Graph.gml')

# --- 1. Load Graphs and Context ---
try:
    G_doc = nx.read_gml(INPUT_DOC_GRAPH)
    G_ref = nx.read_gml(INPUT_REF_ONTOLOGY)
except FileNotFoundError as e:
    print(f"\n[ERROR] Missing input: {e}")
    exit()

# Extract BIZBOK context for the LLM
BIZBOK_CONTEXT = []
for node, data in G_ref.nodes(data=True):
    BIZBOK_CONTEXT.append(f"- {node}: {data.get('definition', 'No definition available.')}")
BIZBOK_LIST_TEXT = "\n".join(BIZBOK_CONTEXT)

# --- 2. Alignment Logic and Schema ---
SYSTEM_INSTRUCTION = f"""
You are a Business Architecture Mapping Agent. Your task is to align 'Document Concepts' to the 'R_Reference_Ontology'.

REFERENCE CONCEPTS (BIZBOK Standard):
{BIZBOK_LIST_TEXT}

CLASSIFICATION RULES:
1. Match: Use if the Document Concept is a direct instance of the Reference Concept.
2. Adaptive: Use for specific/novel terms (e.g., 'Brooklyn Nets'). Map to the closest Reference parent (e.g., 'Common:Business Entity').
3. Unmapped: Use ONLY if the definition is extremely weak (Confidence < 40) or no logical bridge exists.

Output MUST be a valid JSON object.
"""

OUTPUT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "status": types.Schema(type=types.Type.STRING, enum=["Match", "Adaptive", "Unmapped"]),
        "reference_concept": types.Schema(type=types.Type.STRING, description="Domain:Concept key from Reference Layer"),
        "mapping_reason": types.Schema(type=types.Type.STRING),
    },
    required=["status", "reference_concept", "mapping_reason"],
)

# --- 3. Core Mapping Function ---
def align_to_standard(concept_name, concept_data, client):
    user_prompt = f"""
    Align Concept: '{concept_name}'
    Definition: '{concept_data.get('generated_definition')}'
    Confidence: {concept_data.get('confidence_score')}/100
    """
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
    except Exception as e:
        return {"status": "Unmapped", "reference_concept": "N/A", "mapping_reason": str(e)}

# --- 4. Main Execution ---
if __name__ == "__main__":
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Composite Hybrid Graph Construction
    G_hybrid = nx.compose(G_doc, G_ref) # Merges both layers
    
    doc_nodes = list(G_doc.nodes)
    print(f"Aligning {len(doc_nodes)} concepts to the BIZBOK baseline...")

    for i, node_name in enumerate(doc_nodes):
        node_data = G_doc.nodes[node_name]
        print(f"[{i+1}/{len(doc_nodes)}] Aligning: {node_name}")
        
        mapping = align_to_standard(node_name, node_data, client)
        
        status = mapping.get("status")
        ref_target = mapping.get("reference_concept")
        
        # Persist Traceability and Classification
        G_hybrid.nodes[node_name]['node_type'] = f"{status}Concept" if status != "Match" else "DocumentConcept"
        
        if status in ["Match", "Adaptive"] and ref_target in G_ref:
            rel = "IS_ALIGNED_WITH" if status == "Match" else "ADAPTED_FROM"
            G_hybrid.add_edge(
                node_name, ref_target, 
                relationship=rel,
                mapping_justification=mapping.get("mapping_reason"),
                mapping_status=status
            )
            print(f"  -> {status}: {rel} {ref_target}")
        
        time.sleep(RATE_LIMIT_DELAY)

    # Final Persistence
    nx.write_gml(G_hybrid, OUTPUT_GRAPH)
    print(f"\n[SUCCESS] M4_V2 Complete. Hybrid Graph saved: {OUTPUT_GRAPH}")