#!/usr/bin/env python3
"""
compare_m4_alignment.py -- equivalence check: serial M4 vs parallel M4.

Parses the serial run's console log ('Evaluated <node>: <status> -> <target>' lines)
and the parallel run's per-node results (output/M4_alignment_results.jsonl), then
reports how often the two runs made the SAME alignment decision on the SAME nodes.

Interpretation:
  >= 95% status agreement  -> equivalent; residual differences are temperature=0
                              server-side nondeterminism (present even serial-vs-serial).
  <  90%                    -> a real difference; investigate before trusting the run.

Usage:
  python compare_m4_alignment.py --serial-log serial_m4_ref.log
  python compare_m4_alignment.py --serial-log serial_m4_ref.log --parallel output/M4_alignment_results.jsonl
"""
import argparse, json, re, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial-log", required=True, help="frozen copy of the serial run's log")
    ap.add_argument("--parallel", default="output/M4_alignment_results.jsonl")
    ap.add_argument("--show", type=int, default=15)
    args = ap.parse_args()

    # --- parse serial log: keep the LAST decision seen per node ---
    serial = {}
    pat = re.compile(r"Evaluated '(.+?)': (.+)")
    with open(args.serial_log, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = pat.search(line)
            if not m:
                continue
            node, rest = m.group(1), m.group(2).strip()
            status, target = (rest.split(" -> ", 1) + [""])[:2] if " -> " in rest else (rest, "")
            serial[node] = (status.strip(), target.strip())

    # --- parse parallel jsonl ---
    parallel = {}
    with open(args.parallel, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            parallel[d["node"]] = (str(d.get("status", "")).strip(), str(d.get("target", "")).strip())

    common = sorted(set(serial) & set(parallel))
    print(f"serial nodes: {len(serial)} | parallel nodes: {len(parallel)} | overlap compared: {len(common)}")
    if not common:
        sys.exit("No overlapping nodes — check --serial-log path and that parallel M4 has produced results.")

    status_ok = sum(1 for n in common if serial[n][0] == parallel[n][0])
    full_ok = sum(1 for n in common if serial[n] == parallel[n])
    print(f"status agreement      : {status_ok}/{len(common)} ({100*status_ok/len(common):.1f}%)")
    print(f"status+target agreement: {full_ok}/{len(common)} ({100*full_ok/len(common):.1f}%)")

    mism = [n for n in common if serial[n] != parallel[n]]
    print(f"\nmismatches: {len(mism)} (showing up to {args.show})")
    for n in mism[:args.show]:
        print(f"  '{n}': serial={serial[n]}  parallel={parallel[n]}")

    rate = 100 * status_ok / len(common)
    print("\n[verdict]", "EQUIVALENT (>=95% status)" if rate >= 95
          else ("LIKELY OK, spot-check mismatches (90-95%)" if rate >= 90
                else "INVESTIGATE — agreement too low, do not trust the parallel run yet"))

if __name__ == "__main__":
    main()
