# Student report completion

The local `ProductLens_Student_Report_Template.docx` is a structured completion aid, not a submission-ready report. It contains actual experiment tables and the student's three-paragraph reflection supplied on 11 November, retained verbatim. It follows the written Annexure requirements; those override inconsistent margins in the source example. The declaration is unsigned and unfinished. No generated prose is represented as independently authored by the student.

The university guideline states that reports are screened for plagiarism and AI-generated content with potential penalties. The student should confirm permitted assistance and disclosure with the mentor, write the abstract, literature synthesis, interpretation and conclusions, and review all technical descriptions. These are substantive remaining tasks, not a signature-only formality.

## Work in this order

1. Discuss the live app and bounded results with the mentor, especially synthetic validity and missing-ARR sensitivity. Confirm declaration wording and AI-assistance requirements.
2. Complete the marked writing slots in your own words. Read the references in `docs/VERIFIED_REFERENCES.md`; add sources only after verification. Explain metrics and their denominators, not merely their values. Avoid claims of measured PM improvement or real business impact.
3. Use `docs/DEMO_AND_VIVA.md` to rehearse and independently reproduce the demonstrated decisions. The evidence sources are `experiments/semantic_v1`, `ranking_v1` and `robustness_v1`.
4. Replace the template subtitle/prompts, update contents/pages and IEEE citation order, and write a single-paragraph abstract of at most 150 words. Confirm every table/figure is referenced and section-numbered, with table captions above and figure captions below.
5. Render the final Word file to PDF and visually inspect every page. Check A4, margins (1 inch top/bottom, 0.75 inch sides), Times New Roman12/1.5/justified text, 14-point bold uppercase section headings, italic subheads, Roman preliminaries (cover hidden but counted) and Arabic main pages. Student verifies/signs the truthful declaration and submits the final individual PDF to Prof. Deepak Saxena by 15 November 2026.

The builder is `tools/build_report_template.py`. It requires the user-supplied Annexure DOCX and private `report/student_reflection.md`; the original academic sources and the reflection are intentionally not published. Use the bundled document-authoring Python runtime or an isolated environment with python-docx. Do not rerun the template builder over an independently edited final report; save the final version under another filename.

Generated drafts and student writing stay local. The public repository contains technical evidence and generic completion guidance. No report has been submitted or sent to the professor.
