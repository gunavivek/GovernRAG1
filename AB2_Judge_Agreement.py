#!/usr/bin/env python3
"""
AB2_Judge_Agreement.py -- cross-family JUDGE sensitivity add-on (job 7).  NEW STANDALONE FILE.
Pending Vivek's approval (code-change rule); nothing existing is modified.

PURPOSE (deviation entry 2026-10-02, ADD-ON clause): re-judge ~500 sealed Gemini-era
answered pairs with gpt-4.1-mini-2025-04-14 as a second, cross-family judge, holding the
generator constant; report raw agreement and Cohen's kappa with a bootstrap CI
(B=10,000, seed 20261002) against the constant campaign judge (gemini-3.1-pro-preview).

FIDELITY: the judge prompt, marker stripping, refusal detection and verdict parsing are
IMPORTED from the frozen trace_scorer.py (ts.CORRECT_PROMPT, ts.strip_markers,
ts.is_refusal, token-scan order SAFE_SILENCE > NO_MATCH > MATCH, default NO_MATCH)
-- the same objects E3P uses, not copies.  Only the HTTP transport to OpenAI is new.

READ-ONLY SOURCES (sealed):
  reference verdicts : results/run1_rejudge/E3_run1_rejudge_checkpoint.jsonl   (DelucionQA, 3.1-pro)
                       results/run2_hagrid/E3_run2_hagrid_checkpoint.jsonl     (HAGRID,   3.1-pro)
                       results/run3_expertqa/E3_run3_expertqa_checkpoint.jsonl (ExpertQA, 3.1-pro)
  full answers       : per-corpus sealed _spec_<cfg>.jsonl (governed) and
                       serve_results.jsonl (naive) -- checkpoints truncate answers,
                       so judging always goes back to the sealed full text
  full gold          : per-corpus sealed gold_map.json via ts.norm_q(full question)

SAMPLING (--select; seed 20261002): universe = answered pairs (refused False, reference
verdict MATCH/NO_MATCH) in the five dial levels across all three corpora; proportional
allocation over the corpus x config cells to N=500 (largest-remainder), seeded shuffle
within cells.  The selection list is WRITTEN TO DISK AND COMMITTED BEFORE any re-judge
call (pre-commitment).

WRITES (results/ root; refuses to overwrite -- same O3 discipline as AB1):
  ABL_judgeagreement_selection.jsonl   the pre-committed sample
  ABL_judgeagreement_ckpt.jsonl        resumable per-call checkpoint
  ABL_judgeagreement_results.jsonl     per-pair: reference verdict vs second-judge verdict
  ABL_judgeagreement_report.json       confusion matrix, agreement, kappa + bootstrap CI

USAGE (from the Start-GovRAG.ps1 terminal; OPENAI_API_KEY loaded):
  python AB2_Judge_Agreement.py --select
  python AB2_Judge_Agreement.py --rejudge --model gpt-4.1-mini-2025-04-14
"""
import argparse, hashlib, json, os, random, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"
sys.path.insert(0, str(ROOT))
import trace_scorer as ts                      # frozen; read-only import

SEED = 20261002
N_TARGET = 500
B_BOOT = 10000
LEVELS = ["G0_Naive", "G1_Cited", "G2_Grounded", "G3_Strict", "G4_Corrob"]
CORPORA = {
    "run1_delucionqa": RES / "run1_rejudge" / "E3_run1_rejudge_checkpoint.jsonl",
    "run2_hagrid":     RES / "run2_hagrid" / "E3_run2_hagrid_checkpoint.jsonl",
    "run3_expertqa":   RES / "run3_expertqa" / "E3_run3_expertqa_checkpoint.jsonl",
}
SEL_PATH = RES / "ABL_judgeagreement_selection.jsonl"
CKPT_PATH = RES / "ABL_judgeagreement_ckpt.jsonl"
OUT_PATH = RES / "ABL_judgeagreement_results.jsonl"
REP_PATH = RES / "ABL_judgeagreement_report.json"

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def die(msg):
    sys.exit("[FATAL] " + msg)


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def full_text_indexes(corpus):
    """idx->full question/gold (serve+gold_map) and (config,idx)->full answer (spec/serve)."""
    src = RES / corpus
    serve = load_jsonl(src / "serve_results.jsonl")
    gold_map = json.load(open(src / "gold_map.json", encoding="utf-8"))
    q_by_idx, gold_by_idx, naive_by_idx = {}, {}, {}
    for row in serve:
        i = str(int(str(row["idx"])))
        q = row.get("question", "")
        q_by_idx[i] = q
        g = gold_map.get(ts.norm_q(q), {})
        gold_by_idx[i] = g.get("gold_response", row.get("gold", ""))
        naive_by_idx[i] = (row.get("naive") or {}).get("answer", "")
    spec_by = {}
    for cfg in LEVELS[1:]:                     # config names == sealed spec-file suffixes
        m = {}
        for r in load_jsonl(src / ("_spec_%s.jsonl" % cfg)):
            tail = str(r.get("record_id", "")).rsplit("_q", 1)[-1]
            key = str(int(tail)) if tail.isdigit() else str(r.get("record_id"))
            m[key] = r.get("generated_answer", "")
        spec_by[cfg] = m
    return q_by_idx, gold_by_idx, naive_by_idx, spec_by


def select():
    if SEL_PATH.exists():
        die("selection already exists (%s) -- it is pre-committed; refusing to redraw." % SEL_PATH.name)
    cells = {}
    for corpus, ckpt in CORPORA.items():
        if not ckpt.exists():
            die("sealed reference checkpoint missing: %s" % ckpt)
        for r in load_jsonl(ckpt):
            if r.get("config") not in LEVELS:
                continue
            if str(r.get("refused")) == "True":
                continue
            if r.get("verdict") not in ("MATCH", "NO_MATCH"):
                continue
            cells.setdefault((corpus, r["config"]), []).append(
                {"corpus": corpus, "config": r["config"], "idx": str(int(str(r["idx"]))),
                 "ref_verdict": r["verdict"]})
    total = sum(len(v) for v in cells.values())
    if total < N_TARGET:
        die("universe smaller than target: %d" % total)
    rng = random.Random(SEED)
    # largest-remainder proportional allocation
    quotas = {k: N_TARGET * len(v) / total for k, v in cells.items()}
    alloc = {k: int(q) for k, q in quotas.items()}
    rem = N_TARGET - sum(alloc.values())
    for k in sorted(quotas, key=lambda k: quotas[k] - alloc[k], reverse=True)[:rem]:
        alloc[k] += 1
    picked = []
    for k in sorted(cells):
        pool = sorted(cells[k], key=lambda r: (r["idx"],))
        rng.shuffle(pool)
        picked.extend(pool[:alloc[k]])
    with open(SEL_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps({"k": "__header__", "seed": SEED, "n": len(picked),
                            "universe": total, "alloc": {"%s|%s" % k: v for k, v in alloc.items()},
                            "reference_checkpoints_sha256": {c: sha256(p) for c, p in CORPORA.items()},
                            "drawn_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
        for r in picked:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("[SELECT] %d pairs drawn (universe %d, seed %d) -> %s" % (len(picked), total, SEED, SEL_PATH.name))
    print("COMMIT THIS FILE TO GIT BEFORE RUNNING --rejudge (pre-commitment).")


def call_openai(model, prompt, tries=6):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        die("OPENAI_API_KEY is not set in this terminal.")
    body = json.dumps({"model": model, "temperature": 0.0, "max_completion_tokens": 16,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(OPENAI_URL, data=body, method="POST", headers={
            "Content-Type": "application/json", "Authorization": "Bearer %s" % key,
            "User-Agent": "AB2-JudgeAgreement/1.0 (GovernRAG ablation)", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.loads(r.read().decode("utf-8"))
            return (out["choices"][0]["message"]["content"] or "").strip()
        except urllib.error.HTTPError as e:
            last = "HTTP %s: %s" % (e.code, e.read(300).decode("utf-8", "replace"))
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError("non-retryable: %s" % last)
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, e)
        if attempt < tries - 1:
            time.sleep(min(60, 2 ** attempt) + 0.5)
    raise RuntimeError("judge call failed after %d tries: %s" % (tries, last))


def second_verdict(model, gold, answer):
    """ts.correctness logic, OpenAI transport.  Pre-checks and parsing identical to frozen code."""
    if ts.is_refusal(answer, ""):
        return "SAFE_SILENCE"
    if not (answer or "").strip():
        return "NO_MATCH"
    v = call_openai(model, ts.CORRECT_PROMPT.format(gt=gold, ans=ts.strip_markers(answer))).upper()
    for tok in ("SAFE_SILENCE", "NO_MATCH", "MATCH"):
        if tok in v:
            return tok
    return "NO_MATCH"


def kappa(pairs):
    cats = ("MATCH", "NO_MATCH", "SAFE_SILENCE")
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pe = sum((sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n)
             for c in cats)
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def rejudge(model):
    if not SEL_PATH.exists():
        die("run --select first (and commit the selection).")
    for p in (OUT_PATH, REP_PATH):
        if p.exists() and not CKPT_PATH.exists():
            die("O3: %s already exists; refusing to overwrite." % p.name)
    rows = load_jsonl(SEL_PATH)
    header, sel = rows[0], rows[1:]
    done = {}
    if CKPT_PATH.exists():
        for r in load_jsonl(CKPT_PATH):
            done[r["k"]] = r
        print("[resume] %d verdicts in checkpoint" % len(done))
    idxmaps = {c: full_text_indexes(c) for c in CORPORA}
    n_new = 0
    with open(CKPT_PATH, "a", encoding="utf-8", newline="") as ck:
        for s in sel:
            k = "%s|%s|%s" % (s["corpus"], s["config"], s["idx"])
            if k in done:
                continue
            q_by, gold_by, naive_by, spec_by = idxmaps[s["corpus"]]
            answer = naive_by.get(s["idx"], "") if s["config"] == "G0_Naive" else spec_by[s["config"]].get(s["idx"], "")
            gold = gold_by.get(s["idx"], "")
            if not str(answer).strip() or not str(gold).strip():
                die("empty answer/gold for %s -- selection vs sealed sources mismatch; investigate." % k)
            v2 = second_verdict(model, gold, answer)
            rec = {"k": k, **s, "judge2_model": model, "judge2_verdict": v2}
            ck.write(json.dumps(rec, ensure_ascii=False) + "\n"); ck.flush()
            done[k] = rec; n_new += 1
            if n_new % 25 == 0:
                print("  [rejudge] %d new verdicts" % n_new, flush=True)
    results = [done["%s|%s|%s" % (s["corpus"], s["config"], s["idx"])] for s in sel]
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    pairs = [(r["ref_verdict"], r["judge2_verdict"]) for r in results]
    po, k_hat = kappa(pairs)
    rng = random.Random(SEED)
    boots = []
    for _ in range(B_BOOT):
        bs = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
        boots.append(kappa(bs)[1])
    boots.sort()
    conf = {}
    for a, b in pairs:
        conf["%s->%s" % (a, b)] = conf.get("%s->%s" % (a, b), 0) + 1
    report = {
        "n": len(pairs), "seed": SEED, "judge_reference": "gemini-3.1-pro-preview (sealed campaign verdicts)",
        "judge_second": model, "raw_agreement": round(po, 4), "cohens_kappa": round(k_hat, 4),
        "kappa_bootstrap_CI95": [round(boots[int(0.025 * B_BOOT)], 4), round(boots[int(0.975 * B_BOOT)], 4)],
        "B": B_BOOT, "confusion": conf,
        "selection_sha256": sha256(SEL_PATH),
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(REP_PATH, "w", encoding="utf-8", newline="") as f:
        json.dump(report, f, indent=2)
    print("[REPORT] n=%d  agreement=%.3f  kappa=%.3f  CI95=[%.3f, %.3f]  (%d new calls this session)"
          % (len(pairs), po, k_hat, report["kappa_bootstrap_CI95"][0], report["kappa_bootstrap_CI95"][1], n_new))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--rejudge", action="store_true")
    ap.add_argument("--model", default="gpt-4.1-mini-2025-04-14")
    args = ap.parse_args()
    if args.select == args.rejudge:
        ap.error("exactly one of --select / --rejudge")
    if args.select:
        select()
    else:
        rejudge(args.model)


if __name__ == "__main__":
    main()
