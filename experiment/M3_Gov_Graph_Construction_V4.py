# --------------------------------------------------------------------------
# MODULE 3: M3_Gov_Graph_Construction_V4.py
# ARCHITECTURE: Poly-Ontological Graph Construction + In-Memory Resolution
# ENHANCEMENT: Adds "He/It" Resolution & Normalization to V3 Logic
# --------------------------------------------------------------------------
import json
import networkx as nx
import os
import pandas as pd
import sys

# --- 0. Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
INPUT_FILE = os.path.join(PROJECT_ROOT, 'output', 'M2_Extracted_Triples.json')
OUTPUT_GRAPHML = os.path.join(PROJECT_ROOT, 'output', 'M3_Knowledge_Graph.graphml')
OUTPUT_STATS = os.path.join(PROJECT_ROOT, 'output', 'M3_Graph_Stats.csv')

# --- 1. Resolution Logic (The V4 Enhancement) ---
def resolve_and_normalize(triples):
    """
    GOVERNANCE LOGIC: Resolves pronouns and normalizes text before graph build.
    """
    print(f"-> Starting Resolution on {len(triples)} raw triples...")
    
    # 1. Sort by Narrative Order (Record -> Chunk) for correct pronoun tracking
    triples.sort(key=lambda x: (x.get('record_id', ''), x.get('chunk_id', '')))

    resolved_triples = []
    
    # Context Memory
    current_record = None
    last_person = None
    last_org = None
    last_concept = None

    # Maps
    person_pronouns = {"he", "she", "him", "her", "his"}
    org_pronouns = {"it", "they", "them", "its", "their", "the group", "the band", "the series", "the film"}
    
    stats = {"pronouns_fixed": 0, "terms_normalized": 0}

    for t in triples:
        # Reset context on new record
        rec_id = t.get('record_id')
        if rec_id != current_record:
            current_record = rec_id
            last_person, last_org, last_concept = None, None, None

        subj = t['subject'].strip()
        pred = t['predicate'].strip()
        obj = t['object'].strip()
        domain = t.get('domain', 'Unknown')

        # --- A. Pronoun Resolution ---
        clean_subj = subj
        lower_subj = subj.lower()

        if lower_subj in person_pronouns and last_person:
            clean_subj = last_person
            stats['pronouns_fixed'] += 1
        elif lower_subj in org_pronouns:
            if last_org: 
                clean_subj = last_org
                stats['pronouns_fixed'] += 1
            elif last_concept:
                clean_subj = last_concept
                stats['pronouns_fixed'] += 1

        # --- B. Context Update ---
        # If Subject is a Proper Noun (Capitalized), update memory for next turn
        if clean_subj and clean_subj[0].isupper() and clean_subj.lower() not in person_pronouns | org_pronouns:
            # Heuristics
            if "People" in domain or "Bio" in domain or any(x in pred.lower() for x in ["born", "lived", "wrote", "directed"]):
                last_person = clean_subj
            elif "Music" in domain or "Company" in domain or "Team" in domain or "Club" in domain:
                last_org = clean_subj
            else:
                last_concept = clean_subj
                if "Arts" in domain or "Sport" in domain: last_person = clean_subj

        # --- C. Normalization (Tax/Taxes) ---
        def normalize(term):
            term_clean = term.strip()
            lower = term_clean.lower()
            # Governance Rules
            if lower in ["income taxes", "income tax"]: return "Income Tax"
            if lower.endswith("taxes") and "income" not in lower: return term_clean[:-2] # taxes->tax
            return term_clean

        final_subj = normalize(clean_subj)
        final_obj = normalize(obj)
        
        if final_subj != clean_subj or final_obj != obj:
            stats['terms_normalized'] += 1

        # Update Triple
        t['subject'] = final_subj
        t['object'] = final_obj
        resolved_triples.append(t)

    print(f"   [Resolution Stats] Pronouns Fixed: {stats['pronouns_fixed']} | Normalized: {stats['terms_normalized']}")
    return resolved_triples

# --- 2. Main Execution ---
def build_governed_graph():
    print("--- Starting M3_V4.0: Poly-Ontological Graph Construction ---")

    if not os.path.exists(INPUT_FILE):
        sys.exit(f"[CRITICAL] Input file missing: {INPUT_FILE}")

    if os.path.exists(OUTPUT_GRAPHML):
        os.remove(OUTPUT_GRAPHML)
    if os.path.exists(OUTPUT_STATS):
        os.remove(OUTPUT_STATS)

    # 1. Load Extracted Triples
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_triples = json.load(f)

    # 2. Apply V4 Resolution (Enhancement)
    triples = resolve_and_normalize(raw_triples)

    # 3. Initialize Multi-Directed Graph (Retained from V3)
    G = nx.MultiDiGraph()

    print(f"-> Ingesting {len(triples)} Resolved Triples...")

    edge_count = 0
    skipped_count = 0
    domain_counter = {}

    # 4. Graph Assembly Loop (Retained from V3)
    for idx, item in enumerate(triples):
        subj = item.get("subject", "")
        obj = item.get("object", "")
        pred = item.get("predicate", "")
        domain = item.get("domain", "Unknown")
        
        # Validation
        if not subj or not obj or not pred:
            skipped_count += 1
            continue

        # Add Nodes with V3 Attributes
        if subj not in G:
            G.add_node(subj, label=subj, type="Entity")
        if obj not in G:
            G.add_node(obj, label=obj, type="Entity")

        # Track Domain Stats
        domain_counter[domain] = domain_counter.get(domain, 0) + 1

        # Add Weighted Edge with V3 Keys
        G.add_edge(
            subj, 
            obj, 
            key=f"{domain}_{pred}_{item.get('record_id', 'N/A')}_{item.get('chunk_id', 'N/A')}_{idx:05d}",
            predicate=pred,
            weight=float(item.get("weight", 0.1)), 
            domain=domain,
            provenance=item.get("extraction_mode", "STRICT"),
            record_id=item.get("record_id", "N/A"),
            chunk_id=item.get("chunk_id", "N/A")
        )
        edge_count += 1

    # 5. Topology Analytics (Retained from V3)
    print("\n" + "="*40)
    print("M3_V4 GRAPH TOPOLOGY METRICS")
    print("="*40)
    print(f"Total Unique Nodes: {G.number_of_nodes()}")
    print(f"Total Weighted Edges: {G.number_of_edges()}")
    
    # Identify Hubs
    degree_dict = dict(G.degree())
    sorted_degree = sorted(degree_dict.items(), key=lambda item: item[1], reverse=True)
    
    print("\n[TOP 5 AUTHORITY HUBS]")
    for entity, degree in sorted_degree[:5]:
        print(f"  > {entity}: {degree} connections")

    print("\n[DOMAIN DOMINANCE]")
    for dom, count in domain_counter.items():
        print(f"  > {dom}: {count} edges")

    # 6. Export (Retained from V3)
    # Stats to CSV
    stats_data = [{"Entity": k, "Degree": v} for k, v in sorted_degree]
    pd.DataFrame(stats_data).to_csv(OUTPUT_STATS, index=False)

    # GraphML
    nx.write_graphml(G, OUTPUT_GRAPHML)
    
    print("\n" + "="*40)
    print(f"[SUCCESS] Graph serialized to: {OUTPUT_GRAPHML}")
    print("M3_V4 Complete.")

if __name__ == "__main__":
    build_governed_graph()


#HOW TO VERIFY GRAPHML OUTPUT:
#python
#>>>
#import networkx as nx
#g = nx.read_graphml(r"C:\Users\gunav\OneDrive - UA Little Rock\PhD\3 Dissertation\conceptual_GraphRAG\output\M3_Knowledge_Graph.graphml")
#print("Nodes:", g.number_of_nodes())
#print("Edges:", g.number_of_edges())