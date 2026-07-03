# --------------------------------------------------------------------------
# MODULE 4: Business Architecture Enhancement (Concept Alignment)
# FINAL VERSION: Implements Adaptive Fallback Strategy (Strategy 2) and reduced delay.
# --------------------------------------------------------------------------
import os
import json
import networkx as nx
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time 

print("--- Starting Module 4: Business Architecture Enhancement (Hybrid Model Integration) ---")

# --- 0. Setup and Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
# CHANGE 1: Reduced Delay for Pro Plan (High Risk/High Performance)
RATE_LIMIT_DELAY = 2 

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Input Graphs
INPUT_DOC_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_3_Augmented_Graph.gml')
INPUT_REF_ONTOLOGY_FILE = os.path.join(PROJECT_ROOT, 'output', 'M3_5_Reference_Ontology.gml')

# Output Graph (Final Hybrid Graph)
OUTPUT_GRAPH_FILE = os.path.join(PROJECT_ROOT, 'output', 'M4_Hybrid_Graph.gml')

# --- 1. Load Graphs and Prepare LLM Context ---
try:
    G_doc = nx.read_gml(INPUT_DOC_GRAPH_FILE)
    G_ref = nx.read_gml(INPUT_REF_ONTOLOGY_FILE)
except FileNotFoundError as e:
    print(f"\n[ERROR] Required input graph file not found: {e}. Ensure M3.3 and M3.5 were run successfully.")
    exit()

BIZBOK_CONCEPT_LIST = sorted(list(G_ref.nodes))
BIZBOK_LIST_TEXT = "\n".join([f"- {key}" for key in BIZBOK_CONCEPT_LIST])


# --- 2. Define LLM Prompt for Hybrid Concept Mapping ---
SYSTEM_INSTRUCTION = f"""
You are an expert Business Architecture Mapping Agent. Your task is to analyze a 'Document Concept' and its **GENERATED DEFINITION** and classify its best relationship to the provided domain-qualified BIZBOK 'Reference Concepts'.

Available BIZBOK Reference Concepts (Composite Key format: Domain:Concept):
{BIZBOK_LIST_TEXT}

Rules for Classification:
1. If the Document Concept and its definition are highly relevant to one of the BIZBOK Reference Concepts, set 'status' to 'Match'.
2. If the concept is a specific term (e.g., 'Apollo Architecture') but should be linked to the BA layer, set 'status' to 'Adaptive'.
3. If 'status' is 'Adaptive', you MUST propose the single closest BIZBOK Reference Concept to link it to.
4. If the concept's generated definition is weak (e.g., confidence score is low), and no clear connection exists, set 'status' to 'Unmapped'.

**CRITICAL GUIDANCE FOR TECHNICAL/PLATFORM CONCEPTS (Adaptive Fallback):**
If a concept relates to a technology implementation or infrastructure type (e.g., 'cloud-native architecture'), classify it as **Adaptive** and link it to the core 'Platform Architecture Asset' or 'Asset' reference concept.
Output MUST be a valid JSON object.
"""

OUTPUT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "status": types.Schema(type=types.Type.STRING, enum=["Match", "Adaptive", "Unmapped"], description="Classification status: Match, Adaptive, or Unmapped."),
        "reference_concept": types.Schema(type=types.Type.STRING, description="The name of the closest BIZBOK Reference Concept from the list (MUST be in the format Domain:Concept)."),
        "mapping_reason": types.Schema(type=types.Type.STRING, description="A brief justification for the status and connection."),
    },
    required=["status", "reference_concept", "mapping_reason"],
)

# --- 3. Core Mapping Function ---
def map_concept_to_bizbok(concept_name, concept_data, client: genai.Client):
    """Uses Gemini to find the best BIZBOK match/alignment for an augmented document concept."""
    
    generated_def = concept_data.get('generated_definition', 'No generated definition.')
    confidence = concept_data.get('confidence_score', 'N/A')
    
    user_prompt = f"""
    Document Concept: '{concept_name}' 
    Generated Definition: '{generated_def}'
    Definition Confidence: {confidence}/100
    """
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=OUTPUT_SCHEMA,
    )
    
    try:
        response = client.models.generate_content(
            model=LLM_MODEL_NAME,
            contents=[user_prompt],
            config=config,
        )
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        print(f"  [ERROR] Gemini API call failed for concept '{concept_name}'. Error: {e}")
        return {"status": "API_ERROR", "reference_concept": "N/A", "mapping_reason": str(e)}

# --- 4. Main Execution Logic ---
if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("\n[SETUP ERROR] GEMINI_API_KEY not found. Please create a .env file.")
        exit()

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # --- Graph Merging ---
    G_hybrid = nx.compose(G_doc, G_ref) 
    
    document_concepts_to_map = list(G_doc.nodes)

    print(f"Initial Hybrid Graph (M3.3 + M3.5) Status: {G_hybrid.number_of_nodes()} nodes, {G_hybrid.number_of_edges()} edges.")
    print(f"Starting alignment process for {len(document_concepts_to_map)} Document Concepts...")

    for i, doc_concept_name in enumerate(document_concepts_to_map):
        
        doc_concept_data = G_doc.nodes[doc_concept_name] 
        
        G_hybrid.nodes[doc_concept_name]['node_type'] = "DocumentConcept"
        
        print(f"Mapping Document Concept {i+1}/{len(document_concepts_to_map)}: '{doc_concept_name}'")
        
        mapping_result = map_concept_to_bizbok(doc_concept_name, doc_concept_data, client)
        
        status = mapping_result.get("status")
        ref_concept = mapping_result.get("reference_concept", "N/A")
        reason = mapping_result.get("mapping_reason", "Mapping successful.")
        
        is_valid_ref_concept = ref_concept in G_ref.nodes

        if status in ["Match", "Adaptive"] and is_valid_ref_concept:
            
            relationship_type = "IS_ALIGNED_WITH" if status == "Match" else "ADAPTED_FROM"
            
            if status == "Adaptive":
                G_hybrid.nodes[doc_concept_name]['node_type'] = "AdaptiveConcept"

            # Add the semantic link (Triangulation Edge)
            G_hybrid.add_edge(
                doc_concept_name, 
                ref_concept, 
                relationship=relationship_type, 
                mapping_justification=reason,
                mapping_status=status
            )
            print(f"  -> {status}: Linked to '{ref_concept}' via {relationship_type}")

        elif status == "Unmapped" or not is_valid_ref_concept:
            
            G_hybrid.nodes[doc_concept_name]['node_type'] = "UnmappedConcept"
            print(f"  -> Unmapped: No clear BIZBOK alignment found or invalid reference returned.")

        else:
            print(f"  -> API/Invalid Map: Status {status} not processed correctly.")

        # --- RATE LIMITER INJECTION ---
        # Introduce delay to prevent hitting the quota limit again
        print(f"  [RATE LIMITER] Pausing for {RATE_LIMIT_DELAY} seconds...")
        time.sleep(RATE_LIMIT_DELAY) 
        # --- END RATE LIMITER ---

    # --- Save the final Hybrid Graph ---
    try:
        output_dir = os.path.join(PROJECT_ROOT, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        nx.write_gml(G_hybrid, OUTPUT_GRAPH_FILE)
        print(f"\n[SUCCESS] Module 4 successfully completed: Semantic Triangulation achieved!")
        print(f"Hybrid Graph saved to: {OUTPUT_GRAPH_FILE}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save graph. Reason: {e}")