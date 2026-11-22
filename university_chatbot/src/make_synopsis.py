import json, pathlib, copy
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_COLOR_INDEX
ROOT = pathlib.Path(__file__).resolve().parent.parent
im = json.load(open(ROOT/"models/intent_metrics.json")); sm = json.load(open(ROOT/"models/system_metrics.json"))
d = Document("/mnt/user-data/uploads/Project_Synopsis_Template.docx")
P = d.paragraphs

def setp(p, lines, size=None):
    for r in p.runs[1:]: r._r.getparent().remove(r._r)
    r = p.runs[0]; r.italic = False; r.text = lines[0]; r.font.color.rgb = RGBColor(0x22,0x22,0x22)
    if size: r.font.size = Pt(size)
    for ln in lines[1:]:
        r2 = p.add_run(); r2.add_break(); r2.add_text(ln); r2.font.name = r.font.name; r2.font.size = r.font.size; r2.italic = False; r2.font.color.rgb = RGBColor(0x22,0x22,0x22)
setp(P[5], ["Who: University students (and the helpdesk staff who serve them). What: students repeatedly ask the same questions about admissions, timetable, fees, exams, hostel, library and complaints, and wait hours or days for answers during peak periods (admission, fee and result seasons). When/where: through e-mail, phone and walk-ins at the university helpdesk, mostly outside office hours. Why it matters: slow or inconsistent answers frustrate students, overload staff, and delay urgent cases such as harassment reports. How: an AI chatbot answers routine FAQs instantly and detects frustrated, urgent or unanswerable cases to hand over to a human agent."])
setp(P[7], ["I built UniBot, a Python/Flask chatbot with a web chat interface. A TF-IDF + Logistic Regression model classifies each message into 7 student-support intents (plus out-of-scope), a TF-IDF cosine-similarity retriever returns the best answer from a 57-entry FAQ knowledge base, and VADER sentiment analysis plus rules (explicit request for a human, safety keywords, repeated confusion) trigger escalation to a human agent with a ticket and a clear red 'ESCALATED' badge. Privacy is built in: PII is redacted from messages, raw text is never stored (only anonymous metadata in SQLite), and students can opt out at any time."])
# architecture: insert two pictures
p9 = P[9]; setp(p9, ["Figure 1 – System block diagram and Figure 2 – DFD Level 0 (below)."])
for f, w in (("fig_architecture_block.png", 6.3), ("fig_dfd_level0.png", 6.3)):
    run = p9.add_run(); run.add_break(); run.add_picture(str(ROOT/"figures"/f), width=Inches(w))
setp(P[11], ["Frontend / UI:    HTML5 + CSS + JavaScript single-page chat (Flask templates); anonymous usage dashboard",
 "Backend / Logic:  Python 3, Flask REST API (/api/chat, /rate, /optout), NLTK (tokenising/stemming), regex-based PII redaction & rules",
 "Database:         SQLite (anonymous metadata only) + CSV FAQ knowledge base",
 "AI/ML Framework:  scikit-learn (TF-IDF, Logistic Regression), VADER sentiment, cosine-similarity retrieval",
 "Visualisation:    Matplotlib, Seaborn (EDA notebook), Jupyter",
 "Hardware:         None – runs on any laptop (CPU only, < 5 ms per reply)"])
setp(P[13], ["Dataset file name: dataset.csv (provided in project folder; cleaned version saved with 5 engineered columns)",
 "Number of rows:    500 chatbot sessions",
 "Number of columns: 6 original (11 after cleaning & feature engineering)",
 "Key columns (list 5): session_id, user_query_type, intent, confidence_score, escalated (plus user_rating)",
 "Any additional data collected: Yes – 288 hand-written labelled student utterances (8 classes) and a 57-entry FAQ knowledge base (sample content), because dataset.csv contains no message text."])
setp(P[15], [f"Metric 1: Intent classification accuracy — {im['test_accuracy']*100:.1f}% (macro-F1 {im['test_macro_f1']:.2f}) on {im['n_test']} unseen held-out utterances",
 f"Metric 2: Response time — mean {sm['latency_ms']['mean']} ms, 95th percentile {sm['latency_ms']['p95']} ms per reply",
 f"Metric 3: Escalation detection — F1 {sm['escalation']['f1']:.2f} (precision {sm['escalation']['precision']:.2f}, recall {sm['escalation']['recall']:.2f}) on {sm['escalation']['n']} labelled test messages; FAQ top-1 retrieval accuracy {sm['faq_retrieval']['top1_accuracy']*100:.0f}%",
 "Business value achieved: routine questions answered instantly (24x7), unhappy/urgent students are routed to humans with a ticket, and no personal data is retained – reducing helpdesk load while keeping humans in the loop. (Results come from a small self-authored test set; see report for limitations.)"])
setp(P[17], ["Challenge 1: dataset.csv has no message text, so a text classifier cannot be trained from it → Resolution: authored a labelled utterance corpus (288 messages), split train/test BEFORE augmenting to avoid leakage, and used dataset.csv for EDA and policy design.",
 "Challenge 2: EDA showed confidence is uncorrelated with escalation (rho = 0.04) so a confidence threshold alone is not a sound policy → Resolution: designed a multi-signal escalation policy (human request, sentiment, safety keywords, repeated confusion).",
 "Challenge 3: VADER flagged routine words such as 'charges' or 'mess' as negative sentiment → Resolution: neutralised domain words in the lexicon and re-tested for false positives."])
setp(P[19], ["1. Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
 "2. Hutto, C. J. & Gilbert, E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Proc. ICWSM-14.",
 "3. Salton, G. & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. Information Processing & Management, 24(5), 513–523.",
 "4. Government of India (2023). The Digital Personal Data Protection Act, 2023.",
 "5. Flask documentation – https://flask.palletsprojects.com (accessed 2026)."])
# highlight FILL IN placeholders in the table
for row in d.tables[0].rows:
    for c in row.cells:
        for p in c.paragraphs:
            for r in p.runs:
                if "[FILL IN]" in r.text: r.font.highlight_color = WD_COLOR_INDEX.YELLOW
out = ROOT/"Project_Synopsis_[YourName]_[RollNo].docx"; d.save(out); print(out)
