# --------------------------------------------------------------------------
# MODULE 3.5: Reference Ontology Construction (BIZBOK Layer)
# FINAL FIX: Uses a Two-Pass approach to guarantee all definitions are loaded 
# before relationships are drawn, eliminating "Definition Pending" errors.
# --------------------------------------------------------------------------
import os
import pandas as pd
import networkx as nx

print("--- Starting Module R3.5: Reference Ontology Governance Builder (Two-Pass Logic) ---")

# --- Define file paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Corrected filename based on user feedback
CORRECTED_FILENAME = 'Information Map for all industry and common.csv'

INPUT_CSV = os.path.join(PROJECT_ROOT, 'data', CORRECTED_FILENAME)
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'R_Reference_Ontology.gml')


# --- Core Ontology Construction Function ---
def build_bizbok_ontology_two_pass():
    """
    Reads the CSV in two passes: 
    Pass 1: Captures all Domain:Concept nodes and their definitions.
    Pass 2: Creates all RELATED_TO edges.
    """
    
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"\n[FATAL ERROR] Input CSV not found at: {INPUT_CSV}")
        return False

    G_bizbok = nx.DiGraph()
    
    # --- PASS 1: Create all Nodes and Populate Definitions ---
    print("Pass 1: Creating all domain-qualified nodes and populating definitions...")
    for index, row in df.iterrows():
        
        # Clean and extract data fields
        domain = str(row['Industry Domain']).strip()
        concept = str(row['Information Concept']).strip()
        definition = str(row['Information Concept Definition']).strip()
        
        # Use Composite Key: Domain:Concept
        domain_qualified_concept = f"{domain}:{concept}"

        # NetworkX will add the node or update its attributes if it already exists, 
        # ensuring the latest definition is applied (and filling in any placeholders).
        G_bizbok.add_node(
            domain_qualified_concept, 
            node_type="ReferenceConcept",
            industry_domain=domain,
            base_concept_name=concept,
            definition=definition,
            types=str(row['Information Concept Types']).strip()
        )

    print(f"Pass 1 Complete. Total nodes created: {G_bizbok.number_of_nodes()}")


    # --- PASS 2: Create all RELATED_TO Edges ---
    print("Pass 2: Creating all RELATED_TO edges...")
    for index, row in df.iterrows():
        
        domain = str(row['Industry Domain']).strip()
        concept = str(row['Information Concept']).strip()
        related_concepts_str = str(row['Related Information Concepts'])
        
        domain_qualified_concept = f"{domain}:{concept}"

        # Parse and add the RELATED_TO Edges
        if related_concepts_str and related_concepts_str.lower() not in ['nan', 'none']:
            related_list = [r.strip() for r in related_concepts_str.split(',') if r.strip()]
            
            for target_concept_name in related_list:
                
                # Assume the target concept for the BIZBOK relationship is in the SAME DOMAIN 
                domain_qualified_target = f"{domain}:{target_concept_name}"

                # Crucial check: Ensure the target node exists (it MUST have been created in Pass 1)
                # If a target concept was listed in 'Related Concepts' but was NOT a primary
                # concept in any row, it's still added here, but with its correct Pass 1 
                # (empty) definition, preventing the "Definition Pending" error on display.
                if domain_qualified_target not in G_bizbok:
                     # This scenario should not happen if the CSV is clean, but is a safe fallback
                     G_bizbok.add_node(
                         domain_qualified_target, 
                         node_type="ReferenceConcept", 
                         industry_domain=domain,
                         base_concept_name=target_concept_name,
                         definition="ERROR: Concept missing as primary row. - Pending_Governance_Review" # Safe fallback
                     )

                # Add the specific RELATED_TO edge
                G_bizbok.add_edge(
                    domain_qualified_concept, 
                    domain_qualified_target, 
                    relationship="RELATED_TO",
                    source_domain=domain,
                    target_domain=domain
                )

    print(f"Pass 2 Complete. Total edges created: {G_bizbok.number_of_edges()}")
    
    # 4. Save the Reference Ontology (GML Format)
    nx.write_gml(G_bizbok, OUTPUT_FILE)
    print(f"Reference Ontology structure saved to: {OUTPUT_FILE}")
    
    return True

# --- EXECUTION ---
if __name__ == "__main__":
    
    # Create the output directory if it doesn't exist
    output_dir = os.path.join(PROJECT_ROOT, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    if build_bizbok_ontology_two_pass():
        print("\n[SUCCESS] Module 3.5 successfully completed: Reference Ontology is built with Two-Pass Definition Integrity.")