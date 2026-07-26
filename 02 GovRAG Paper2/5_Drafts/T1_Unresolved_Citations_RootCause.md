# T1 — Root Cause: the 1.2–2.3% Uncited Governed Answers (DelucionQA, run 1)

*2026-07-26 · read-only analysis of sealed run-1 archives + frozen Q6 code · no
archive or frozen code modified. Disclosure wording approved by Vivek 2026-07-26.*

## Question
Sealed results report Cited = 97.7–99.9% per governed config on DelucionQA.
T1 (from Spine Topic 4c): root-cause the ≤2.3% gap.

## Verified facts (each reproduced from sealed artifacts)
1. Reproduction: using the study's own detector (`has_citations`,
   A0_GovRAG_Runner.py: `\[(?:CHNK_[^\]]+|RESIDUAL_[^\]]+)\]`) joined with judge
   verdicts (answered = MATCH/NO_MATCH), per-config Cited% reproduces the sealed
   table exactly: G1 100.0 · G2 98.8 · G3 97.7 · G4 98.1 · G2-axis 97.8–98.5%.
2. The gap = 49 uncited answers of 3,511 answered governed pairs (1.40%
   overall; 1.2–2.3% per config). All 49 at G2+; zero at G1.
3. Zero fabricated citations: of 3,462 cited answers, no citation identifier
   fails to resolve to the prompt's admitted evidence (0 bad ids).
4. Citation grammar (frozen Q6 prompt, lines 87/94): tags exist for text chunks
   ([CHNK_PRIMARY] block containing [CHNK_*id*] entries) and residuals
   ([RESIDUAL_X]); the TIER-1 symbolic-triplet list is rendered untagged — no
   triplet tag exists in the vocabulary.
5. Q6's citation check is advisory: missing citation → printed WARNING, answer
   returned (not blocked).
6. Discriminating test: 96% of uncited answers (47/49) carry Tier-1 attribution
   phrasing vs 28% of cited answers. Within the Tier-1-phrased class the tag is
   omitted in ~6% of answers (47/792); elsewhere ~0.1% (2/1,876).
7. Granularity note: ~38% of cited G2+ answers use the designed block-level
   [CHNK_PRIMARY] tag (contents enumerated in the Q5 decision log); G1 answers
   cite individual chunk ids (98.6% specific).

## Root cause (final wording, evidence-bounded)
The gap concentrates almost entirely (47/49) in answers synthesised from the
admitted symbolic-triplet tier, for which the citation vocabulary offers no
expressible tag; within that class the model omits the tag in ~6% of answers.
The affected answers remain governed and auditable via the Q5 logs. The failure
mode is omission, never fabrication. (2/49 cases outside the pattern are
disclosed as unexplained residue.)

## Falsified hypotheses (trail)
- Unresolvable citation keys (0 found) → falsified.
- Strict-regex artefact (multi-id brackets) → measurement artefact only.
- Empty [CHNK_PRIMARY] block in affected prompts → falsified (blocks populated).

## Approved manuscript disclosure (Vivek, 2026-07-26) — the ONLY public footprint
- §V, attached to the auditability result: "The remaining 1–2% are answers
  synthesised from admitted symbolic triplets, for which the citation vocabulary
  offers no tag; no cited identifier in the study failed to resolve to admitted
  evidence."
- §VII, one line: "The citation vocabulary covers chunks but not triplets; a
  triplet-level tag is future work."
This file is defence material; the investigation detail stays out of the paper.
