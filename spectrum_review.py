#!/usr/bin/env python3
"""
spectrum_review.py -- read-only viewer for the per-record spectrum results (N=20).

Default: a grid of every record x level with its correctness verdict + faithfulness,
plus the answerability label. Use --record <idx> to drill into one record (question,
gold, and each level's actual answer + verdict + adherence).

Dimensions shown:
  verdict  = answer vs RAGBench gold : MATCH / WRONG(NO_MATCH) / refuse(SAFE_SILENCE)
  adh      = faithfulness vs context : 1.0 grounded, 0.0 drifted, "-" if refused
  ans      = answerability stratum   : Y answerable / N unsupported

RUN from repo root:
  python spectrum_review.py
  python spectrum_review.py --record 530
"""
import argparse, json, os

LEVELS = ["G0", "G1", "G2", "G3", "G4"]
VMAP = {"MATCH": "MATCH ", "NO_MATCH": "WRONG ", "SAFE_SILENCE": "refuse"}


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []


def by_rid(rows):
    return {str(r.get("record_id")): r for r in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="results/spectrum_real_scores.jsonl")
    ap.add_argument("--serve", default="results/serve_results.jsonl")
    ap.add_argument("--gold-map", default="results/gold_map.json")
    ap.add_argument("--record", default=None, help="drill into one record by idx")
    args = ap.parse_args()

    scores = load_jsonl(args.scores)
    if not scores:
        raise SystemExit("[FATAL] no %s -- run B3_spectrum.py first." % args.scores)
    serve = {str(r.get("idx")): r for r in load_jsonl(args.serve)}
    gold_map = json.load(open(args.gold_map, encoding="utf-8")) if os.path.exists(args.gold_map) else {}
    lvl_ans = {L: by_rid(load_jsonl("results/_spec_%s.jsonl" % L)) for L in ["G1", "G2", "G3", "G4"]}

    import re
    def norm_q(q): return re.sub(r"\s+", " ", (q or "").strip().lower())

    # ---- drill-down ----
    if args.record is not None:
        rid = "delucionqa_q%05d" % int(args.record)
        rec = next((r for r in scores if str(r.get("idx")) == str(args.record)), None)
        if not rec:
            raise SystemExit("record idx %s not found" % args.record)
        q = rec["question"]; g = gold_map.get(norm_q(q), {})
        print("=" * 78)
        print("RECORD idx=%s   answerable=%s" % (args.record, rec.get("answerable")))
        print("QUESTION: %s" % q)
        print("GOLD    : %s" % (g.get("gold_response", "")[:300]))
        print("=" * 78)
        for L in LEVELS:
            lv = rec["levels"].get(L, {})
            if L == "G0":
                ans = serve.get(str(args.record), {}).get("naive", {}).get("answer", "")
            else:
                ans = lvl_ans[L].get(rid, {}).get("generated_answer", "")
            adh = lv.get("adherence")
            print("\n[%s]  verdict=%s  faithfulness=%s" % (L, lv.get("verdict"), ("-" if adh is None else adh)))
            print("     %s" % (str(ans)[:400]))
        return

    # ---- grid ----
    print("=" * 92)
    print("SPECTRUM PER-RECORD  (verdict vs gold; ans=answerable)   N=%d" % len(scores))
    print("=" * 92)
    print("%-7s %4s  %-6s %-6s %-6s %-6s %-6s  %s" % ("idx", "ans", *LEVELS, "question"))
    print("-" * 92)
    for r in scores:
        ans = {True: "Y", False: "N"}.get(r.get("answerable"), "?")
        cells = [VMAP.get(r["levels"].get(L, {}).get("verdict", ""), "  .  ") for L in LEVELS]
        print("%-7s %4s  %-6s %-6s %-6s %-6s %-6s  %s"
              % (r.get("idx"), ans, cells[0], cells[1], cells[2], cells[3], cells[4], r["question"][:40]))
    print("-" * 92)
    # per-level tallies
    print("%-14s %-8s %-8s %-8s %-8s" % ("level", "MATCH", "WRONG", "refuse", "faith(ans)"))
    for L in LEVELS:
        m = sum(1 for r in scores if r["levels"].get(L, {}).get("verdict") == "MATCH")
        w = sum(1 for r in scores if r["levels"].get(L, {}).get("verdict") == "NO_MATCH")
        s = sum(1 for r in scores if r["levels"].get(L, {}).get("verdict") == "SAFE_SILENCE")
        fa = [r["levels"][L]["adherence"] for r in scores if r["levels"].get(L, {}).get("adherence") is not None]
        favg = ("%.2f" % (sum(fa) / len(fa))) if fa else "-"
        print("%-14s %-8d %-8d %-8d %-8s" % (L, m, w, s, favg))
    print("\nTip: python spectrum_review.py --record <idx>  to see the answers for one question.")


if __name__ == "__main__":
    main()
