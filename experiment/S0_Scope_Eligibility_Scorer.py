#!/usr/bin/env python3
"""
S0_Scope_Eligibility_Scorer.py  (v2 — proposal-grounded lexicon)
================================================================
Pre-flight scope-eligibility scorer for the GovRAG DSR artifact.

WHAT IT DOES
------------
For each RGB-shape record, computes TWO independent measurements:

  1. SUITABILITY SCORE (0-100) -- question-shape eligibility.
     Does the question's logical form match the architecture's
     predicate-bounded relational entity-output shape?
     Verdict: IN-SCOPE / BORDERLINE / OUT-OF-SCOPE.

  2. CDEII RICHNESS (0-100%) -- content alignment with Cross-Domain
     Enterprise Information Integration. Measured as the percentage
     of BIZBOK Common (cross-industry) Information Concepts that the
     record's content lexically touches. Lexicon is the same
     Information Map (CSV) consumed by R3.5/R4 -- single source of
     truth across the architecture.

Together the two axes characterise architectural fit:
    high Q-shape + high CDEII = architectural sweet spot
    high Q-shape + low  CDEII = relational but light enterprise content
    low  Q-shape + high CDEII = enterprise-rich but wrong question shape
    low  Q-shape + low  CDEII = out-of-scope on both axes

WHY IT EXISTS
-------------
Operationalises the proposal-grounded scope claim:
  "Predicate-bounded governance for relational entity-output queries
   in Cross-Domain Enterprise Information Integration."
Reviewers can re-run S0 against any RGB-shape dataset and verify
scope eligibility is principled, not post-hoc.

D00 INTEGRATION
---------------
Point D00's INPUT_FILE at the S0 output:
    INPUT_FILE = os.path.join(PROJECT_ROOT, "..", "data", "en_refine_scored.jsonl")
The runtime pipeline (D, M, Q, E) is unchanged -- S0 only constrains
upstream record selection.

USAGE
-----
    python experiment/S0_Scope_Eligibility_Scorer.py
    python experiment/S0_Scope_Eligibility_Scorer.py \\
        --input  ../data/en_refine.json \\
        --info-map ../data/Information_Map_for_all_industry_and_common.csv \\
        --output-dir ../data
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


# -------------------------------------------------------------------------
# 1. Question-shape lexicons (unchanged from v1)
# -------------------------------------------------------------------------
ENTITY_LEAD = [
    "who ", "which company", "which team", "which firm", "which organization",
    "which player", "which artist", "which actor", "which director",
    "which league", "which channel", "which network", "which institution",
    "which university", "what company", "which entity",
]

PREDICATES_MA = [
    "acquired", "acquires", "acquiring", "acquire",
    "bought", "buys", "buy", "purchase", "purchased", "purchases",
    "merged with", "merges with", "merge with", "merger with",
    "took over", "takeover",
    "owns", "owned by", "owner of",
    "subsidiary of", "parent of", "parent company",
    "spun off", "divested", "divestiture",
    "invested in", "invested by", "funded by", "backed by",
]
PREDICATES_PARTNERSHIP = [
    "partnered with", "partners with", "allied with", "joined with",
    "sponsors", "sponsored by",
]
PREDICATES_PERSONNEL = [
    "named ", "appointed", "hired", "fired", "succeeded", "replaced",
    "replaced by", "succeeded by", "was named", "is the new",
]
PREDICATES_AWARDS = [
    "awarded", "awarded to", "won the", "won best",
]
PREDICATES_OUTCOME = [
    "won ", "beat ", "beats ", "defeated", "lost to",
]
RELATIONAL_VERBS = (
    PREDICATES_MA + PREDICATES_PARTNERSHIP + PREDICATES_PERSONNEL +
    PREDICATES_AWARDS + PREDICATES_OUTCOME
)

SCALAR_LEADS = [
    "how much", "how many", "what price", "what is the price",
    "what is the cost", "what amount", "what rate", "what percent",
    "revenue", "worth ", "market cap",
]
TEMPORAL_LEADS = [
    "when ", "what year", "what date", "what time", "date of",
    "start date", "launch date",
]
ROLE_LEADS = [
    "what position", "what role", "what title", "what job", "what rank",
]
LOCATION_LEADS = [
    "where ", "what city", "what country", "what venue",
    "what location", "what stadium", "what arena",
]
NAMEOF_LEADS = [
    "what is the codename", "what is the name of", "what is the title",
    "what is called",
]


# -------------------------------------------------------------------------
# 2. BIZBOK Information Map -> CDEII lexicon
#
# Loads the Common (cross-industry) concepts from the Information Map CSV.
# For each concept, builds a regex from:
#   - the concept name (and simple morphological variations)
#   - the concept types (comma-separated subtypes)
# This is the SAME vocabulary R3.5/R4 use, so CDEII richness is
# architecturally consistent -- no separate "why this lexicon" defense.
# -------------------------------------------------------------------------
def _word_pattern(text: str) -> str:
    """Escape a phrase for regex with word boundaries; keep multi-word phrases."""
    text = text.strip()
    if not text:
        return ""
    return r"\b" + re.escape(text) + r"\w{0,3}\b"


def load_bizbok_lexicon(info_map_path: Path) -> Dict[str, List[re.Pattern]]:
    """
    Parse the Information Map CSV and return:
      { concept_name: [compiled regex hooks for that concept] }
    Restricted to industry domain == 'Common' (54 cross-industry concepts).
    """
    lexicon: Dict[str, List[re.Pattern]] = {}
    with open(info_map_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = (row.get("Industry Domain") or "").strip()
            concept = (row.get("Information Concept") or "").strip()
            if domain != "Common" or not concept:
                continue

            # Build hooks: concept name + each subtype
            subtypes_field = (row.get("Information Concept Types") or "").strip()
            hooks: List[str] = [concept]
            if subtypes_field:
                for sub in subtypes_field.split(","):
                    sub = sub.strip()
                    if sub and len(sub) >= 3:
                        hooks.append(sub)

            patterns: List[re.Pattern] = []
            for h in hooks:
                p = _word_pattern(h)
                if p:
                    try:
                        patterns.append(re.compile(p, re.IGNORECASE))
                    except re.error:
                        continue
            if patterns:
                lexicon[concept] = patterns
    return lexicon


# -------------------------------------------------------------------------
# 3. Helpers
# -------------------------------------------------------------------------
def first_answer_string(rec: Dict[str, Any]) -> str:
    a = rec.get("answer")
    if isinstance(a, list) and a:
        x = a[0]
        if isinstance(x, list) and x:
            return str(x[0])
        return str(x)
    return str(a or "")


def all_answer_variants(rec: Dict[str, Any]) -> List[str]:
    a = rec.get("answer")
    out: List[str] = []
    if isinstance(a, list):
        for x in a:
            if isinstance(x, list):
                out.extend(str(t) for t in x)
            else:
                out.append(str(x))
    elif a:
        out.append(str(a))
    return [s for s in out if s]


def has_token(text: str, tokens: List[str]) -> bool:
    t = text.lower()
    return any(tok in t for tok in tokens)


def find_predicate(query: str) -> str:
    ql = query.lower()
    for p in RELATIONAL_VERBS:
        if p in ql:
            return p.strip()
    return ""


def extract_object_entity(query: str, predicate: str) -> str:
    if not predicate:
        return ""
    m = re.search(rf"\b{re.escape(predicate)}\s+(.+?)(?:\?|$)", query, re.IGNORECASE)
    if m:
        target = m.group(1).strip().rstrip(".?!,")
        target = re.sub(r"^(a |an |the |in |for |to |from |of |by )+", "", target,
                        flags=re.IGNORECASE)
        return target
    return ""


def classify_answer_entity_type(answer: str) -> str:
    a = answer.strip()
    if not a:
        return "Unknown"
    if re.match(r"^\$|^[\d,]+(\.\d+)?$|^\d+\s*(percent|%|million|billion|thousand)",
                a, re.IGNORECASE):
        return "NumericValue"
    if re.match(r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4}|\d{1,2}/)",
                a, re.IGNORECASE):
        return "DateValue"
    if len(a.split()) <= 5 and re.match(r"^[A-Z]", a):
        if any(k in a.lower() for k in
               ["inc", "corp", "company", "group", "ltd", "llc", "co.",
                "university", "tech", "studios"]):
            return "Organization"
        return "ProperNoun"
    if any(w in a.lower() for w in
           ["coordinator", "coach", "director", "officer", "president",
            "manager", "ceo", "cto", "cfo"]):
        return "RoleOrTitle"
    return "ProperNoun" if re.match(r"^[A-Z]", a) else "Other"


# -------------------------------------------------------------------------
# 4. Use-case content domain tagger (precedence-ordered)
# -------------------------------------------------------------------------
def tag_content_domain(query: str, answer: str) -> Tuple[str, str]:
    """Returns (content_domain, bizbok_capability)."""
    ql = query.lower()
    if has_token(ql, PREDICATES_MA):
        return ("M&A", "Mergers and Acquisitions Management")
    if any(k in ql for k in
           ["beneficial owner", "ultimate parent", "regulator",
            "compliance", "sanctioned", "licens"]):
        return ("KYC-or-Regulatory", "Compliance and Regulatory Management")
    if has_token(ql, PREDICATES_PERSONNEL):
        return ("Org-Personnel", "Human Capital Management")
    if any(k in ql for k in
           ["election", "presidential", "senate", "primary", "midterm"]):
        return ("Politics", "Public-Sector Governance")
    if "won" in ql and any(k in ql for k in
           ["award", "prize", "trophy", "best ", "academy", "grammy",
            "nobel", "biletnikoff"]):
        return ("Awards-Recognition", "Brand and Recognition Management")
    if any(p in ql for p in PREDICATES_OUTCOME) and any(k in ql for k in
           ["bowl", "cup", "tournament", "open", "championship", "olympics",
            "grand prix", "masters", "finals", "wimbledon", "world cup"]):
        return ("Sports-Organizational", "Sports / Event Management")
    if has_token(ql, PREDICATES_PARTNERSHIP):
        return ("Partnership", "Partner Management")
    return ("Other-Relational", "General Enterprise Information Integration")


# -------------------------------------------------------------------------
# 5. Scoring engine
# -------------------------------------------------------------------------
WEIGHTS = {
    "entity_lead":          30,
    "relational_predicate": 30,
    "entity_answer":        20,
    "neg_clean":            10,
    "scalar_lead":         -40,
    "temporal_lead":       -40,
    "role_lead":           -40,
    "location_lead":       -30,
    "nameof_lead":         -20,
    "numeric_or_date_ans": -20,
}
THRESHOLD_IN_SCOPE   = 70
THRESHOLD_BORDERLINE = 40


def compute_cdeii(rec: Dict[str, Any],
                  bizbok_lexicon: Dict[str, List[re.Pattern]]) -> Tuple[float, List[str]]:
    """
    Return (cdeii_pct, sorted list of BIZBOK Common concepts touched).
    Scans query + answer + positive passages.
    """
    full_text = " ".join([
        rec.get("query") or "",
        " ".join(str(a) for ans in (rec.get("answer") or [])
                 for a in (ans if isinstance(ans, list) else [ans])),
        " ".join(rec.get("positive") or []),
    ])
    touched: List[str] = []
    for concept, patterns in bizbok_lexicon.items():
        for p in patterns:
            if p.search(full_text):
                touched.append(concept)
                break
    pct = round(len(touched) * 100 / max(1, len(bizbok_lexicon)), 1)
    return pct, sorted(touched)


def compute_score(rec: Dict[str, Any],
                  bizbok_lexicon: Dict[str, List[re.Pattern]]) -> Dict[str, Any]:
    query = rec.get("query") or ""
    ql = query.lower().strip()
    answer = first_answer_string(rec)

    breakdown: Dict[str, int] = {}
    is_entity_lead = has_token(ql, ENTITY_LEAD)
    if is_entity_lead:
        breakdown["entity_lead"] = WEIGHTS["entity_lead"]

    predicate = find_predicate(query)
    if predicate:
        breakdown["relational_predicate"] = WEIGHTS["relational_predicate"]

    answer_type = classify_answer_entity_type(answer)
    if answer_type in ("Organization", "ProperNoun") and 1 <= len(answer) <= 80:
        breakdown["entity_answer"] = WEIGHTS["entity_answer"]

    neg_text = " ".join(rec.get("negative", []) or [])
    answers = all_answer_variants(rec)
    ans_in_neg = sum(neg_text.lower().count(a.lower())
                     for a in answers if len(a) >= 3)
    if ans_in_neg == 0:
        breakdown["neg_clean"] = WEIGHTS["neg_clean"]

    if has_token(ql, SCALAR_LEADS):     breakdown["scalar_lead"]   = WEIGHTS["scalar_lead"]
    if has_token(ql, TEMPORAL_LEADS):   breakdown["temporal_lead"] = WEIGHTS["temporal_lead"]
    if has_token(ql, ROLE_LEADS):       breakdown["role_lead"]     = WEIGHTS["role_lead"]
    if has_token(ql, LOCATION_LEADS):   breakdown["location_lead"] = WEIGHTS["location_lead"]
    if has_token(ql, NAMEOF_LEADS):     breakdown["nameof_lead"]   = WEIGHTS["nameof_lead"]
    if answer_type in ("NumericValue", "DateValue", "RoleOrTitle"):
        breakdown["numeric_or_date_ans"] = WEIGHTS["numeric_or_date_ans"]

    score = max(0, min(100, sum(breakdown.values())))

    if score >= THRESHOLD_IN_SCOPE:    verdict = "IN-SCOPE"
    elif score >= THRESHOLD_BORDERLINE: verdict = "BORDERLINE"
    else:                               verdict = "OUT-OF-SCOPE"

    object_entity = extract_object_entity(query, predicate) if predicate else ""
    content_domain, bizbok_capability = tag_content_domain(query, answer)

    cdeii_pct, concepts_touched = compute_cdeii(rec, bizbok_lexicon)

    if has_token(ql, SCALAR_LEADS):    qshape = "scalar-attribute"
    elif has_token(ql, TEMPORAL_LEADS): qshape = "temporal-attribute"
    elif has_token(ql, ROLE_LEADS):     qshape = "role-attribute"
    elif has_token(ql, LOCATION_LEADS): qshape = "location-attribute"
    elif has_token(ql, NAMEOF_LEADS):   qshape = "name-of-thing"
    elif is_entity_lead and predicate:  qshape = "entity-lead-relational"
    elif is_entity_lead:                qshape = "entity-attribute"
    elif predicate:                     qshape = "relational-non-entity"
    else:                               qshape = "other"

    return {
        "score":                  score,
        "verdict":                verdict,
        "cdeii_pct":              cdeii_pct,
        "bizbok_concepts_touched": concepts_touched,
        "predicate":              predicate,
        "object_entity":          object_entity,
        "answer_entity_type":     answer_type,
        "content_domain":         content_domain,
        "bizbok_capability":      bizbok_capability,
        "question_shape":         qshape,
        "neg_contamination":      ans_in_neg,
        "score_breakdown":        breakdown,
    }


# -------------------------------------------------------------------------
# 6. I/O
# -------------------------------------------------------------------------
def load_records(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(2); f.seek(0)
        if first.startswith("["):
            records = json.load(f)
        else:
            for line in f:
                line = line.strip()
                if not line: continue
                try: records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[WARN] Skipping malformed line: {e}", file=sys.stderr)
    return records


def write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(records: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "id", "score", "verdict", "cdeii_pct",
        "content_domain", "predicate", "object_entity", "answer_entity_type",
        "bizbok_capability", "question_shape", "neg_contamination",
        "query", "answer",
        "bizbok_concepts_touched", "score_breakdown",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in records:
            s0 = r["_s0"]
            w.writerow({
                "id":                  r.get("id"),
                "score":               s0["score"],
                "verdict":             s0["verdict"],
                "cdeii_pct":           s0["cdeii_pct"],
                "content_domain":      s0["content_domain"],
                "predicate":           s0["predicate"],
                "object_entity":       s0["object_entity"],
                "answer_entity_type":  s0["answer_entity_type"],
                "bizbok_capability":   s0["bizbok_capability"],
                "question_shape":      s0["question_shape"],
                "neg_contamination":   s0["neg_contamination"],
                "query":               r.get("query", ""),
                "answer":              first_answer_string(r),
                "bizbok_concepts_touched": "; ".join(s0["bizbok_concepts_touched"]),
                "score_breakdown":     "; ".join(f"{k}={v:+d}"
                                                 for k, v in s0["score_breakdown"].items()),
            })


# -------------------------------------------------------------------------
# 7. Main
# -------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="GovRAG S0 Scope Eligibility Scorer (v2)")
    here = Path(__file__).resolve().parent
    default_input    = (here / ".." / "data" / "en_refine.json").resolve()
    default_outdir   = (here / ".." / "data").resolve()
    default_info_map = (here / ".." / "data" / "Information Map for all industry and common.csv").resolve()

    ap.add_argument("--input",      type=Path, default=default_input)
    ap.add_argument("--info-map",   type=Path, default=default_info_map,
                    help="BIZBOK Information Map CSV (Common-domain concepts used as CDEII lexicon)")
    ap.add_argument("--output-dir", type=Path, default=default_outdir)
    args = ap.parse_args()

    if not args.input.exists():
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr); sys.exit(1)
    if not args.info_map.exists():
        print(f"[ERROR] Information Map not found: {args.info_map}", file=sys.stderr); sys.exit(1)

    print("=" * 72)
    print("S0 Scope Eligibility Scorer (v2 -- proposal-grounded BIZBOK lexicon)")
    print("=" * 72)
    print(f"  Input:        {args.input}")
    print(f"  Info Map:     {args.info_map}")
    print(f"  Output:       {args.output_dir}")
    print()

    bizbok = load_bizbok_lexicon(args.info_map)
    print(f"  Loaded {len(bizbok)} BIZBOK Common Information Concepts as CDEII lexicon.")
    print(f"  (Same lexicon consumed by R3.5/R4 -- single source of truth.)")
    print()

    records = load_records(args.input)
    print(f"  Loaded {len(records)} records")

    scored: List[Dict[str, Any]] = []
    for rec in records:
        s0 = compute_score(rec, bizbok)
        rec_out = dict(rec); rec_out["_s0"] = s0
        scored.append(rec_out)

    verdict_counts = Counter(r["_s0"]["verdict"] for r in scored)
    domain_counts = Counter(r["_s0"]["content_domain"]
                            for r in scored if r["_s0"]["verdict"] == "IN-SCOPE")

    print()
    print("  Verdict distribution:")
    for v, n in verdict_counts.most_common(): print(f"    {n:>4}  {v}")
    print()
    print("  IN-SCOPE records by content domain:")
    for d, n in domain_counts.most_common():  print(f"    {n:>4}  {d}")
    print()

    cdeii_vals = [r["_s0"]["cdeii_pct"] for r in scored]
    import statistics
    print(f"  CDEII richness across all 300 records: "
          f"mean={statistics.mean(cdeii_vals):.1f}%, median={statistics.median(cdeii_vals):.1f}%, "
          f"min={min(cdeii_vals):.0f}%, max={max(cdeii_vals):.0f}%")
    in_scope_cdeii = [r["_s0"]["cdeii_pct"] for r in scored
                      if r["_s0"]["verdict"] == "IN-SCOPE"]
    if in_scope_cdeii:
        print(f"  CDEII richness for IN-SCOPE only:      "
              f"mean={statistics.mean(in_scope_cdeii):.1f}%, median={statistics.median(in_scope_cdeii):.1f}%")
    print()

    print("  Calibration on known records:")
    print(f"    {'rec':<8}  {'score':>5}  {'cdeii':>6}  {'verdict':<13}  {'domain':<24}  query")
    print("    " + "-" * 110)
    for rid in [5, 12, 3, 48, 254, 104, 115, 175, 72, 0, 1, 13]:
        m = next((r for r in scored if r.get("id") == rid), None)
        if m:
            s0 = m["_s0"]
            print(f"    rgb_{rid:<4}  {s0['score']:>5}  {s0['cdeii_pct']:>5}%  "
                  f"{s0['verdict']:<13}  {s0['content_domain']:<24}  "
                  f"{(m.get('query') or '')[:60]}")
    print()

    out_scored   = args.output_dir / "en_refine_scored.jsonl"
    out_in_scope = args.output_dir / "en_refine_in_scope.jsonl"
    out_csv      = args.output_dir / "S0_RGB_Scope_Eligibility.csv"

    write_jsonl(scored, out_scored)
    write_jsonl([r for r in scored if r["_s0"]["verdict"] == "IN-SCOPE"], out_in_scope)
    write_csv(scored, out_csv)

    print(f"  [OK] Wrote {out_scored.name} ({len(scored)} records)")
    print(f"  [OK] Wrote {out_in_scope.name} ({verdict_counts['IN-SCOPE']} records)")
    print(f"  [OK] Wrote {out_csv.name}")
    print()
    print("=" * 72)
    print("Next: point D00 INPUT_FILE at en_refine_scored.jsonl")
    print("=" * 72)


if __name__ == "__main__":
    main()
