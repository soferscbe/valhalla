"""Build the student completion template from Annexure I; use bundled python-docx."""
from pathlib import Path
from io import BytesIO
import json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION_START
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Annexure-I_Format and Guidelies for submission of Project (1).docx'
OUT=ROOT/'report/ProductLens_Student_Report_Template.docx'
d=Document(SOURCE)
logos=[r.target_part.blob for r in d.part.rels.values() if 'image' in r.reltype]
# All source body slots are blank/example material; retain source package styles/resources.
for child in list(d._element.body):
    d._element.body.remove(child)
sect=OxmlElement('w:sectPr');d._element.body.append(sect)
for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
    if name not in d.styles:d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
    s=d.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0)
    s.font.underline=False;s.paragraph_format.line_spacing=1.5
    s.paragraph_format.space_after=Pt(6)
    s.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    s._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Times New Roman')
    pp=s._element.find(qn('w:pPr'))
    if pp is not None:
        for node in list(pp):
            if node.tag==qn('w:pBdr'):pp.remove(node)
d.styles['Title'].font.size=Pt(16);d.styles['Title'].font.bold=True
d.styles['Heading 1'].font.size=Pt(14);d.styles['Heading 1'].font.bold=True
d.styles['Heading 2'].font.italic=True;d.styles['Heading 2'].font.bold=False
for name in ['Heading 1','Heading 2','Caption']:
    d.styles[name].paragraph_format.keep_with_next=True
    d.styles[name].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT

def settings(s,fmt='decimal',start=None):
    s.page_width=Inches(8.2677);s.page_height=Inches(11.6929)
    s.top_margin=s.bottom_margin=Inches(1);s.left_margin=s.right_margin=Inches(.75)
    s.header_distance=s.footer_distance=Inches(.5)
    s.footer.is_linked_to_previous=False
    p=s.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');p._p.append(field)
    num=OxmlElement('w:pgNumType');num.set(qn('w:fmt'),fmt)
    if start is not None:num.set(qn('w:start'),str(start))
    s._sectPr.append(num)
settings(d.sections[0],'lowerRoman',1);d.sections[0].different_first_page_header_footer=True

def p(text='',style=None):return d.add_paragraph(text,style)
def center(text='',style=None):
    a=p(text,style);a.alignment=WD_ALIGN_PARAGRAPH.CENTER;return a
def page(title):
    d.add_page_break();p(title,'Heading 1')
def prompt(text):
    a=p('STUDENT WRITING REQUIRED: '+text);a.runs[0].italic=True
    return a
def table(caption,headers,rows,widths=None):
    center(caption,'Caption')
    t=d.add_table(rows=1, cols=len(headers));t.autofit=False
    t.alignment=1
    if widths:
        for col,w in zip(t.columns,widths):col.width=Inches(w)
    for c,txt in zip(t.rows[0].cells,headers):c.text=txt
    for row in rows:
        for c,txt in zip(t.add_row().cells,row):c.text=str(txt)
    for i,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
        if i==0:trpr.append(OxmlElement('w:tblHeader'))
        for j,c in enumerate(row.cells):
            if widths:c.width=Inches(widths[j])
            cp=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');b.append(el)
            cp.append(b)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8E8E8' if i==0 else 'FFFFFF');cp.append(shade)
            for a in c.paragraphs:
                a.paragraph_format.space_before=Pt(4);a.paragraph_format.space_after=Pt(4)
                a.paragraph_format.line_spacing=1.5;a.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for r in a.runs:r.font.size=Pt(12);r.bold=(i==0)
    p()
    return t

TITLE='Design and Evaluation of an Explainable AI-Assisted Product Intelligence System for Evidence-Based SaaS Feature Prioritisation'
center(TITLE,'Title')
center('Student completion template')
p()
center('A Project Report submitted by')
center('Sofers Paul Durai Alexander')
center('Roll Number M24SME2042')
p()
center('in partial fulfillment of the requirements for the award of the degree of')
center('Master of Business Administration Technology')
center('Faculty Mentor: Prof. Deepak Saxena')
p()
if logos:
    center().add_run().add_picture(BytesIO(logos[0]),width=Inches(.85))
center('Indian Institute of Technology Jodhpur')
center('School of Management & Entrepreneurship')
center('November 2026')
page('DECLARATION')
prompt('Confirm the declaration wording with your mentor, including the degree name and the permitted disclosure of AI assistance. Insert only a declaration that truthfully describes your work. The supplied Annexure sample names unrelated degrees; do not copy those placeholders.')
p('Student: Sofers Paul Durai Alexander\nRoll Number: M24SME2042\nFaculty Mentor: Prof. Deepak Saxena').alignment=WD_ALIGN_PARAGRAPH.LEFT
p('Signature: ____________________\nDate: ____________________').alignment=WD_ALIGN_PARAGRAPH.LEFT
p('No declaration or signature has been completed on the student’s behalf.')
page('ABSTRACT')
prompt('Write one paragraph of no more than 150 words after completing your analysis. Include the problem, DSR artefact, synthetic-data evaluation, principal results and a bounded conclusion. Avoid claiming proven business benefit, PM productivity or universal ranking correctness.')
p('Evidence to select from: 1,500 synthetic records; 293 customers; held-out unique-text theme ARI 0.6065; duplicate precision 0.9615 and recall 0.4717; 27 ranking candidates with 14 initially scorable; full evidence coverage; material sensitivity to missing account values.')
page('CONTENTS')
contents=[('1. INTRODUCTION',1),('2. LITERATURE AND METHODOLOGY',2),('3. SYSTEM DESIGN',3),('4. EVALUATION RESULTS',4),('4.1 Data robustness',5),('5. DISCUSSION AND LIMITATIONS',6),('6. CONCLUSIONS',7),('REFERENCES',8)]
for title,num in contents:
    a=p(f'{title}\t{num}');a.paragraph_format.tab_stops.add_tab_stop(Inches(6.3),WD_ALIGN_PARAGRAPH.RIGHT)
p('Update the contents and page numbers after replacing all student-writing prompts. This template is not a submission-ready report.')
s=d.add_section(WD_SECTION_START.NEW_PAGE);settings(s,'decimal',1);s.different_first_page_header_footer=False
p('1. INTRODUCTION','Heading 1')
p('Approved research question: Can an explainable AI-assisted Product Intelligence system improve the consistency, efficiency and use of customer evidence in SaaS feature prioritisation when compared with conventional prioritisation methods?')
reflection=(ROOT/'report/student_reflection.md').read_text().strip().split('\n\n')
for paragraph in reflection[:2]:p(paragraph)
p('1.1 Objectives and scope','Heading 2')
p('Proposal objectives: semantic similarity and duplicate detection; evidence-grounded opportunity grouping; customer/business/urgency/trend/effort analysis; transparent scoring; comparison with votes, fixed weighted benefit and a RICE-style proxy; human accept/override decisions and history.')
prompt('Explain which objectives the artefact demonstrates and which improvement claims remain untested. Refer to the explicit evaluation limits in Section 5. Do not describe synthetic records as actual customer outcomes.')
p('Application: ProductLens AI. The deployed demonstrator and source are available at the links below.')
p('https://valhalla-arkjg4bdxtfmm3d9z55dwu.streamlit.app/')
p('https://github.com/soferscbe/valhalla')
page('2. LITERATURE AND METHODOLOGY')
p('Reading map: Peffers et al. provide a Design Science Research process [1]. Sentence-BERT supplies background on semantic sentence representations [2], while the actual MiniLM model is documented separately [3]. Intercom describes the original RICE framework [4]. Scikit-learn documents clustering evaluation measures [5].')
prompt('Read these sources and write a critical synthesis: what does each support, what differs in ProductLens, and what product-management evidence is still missing? This reading map is not a completed literature review.')
p('2.1 Research design','Heading 2')
p('The project follows the approved DSR direction: problem identification, objectives, design/development, demonstration, evaluation and communication. Application tests establish executed behaviour; synthetic experiments describe grouping and ranking properties; neither substitutes for a real-user utility study.')
p('2.2 Data and evaluation separation','Heading 2')
p('Generator v1.0.0, seed 42, supplies 500-row development/semantic and 1,500-row comparison bundles. Labels remain separate from model inputs. Whole request families and customers are split between tuning and held-out evaluation; vocabulary still comes from one authored catalog. The 1,500-row ranking set is not an independent semantic holdout.')
p('Frozen thresholds are 0.20 for opportunities and 0.55 for candidate duplicates. They were selected on tuning data and not changed after holdout. Clear records support single-theme metrics; 38 ambiguous/overlapping held-out records remain processed but excluded from those metrics.')
page('3. SYSTEM DESIGN')
p('3.1 Evidence pipeline','Heading 2')
p('CSV/XLSX → validation → unique normalized feedback text → pinned MiniLM embeddings → complete-linkage cosine groups → account/subgroup aggregation → auditable scoring → human review and immutable snapshot.')
p('The ranking formula does not use an LLM. TF-IDF terms and an original medoid request describe candidate groups. Human inspection is needed because a group can contain distinct or overlapping needs.')
p('3.2 Scoring contract','Heading 2')
p('Reach and ARR divide by their candidate-set maxima. Urgency and alignment ratings normalize as (rating − 1) / 4. The default normalized weights are 0.30, 0.30, 0.20 and 0.20. Eqn. (3.1) defines the auditable priority score; weights sum to one.')
a=p();a.paragraph_format.tab_stops.add_tab_stop(Inches(3.3),1);a.paragraph_format.tab_stops.add_tab_stop(Inches(6.7),2)
a.add_run('\tPriority = 100 × Σ(weight × factor) / effort\t(3.1)')
p('ARR is resolved once per customer globally and counted once per opportunity. Ratings average distinct assessments per customer, then customers equally. Effort is the sum of maximum known effort within each duplicate subgroup. Unknown active factors or subgroup effort leave the score unavailable. Synthetic units are USD ARR and person-days.')
p('3.3 Human decisions and deployment','Heading 2')
p('Accept/defer/manual-priority decisions require a reason and preserve the computed ranking. PostgreSQL stores append-only events with immutable evidence/strategy snapshots. Workspace bearer keys isolate history; reviewer labels are self-reported. SQLite supports local use. Cloud mode requires PostgreSQL and rejects local fallback. This is a research demonstrator, not production authentication.')
page('4. EVALUATION RESULTS')
p('Table 4.1 reports the frozen held-out semantic evaluation: 250 records, including 212 clear rows and 56 unique clear texts. These are agreement measures on synthetic annotations, not business-priority accuracy.')
table('Table 4.1: Held-out semantic results',['Measure','Value'],[['Unique-text theme ARI','0.6065'],['Unique-text theme NMI','0.8282'],['Duplicate-pair precision','0.9615'],['Duplicate-pair recall','0.4717'],['Duplicate-pair F1','0.6329'],['Row-pair F1 excluding identical text pairs','0.5040']],[4.7,2.0])
p('The 1,500-row comparison yielded 27 candidates: 14 scored by strategy/effort and RICE-style, 20 by fixed benefit and 27 by votes. Table 4.2 uses the common 14 scorable candidates, with average ranks for ties and ID ordering for Top-K ties.')
table('Table 4.2: Agreement with the balanced strategy',['Comparator','Spearman','Top-5'],[['Votes','−0.3363','0/5'],['Fixed weighted benefit','−0.2442','0/5'],['RICE-style proxy','0.9385','4/5']],[3.5,1.6,1.6])
p('Evidence coverage was 1,500/1,500 IDs. Local grouping took 1.8823 seconds and aggregation/scoring/comparison 0.2744 seconds in the recorded run. No manual time baseline or participant study was conducted.')
page('4.1 Data robustness')
# Subsection format overrides the page helper main-heading style.
d.paragraphs[-1].style=d.styles['Heading 2']
p('Five diagnostics were specified before execution on 11 November. Table 4.3 reports both score coverage and retention of the original Top-5. Grouping was rerun for row order and repetition; it stayed fixed for business-signal changes.')
table('Table 4.3: Predeclared data perturbation outcomes',['Scenario','Scored / 27','Base Top-5 retained'],[['Row permutation','14','5/5'],['Twenty repeated account records','14','5/5'],['ARR uncertainty ±20%','14','5/5'],['Effort uncertainty ±20%','14','4/5'],['ARR absent for 30/293 accounts','1','0/5']],[3.7,1.4,1.6])
p('The base run reproduced the saved ranking assignments and scores within 1e-10. Repetition left customer-level factors and strategy scores unchanged. Effort uncertainty produced Spearman 0.9912 on 14 candidates. Missingness left only one common candidate: Spearman was undefined and agreement was 1/1. That small-intersection agreement must not be interpreted as stability.')
p('Eight earlier ±20% weight changes retained the Top-5. Enterprise and reach emphasis each retained 4/5. Weight stability does not imply robustness to incomplete evidence.')
p('All robustness scenarios preserved exact source-ID coverage. Only one seeded draw per uncertainty scenario was tested; no sampling confidence interval or general stability probability is estimated.')
prompt('Explain what these results tell you about evidence collection and engineering estimates. Distinguish demonstrated invariance from strategic disagreement and sensitivity to missing information.')
page('5. DISCUSSION AND LIMITATIONS')
prompt('Write your interpretation of the research question using the evidence below. Discuss implications for product managers, challenge the assumptions, and state what further study would be needed. Do not claim the project proves improved human decisions.')
table('Table 5.1: Research claims and available evidence',['Question aspect','Evidence boundary'],[['Consistency','Deterministic calculations, row-order and repeated-account invariance demonstrated for tested fixtures. No comparison of human decision consistency.'],['Efficiency','Local processing times recorded. No measured manual workflow or end-to-end PM time savings.'],['Customer evidence','Exact input-ID traceability and auditable calculations demonstrated. No user comprehension or adoption measurement.']],[1.6,5.1])
p('Principal limitations: synthetic authored vocabulary; missed paraphrases and broad over-merging; single-group assignment for multi-intent records; proxy effort/impact; shared effort denominator with RICE; candidate-set normalization; incomplete score coverage; sensitive missing-data policy; no independent real-world or participant utility evaluation.')
p('Hosted verification covered sample/CSV/XLSX input, real grouping/scoring, weight changes, PostgreSQL save, workspace isolation, fresh-session recovery and recovery after an owner-reported reboot. The user confirms Data API disabled. Hosted invalid input was rejected with a required-column error. Hosted assumptions/key downloads remain incompletely verified; an assumptions-download attempt timed out. Concurrency and production operations were not tested.')
page('6. CONCLUSIONS')
prompt('Answer the approved question in your own words. Separate successful construction/demonstration from evidence of improvement. Explain why transparent trade-offs, preserved evidence and retained human judgment matter, without asserting a universally correct ranking.')
p(reflection[2])
prompt('Acknowledge assistance in the form permitted by your mentor/institute. Complete the declaration only when it truthfully represents the work and required disclosures.')
p('6.1 Future work','Heading 2')
p('Evidence-supported candidates for further work: independently collected and annotated feedback; multi-intent/group-review improvements; engineering-validated effort; declared alternative missingness policies; structured PM evaluation; verified authentication; operational/concurrency testing. These are proposals, not completed features or results.')
p('Completion checklist: replace every student-writing prompt; verify all facts against experiment outputs; confirm mentor/declaration requirements; write a ≤150-word abstract; refresh contents; check citation order; inspect all final PDF pages; submit the individual PDF to the faculty mentor by 15 November 2026.')
page('REFERENCES')
refs=[
'[1] K. Peffers, T. Tuunanen, M. A. Rothenberger, and S. Chatterjee, “A design science research methodology for information systems research,” Journal of Management Information Systems, vol. 24, no. 3, pp. 45–77, 2007, doi: 10.2753/MIS0742-1222240302.',
'[2] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using Siamese BERT-networks,” in Proc. EMNLP-IJCNLP, 2019, pp. 3982–3992, doi: 10.18653/v1/D19-1410.',
'[3] Sentence Transformers, “all-MiniLM-L6-v2,” Hugging Face, model card. Accessed: Nov. 11, 2026. [Online]. Available: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2',
'[4] S. McBride, “RICE: Simple prioritization for product managers,” Intercom, Jan. 5, 2018. Accessed: Nov. 11, 2026. [Online]. Available: https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/',
'[5] Scikit-learn developers, “Clustering performance evaluation,” scikit-learn 1.9.1 documentation. Accessed: Nov. 11, 2026. [Online]. Available: https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation']
for r in refs:p(r)
d.core_properties.title=TITLE;d.core_properties.subject='Student completion template with verified project evidence'
d.core_properties.author='';d.core_properties.last_modified_by=''
OUT.parent.mkdir(exist_ok=True);d.save(OUT)
print(OUT)
