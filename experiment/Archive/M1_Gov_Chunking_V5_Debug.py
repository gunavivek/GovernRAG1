# --------------------------------------------------------------------------
# MODULE 1: M1_Gov_Chunking_V5_Debug.py
# ARCHITECTURE: Poly-Ontological Coverage + Negative Constraint Governance
# DISSERTATION VALUE: Proves Structural Relativity (Focus Mode)
# PURPOSE: DEBUG / STABILIZATION VERSION FOR M1
# --------------------------------------------------------------------------

import pandas as pd
import json
import os
import sys
import time
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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MANIFEST = os.path.join(PROJECT_ROOT, "output", "D5_Extraction_Manifest.jsonl")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "output", "M1_Governed_Chunks.csv")

# --- CONFIGURATION ---
PHYSICAL_WINDOW_CHARS = 12000
MAX_TRANSPORT_ATTEMPTS = 3


def resolution_based_partitioner(
    text_segment: str,
    domain_profile: dict,
    z_score: float,
    record_id: str = "",
    slice_idx: int = -1,
    total_slices: int = -1,
) -> list:
    """
    Partitions text using 'Focus Mode'.
    Applies Negative Constraints to prevent splitting irrelevant text.
    Debug version: logs request context and retries transient transport failures.
    """
    domain_name = domain_profile["domain"]
    rules = domain_profile["rules"]

    # --- GOVERNANCE MAPPING ---
    target_depth = rules.get("search_exit_depth", 4)
    predicates = rules.get("relational_predicates", [])
    disambiguation = rules.get("disambiguation_keys", {})

    # --- V5.1 EXCLUSIONARY LOGIC ---
    if target_depth >= 4:
        res_mode = "ATOMIC FOCUS (Exclusionary)"
        instruction = f"""
        1. SCAN the text for concepts strictly related to '{domain_name}' and these actions: {predicates}.
        2. POSITIVE CONSTRAINT (Relevant Text): If a sentence IS related to {domain_name}, SPLIT IT aggressively. Isolate specific facts.
        3. NEGATIVE CONSTRAINT (Irrelevant Text): If a section is NOT related to {domain_name}, DO NOT SPLIT IT. Merge it into a single summary block.
        """
    elif target_depth == 3:
        res_mode = "STANDARD RESOLUTION"
        instruction = (
            f"Split naturally. Group related sentences, but split when the sub-topic "
            f"shifts based on {predicates}."
        )
    else:
        res_mode = "THEMATIC RESOLUTION"
        instruction = "Group text broadly. Only split when the major theme changes completely."

    discovery_mode = "EXPLORATORY" if z_score >= 2.5 else "STRICT"

    prompt = f"""
    You are a Domain-Aware Text Chunking Architect working within the {domain_name} business domain.

    CONFIGURATION:
    - MODE: {discovery_mode}
    - STRATEGY: {res_mode}

    TASK: Partition the text into 'Knowledge Pockets' using ONLY the lens of {domain_name}.

    CRITICAL GOVERNANCE LAWS:
    {instruction}

    VOCABULARY DEFENSE:
    Use these definitions to resolve ambiguity: {disambiguation}.

    OUTPUT FORMAT:
    - Return a valid JSON Array of strings.
    - Content must be RAW text from the source (no summarizing, just grouping).

    <TEXT>
    {text_segment}
    </TEXT>
    """

    try:
        prompt_len = len(prompt)
        text_len = len(text_segment)

        print(
            f"[M1 DEBUG] record={record_id} domain={domain_name} "
            f"slice={slice_idx + 1}/{total_slices} text_len={text_len} "
            f"prompt_len={prompt_len} model={LLM_MODEL} z={z_score}"
        )

        last_error = None
        response = None

        for attempt in range(1, MAX_TRANSPORT_ATTEMPTS + 1):
            try:
                print(f"[M1 DEBUG] transport_attempt={attempt}")

                response = client.models.generate_content(
                    model=LLM_MODEL,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0,
                    ),
                )
                break

            except Exception as inner_e:
                last_error = inner_e
                print(
                    f"[M1 DEBUG] transport_attempt={attempt} failed "
                    f"| record={record_id} | domain={domain_name} "
                    f"| slice={slice_idx + 1}/{total_slices} | error={inner_e}"
                )

                if attempt == MAX_TRANSPORT_ATTEMPTS:
                    raise

                time.sleep(2 * attempt)

        if response is None:
            raise RuntimeError(
                f"No response returned after {MAX_TRANSPORT_ATTEMPTS} attempts."
            ) from last_error

        result = json.loads(response.text)

        if not isinstance(result, list):
            raise ValueError("Expected JSON array of chunk strings.")

        clean_chunks = [str(x).strip() for x in result if str(x).strip()]

        if not clean_chunks:
            raise ValueError(f"Empty chunk list returned for {domain_name}.")

        return clean_chunks

    except Exception as e:
        raise RuntimeError(
            f"Chunking failed | record={record_id} | domain={domain_name} "
            f"| slice={slice_idx + 1}/{total_slices} | text_len={len(text_segment)} "
            f"| prompt_len={len(prompt)} | model={LLM_MODEL} | error={e}"
        ) from e


def run_m1_v5_1_focus_mode():
    if not os.path.exists(INPUT_MANIFEST):
        sys.exit("Manifest missing.")

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    final_chunks = []
    print("M1_V5.1: Initializing Poly-Ontological Ingestion (Focus Mode)...")

    with open(INPUT_MANIFEST, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            contract = json.loads(line)
            rid = contract["record_id"]
            z_score = contract.get("z_score", 0.0)

            # 1. Forensic Stripping
            text = contract["source_text"]
            evidence = text.split(" | Document: ", 1)[1] if " | Document: " in text else text

            # 2. Total Coverage Loop: Iterate ALL domains
            all_domains = sorted(
                contract["governance_profile"],
                key=lambda x: x["affinity_weight"],
                reverse=True,
            )

            for view in all_domains:
                domain_name = view["domain"]

                # 3. Physical Safety Slicing
                text_len = len(evidence)
                physical_slices = [
                    evidence[k:k + PHYSICAL_WINDOW_CHARS]
                    for k in range(0, text_len, PHYSICAL_WINDOW_CHARS)
                ]

                print(
                    f"[M1 DEBUG] record={rid} domain={domain_name} "
                    f"total_text_len={text_len} physical_slices={len(physical_slices)}"
                )

                view_chunks = []
                for s_idx, p_slice in enumerate(physical_slices):
                    c = resolution_based_partitioner(
                        p_slice,
                        view,
                        z_score,
                        record_id=rid,
                        slice_idx=s_idx,
                        total_slices=len(physical_slices),
                    )
                    view_chunks.extend(c)

                # 4. Stapling & ID Generation
                for j, pocket_text in enumerate(view_chunks):
                    safe_dom = domain_name.upper().replace(" ", "_").replace("&", "AND")[:15]

                    final_chunks.append(
                        {
                            "record_id": rid,
                            "chunk_id": f"CHNK_{rid[-4:]}_{safe_dom}_{j:02d}",
                            "viewpoint_domain": domain_name,
                            "chunk_text": pocket_text,
                            "wa_score": view["affinity_weight"],
                            "granularity_level": view["rules"].get("search_exit_depth", 4),
                            "z_score": z_score,
                            "predicates": json.dumps(
                                view["rules"].get("relational_predicates", [])
                            ),
                            "disambiguation": json.dumps(
                                view["rules"].get("disambiguation_keys", {})
                            ),
                        }
                    )

                print(
                    f"Record {rid} | View: {domain_name} "
                    f"(Wa:{view['affinity_weight']:.4f}) | Chunks: {len(view_chunks)}"
                )

    pd.DataFrame(final_chunks).to_csv(OUTPUT_FILE, index=False)
    print(f"\nM1_V5.1 COMPLETE. Focus Mode Artifact: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_m1_v5_1_focus_mode()