#!/usr/bin/env python3
# W4 — §VI Discussion + §VII Threats to Validity and Reproducibility: draft v1.
from docx import Document
from docx.shared import Pt, RGBColor

OUT = "/tmp/gr/W4_SectionVI_VII_DRAFT.docx"
NAVY = RGBColor(0x1F, 0x4E, 0x79)
INK  = RGBColor(0x1A, 0x1A, 0x1A)
MUT  = RGBColor(0x55, 0x55, 0x55)

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)

def P(runs, size=11, before=0, after=8):
    if isinstance(runs, str): runs = [(runs, {})]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    for text, opts in runs:
        r = p.add_run(text)
        r.font.name = "Calibri"; r.font.size = Pt(opts.get("size", size))
        r.font.bold = opts.get("bold", False); r.font.italic = opts.get("italic", False)
        r.font.color.rgb = opts.get("color", INK)
    return p

P([("W4 — §VI + §VII draft v2 · 27 July 2026 · §VI.A/B/C ALL APPROVED (plain VI.A + regulated-enterprise closing w/ FINRA-SEC; VI.B benchmark-pattern economics; VI.C architectural contrast) · §VII pending review · not yet poured · "
    "sources: spine v2.4 §6/§7 + F8, T1/T2 records, ledger-verified numbers",
    {"italic": True, "size": 9, "color": MUT})], after=14)

P([("VI. DISCUSSION", {"bold": True, "size": 13, "color": NAVY})], after=8)

P([("A. What governance costs, and what it buys", {"bold": True,
    "italic": True})], after=4)

P("The dial gives an operator two useful settings. G1 keeps most of the "
  "coverage and adds citations and the full audit trail at almost no cost. "
  "The G2 tier refuses much of what it could answer; in return it delivers "
  "policy-grade refusal and, where abstention matters, beats the ungoverned "
  "baseline. Choosing between them is a policy decision, not a tuning "
  "exercise. The aligned concept share, measured at build time, indicates how "
  "far the dial can usefully turn.")

P("The results indicate where this approach fits best. Three conditions "
  "matter: the corpus speaks a documented domain vocabulary, so the dial "
  "stays usable; a meaningful share of questions ought to be refused, which "
  "is where governance wins outright; and answers must be auditable. This is "
  "the profile of regulated enterprise documentation — product support, "
  "compliance, and safety procedures — rather than open-domain knowledge. "
  "Financial services is a concrete instance: supervisory regimes such as "
  "FINRA's and the SEC's require firms to evidence how an answer was "
  "produced, and an ungoverned pipeline retains no decision-level record to "
  "produce; a governed pipeline emits that record for every question, "
  "including refusals. It is also the setting nearest our abstention-heavy "
  "corpus, whose concept graph is dominated by financial-services entities.")

P([("B. The economics of build-once, serve-many", {"bold": True,
    "italic": True})], before=4, after=4)

P("Total cost separates into one build per corpus and a marginal cost per "
  "query: T = D\u00b7C_build + n\u00b7C_query. The full DelucionQA benchmark — 912 "
  "questions under nine configurations — was served and judged for $222 on a "
  "$498 build, about 2.7 cents per judged answer-pair; the two additional "
  "corpora cost under $45 combined. The whole evaluation cost roughly $765 on "
  "commodity APIs. At serve time, enforcement itself is nearly free: the "
  "Reference Monitor accounts for under 1% of per-question latency, which is "
  "dominated by the pipeline's LLM calls (signature extraction alone is "
  "58–93% of stage time).")

P("The benchmarks pair each question with its own source documents — close "
  "to one document, one question, one answer. Enterprise use differs in both "
  "directions. A deployed corpus is queried by many questions per document "
  "over its life, so the build cost amortises further than measured here: n "
  "grows while the build is paid once. And deployed retrieval searches the "
  "whole corpus, distractors included, where the benchmark's evidence scoping "
  "deliberately isolated authorisation from retrieval difficulty; measuring "
  "governance under open-corpus retrieval is future work.")

P("The design alternative — rebuilding the governed index per question — was "
  "rejected at design time: at hours per question it cannot reach benchmark "
  "scale, and it pays the build cost n times instead of once. Governance, on "
  "this evidence, is an affordable property: the expensive parts of a "
  "governed pipeline are the same LLM calls an ungoverned pipeline already "
  "makes.")

P([("C. Position among governed systems", {"bold": True, "italic": True})],
  before=4, after=4)

P("Knowledge graphs enter RAG systems before generation, to improve retrieval "
  "context, or after generation, to verify outputs. GovernRAG occupies a third "
  "position: authorisation of the evidence admitted to generation. The "
  "positions differ in what they can evidence. A post-generation validator "
  "certifies that an output was checked; it does not control which evidence "
  "the model consumed, and its audit record begins after generation. "
  "Pre-admission authorisation controls consumption itself and records every "
  "admit and drop decision before an answer exists — the form of "
  "decision-level record that evidentiary regimes in regulated settings "
  "request. The comparison with prior governed systems is therefore "
  "architectural rather than competitive: post-generation validators such as "
  "CogniGraph and SITL gate at a different pipeline position, their code and "
  "benchmark are not available for a live baseline, and this study reports "
  "the per-level frontier that any single operating point sits on. Within "
  "this study, Constrained-F1 spans 0.080–0.350 for the contained "
  "refuse-everything policies to 0.566–0.668 for the best governed "
  "configurations — the scale on which the within-system metric should be "
  "read; no cross-benchmark comparison is made.")

P([("VII. THREATS TO VALIDITY AND REPRODUCIBILITY", {"bold": True, "size": 13,
    "color": NAVY})], before=10, after=8)

P([("A. Threats to validity", {"bold": True, "italic": True})], after=4)

P("Judge validity. Both judges are drawn from one model family; the run-1 "
  "dual-judge study bounds within-family variation (κ = 0.681 on jointly "
  "graded answers), but a cross-family check is future work. The dual-judge "
  "comparison covers run 1 only; runs 2 and 3 carry single-judge scoring and "
  "point estimates, with bootstrap intervals at those sample sizes pending. "
  "The faithfulness ceiling may partly reflect adherence-judging leniency on "
  "short cited answers — a pre-registered caveat; a discriminant check is "
  "future work.")

P("Generalisation. Claims for HAGRID and ExpertQA are scoped to the selected "
  "subsets; they probe the frontier's shape and are not population estimates. "
  "The ontology-fit observation rests on three corpora, and aligned share "
  "co-varies with concept-graph size at N = 3, so the two cannot be "
  "separated; its out-of-sample test is future work. Each run was executed "
  "once; no seed replication was performed.")

P("Instrumentation. The citation vocabulary covers chunks but not triplets; a "
  "triplet-level tag is future work. Per-question latency is reported as "
  "amortised per-batch wall-clock, not per-individual-question measurement. "
  "Two serving models were withdrawn by the provider mid-study; every "
  "withdrawal and repoint is a dated entry in the public deviation log, "
  "pushed before the affected step ran.")

P([("B. Reproducibility", {"bold": True, "italic": True})], before=4, after=4)

P("The pre-registration (hypotheses, metrics, stopping rule), the deviation "
  "log, the selection code and lists, and the per-run archives with SHA-256 "
  "manifests are public [anonymised repository link — resolved at W6]. Every "
  "reported number recomputes from the sealed evaluation logs under the "
  "metric definitions of Section IV; models are pinned by exact identifier. "
  "The sealed archives permit re-judging without re-serving, and the Q5 "
  "decision logs permit audit reconstruction without re-running the system.")

P([("Reviewer notes (not part of the manuscript)", {"bold": True, "size": 11,
    "color": NAVY})], before=10, after=4)
for t in [
 "Length: §VI ~430 words + §VII ~300 words ≈ 1.05 pp two-column — within the combined 1.0 pp budget once trimmed at W6 if needed; trim candidates: VI.A's final sentence (repeats V.F), VII.B's last sentence.",
 "All numbers ledger-verified: cost figures are sealed-artifact quotations ($498/$222/<$45/≈$765, 2.7¢ per pair — spend screenshots + manifests); Q5 <1% and 58–93% from T2 timing extraction; the rest from §V.",
 "VI.B states the rejected per-question-rebuild alternative WITHOUT naming Paper 1, per the locked policy ('hours per question' — master says ~3 h/question; kept vague to avoid a traceable self-reference).",
 "VI.C follows the spine's CF1 guardrail verbatim: no cross-benchmark comparison; 'the curve their operating points sit on' framing.",
 "§VII.A folds in: your approved citation-vocabulary one-liner; the leniency caveat; model-withdrawal disclosure as one factual sentence.",
 "DECISION for review: §VII currently omits the 238-vs-234 auditability-denominator note and the serve-map folder rotation (both ledger 'no action' items) — recommend keeping them out of the paper (internal bookkeeping), on record in the ledger.",
]:
    P([("– ", {}), (t, {"size": 10})], after=3)

doc.save(OUT)
print("saved", OUT)
