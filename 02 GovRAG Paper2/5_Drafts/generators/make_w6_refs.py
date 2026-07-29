#!/usr/bin/env python3
# W6 — final References section: IEEE-numbered [1]-[33], all verified/pinned.
# Pours into the shell's last placeholder + applies in-text citation fixes.
import copy
from docx import Document
from docx.shared import Pt, RGBColor

REFS = [
"H. Kumar, “CogniGraph: Governed graph-of-agents reasoning over knowledge graph topologies with semantic SHACL validation and Constrained F1 evaluation,” SSRN preprint 6837300, 2026.",
"V. Nadimuthu, A. Das, V. Soni, and A. P. Sheth, “Symbolic-in-the-loop: Leveraging knowledge graph engineering to ensure high-assurance generative artificial intelligence outcomes,” IEEE Internet Computing, 2026.",
"A. H. Jain, S. R. Yarrrabothu, N. K. Kande, and D. R. Kethireddy, “Governance-aware agentic retrieval-augmented generation with evidence abstention for reliable AI policy question answering,” in Proc. Int. Conf. Artificial Intelligence, Systems, and Emerging Technologies (ICAISET), Cairo, Egypt, 2026, pp. 1–6, doi: 10.1109/ICAISET66439.2026.11541329.",
"M. Singh, S. Pandey, S. K. Yadav, B. Gridhar, and V. M. Manikandan, “Korosuke: A principled framework for security-preserving contextual retrieval in enterprise knowledge systems,” in Proc. IEEE Int. Students’ Conf. Electrical, Electronics and Computer Science (SCEECS), Bhopal, India, 2026, pp. 1–6, doi: 10.1109/SCEECS68810.2026.11429793.",
"V. Noël, E. Y. Seidou, C. K. Capo-Chichi, and G. Amari, “HalluGraph: Auditable hallucination detection for legal RAG systems via knowledge graph alignment,” arXiv:2512.01659, 2025.",
"M. Kang, N. M. Gürel, N. Yu, D. Song, and B. Li, “C-RAG: Certified generation risks for retrieval-augmented language models,” in Proc. ICML, 2024.",
"N. Feng, Y. Sui, S. Hou, J. C. Cresswell, and G. Wu, “Response quality assessment for retrieval-augmented generation via conditional conformal factuality,” in Proc. SIGIR, 2025, doi: 10.1145/3726302.3730244.",
"V. Quach, A. Fisch, T. Schuster, A. Yala, J. H. Sohn, T. S. Jaakkola, and R. Barzilay, “Conformal language modeling,” in Proc. ICLR, 2024.",
"S. Tayebati et al., “Learning conformal abstention policies for adaptive risk management in large language and vision-language models,” arXiv:2502.06884, 2025.",
"A. Kamath, R. Jia, and P. Liang, “Selective question answering under domain shift,” in Proc. ACL, 2020.",
"J. Chen, J. Yoon, S. Ebrahimi, S. Arik, T. Pfister, and S. Jha, “Adaptation with self-evaluation to improve selective prediction in LLMs,” in Findings of EMNLP, 2023.",
"B. Wen et al., “Know your limits: A survey of abstention in large language models,” Trans. Assoc. Comput. Linguistics, vol. 13, 2025, doi: 10.1162/tacl_a_00754.",
"M. Knechtel and J. Hladik, “RBAC authorization decision with DL reasoning,” in Proc. IADIS Int. Conf. WWW/Internet (ICWI), 2008.",
"M. Valzelli, A. Maurino, and M. Palmonari, “A fine-grained access control model for knowledge graphs,” in Proc. 17th Int. Joint Conf. e-Business and Telecommunications (ICETE) – SECRYPT, 2020, pp. 595–601.",
"R. K. Saripalle, A. De La Rosa Algarin, and T. B. Ziminski, “Towards knowledge level privacy and security using RDF/RDFS and RBAC,” in Proc. IEEE 9th Int. Conf. Semantic Computing (ICSC), Anaheim, CA, USA, 2015, pp. 264–267, doi: 10.1109/ICOSC.2015.7050817.",
"L. Abdelrazek, L. Karaçay, and M. Orlic, “Authorization of knowledge-base agents in an intent-based management function,” arXiv:2510.19324, 2025.",
"V. Venkatesan, P. Saha, G. Vasudevan, G. Balakumar, and G. P. Balu, “Policy-aware RAG on the lakehouse: Lineage-driven retrieval over Apache Iceberg on S3 to reduce hallucination and cost,” in Proc. IEEE 16th Annu. Computing and Communication Workshop and Conf. (CCWC), Las Vegas, NV, USA, 2026, pp. 0291–0298, doi: 10.1109/CCWC67433.2026.11393771.",
"D. Edge et al., “From local to global: A Graph RAG approach to query-focused summarization,” arXiv:2404.16130, 2024.",
"K. Li et al., “Decoding on graphs: Faithful and sound reasoning on knowledge graphs through generation of well-formed chains,” in Proc. ACL, 2025.",
"Y. Ma, J. Xu, T. Wen, Q. Chen, J. Li, R. Wang, M. Li, S. Liang, and K. Qin, “Toward robust GraphRAG: Mitigating retrieval drift and hallucination from imperfect knowledge graphs,” arXiv:2603.14828, 2026.",
"P. Lewis et al., “Retrieval-augmented generation for knowledge-intensive NLP tasks,” in Proc. NeurIPS, 2020.",
"B. Bohnet et al., “Attributed question answering: Evaluation and modeling for attributed large language models,” arXiv:2212.08037, 2022.",
"Y. Li et al., “AttributionBench: How hard is automatic attribution evaluation?” in Findings of ACL, 2024.",
"T. Schreieder et al., “Attribution, citation, and quotation: A survey of evidence-based text generation with large language models,” arXiv:2508.15396, 2025.",
"J. Wallat et al., “Correctness is not faithfulness in RAG attributions,” arXiv:2412.18004, 2024.",
"R. Friel, M. Belyi, and A. Sanyal, “RAGBench: Explainable benchmark for retrieval-augmented generation systems,” arXiv:2407.11005, 2024.",
"M. Sadat et al., “DelucionQA: Detecting hallucinations in domain-specific question answering,” in Findings of EMNLP, 2023.",
"E. Kamalloo et al., “HAGRID: A human-LLM collaborative dataset for generative information-seeking with attribution,” arXiv:2307.16883, 2023.",
"C. Malaviya et al., “ExpertQA: Expert-curated questions and attributed answers,” in Proc. NAACL, 2024.",
"J. P. Anderson, “Computer security technology planning study,” U.S. Air Force, Tech. Rep. ESD-TR-73-51, 1972.",
"European Union, “Artificial Intelligence Act,” Regulation (EU) 2024/1689, 2024.",
"J. H. Saltzer and M. D. Schroeder, “The protection of information in computer systems,” Proc. IEEE, vol. 63, no. 9, pp. 1278–1308, 1975.",
"Anonymous authors, “GovernRAG: A governance manifest architecture with reference monitor mediation for auditable RAG,” under review, 2026. [Citation form updates on acceptance; author names withheld in the anonymised submission and restored at camera-ready.]",
"National Institute of Standards and Technology, “Artificial intelligence risk management framework (AI RMF 1.0),” NIST AI 100-1, Jan. 2023, doi: 10.6028/NIST.AI.100-1.",
]

shell = Document("GovernRAG_Paper2_IEEE_Shell.docx")

# 1) pour references into the last placeholder
target = None
for p in shell.paragraphs:
    if p.text.strip().startswith("[SHELL") and "References.docx" in p.text:
        target = p; break
assert target is not None, "references placeholder not found"
anchor = target._p
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph as DP
for i, ref in enumerate(REFS, 1):
    np_el = OxmlElement("w:p")
    anchor.addnext(np_el); anchor = np_el
    para = DP(np_el, target._parent)
    r = para.add_run("[%d] %s" % (i, ref))
    r.font.name = "Calibri"; r.font.size = Pt(9)
    para.paragraph_format.space_after = Pt(3)
target._p.getparent().remove(target._p)
print("references poured: %d entries" % len(REFS))

# 2) in-text fixes
fixes = [
 ("[Anderson; Saltzer–Schroeder — refs resolved at W6]", "[30], [32]"),
 ("Gunasekaran and Xu [x — under review]", "the architecture paper [33]"),
 ("adopt Constrained-F1 [1] for comparability", "adopt Constrained-F1 [1] for comparability"),
]
def fix_para(p, old, new):
    if old in p.text:
        # rebuild paragraph text in first run, preserving its formatting
        full = p.text.replace(old, new)
        for r in list(p.runs)[1:]:
            r._r.getparent().remove(r._r)
        p.runs[0].text = full
        return True
    return False

count = 0
for p in shell.paragraphs:
    for old, new in fixes:
        if old != new and fix_para(p, old, new): count += 1
print("in-text fixes applied:", count)

# 3) corpora citations in §IV.B
for p in shell.paragraphs:
    if p.text.startswith("We evaluate on three corpora from RAGBench"):
        t = p.text
        t = t.replace("three corpora from RAGBench, chosen", "three corpora from RAGBench [26], chosen")
        t = t.replace("DelucionQA (automotive troubleshooting;", "DelucionQA [27] (automotive troubleshooting;")
        t = t.replace("HAGRID (attributable", "HAGRID [28] (attributable")
        t = t.replace("ExpertQA —", "ExpertQA —")
        t = t.replace("and ExpertQA (expert-curated", "and ExpertQA [29] (expert-curated")
        for r in list(p.runs)[1:]:
            r._r.getparent().remove(r._r)
        p.runs[0].text = t
        print("corpora citations inserted")
        break

shell.save("GovernRAG_Paper2_IEEE_Shell.docx")
print("saved")
