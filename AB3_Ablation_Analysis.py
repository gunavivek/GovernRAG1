#!/usr/bin/env python3
"""
AB3_Ablation_Analysis.py -- formal analysis of the cross-family generation ablation.
READ-ONLY over sealed archives; writes only results/ablation_analysis/.

Evaluates the PRE-STATED decision rule (deviation entry 2026-10-02) per family:
  (a) coverage non-increasing G0->G4 on each corpus;
  (b) G1->G2 cliff on the aligned corpus (DelucionQA) and above-G1 collapse on HAGRID;
  (c) correct-refusal ordering governed >> naive on the unanswerable stratum;
  (d) resolvable-citation auditability at ceiling (measured from sealed answers, not assumed).
Paired bootstrap (resample records, B=10,000, seed 20261002) for all deltas.
Also: campaign (Gemini) reference metrics from the sealed 3.1-pro checkpoints, and a
family performance table from the sealed replay checkpoints.
"""
import json, hashlib, re, time
from pathlib import Path
import numpy as np

RES = Path(__file__).resolve().parent / "results"
OUT = RES / "ablation_analysis"
SEED = 20261002
B = 10000
LEVELS = ["G0_Naive", "G1_Cited", "G2_Grounded", "G3_Strict", "G4_Corrob"]

SOURCES = {
    ("gemini", "run1_delucionqa"): RES / "run1_rejudge" / "E3_run1_rejudge_checkpoint.jsonl",
    ("gemini", "run2_hagrid"):     RES / "run2_hagrid" / "E3_run2_hagrid_checkpoint.jsonl",
    ("gemini", "run3_expertqa"):   RES / "run3_expertqa" / "E3_run3_expertqa_checkpoint.jsonl",
    ("openai", "run1_delucionqa"): RES / "ablation_openai_run1_delucionqa" / "ABL_openai_run1_delucionqa_checkpoint.jsonl",
    ("openai", "run2_hagrid"):     RES / "ablation_openai_run2_hagrid" / "ABL_openai_run2_hagrid_checkpoint.jsonl",
    ("openai", "run3_expertqa"):   RES / "ablation_openai_run3_expertqa" / "ABL_openai_run3_expertqa_checkpoint.jsonl",
    ("llama", "run1_delucionqa"):  RES / "ablation_together_run1_delucionqa" / "ABL_together_run1_delucionqa_checkpoint.jsonl",
    ("llama", "run2_hagrid"):      RES / "ablation_together_run2_hagrid" / "ABL_together_run2_hagrid_checkpoint.jsonl",
    ("llama", "run3_expertqa"):    RES / "ablation_together_run3_expertqa" / "ABL_together_run3_expertqa_checkpoint.jsonl",
}
SPEC_DIR = {  # for criterion (d): full answers + prompts
    ("openai", c): RES / ("ablation_openai_%s" % c) for c in ["run1_delucionqa", "run2_hagrid", "run3_expertqa"]
} | {
    ("llama", c): RES / ("ablation_together_%s" % c) for c in ["run1_delucionqa", "run2_hagrid", "run3_expertqa"]
} | {
    ("gemini", "run1_delucionqa"): RES / "run1_delucionqa",
    ("gemini", "run2_hagrid"): RES / "run2_hagrid",
    ("gemini", "run3_expertqa"): RES / "run3_expertqa",
}


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def as_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v)
    return True if s == "True" else False if s == "False" else None


def build_matrices(path):
    """Per (family,corpus): refused[n,5], safe[n,5] (verdict SAFE_SILENCE), answerable[n]."""
    rows = load_jsonl(path)
    per = {}
    for r in rows:
        if r.get("config") not in LEVELS:
            continue
        i = str(int(str(r["idx"])))
        per.setdefault(i, {})[r["config"]] = r
    idxs = sorted(per, key=int)
    idxs = [i for i in idxs if all(l in per[i] for l in LEVELS)]
    n = len(idxs)
    refused = np.zeros((n, 5), dtype=np.int8)
    safe = np.zeros((n, 5), dtype=np.int8)
    ans = np.zeros(n, dtype=np.int8)  # 1 answerable, 0 unanswerable, -1 unknown
    for k, i in enumerate(idxs):
        a = as_bool(per[i][LEVELS[0]].get("answerable"))
        ans[k] = 1 if a is True else 0 if a is False else -1
        for j, l in enumerate(LEVELS):
            r = per[i][l]
            refused[k, j] = 1 if as_bool(r.get("refused")) else 0
            safe[k, j] = 1 if r.get("verdict") == "SAFE_SILENCE" else 0
    return idxs, refused, safe, ans


def boot_mean_ci(values, rng):
    """values: 1-D array per record; paired bootstrap CI of the mean."""
    n = len(values)
    sums = np.zeros(B)
    chunk = 1000
    for s in range(0, B, chunk):
        e = min(s + chunk, B)
        idx = rng.integers(0, n, size=(e - s, n))
        sums[s:e] = values[idx].mean(axis=1)
    lo, hi = np.percentile(sums, [2.5, 97.5])
    return float(values.mean()), float(lo), float(hi)


CIT_RE = re.compile(r"\[(CHNK_[^\]\s]+|RESIDUAL_[^\]\s]+)\]")


def citation_resolvability(spec_dir):
    """Across answered governed records: fraction of cited markers present in that record's prompt."""
    cited = resolved = answered_with_citations = 0
    for cfg in LEVELS[1:]:
        for r in load_jsonl(spec_dir / ("_spec_%s.jsonl" % cfg)):
            if str(r.get("mode", "")).startswith("BLOCKED"):
                continue
            ans_text = str(r.get("generated_answer") or "")
            prompt = str(r.get("final_prompt") or "")
            toks = CIT_RE.findall(ans_text)
            if toks:
                answered_with_citations += 1
            for t in set(toks):
                cited += 1
                if t in prompt:
                    resolved += 1
    return {"records_with_citations": answered_with_citations, "distinct_citations": cited,
            "resolved": resolved, "resolvability": round(resolved / cited, 4) if cited else None}


def main():
    OUT.mkdir(exist_ok=False)
    rng = np.random.default_rng(SEED)
    report = {"seed": SEED, "B": B, "inputs_sha256": {"%s|%s" % k: sha(p) for k, p in SOURCES.items()},
              "families": {}, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    for fam in ("gemini", "openai", "llama"):
        fam_out = {}
        for corpus in ("run1_delucionqa", "run2_hagrid", "run3_expertqa"):
            idxs, refused, safe, ans = build_matrices(SOURCES[(fam, corpus)])
            cov = 1 - refused  # answered
            entry = {"n": len(idxs),
                     "coverage": [round(float(cov[:, j].mean()), 4) for j in range(5)]}
            # (a) adjacent coverage deltas with paired bootstrap CI
            deltas = []
            for j in range(4):
                d = (cov[:, j + 1] - cov[:, j]).astype(np.float64)
                m, lo, hi = boot_mean_ci(d, rng)
                deltas.append({"step": "%s->%s" % (LEVELS[j], LEVELS[j + 1]),
                               "delta": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)]})
            entry["coverage_deltas"] = deltas
            entry["monotone_nonincreasing"] = all(d["delta"] <= 1e-9 for d in deltas)
            # (c) correct refusal on unanswerable stratum: SAFE_SILENCE rate
            un = ans == 0
            entry["n_unanswerable"] = int(un.sum())
            if un.sum() >= 5:
                cr = {}
                for j, l in enumerate(LEVELS):
                    m, lo, hi = boot_mean_ci(safe[un, j].astype(np.float64), rng)
                    cr[l] = {"rate": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)]}
                entry["correct_refusal_unanswerable"] = cr
                dvs = {}
                for j in range(1, 5):
                    d = (safe[un, j] - safe[un, 0]).astype(np.float64)
                    m, lo, hi = boot_mean_ci(d, rng)
                    dvs[LEVELS[j]] = {"delta_vs_naive": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)]}
                entry["correct_refusal_delta_vs_naive"] = dvs
            # (d) citation resolvability
            entry["auditability"] = citation_resolvability(SPEC_DIR[(fam, corpus)])
            fam_out[corpus] = entry
        report["families"][fam] = fam_out

    # criteria verdicts per ablation family (campaign = reference)
    verdicts = {}
    for fam in ("openai", "llama"):
        f = report["families"][fam]
        a_ok = all(f[c]["monotone_nonincreasing"] for c in f)
        cliff = f["run1_delucionqa"]["coverage_deltas"][1]       # G1->G2
        b1 = cliff["delta"] < 0 and cliff["ci95"][1] < 0
        hag = f["run2_hagrid"]
        b2 = hag["coverage"][2] < 0.5 * hag["coverage"][1] and hag["coverage_deltas"][1]["ci95"][1] < 0
        c_ok = True
        c_detail = {}
        for c in f:
            dvs = f[c].get("correct_refusal_delta_vs_naive")
            if not dvs:
                continue
            g2plus = [dvs[l] for l in ("G2_Grounded", "G3_Strict", "G4_Corrob")]
            ok = all(d["delta_vs_naive"] > 0 and d["ci95"][0] > 0 for d in g2plus)
            c_detail[c] = {"g2plus_all_above_naive_ci_excl_0": ok,
                           "g1_delta": dvs.get("G1_Cited")}
            c_ok = c_ok and ok
        d_vals = [f[c]["auditability"]["resolvability"] for c in f if f[c]["auditability"]["resolvability"] is not None]
        d_ok = all(v >= 0.99 for v in d_vals)
        verdicts[fam] = {"a_monotonicity": a_ok,
                         "b_cliff_delu_and_hagrid_collapse": bool(b1 and b2),
                         "b_detail": {"delu_G1G2": cliff, "hagrid_cov": hag["coverage"]},
                         "c_governed_refusal_over_naive_G2plus": c_ok, "c_detail": c_detail,
                         "d_auditability_min": min(d_vals) if d_vals else None, "d_at_ceiling": d_ok}
    report["criteria_verdicts"] = verdicts
    with open(OUT / "analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    man = {p.name: sha(p) for p in OUT.iterdir()}
    with open(OUT / "SHA256SUMS.json", "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)
    print(json.dumps(report["criteria_verdicts"], indent=1)[:3000])
    print("[DONE] full report -> results/ablation_analysis/analysis_report.json")


if __name__ == "__main__":
    main()
