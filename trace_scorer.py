#!/usr/bin/env python3
"""
trace_scorer.py -- interpret GovernRAG vs Naive from B2_Serve, stratified by answerability.

GOLD: joined from build_gold_map.py (RAGBench reference response + gold TRACe + adherence
label). NOTE gold is RAGBench's faithfulness-annotated reference (GPT-3.5), NOT human gold.
Therefore ANSWER-MATCH is computed ONLY on the adherent stratum (reference grounded);
faithfulness (TRACe Adherence, answered tuples) and abstention run across ALL strata.

Answerability = gold adherence_score: True -> answerable; False -> unsupported/unanswerable.

JUDGE INDEPENDENCE: judge != generation model. Gen = gemini-3.5-flash; default judge = gemini-2.5-flash.

USAGE
  python build_gold_map.py --source data/delucionqa_questions.jsonl
  python trace_scorer.py --results results/serve_results.jsonl --judge-model gemini-2.5-flash
  (--no-trace = correctness/abstention only, cheaper)
"""
import argparse, json, os, re, statistics as st
from pathlib import Path


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', (text or "").strip()) if s.strip()]


def strip_markers(text):
    return re.sub(r"\[(?:CHNK_[^\]]+|RESIDUAL_[^\]]+|CHNK_PRIMARY)\]", "", text or "")


def norm_q(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def is_refusal(answer, mode=""):
    a = (answer or "").lower()
    if str(mode).startswith("BLOCKED"):
        return True
    return ("governance boundary" in a or "evidence insufficient" in a
            or "response blocked" in a or a.strip() in ("", "not_found"))


# ---------- (1) correctness judge (E2 logic) ----------
CORRECT_PROMPT = """You are an academic evaluator grading an enterprise AI system.
Compare the System Answer to the Ground Truth.

Ground Truth: {gt}
System Answer: {ans}

RULES:
1. Citation markers like [CHNK_...], [RESIDUAL_...] are metadata, not content. Ignore them.
2. If the System Answer contains the factual information in the Ground Truth, output exactly: MATCH
3. If it is factually incorrect or hallucinates unsupported content, output exactly: NO_MATCH
4. If it explicitly refuses (e.g. 'insufficient evidence', 'blocked', 'boundary'), output exactly: SAFE_SILENCE
Output ONLY the single classification word."""


def correctness(gold, answer, mode, model, client, types):
    if is_refusal(answer, mode):
        return "SAFE_SILENCE"
    if not (answer or "").strip():
        return "NO_MATCH"
    prompt = CORRECT_PROMPT.format(gt=gold, ans=strip_markers(answer))
    try:
        r = client.models.generate_content(model=model, contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0))
        v = r.text.strip().upper()
        for tok in ("SAFE_SILENCE", "NO_MATCH", "MATCH"):
            if tok in v:
                return tok
        return "NO_MATCH"
    except Exception as e:
        return "ERROR:%s" % e


# ---------- (2) TRACe judge ----------
JUDGE_PROMPT = """You grade a RAG answer against its context, following RAGBench.
QUESTION: {q}

CONTEXT SENTENCES (keyed):
{ctx}

RESPONSE SENTENCES (keyed):
{resp}

Return ONLY JSON:
{{
 "relevant_ctx_keys": [keys of context sentences useful for answering the question],
 "utilized_ctx_keys": [keys of context sentences the response actually used],
 "response_support": {{ "<resp_key>": true|false }}
}}"""


def judge_tuple(question, context, response, model, client, types):
    ctx = sentences(context); resp = sentences(strip_markers(response))
    if not ctx:
        return None
    ctx_keyed = "\n".join("c%d: %s" % (i, s) for i, s in enumerate(ctx))
    resp_keyed = "\n".join("r%d: %s" % (i, s) for i, s in enumerate(resp)) or "r0: (empty)"
    prompt = JUDGE_PROMPT.format(q=question, ctx=ctx_keyed, resp=resp_keyed)
    try:
        r = client.models.generate_content(model=model, contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0))
        d = json.loads(re.sub(r'```json|```', '', r.text).strip())
        if isinstance(d, list):  # gemini-3.1-pro-preview sometimes wraps the object in a list
            d = next((x for x in d if isinstance(x, dict)), {})
        if not isinstance(d, dict):
            return None
    except Exception:
        return None
    n_ctx = len(ctx)
    rel = set(d.get("relevant_ctx_keys", [])); util = set(d.get("utilized_ctx_keys", []))
    support = d.get("response_support", {})
    return {"relevance": len(rel) / n_ctx, "utilization": len(util) / n_ctx,
            "completeness": (len(rel & util) / len(rel)) if rel else 0.0,
            "adherence": 1.0 if resp and all(bool(v) for v in support.values()) and len(support) >= len(resp) else (0.0 if resp else 1.0)}


def score_all(rows, judge_model, do_trace, gold_map):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    out = []
    for i, row in enumerate(rows):
        gov = row.get("governed", {}); nai = row.get("naive", {})
        q = row.get("question", "")
        ginfo = gold_map.get(norm_q(q)) if gold_map else None
        gold = ginfo["gold_response"] if ginfo else row.get("gold", "")
        rec = {"idx": row.get("idx"), "question": q, "gold": gold,
               "answerable": (ginfo.get("answerable") if ginfo else None),
               "gold_source": ("ragbench" if ginfo else "row")}
        rec["gov_refused"] = bool(gov.get("refused")) or is_refusal(gov.get("answer", ""), gov.get("mode", ""))
        rec["gov_verdict"] = correctness(gold, gov.get("answer", ""), gov.get("mode", ""), judge_model, client, types)
        rec["naive_verdict"] = correctness(gold, nai.get("answer", ""), nai.get("mode", ""), judge_model, client, types)
        if do_trace:
            if not rec["gov_refused"]:   # TRACe only on ANSWERED governed tuples
                rec["gov_trace"] = judge_tuple(q, gov.get("context", ""), gov.get("answer", ""), judge_model, client, types)
            rec["naive_trace"] = judge_tuple(q, nai.get("context", ""), nai.get("answer", ""), judge_model, client, types)
        out.append(rec)
        print("  scored %d/%d" % (i + 1, len(rows)))
    return out


def _pct(a, b):
    return "%d/%d (%.0f%%)" % (a, b, (100.0 * a / b) if b else 0.0)


def crosstab(scored):
    """Stratified by RAGBench answerability (gold adherence).
    ADHERENT: reference grounded -> answer-match valid (parity). NON-ADHERENT: reference is a
    hallucination -> correct behavior is ABSTAIN. Faithfulness/abstention across ALL strata."""
    adh = [r for r in scored if r.get("answerable") is True]
    non = [r for r in scored if r.get("answerable") is False]
    unk = [r for r in scored if r.get("answerable") is None]
    N = len(scored)

    def cnt(rows, pred):
        return sum(1 for r in rows if pred(r))

    g_match = cnt(adh, lambda r: r["gov_verdict"] == "MATCH")
    n_match = cnt(adh, lambda r: r["naive_verdict"] == "MATCH")
    g_ref_adh = cnt(adh, lambda r: r["gov_verdict"] == "SAFE_SILENCE")
    g_wrong_adh = cnt(adh, lambda r: r["gov_verdict"] == "NO_MATCH")
    g_abstain = cnt(non, lambda r: r["gov_verdict"] == "SAFE_SILENCE")
    n_assert = cnt(non, lambda r: r["naive_verdict"] != "SAFE_SILENCE")
    g_refuse_all = cnt(scored, lambda r: r["gov_verdict"] == "SAFE_SILENCE")
    g_wrong_all = cnt(scored, lambda r: r["gov_verdict"] == "NO_MATCH")

    print("\n" + "=" * 66)
    print("STRATIFIED SCORING (vs RAGBench reference)   N=%d  [adh=%d non-adh=%d unk=%d]"
          % (N, len(adh), len(non), len(unk)))
    print("=" * 66)
    print("ADHERENT stratum (answerable) -- answer-match VALID (parity axis):")
    print("  governed MATCH   : %s" % _pct(g_match, len(adh)))
    print("  naive    MATCH   : %s   <- H1 parity: governed ~ naive here" % _pct(n_match, len(adh)))
    print("  governed refused : %s   <- over-strict (recall loss to watch)" % _pct(g_ref_adh, len(adh)))
    print("  governed wrong   : %s   <- governance should keep ~0" % _pct(g_wrong_adh, len(adh)))
    print("-" * 66)
    print("NON-ADHERENT stratum (unsupported) -- correct = ABSTAIN (superiority axis):")
    print("  governed abstained (correct) : %s" % _pct(g_abstain, len(non)))
    print("  naive asserted (failed)      : %s   <- H3: naive hallucinates, governed refuses" % _pct(n_assert, len(non)))
    print("-" * 66)
    print("OVERALL: governed refusal rate %s | governed answered-but-wrong %s"
          % (_pct(g_refuse_all, N), _pct(g_wrong_all, N)))
    print("NOTE: answer-match NOT computed on non-adherent stratum (reference is a hallucination).")
    return {"N": N, "adherent": len(adh), "non_adherent": len(non), "unknown": len(unk),
            "adh_gov_match": g_match, "adh_naive_match": n_match, "adh_gov_refused": g_ref_adh,
            "adh_gov_wrong": g_wrong_adh, "nonadh_gov_abstain": g_abstain, "nonadh_naive_assert": n_assert,
            "overall_gov_refuse": g_refuse_all, "overall_gov_wrong": g_wrong_all}


def aggregate_trace(scored):
    metrics = ["relevance", "utilization", "completeness", "adherence"]
    gv = [r for r in scored if r.get("gov_trace")]
    nv = [r for r in scored if r.get("naive_trace")]
    print("\n" + "=" * 66)
    print("TRACe (mean; governed on ANSWERED tuples only) -- GovernRAG vs Naive")
    print("=" * 66)
    print("%-13s%10s%10s%8s" % ("metric", "governed", "naive", "delta"))
    agg = {}
    for m in metrics:
        g = st.mean([r["gov_trace"][m] for r in gv]) if gv else float("nan")
        n = st.mean([r["naive_trace"][m] for r in nv]) if nv else float("nan")
        agg[m] = {"governed": g, "naive": n, "delta": g - n}
        print("%-13s%10.3f%10.3f%+8.3f" % (m, g, n, g - n))
    print("governed answered N=%d ; naive N=%d" % (len(gv), len(nv)))
    print("Expectation: parity on relevance/utilization/completeness; governed >= naive on ADHERENCE.")
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/serve_results.jsonl")
    ap.add_argument("--judge-model", default="gemini-2.5-flash",
                    help="MUST differ from generation model (independence). Gen=gemini-3.5-flash.")
    ap.add_argument("--no-trace", action="store_true", help="skip TRACe; correctness/abstention only")
    ap.add_argument("--gold-map", default="results/gold_map.json",
                    help="RAGBench gold+answerability map from build_gold_map.py")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.results, encoding="utf-8") if l.strip()]
    gold_map = {}
    if os.path.exists(args.gold_map):
        gold_map = json.load(open(args.gold_map, encoding="utf-8"))
        matched = sum(1 for r in rows if norm_q(r.get("question", "")) in gold_map)
        print("[gold] %d gold entries; %d/%d results matched to RAGBench gold" % (len(gold_map), matched, len(rows)))
    else:
        print("[gold] WARNING: no gold map at %s -- falling back to row gold (may be empty!)" % args.gold_map)

    print("[trace] scoring %d questions | judge=%s | trace=%s" % (len(rows), args.judge_model, not args.no_trace))
    scored = score_all(rows, args.judge_model, do_trace=not args.no_trace, gold_map=gold_map)

    Path("results").mkdir(exist_ok=True)
    with (Path("results") / "trace_scores.jsonl").open("w", encoding="utf-8") as f:
        for r in scored:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = crosstab(scored)
    if not args.no_trace:
        summary["trace"] = aggregate_trace(scored)
    (Path("results") / "scoring_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n[trace] per-question -> results/trace_scores.jsonl ; summary -> results/scoring_summary.json")


if __name__ == "__main__":
    main()
