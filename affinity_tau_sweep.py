#!/usr/bin/env python3
"""
affinity_tau_sweep.py -- READ-ONLY characterization of Axis B (domain affinity). Documents the
evidence-reduction-vs-threshold curve HONESTLY (including nulls), and tests the redundancy
hypothesis: are predicate-authorized chunks already high-affinity (so affinity adds no separable
filtering)?

Method (no generation, no judge, one Q5 pass):
  1. Run Q5 ONCE at G2 (predicate authorization on, affinity OFF) -> authorized surviving chunks.
  2. Join each survivor's M1 wa_score.
  3. Compute mean chunks-dropped-per-record for a grid of tau across the real percentiles.
  4. Compare the SURVIVOR wa_score distribution to the GLOBAL distribution (the redundancy test).

Writes results/affinity_tau_sweep.csv (+ .png if matplotlib present). Changes no pipeline code.
RUN from repo root:  python affinity_tau_sweep.py
"""
import csv, json, os, re, subprocess, sys, statistics as st
from pathlib import Path

def find_root(start):
    for p in [start, *start.parents]:
        if (p / "output").exists() and (p / "experiment").exists():
            return p
    return start

ROOT = find_root(Path.cwd()); EXP = ROOT / "experiment"; OUT = ROOT / "output"; RES = ROOT / "results"
RES.mkdir(exist_ok=True)
Q5_OUT = OUT / "Q5_routed_context.jsonl"
M1 = OUT / "M1_Governed_Chunks.csv"

def load_wa():
    wa = {}
    if not M1.exists():
        # fall back to index/*/ like the Q5 loader does
        import glob
        cands = sorted(glob.glob(str(ROOT / "index" / "**" / "M1_Governed_Chunks.csv"), recursive=True))
        path = cands[0] if cands else None
    else:
        path = str(M1)
    if not path:
        sys.exit("[FATAL] M1_Governed_Chunks.csv not found.")
    csv.field_size_limit(10_000_000)
    for row in csv.DictReader(open(path, encoding="utf-8")):
        try: wa[row.get("chunk_id") or ""] = float(row.get("wa_score"))
        except (TypeError, ValueError): pass
    print("[tau] wa_scores loaded: %d chunks from %s" % (len(wa), path))
    return wa

def pctl(xs, p):
    if not xs: return float("nan")
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p / 100.0 * len(xs)))]

def main():
    # 1) run Q5 once at clean G2 (authorization on, both axes off)
    env = dict(os.environ); env["GOVRAG_LEVEL"] = "G2"; env["GOVRAG_ONTOLOGY"] = "all"; env["GOVRAG_AFFINITY_MIN"] = "0"
    print("[tau] running Q5 once at G2 (affinity off) to capture authorized survivors ...")
    r = subprocess.run([sys.executable, "-u", str(EXP / "Q5_Gov_Context_Router.py")], cwd=str(ROOT), env=env)
    if r.returncode != 0:
        sys.exit("[FATAL] Q5 run failed.")

    wa = load_wa()
    global_scores = list(wa.values())

    # 2) parse authorized survivors per record; join wa
    per_record = []          # list of lists of survivor wa_scores
    joined, missed = 0, 0
    for rec in (json.loads(l) for l in open(Q5_OUT, encoding="utf-8") if l.strip()):
        chunk_str = str(rec.get("semantic_chunk", ""))
        ids = re.findall(r"\[(CHNK_[^\]]+)\]", chunk_str)
        scores = []
        for cid in ids:
            if cid in wa: scores.append(wa[cid]); joined += 1
            else: missed += 1
        per_record.append(scores)
    survivor_scores = [s for rec in per_record for s in rec]
    n_rec = len(per_record)
    print("[tau] records=%d  authorized survivor chunks=%d  join: %d matched / %d missed"
          % (n_rec, len(survivor_scores), joined, missed))

    # 3) redundancy test: survivor distribution vs global distribution
    def dist(xs):
        return "min=%.3f p25=%.3f med=%.3f p75=%.3f p90=%.3f max=%.3f mean=%.3f" % (
            min(xs), pctl(xs,25), pctl(xs,50), pctl(xs,75), pctl(xs,90), max(xs), st.mean(xs)) if xs else "(empty)"
    print("\n[tau] GLOBAL   wa_score: %s" % dist(global_scores))
    print("[tau] SURVIVOR wa_score: %s" % dist(survivor_scores))
    if survivor_scores and global_scores:
        print("[tau] REDUNDANCY CHECK: survivor median %.3f vs global median %.3f  (higher survivor => authorized chunks already high-affinity)"
              % (pctl(survivor_scores,50), pctl(global_scores,50)))

    # 4) affChk-vs-tau curve over the real (survivor) percentiles + a few global ones
    tau_set = set(round(pctl(survivor_scores, p), 4) for p in (10, 25, 50, 60, 70, 75, 80, 85, 90, 95, 99))
    tau_set |= set(round(pctl(global_scores, p), 4) for p in (50, 75, 90, 95))
    taus = sorted(t for t in tau_set if t == t)  # drop NaN
    print("\n" + "=" * 72)
    print("AXIS B  affinity threshold sensitivity (authorized survivors, N=%d records)" % n_rec)
    print("=" * 72)
    print("%10s %14s %16s %14s" % ("tau", "mean affChk", "mean chkKept", "%records hit"))
    rows = [("tau", "mean_affChk_dropped", "mean_chkKept_after", "pct_records_hit")]
    for tau in taus:
        drops = [sum(1 for s in rec if s < tau) for rec in per_record]
        kept  = [sum(1 for s in rec if s >= tau) for rec in per_record]
        hit = sum(1 for d in drops if d > 0)
        print("%10.4f %14.2f %16.2f %13.0f%%" % (tau, st.mean(drops), st.mean(kept), 100*hit/n_rec if n_rec else 0))
        rows.append((("%.4f"%tau), ("%.4f"%st.mean(drops)), ("%.4f"%st.mean(kept)), ("%.4f"%(hit/n_rec if n_rec else 0))))
    with open(RES / "affinity_tau_sweep.csv", "w", encoding="utf-8") as f:
        for r in rows: f.write(",".join(map(str, r)) + "\n")
    print("-" * 72)
    print("[tau] curve -> results/affinity_tau_sweep.csv")
    print("READ: the tau at which mean affChk first exceeds 0 is where affinity starts pruning authorized")
    print("      evidence. If that tau sits ABOVE the global median, affinity is redundant with authorization")
    print("      on this corpus (authorized chunks are already domain-aligned).")

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        xs = [float(r[0]) for r in rows[1:]]; ys = [float(r[1]) for r in rows[1:]]
        plt.figure(figsize=(6,4)); plt.plot(xs, ys, "-o", color="#C55A11")
        plt.axvline(pctl(global_scores,50), ls="--", color="gray", label="global median")
        plt.xlabel("affinity threshold tau"); plt.ylabel("mean chunks dropped / record")
        plt.title("Axis B sensitivity: evidence pruned vs threshold"); plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
        plt.savefig(RES / "affinity_tau_sweep.png", dpi=150); print("[tau] plot -> results/affinity_tau_sweep.png")
    except Exception as e:
        print("[tau] plot skipped (%s)" % e)

if __name__ == "__main__":
    main()
