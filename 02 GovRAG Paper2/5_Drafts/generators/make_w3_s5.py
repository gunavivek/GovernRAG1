#!/usr/bin/env python3
# W3 — §V Results: review draft v1 for Vivek. Numbers verbatim from sealed
# frontier summaries (run1_rejudge = primary judge, run2_hagrid, run3_expertqa).
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

OUT = "/tmp/gr/W3_SectionV_Results_DRAFT.docx"
NAVY = RGBColor(0x1F, 0x4E, 0x79)
INK  = RGBColor(0x1A, 0x1A, 0x1A)
MUT  = RGBColor(0x55, 0x55, 0x55)
GRN  = RGBColor(0x1E, 0x6B, 0x34)

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

P([("W3 — §V FINAL v12 · 27 July 2026 · Table I config glosses added (Vivek) · ALL APPROVED: V.A–V.G; Table I keeps OntNU (Vivek); Table II hypothesis ledger added (Vivek) · V.C halluc figures restored with judge labels (S42e) · LEDGER FIXES 1–5 applied (Table I caption; V.G agreement label, leniency direction, H1 7.4; V.C halluc figure held out pending source) · V.A frontier terminology explained (pending on-ramp decision); V.B leakage corrected to primary-judge values (23.4→15.6→1.6–7.8%) with initial-judge robustness clause, S41 queued · not yet poured · every number "
    "verbatim from the sealed frontier summaries (primary judge): "
    "run1_rejudge / run2_hagrid / run3_expertqa E3 frontier_summary.csv",
    {"italic": True, "size": 9, "color": MUT})], after=14)

P([("V. RESULTS", {"bold": True, "size": 13, "color": NAVY})], after=8)

P([("A. The governance frontier", {"bold": True, "italic": True})], after=4)

P("Figure 2 plots the study's central object: the trade-off between how much "
  "the system answers and how well, traced as the governance dial turns — the "
  "risk–coverage frontier — on each corpus, with Table I reporting the headline "
  "operating points. Turning the dial from G0 to G2 moves every corpus in the "
  "same direction — coverage falls from 100% to 44.1% (DelucionQA), 16.6% "
  "(HAGRID), and 32.7% (ExpertQA), while the correct-refusal rate rises from "
  "40.6%, 42.3%, and 43.8% under the naive baseline to 78.1%, 76.9%, and 75.2% "
  "under G2-tier governance. The naive baseline's correct-refusal rates are not "
  "zero because an ungoverned model sometimes declines spontaneously; governance "
  "roughly doubles the rate and, unlike spontaneous declination, does so by "
  "declared policy. G2 is the strictest level at which all three corpora still "
  "answer; at G3 and G4, HAGRID and ExpertQA refuse every question, and only "
  "DelucionQA — the corpus whose concepts almost fully align with the reference "
  "ontology — continues to trade coverage for refusal quality (82.8% "
  "correct-refusal at G4).")

P([("B. What refusal quality costs", {"bold": True, "italic": True})],
  before=4, after=4)

P("The price of the frontier is false rejection: at the G2 tier, 54.3%, 84.7%, "
  "and 51.1% of answerable questions are refused on the three corpora. The cost "
  "is localised in the Reference Monitor's admission decisions — at G1 the "
  "monitor drops no chunks (0.0 per question), while at G2 and above it drops "
  "35.9 chunks per question on average on DelucionQA — and the drop pattern, "
  "not the answer model, is what separates the levels. Governance also "
  "suppresses parametric leakage: the share of unanswerable questions on which "
  "the model nonetheless asserts an answer agreeing with the benchmark's "
  "hallucinated reference falls from 23.4% (naive) to 15.6% (G1) to 1.6–7.8% "
  "(range across the seven G2-and-stricter configurations) on DelucionQA; the "
  "initial judge shows the same monotone fall (17.2% → 12.5% → 4.7–7.8%). G1 "
  "emerges as "
  "a nearly free operating point: for 7.5%, 22.1%, and 41.3% of coverage "
  "forgone, it adds citation discipline and the full audit trail.")

P([("C. Faithfulness is at ceiling in both arms", {"bold": True,
    "italic": True})], before=4, after=4)

P("Faithfulness — adherence of answered content to the supplied evidence — is "
  "at or above 0.98 for governed and naive arms alike on every corpus, under "
  "both judges (hallucination-on-answered: 0–0.7% under the primary judge, "
  "1.2–2.2% under the initial judge on run 1). We therefore make no "
  "hallucination-reduction claim: on gold-context benchmarks, where retrieval "
  "is scoped to the question's own source documents, there is no hallucination "
  "headroom for governance to recover. A pre-registered caveat applies in that "
  "TRACe-style adherence judging may be lenient on short cited answers. The "
  "measured value of governance on these benchmarks lies in refusal quality "
  "and auditability, not in faithfulness.")

P([("D. Auditability", {"bold": True, "italic": True})], before=4, after=4)

P("Citation resolvability is 97.7–100% of answered governed outputs across "
  "corpora and levels: every bracket citation in those answers resolves to "
  "evidence the monitor admitted. The remaining 1–2% are answers synthesised "
  "from admitted symbolic triplets, for which the citation vocabulary offers "
  "no tag; no cited identifier in the study failed to resolve to admitted "
  "evidence. Independently of citation formatting, the Q5 decision log is "
  "complete by construction — every admit and drop decision, the rule applied, "
  "and the evidence identity are recorded for every question, including "
  "refusals — so an auditor can reconstruct which evidence was admitted, which "
  "was dropped and under which rule, and which citations support each answer, "
  "from the logs alone, without re-running the system.")

P([("E. On the abstention-heavy corpus, governance beats the baseline",
    {"bold": True, "italic": True})], before=4, after=4)

P("The direction of the net governance effect follows the corpus's answerable "
  "share. On the answer-heavy corpora the naive baseline retains higher "
  "governance accuracy (82.7% vs 75.9% on DelucionQA; 79.1% vs 68.1% on "
  "HAGRID). On the abstention-heavy corpus the ordering reverses: on ExpertQA "
  "(70% of the evaluated set unanswerable), the governed G2-tier configuration "
  "beats the naive baseline on governance accuracy, 66.0% against 55.3%, and "
  "on Constrained-F1, 0.566 against 0.502. Governance answers fewer questions "
  "here, yet it scores higher overall: the gain in correctness outweighs the "
  "loss in coverage. This is not the trivial win of refusing everything: "
  "the study contains that policy empirically, since the refuse-all behaviour "
  "at G3/G4 scores Constrained-F1 of only 0.080 (HAGRID) and 0.350 (ExpertQA), "
  "while the governed configuration answers a third of the questions and "
  "reaches 0.566. Nor is it an artefact of the axis variant: plain G2 shows "
  "the same reversal (64.7%, 0.559). ExpertQA was selected under the "
  "complementary-strata design precisely to probe this regime; replication on "
  "further abstention-heavy corpora is future work.")

P([("F. Ontology fit anticipates the frontier (exploratory)", {"bold": True,
    "italic": True})], before=4, after=4)

P("The fraction of extracted corpus concepts that align to the reference "
  "ontology — 98.2% (DelucionQA), 47.2% (ExpertQA), 25.8% (HAGRID), a "
  "build-time statistic available before any question is served — orders how "
  "far the dial can be turned before coverage collapses. All three coverage "
  "curves fall as the dial tightens; they differ in where they stop. "
  "DelucionQA still answers at G4 (34.8% coverage). ExpertQA answers through "
  "the G2 tier (32.7% coverage) and reaches zero at G3. HAGRID retains only "
  "16.6% at G2, refusing 84.7% of its answerable questions, and reaches zero "
  "at G3 — in practice usable only to G1. The strictest usable level per "
  "corpus — G4, G2, G1 — follows the ontology-alignment ordering. We label "
  "this an observation, not a validated predictor: with three corpora the "
  "ordering could arise by chance, and aligned share co-varies with concept-"
  "graph size (3,781 / 703 / 298 nodes) at N=3. The observation has a "
  "mechanism — low alignment gives the predicate filter less to authorise, the "
  "same evidence-dropping that Section V-B localises — and its pre-registered "
  "out-of-sample test is future work. The axis variants supply a negative "
  "result of the same kind: on the single-domain corpus the ontology-"
  "conformance and domain-affinity filters could not be exercised at all "
  "(triplet retrieval starved; affinity degenerate at 1.0 for all 5,037 "
  "chunks), so the study also characterises when ontology-derived filters "
  "cannot act.")

P([("G. Judge sensitivity", {"bold": True, "italic": True})], before=4, after=4)

P("Every run-1 answer was graded by both judges — 8,208 pairs. Agreement is "
  "measured with Cohen's kappa, the standard chance-corrected statistic: "
  "κ = 0.681 on answers both judges graded (raw agreement 84.1%), rising to "
  "0.863 when refusals are included; values between 0.6 and 0.8 are "
  "conventionally read as substantial agreement. When the judges disagree, the "
  "disagreement has a direction: in 504 cases the primary judge accepted an "
  "answer the initial judge had rejected, and in 190 cases the reverse — the "
  "primary judge is the more generous grader. The disagreement concentrates at "
  "the permissive levels (net +17.9% on G0 and +14.4% on G1, against +1.5% at "
  "the G2 tier, +3.2% at G3, and −0.3% at G4): governed answers are graded "
  "more consistently than ungoverned ones. No finding in Table I reverses "
  "under either judge. One result is judge-sensitive in degree: H1, quality "
  "parity between G1 and the baseline. The accuracy gap is 3.4 points under "
  "the initial judge and 7.4 under the primary judge on DelucionQA (13.9 and "
  "13.3 points on the other two corpora), and the paired bootstrap gives "
  "−.018 [−.050, +.014] and −.065 [−.090, −.041] respectively. Near-parity "
  "therefore holds only on the in-ontology corpus, and its size depends on "
  "the judge. The full protocol and per-configuration tables are in the "
  "appendix.")

# ---- Table I ----
P([("TABLE I — Headline operating points (primary judge). Cov = coverage; "
    "Acc = accuracy on the answerable stratum (refusals counted as misses); "
    "Faith = faithfulness; cRef = correct-refusal "
    "rate; fRej = false-rejection rate; CF1 = Constrained-F1. Refuse-all rows "
    "show refusal metrics only. Level criteria are shown once in the first "
    "block and apply to all corpora; OntNU admits every concept status except "
    "unmapped.", {"italic": True, "size": 9, "color": MUT})],
  before=8, after=4)

rows = [
 ("DelucionQA (912 q; 7.0% unanswerable)", None),
 ("  G0 naive — ungoverned; query pipeline bypassed", "100.0", "85.9", "1.00", "40.6", "0.0",  "0.699"),
 ("  G1 Cited — \u22651 retrieved chunk; citation required", "92.5",  "78.4", "1.00", "42.2", "5.0",  "0.668"),
 ("  G2 Grounded — \u22651 authorised chunk + citation", "44.1",  "19.3", "1.00", "78.1", "54.3", "0.327"),
 ("  G2+OntNU — G2 + ontology filter (drops unmapped-concept evidence)", "44.5",  "19.6", "1.00", "75.0", "54.0", "0.326"),
 ("  G3 Strict — \u22651 authorised triplet + citation", "38.1",  "15.9", "1.00", "78.1", "60.7", "0.306"),
 ("  G4 Corrob — multiple triplets, or triplet + agreeing chunk", "34.8",  "14.4", "1.00", "82.8", "63.9", "0.298"),
 ("HAGRID (163 q; 16.0% unanswerable)", None),
 ("  G0 naive",      "100.0", "86.1", "1.00", "42.3", "0.0",  "0.661"),
 ("  G1 Cited",      "77.9",  "72.3", "1.00", "46.2", "17.5", "0.646"),
 ("  G2 Grounded",   "16.6",  "13.1", "1.00", "76.9", "84.7", "0.396"),
 ("  G2+OntNU",      "16.0",  "13.9", "1.00", "80.8", "84.7", "0.408"),
 ("  G3/G4 (refuse-all)", "0.0", "—", "—",   "100.0","100.0","0.080"),
 ("ExpertQA (150 q; 70.0% unanswerable)", None),
 ("  G0 naive",      "100.0", "82.2", "0.99", "43.8", "0.0",  "0.502"),
 ("  G1 Cited",      "58.7",  "68.9", "1.00", "50.5", "20.0", "0.535"),
 ("  G2 Grounded",   "32.7",  "40.0", "1.00", "75.2", "51.1", "0.559"),
 ("  G2+OntNU",      "33.3",  "44.4", "1.00", "75.2", "48.9", "0.566"),
 ("  G3/G4 (refuse-all)", "0.0", "—", "—",   "100.0","100.0","0.350"),
]
tbl = doc.add_table(rows=1, cols=7)
tbl.style = "Light Grid Accent 1"
hdr = tbl.rows[0].cells
for i, h in enumerate(["Config", "Cov %", "Acc %", "Faith", "cRef %", "fRej %", "CF1"]):
    hdr[i].text = h
    for pr in hdr[i].paragraphs:
        for r in pr.runs: r.font.size = Pt(9); r.font.bold = True
for row in rows:
    cells = tbl.add_row().cells
    if row[1] is None:
        cells[0].merge(cells[6])
        cells[0].text = row[0]
        for pr in cells[0].paragraphs:
            for r in pr.runs: r.font.size = Pt(9); r.font.bold = True
    else:
        for i, v in enumerate(row):
            cells[i].text = v
            for pr in cells[i].paragraphs:
                for r in pr.runs: r.font.size = Pt(9)

P([("TABLE II — Pre-registered hypothesis ledger (verdicts under the primary "
    "judge; H1 also shown under the initial judge).", {"italic": True,
    "size": 9, "color": MUT})], before=8, after=4)

h_rows = [
 ("H1 Quality parity on the answerable stratum (governed within 0.05 of naive)",
  "NOT SUPPORTED (primary); borderline (initial, run 1)",
  "gap .034 initial / .074 primary / .139 / .133; bootstrap −.018 [−.050,+.014] / −.065 [−.090,−.041]"),
 ("H2 Faithfulness superiority (governed above naive)",
  "REFUTED",
  "both arms at ceiling ≥0.98 on every corpus"),
 ("H3 Selective abstention (correct refusal far above naive; coverage cost reported)",
  "SUPPORTED; pre-registered coverage-cost branch triggered",
  "correct refusal 75–78% vs 41–44%; false rejection 51–85% at G2; leakage 23.4→15.6→1.6–7.8%"),
 ("H4 Auditability (provenance + decision-log coverage near 100%)",
  "SUPPORTED",
  "citation resolvability 97.7–100% on every corpus; decision log complete by construction"),
]
t2 = doc.add_table(rows=1, cols=3)
t2.style = "Light Grid Accent 1"
h2c = t2.rows[0].cells
for i, h in enumerate(["Hypothesis", "Verdict", "Key numbers"]):
    h2c[i].text = h
    for pr in h2c[i].paragraphs:
        for r in pr.runs: r.font.size = Pt(9); r.font.bold = True
for row in h_rows:
    cells = t2.add_row().cells
    for i, v in enumerate(row):
        cells[i].text = v
        for pr in cells[i].paragraphs:
            for r in pr.runs: r.font.size = Pt(9)

P([("[Figure 2 near §V.A — Frontier_ThreeCorpora.png (sealed, 3_Figures / "
    "6_Results); inserted at pour.]", {"italic": True, "size": 10,
    "color": GRN})], before=10, after=12)

P([("Reviewer notes (not part of the manuscript)", {"bold": True, "size": 11,
    "color": NAVY})], after=4)
for t in [
 "Length: ~1,050 words + Table I + Figure 2 ≈ 2.0–2.1 pp two-column. If over at W6, V.B's G1 sentence and V.G's flip percentages are the trim candidates.",
 "All numbers re-verified against the three sealed frontier_summary.csv files today (primary judge = run1_rejudge for DelucionQA). Faithfulness rounded to 2 dp; G2+Aff DelucionQA 0.9949 → not shown (axis rows limited to OntNU, the best variant — DECISION: show all four axis variants or best-only?)",
 "Naive GA on answered-heavy corpora quoted in V.E as 82.7/79.1 vs governed 75.9/68.1 — from sealed governance_accuracy column (G0 .8268/.7914; G1 .7588/.6810).",
 "Table I shows G2+OntNU as the axis representative; HAGRID G2+OntConf (CF1 0.412) slightly beats OntNU (0.408) — flagged for your ruling on which variant Table I carries for HAGRID.",
 "Hypothesis ledger (H1–H4 outcomes): currently woven into prose (H1 in V.G, H2 in V.C, H3 in V.A/B, H4 in V.D). DECISION: add a compact ledger table, or leave prose-only?",
 "T1 disclosure sentence included verbatim in V.D as approved; §VII one-liner comes in W4.",
 "V.F node counts 3,781/703/298 and 5,037 chunks from spine v2.3 (sealed M-pipeline stats).",
]:
    P([("– ", {}), (t, {"size": 10})], after=3)

doc.save(OUT)
print("saved", OUT)
