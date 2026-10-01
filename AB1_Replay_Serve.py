#!/usr/bin/env python3
"""
AB1_Replay_Serve.py -- cross-family ablation replay adapter.  NEW STANDALONE FILE.
v2.1 (2026-10-02): OpenAI max_completion_tokens rename + User-Agent header (probe findings, approved).
Draft v2 (2026-10-01): v1 was adversarially reviewed; six defects fixed (slot-owner
guard, model-pinned checkpoint, manifest overwrite guard, tolerant checkpoint resume,
naive-context validation, real byte-identity check).  Pending Vivek's approval
(code-change rule); nothing existing is modified or imported.

PURPOSE (Ablation_CrossFamily_Runplan.md, locked design v2, 2026-09-30):
  Replay the SEALED serve prompts of the Gemini campaign byte-identical to a different
  model family at temperature 0, so that every verdict difference is attributable to
  exactly one variable -- the generation model.  Q1-Q5 are inherited from the sealed
  record, not re-run.  E3_Parallel_Evaluation.py is then run UNMODIFIED on the outputs.

READS (read-only; SHA-256 recorded before the first call and re-verified after the last):
  results/<corpus>/_spec_<cfg>.jsonl        cfg in G1_Cited, G2_Grounded, G3_Strict, G4_Corrob
  results/<corpus>/_spec_<cfg>_red.jsonl    evidence-reduction stats (copied verbatim)
  results/<corpus>/serve_results.jsonl      naive inputs: question + naive.context

WRITES (results/ root slot; never overwrites -- see GUARDS):
  _spec_<cfg>.jsonl           prompt fields byte-identical, generated_answer replaced,
                              ablation metadata added under metadata.ablation
  _spec_<cfg>_red.jsonl       verbatim copies of the sealed reduction stats
  serve_results.jsonl         sealed rows with ONLY naive.answer replaced (+ naive.ablation)
  ABL_slot_owner.json         which (tag, model) owns the slot until it is sealed
  ABL_<provider>_<corpus>_replay_ckpt.jsonl      resumable per-call checkpoint
  ABL_<provider>_<corpus>_replay_manifest.json   pins, input hashes, counts, timestamps

GUARDS:
  O3  fresh start refuses to write if ANY destination (incl. manifest) exists;
  O3b the slot is claimed by ABL_slot_owner.json (tag+model+limit); a resume refuses to
      run unless the owner matches exactly, so job A's resume can never clobber job B;
  O5  no write path may name a sealed archive (run1_/run2_/run3_); enforced with real
      checks, not asserts (asserts vanish under python -O);
  J3  every output record is re-serialized minus its two permitted deltas and compared
      canonically against the sealed record -- a real check, not a self-comparison.

NAIVE PROMPT TEMPLATE: verbatim from frozen B2_Serve.py, naive_baseline(), line 144
  (reproduced below; B2 itself is NOT imported and NOT executed).  A sealed naive row
  with a missing/empty context HARD-STOPS the run (no silent garbage prompts); a sealed
  naive answer that was an ERROR string is replayed normally (its context is intact) and
  flagged sealed_answer_was_error in naive.ablation.

USAGE (from the Start-GovRAG.ps1 terminal):
  python AB1_Replay_Serve.py --probe  --provider openai --model <pinned>
  python AB1_Replay_Serve.py --corpus run1_delucionqa --provider openai --model <pinned> [--limit 20]
  (interrupted?  rerun the SAME command -- resumes from the checkpoint)
"""
import argparse, hashlib, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"

FRONTIER = ["G1_Cited", "G2_Grounded", "G3_Strict", "G4_Corrob"]
CORPORA = ["run1_delucionqa", "run2_hagrid", "run3_expertqa"]
SEALED_MARKERS = ("run1_", "run2_", "run3_", "full_run")

PROVIDERS = {
    "openai":   {"url": "https://api.openai.com/v1/chat/completions",      "key_env": "OPENAI_API_KEY"},
    "groq":     {"url": "https://api.groq.com/openai/v1/chat/completions", "key_env": "GROQ_API_KEY"},
    "together": {"url": "https://api.together.xyz/v1/chat/completions",    "key_env": "TOGETHER_API_KEY"},
}

# Verbatim from frozen B2_Serve.py naive_baseline() (line 144) -- do not edit.
NAIVE_TEMPLATE = ("Instructions: Answer the question based ONLY on the context.\n\n"
                  "Context: %s\n\nQuestion: %s")

MAX_TOKENS = 2048          # campaign G1 answers averaged ~755 chars; 2048 tokens is generous
TIMEOUT_S = 120            # same per-call ceiling discipline as E3P (approved 2026-07-19)

OWNER_PATH = RES / "ABL_slot_owner.json"


def die(msg):
    sys.exit("[FATAL] " + msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def load_ckpt(p):
    """Checkpoint load tolerant of ONE truncated final line (kill mid-write)."""
    lines = [l for l in open(p, encoding="utf-8") if l.strip()]
    out = []
    for i, l in enumerate(lines):
        try:
            out.append(json.loads(l))
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                print("[resume][warn] dropping one truncated final checkpoint line "
                      "(interrupted mid-write); that call will be redone.")
                break
            die("checkpoint corrupted at line %d (not the final line) -- investigate %s" % (i + 1, p))
    return out


def canon_without_deltas(rec, kind):
    """Canonical JSON of a record minus the fields this adapter is permitted to change.
    kind='spec': drop generated_answer and metadata.ablation.
    kind='serve': drop naive.answer and naive.ablation."""
    c = json.loads(json.dumps(rec))                     # deep copy
    if kind == "spec":
        c.pop("generated_answer", None)
        if isinstance(c.get("metadata"), dict):
            c["metadata"].pop("ablation", None)
        if c.get("metadata") in ({}, None):
            c.pop("metadata", None)   # creating metadata={} to hold the ablation
                                      # annotation is part of the permitted delta
    else:
        if isinstance(c.get("naive"), dict):
            c["naive"].pop("answer", None)
            c["naive"].pop("ablation", None)
    return json.dumps(c, sort_keys=True, ensure_ascii=False)


def identity_check(sealed, out, kind, label):
    if canon_without_deltas(sealed, kind) != canon_without_deltas(out, kind):
        die("J3 identity violation at %s -- output differs from sealed record "
            "beyond the permitted fields. Nothing further will be written." % label)


def call_model(provider, model, prompt, tries=6):
    """POST an OpenAI-compatible chat completion at T=0.  Returns (text, usage, latency_s, echo).
    Retries 429/5xx/network with exponential backoff (honours Retry-After); configuration
    errors (400/401/403/404) fail immediately."""
    cfg = PROVIDERS[provider]
    key = os.getenv(cfg["key_env"])
    if not key:
        die("%s is not set in this terminal." % cfg["key_env"])
    tok_param = "max_completion_tokens" if provider == "openai" else "max_tokens"
    body = json.dumps({"model": model, "temperature": 0.0, tok_param: MAX_TOKENS,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(cfg["url"], data=body, method="POST", headers={
            "Content-Type": "application/json", "Authorization": "Bearer %s" % key,
            "User-Agent": "AB1-Replay/2.1 (GovernRAG ablation)", "Accept": "application/json"})
        t0 = time.perf_counter()
        wait = min(60, 2 ** attempt) + 0.5
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                out = json.loads(r.read().decode("utf-8"))
            dt = round(time.perf_counter() - t0, 3)
            text = (out["choices"][0]["message"]["content"] or "").strip()
            return text, out.get("usage", {}), dt, out.get("model", "")
        except urllib.error.HTTPError as e:
            last = "HTTP %s: %s" % (e.code, e.read(300).decode("utf-8", "replace"))
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError("non-retryable configuration error: %s" % last)
            ra = e.headers.get("Retry-After") if e.headers else None
            if ra and str(ra).isdigit():
                wait = max(wait, min(120, int(ra)))
        except Exception as e:              # timeouts, resets
            last = "%s: %s" % (type(e).__name__, e)
        if attempt < tries - 1:
            time.sleep(wait)
    raise RuntimeError("model call failed after %d tries: %s" % (tries, last))


def probe(provider, model):
    """One tiny call.  Prints the server's model echo so the pinned string is verified LIVE."""
    text, usage, dt, echo = call_model(provider, model, "Reply with exactly: OK")
    print("[PROBE] provider=%s  requested=%s" % (provider, model))
    print("[PROBE] server model echo : %s" % echo)
    print("[PROBE] reply             : %r   (%.2fs)" % (text[:40], dt))
    print("[PROBE] usage             : %s" % json.dumps(usage))
    print("[PROBE] T=0 accepted, HTTP 200.  Record this transcript + billing screenshot.")


def guard_path(p):
    # O5: every write lands directly in results/ root; a sealed archive is a
    # SUBDIRECTORY of results/, so parent==RES structurally forbids writing into one.
    # (A filename-substring test misfires on our own tags, which embed the corpus name.)
    if p.parent != RES:
        die("O5 violation: refusing write path %s" % p)


def replay(corpus, provider, model, limit=None):
    src = RES / corpus
    tag = "ABL_%s_%s" % (provider, corpus)
    owner = {"tag": tag, "model": model, "limit": limit}
    ckpt_path = RES / ("%s_replay_ckpt.jsonl" % tag)
    man_path = RES / ("%s_replay_manifest.json" % tag)

    # ---- inputs (read-only) ----
    inputs = {}
    for cfg in FRONTIER:
        inputs["_spec_%s.jsonl" % cfg] = src / ("_spec_%s.jsonl" % cfg)
        inputs["_spec_%s_red.jsonl" % cfg] = src / ("_spec_%s_red.jsonl" % cfg)
    inputs["serve_results.jsonl"] = src / "serve_results.jsonl"
    missing = [str(p) for p in inputs.values() if not p.exists()]
    if missing:
        die("sealed input(s) missing:\n  " + "\n  ".join(missing))
    hashes_before = {k: sha256(v) for k, v in inputs.items()}       # hashed BEFORE any call

    # ---- outputs + guards ----
    outputs = [RES / ("_spec_%s.jsonl" % c) for c in FRONTIER]
    outputs += [RES / ("_spec_%s_red.jsonl" % c) for c in FRONTIER]
    outputs += [RES / "serve_results.jsonl"]
    for p in outputs + [ckpt_path, man_path, OWNER_PATH]:
        guard_path(p)

    if ckpt_path.exists() or OWNER_PATH.exists():
        # RESUME path: the slot must be owned by exactly this (tag, model, limit).
        if not OWNER_PATH.exists():
            die("checkpoint exists but no slot owner file -- slot state unclear; investigate.")
        try:
            cur = json.load(open(OWNER_PATH, encoding="utf-8"))
        except Exception:
            die("slot owner file unreadable -- investigate %s" % OWNER_PATH)
        if cur != owner:
            die("slot is owned by %s -- this command is %s.\n"
                "Seal/clear the previous job before starting another; nothing was written."
                % (json.dumps(cur), json.dumps(owner)))
        if not ckpt_path.exists():
            die("slot owner matches but checkpoint is missing -- slot state unclear; investigate.")
    else:
        # FRESH START: nothing this job writes may already exist (manifest included).
        clash = [str(p) for p in outputs + [man_path] if p.exists()]
        if clash:
            die("O3: refusing to write -- destination(s) already exist:\n  "
                + "\n  ".join(clash)
                + "\nRun the slot-hygiene step first; nothing was written.")
        with open(OWNER_PATH, "w", encoding="utf-8", newline="") as f:
            json.dump(owner, f)

    # ---- checkpoint ----
    done = {}
    if ckpt_path.exists():
        for r in load_ckpt(ckpt_path):
            done[r["k"]] = r
        print("[resume] %d calls already in checkpoint (tag=%s model=%s)" % (len(done), tag, model))

    t_start = time.time(); n_calls = 0
    with open(ckpt_path, "a", encoding="utf-8", newline="") as ck:

        def get_answer(key, prompt):
            nonlocal n_calls
            if key in done:
                return done[key]
            text, usage, dt, echo = call_model(provider, model, prompt)
            rec = {"k": key, "answer": text, "usage": usage, "latency_s": dt,
                   "model_requested": model, "model_echo": echo}
            ck.write(json.dumps(rec, ensure_ascii=False) + "\n"); ck.flush()
            done[key] = rec; n_calls += 1
            if n_calls % 25 == 0:
                print("  [replay] %d new calls  (%.1f min)" % (n_calls, (time.time() - t_start) / 60), flush=True)
            return rec

        # ---- governed configs: replay sealed final_prompt verbatim ----
        new_specs = {}
        for cfg in FRONTIER:
            rows = load_jsonl(inputs["_spec_%s.jsonl" % cfg])
            if limit:
                rows = rows[:limit]
            out_rows = []
            for r in rows:
                rid = r.get("record_id")
                if rid is None:
                    die("spec record with no record_id in %s -- investigate before spending." % cfg)
                mode = str(r.get("mode", ""))
                out = json.loads(json.dumps(r))                     # deep copy
                if not mode.startswith("BLOCKED"):
                    # BLOCKED records are substrate behaviour (frozen): inherited, not re-asked.
                    a = get_answer("spec|%s|%s" % (cfg, rid), r["final_prompt"])
                    out["generated_answer"] = a["answer"]
                md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
                md["ablation"] = {"provider": provider, "model": model,
                                  "replayed": not mode.startswith("BLOCKED")}
                out["metadata"] = md
                identity_check(r, out, "spec", "%s record_id=%s" % (cfg, rid))
                out_rows.append(out)
            new_specs[cfg] = out_rows

        # ---- naive: sealed context + frozen B2 template ----
        serve_rows = load_jsonl(inputs["serve_results.jsonl"])
        if limit:
            serve_rows = serve_rows[:limit]
        new_serve = []
        for row in serve_rows:
            idx = row.get("idx")
            if idx is None:
                die("serve row with no idx -- investigate before spending.")
            naive_in = row.get("naive") if isinstance(row.get("naive"), dict) else {}
            ctx = naive_in.get("context")
            if not isinstance(ctx, str) or not ctx.strip():
                die("serve idx=%s has missing/empty naive.context -- no silent garbage "
                    "prompts; investigate the sealed record first." % idx)
            prompt = NAIVE_TEMPLATE % (ctx, row.get("question", ""))
            a = get_answer("naive|G0|%s" % idx, prompt)
            out = json.loads(json.dumps(row))                       # deep copy
            out["naive"]["answer"] = a["answer"]
            out["naive"]["ablation"] = {
                "provider": provider, "model": model,
                "sealed_answer_was_error": str(naive_in.get("answer", "")).startswith("ERROR")}
            identity_check(row, out, "serve", "serve idx=%s" % idx)
            new_serve.append(out)

    # ---- inputs must not have changed while we ran ----
    hashes_after = {k: sha256(v) for k, v in inputs.items()}
    if hashes_after != hashes_before:
        die("sealed input changed during the run (hash mismatch) -- outputs NOT written.")

    # ---- write outputs (slot owned by this job; LF endings to match sealed files) ----
    for cfg in FRONTIER:
        with open(RES / ("_spec_%s.jsonl" % cfg), "w", encoding="utf-8", newline="") as f:
            for r in new_specs[cfg]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        red_src = inputs["_spec_%s_red.jsonl" % cfg]
        (RES / ("_spec_%s_red.jsonl" % cfg)).write_bytes(red_src.read_bytes())   # verbatim copy
    with open(RES / "serve_results.jsonl", "w", encoding="utf-8", newline="") as f:
        for r in new_serve:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "tag": tag, "corpus": corpus, "provider": provider, "model_pinned": model,
        "temperature": 0.0, "max_tokens": MAX_TOKENS, "limit": limit,
        "naive_template_source": "B2_Serve.py naive_baseline() line 144 (frozen; reproduced verbatim)",
        "sealed_inputs_sha256": hashes_before,
        "records": {"serve": len(new_serve), **{c: len(new_specs[c]) for c in FRONTIER}},
        "calls_this_session": n_calls,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_start)),
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(man_path, "w", encoding="utf-8", newline="") as f:
        json.dump(manifest, f, indent=2)
    print("[DONE] %s: %d serve rows, %s spec rows, %d new calls.  Manifest: %s"
          % (tag, len(new_serve), {c: len(new_specs[c]) for c in FRONTIER}, n_calls, man_path.name))
    print("Slot stays owned by this job until it is sealed to results/ablation_* "
          "(owner file: %s)." % OWNER_PATH.name)
    print("Next: python E3_Parallel_Evaluation.py --serve results/serve_results.jsonl "
          "--gold-map results/%s/gold_map.json --out-prefix %s" % (corpus, tag))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--corpus", choices=CORPORA)
    ap.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int, default=None, help="pilot: first N records per config")
    args = ap.parse_args()
    if args.limit is not None and args.limit <= 0:
        ap.error("--limit must be a positive integer")
    if args.probe:
        probe(args.provider, args.model)
    elif args.corpus:
        replay(args.corpus, args.provider, args.model, args.limit)
    else:
        ap.error("either --probe or --corpus is required")


if __name__ == "__main__":
    main()
