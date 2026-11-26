import json, pathlib
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = pathlib.Path(__file__).resolve().parent.parent; FIG = ROOT / "figures"
im = json.load(open(ROOT / "models/intent_metrics.json")); sm = json.load(open(ROOT / "models/system_metrics.json"))
dlg = json.load(open(ROOT / "docs/sample_dialogues.json"))
NAVY = RGBColor(0x1F, 0x3A, 0x6E)

d = Document()
sec = d.sections[0]; sec.page_width = Inches(8.27); sec.page_height = Inches(11.69)
for m in ("left_margin", "right_margin"): setattr(sec, m, Inches(1.0))
sec.top_margin = Inches(0.9); sec.bottom_margin = Inches(0.9)
st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11); st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.12
for name, size in (("Heading 1", 17), ("Heading 2", 13.5), ("Heading 3", 11.5)):
    h = d.styles[name]; h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = NAVY
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri"); h.element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); h.element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10); h.paragraph_format.space_after = Pt(5); h.paragraph_format.keep_with_next = True

def fld(par, instr):
    for t, txt in (("begin", None), (None, instr), ("separate", None), ("text", "1"), ("end", None)):
        r = par.add_run()
        if t in ("begin", "separate", "end"):
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); r._r.append(e)
        elif t is None:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)
        else: r.text = txt
def P(text="", bold=False, italic=False, align=None, size=None, color=None, after=None, style=None):
    p = d.add_paragraph(style=style); 
    if text:
        r = p.add_run(text); r.bold = bold; r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if align == "j": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p
def rich(text, style=None, align="j"):
    """**bold** inline markup"""
    p = d.add_paragraph(style=style); parts = text.split("**")
    for i, s in enumerate(parts):
        if s: r = p.add_run(s); r.bold = (i % 2 == 1)
    if align == "j": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p
def B(items):
    for t in items: rich(t, style="List Bullet", align=None).paragraph_format.space_after = Pt(2)
def N(items):
    for t in items: rich(t, style="List Number", align=None).paragraph_format.space_after = Pt(2)
H1 = lambda t: d.add_heading(t, 1); H2 = lambda t: d.add_heading(t, 2); H3 = lambda t: d.add_heading(t, 3)
fig_n = [0]; tab_n = [0]
def FIGURE(file, caption, w=6.0):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(FIG / file), width=Inches(w)); fig_n[0] += 1
    c = P(f"Figure {fig_n[0]}: {caption}", italic=True, align="c", size=9.5, after=10)
def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcPr.append(s)
def TABLE(rows, widths, caption=None, header=True, size=9.5):
    if caption:
        tab_n[0] += 1; c = P(f"Table {tab_n[0]}: {caption}", italic=True, align="c", size=9.5, after=3); c.paragraph_format.keep_with_next = True
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for j, w_ in enumerate(widths): t.columns[j].width = Inches(w_)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j); cell.width = Inches(widths[j]); cell.text = ""
            p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(1); p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(val)); r.font.size = Pt(size)
            if header and i == 0: r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); shade(cell, "1F3A6E")
            elif i % 2 == 0: shade(cell, "EEF2FA")
    d.add_paragraph().paragraph_format.space_after = Pt(4); return t
def PLACE(text):
    p = d.add_paragraph(); r = p.add_run(text); r.font.highlight_color = WD_COLOR_INDEX.YELLOW; return p

# ============ TITLE PAGE ============
P("", after=40)
P("HCLTech Career Shaper Programme", bold=True, align="c", size=14, color=NAVY, after=2)
P("III Year Industry Project  |  Academic Year 2025-26", align="c", size=11, after=40)
P("PROJECT REPORT", bold=True, align="c", size=13, after=14)
P("AI-Powered Chatbot for University Student Support", bold=True, align="c", size=26, color=NAVY, after=10)
P("Intent classification, FAQ retrieval and sentiment-aware escalation to a human agent", italic=True, align="c", size=12.5, after=40)
P("Project No. 30  ·  Domain: Digital-Data-AI / AIML  ·  Difficulty: Intermediate  ·  Duration: 4 weeks  ·  Individual project", align="c", size=10.5, after=30)
TABLE([["Learner name", "[FILL IN]"], ["Roll number", "[FILL IN]"], ["College / Campus", "[FILL IN]"], ["Mentor name", "[FILL IN]"], ["Submission date", "[FILL IN]"]], [2.0, 3.6], header=False, size=11)
for row in d.tables[-1].rows:
    for r in row.cells[1].paragraphs[0].runs: r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    for r in row.cells[0].paragraphs[0].runs: r.bold = True
d.add_page_break()

# ============ DECLARATION + ABSTRACT ============
H1("Declaration")
rich("I hereby declare that this project report titled **“AI-Powered Chatbot for University Student Support”** is my own work, carried out as part of the HCLTech Career Shaper Programme. The dataset used for exploratory analysis is the project-provided dataset.csv; the additional labelled utterances and FAQ knowledge base were created for this project. AI assistants were used for code and writing support and are disclosed in Appendix B. No personally identifiable information is stored by the system.")
P("Learner signature: ______________________      Date: ______________", after=20)
H1("Abstract")
rich(f"University helpdesks receive large volumes of repetitive questions about admissions, timetables, fees, examinations, hostels, libraries and complaints. Students wait for answers, staff are overloaded, and urgent cases – harassment reports, distressed students – can be buried in the queue. This project designs, implements and evaluates **Abes Assist**, an NLP chatbot for university student support. Abes Assist (i) removes personal information from every message, (ii) classifies the message into one of seven helpdesk intents plus an out-of-scope class using TF-IDF features and Logistic Regression, (iii) retrieves the best answer from a 57-entry FAQ knowledge base with cosine similarity, (iv) measures sentiment with VADER, and (v) applies a transparent multi-signal policy to **escalate to a human agent** when the student asks for one, is strongly dissatisfied, reports an incident or safety concern, or the bot repeatedly fails to understand.")
rich(f"Exploratory analysis of the 500-session dataset.csv showed an escalation rate of 7.8 %, mean satisfaction of 3.08/5 and, importantly, no relationship between model confidence and escalation (Spearman ρ = 0.04), which motivated a multi-signal escalation policy rather than a confidence threshold alone. On {im['n_test']} unseen held-out utterances the intent classifier reached **{im['test_accuracy']*100:.1f} % accuracy (macro-F1 {im['test_macro_f1']:.2f})**; FAQ retrieval reached {sm['faq_retrieval']['top1_accuracy']*100:.0f} % top-1 accuracy; the escalation policy scored F1 = {sm['escalation']['f1']:.2f} on {sm['escalation']['n']} labelled messages; and the mean response time is {sm['latency_ms']['mean']} ms. A privacy audit confirmed that no message text or PII is written to the database and that opt-out deletes session data. The report also states the limitations of the evaluation honestly – small, self-authored test sets and a dataset that appears to be synthetic.")
P("Keywords: chatbot, intent classification, FAQ retrieval, sentiment analysis, human escalation, NLP, privacy, DPDP Act", italic=True, size=10)
d.add_page_break()
H1("Table of Contents")
for t_, sub in [("Declaration", ""), ("Abstract", ""), ("1. Introduction", "Background and motivation · Scope · Report organisation"),
    ("2. Problem Statement and Objectives", "5W1H problem statement · Objectives and success criteria"),
    ("3. Approaches Considered and Tool Choices", "Chatbot approaches · Design decision · Technology stack"),
    ("4. Data Description and Exploratory Analysis", "Provided dataset · Quality and pre-processing · Additional data · Key EDA findings"),
    ("5. System Design", "Architecture · DFD Level 0 · Modules · Escalation policy · Storage and privacy · REST API"),
    ("6. Implementation", "Intent classification · FAQ retrieval · Sentiment · Privacy features · User interface · Running"),
    ("7. Testing and Results", "Intent classification · FAQ retrieval · Escalation · Latency · Privacy audit · Tests and samples · Summary"),
    ("8. Ethical Considerations and Compliance", ""), ("9. Challenges Faced and How They Were Resolved", ""),
    ("10. Limitations and Future Work", ""), ("11. Conclusion", ""), ("References", ""),
    ("Appendix A – Project structure and how to run", ""), ("Appendix B – Disclosure of AI tools", ""), ("Appendix C – Mapping to the 4-week plan", "")]:
    pp = P(t_, bold=True, after=0 if sub else 4); 
    if sub: P(sub, italic=True, size=9.5, after=4).paragraph_format.left_indent = Inches(0.3)
d.add_page_break()

# ============ 1 INTRO ============
H1("1. Introduction")
H2("1.1 Background and motivation")
rich("Universities serve thousands of students whose questions are largely predictable: “When is the fee deadline?”, “How do I download my hall ticket?”, “What are the library timings?”. Answering these by e-mail, phone or at a counter is slow and inconsistent, and demand is highly seasonal (admission, fee, result and exam periods). A well-designed chatbot can answer routine questions instantly at any hour and leave human staff free for the cases that really need them – complaints, exceptions, and sensitive situations.")
rich("However, a helpdesk chatbot that cannot recognise when to stop is worse than no chatbot: a frustrated student trapped in a loop of “I did not understand” replies, or a student reporting ragging who receives a generic FAQ link, is a failure of service. The core design question of this project is therefore not only “can the bot answer?” but also **“when must the bot hand over to a human, and can it do so visibly and safely?”**")
H2("1.2 Scope")
B(["A working prototype: web chat interface, REST API, NLP engine, FAQ knowledge base, anonymous metrics store.",
   "Seven helpdesk intents taken from dataset.csv – admissions, schedule, fees, exams, grievance, hostel, library – plus an out-of-scope class.",
   "Escalation to a human agent via sentiment analysis and safety rules, with a clear on-screen indicator and a ticket.",
   "Ethical safeguards required by the project brief: no PII retained beyond the session, opt-out, clearly indicated escalation.",
   "Exploratory data analysis, quantitative evaluation, and documentation."])
H2("1.3 Report organisation")
rich("Section 2 states the problem and objectives. Section 3 reviews approaches and justifies tool choices. Section 4 describes the data and EDA. Sections 5 and 6 present design and implementation. Section 7 reports results. Sections 8–10 cover ethics, challenges and limitations, and Section 11 concludes.")

# ============ 2 PROBLEM ============
H1("2. Problem Statement and Objectives")
H2("2.1 Problem statement (5W1H)")
TABLE([["Who", "University students, and the helpdesk staff who answer them."],
       ["What", "Repetitive questions about admissions, schedule, fees, exams, hostel, library and complaints are answered slowly and inconsistently; urgent or distressed cases are not prioritised."],
       ["When / where", "Round the clock through e-mail, phone and walk-ins; worst in admission, fee, exam and result seasons and outside office hours."],
       ["Why it matters", "Delays frustrate students, overload staff and can put students at risk when safety or wellbeing reports are not seen quickly."],
       ["How", "An AI chatbot that answers FAQs instantly, understands the topic of a message, senses frustration or urgency, and escalates to a human agent with a ticket – while protecting student privacy."]],
      [1.2, 5.2], caption="Problem statement in 5W1H form", header=False)
H2("2.2 Objectives and success criteria")
TABLE([["#", "Objective", "Measurable target", "Section"],
       ["O1", "Classify student messages by topic", "≥ 80 % accuracy on unseen utterances", "7.1"],
       ["O2", "Return the right FAQ answer", "≥ 90 % top-1 retrieval accuracy", "7.2"],
       ["O3", "Detect cases that need a human", "Recall ≥ 90 % on escalation test set (safety cases = 100 %)", "7.3"],
       ["O4", "Respond fast", "< 1 s per reply (target far below)", "7.4"],
       ["O5", "Protect privacy", "0 message texts / PII in storage; working opt-out", "7.5"],
       ["O6", "Make escalation visible", "Red badge + ticket ID shown to the student", "5.4, 7.6"]],
      [0.4, 2.3, 2.9, 0.8], caption="Objectives and how they are validated")

# ============ 3 RELATED WORK ============
H1("3. Approaches Considered and Tool Choices")
H2("3.1 Chatbot approaches")
rich("**Rule-based / keyword bots** are predictable but brittle: any wording not anticipated fails. **Retrieval-based bots** match the user’s question to a curated set of answers and are the dominant choice for institutional FAQ helpdesks, because every answer is authored and approved by the institution. **Generative bots** (for example DialoGPT-style language models) produce fluent text but can invent policies, dates and fees – an unacceptable risk when students act on the answer. Frameworks such as Rasa combine intent classification, entity extraction and dialogue management.")
H2("3.2 Design decision")
rich("This project adopts a **hybrid retrieval architecture**: a supervised intent classifier (topic and routing), a similarity-based FAQ retriever (the answer text), a sentiment model and a rule layer (escalation). The decision rests on four points: (1) *accuracy of content* – answers come only from approved FAQ text; (2) *small data* – only a few hundred labelled utterances are available, where TF-IDF with Logistic Regression is strong and stable; (3) *explainability* – every escalation lists the reason, which matters for audits; (4) *speed and cost* – replies take a few milliseconds on a CPU. Rasa and DialoGPT are listed in the brief as options; they are natural extensions (Section 10) but were not necessary to meet the objectives.")
H2("3.3 Technology stack")
TABLE([["Layer", "Choice", "Reason"],
       ["Language", "Python 3", "Rich ML ecosystem"],
       ["Web / API", "Flask", "Lightweight REST + templates (listed in brief)"],
       ["NLP features", "scikit-learn TF-IDF (word 1–2-grams + char 2–5-grams), NLTK Porter stemmer", "Robust to typos and spelling variants"],
       ["Intent model", "Logistic Regression (compared with SVM, Naive Bayes, Random Forest)", "Best held-out accuracy; gives probabilities for confidence"],
       ["Retrieval", "TF-IDF cosine similarity", "Deterministic, approved answers only"],
       ["Sentiment", "VADER with domain lexicon tweaks", "No training data required, works on short text"],
       ["Storage", "SQLite", "Zero-setup, stores anonymous metadata only"],
       ["Analysis", "Pandas, SciPy, Matplotlib, Seaborn, Jupyter", "EDA and statistical tests"]],
      [1.2, 2.9, 2.3], caption="Technology stack")

# ============ 4 DATA ============
H1("4. Data Description and Exploratory Analysis")
H2("4.1 The provided dataset")
rich("dataset.csv contains **500 chatbot sessions** with six columns. The data dictionary describes each field; the session identifier is anonymous (S0001–S0500). Notably, the file does **not** contain the text of the student’s question or the bot’s reply – only metadata about the interaction.")
TABLE([["Column", "Type", "Description"],
       ["session_id", "string", "Anonymous session identifier"],
       ["user_query_type", "categorical (5 levels)", "Query structure / complexity tier (query_type_1 … 5)"],
       ["intent", "categorical (7 classes)", "admissions, schedule, fees, exams, grievance, hostel, library"],
       ["confidence_score", "float", "Intent-classifier confidence, 0.602 – 0.999 (mean 0.797)"],
       ["escalated", "binary int", "1 = handed to human agent, 0 = handled by bot"],
       ["user_rating", "ordinal int", "Satisfaction on a 1–5 scale"]],
      [1.5, 1.6, 3.3], caption="Columns of dataset.csv")
H2("4.2 Data quality and pre-processing")
rich("The checks (see EDA notebook) found **no missing values, no duplicate rows or session IDs, and no out-of-range values**. Pre-processing therefore consisted of: trimming and lower-casing categorical text, converting types (category, int8), and adding five engineered features – confidence_band (4 bins), low_confidence (confidence < 0.70), satisfied (rating ≥ 4), dissatisfied (rating ≤ 2) and query_type_num. The cleaned file (11 columns) replaces dataset.csv in the data folder, and the data dictionary was extended with the new columns. The untouched originals are kept as dataset_raw.csv and data_dictionary_original.csv.")
H2("4.3 Additional data created for the NLP components")
rich(f"Because dataset.csv has no text, a chatbot cannot be trained from it. Two resources were therefore created: (1) a **labelled utterance corpus** of {im['n_base']} short student messages (36 for each of the seven intents plus 36 out-of-scope messages) in realistic phrasing, including typos and a few Hinglish queries; and (2) a **FAQ knowledge base** of 57 question–answer entries (7–8 per intent, each with 3 paraphrases). The FAQ content is **sample content** written in generic terms and flagged in the file; a real deployment must replace it with the university’s official policies.")
rich(f"To obtain an honest estimate, the utterances were split **before** augmentation: 25 % ({im['n_test']} messages, 9 per class) were set aside as an untouched test set, and only the remaining {im['n_train_base']} were augmented (prefixes, suffixes, typos, lower-casing) to {im['n_train_aug']} training examples.")
H2("4.4 Key findings from EDA")
FIGURE("fig_eda_intent_volume.png", "Sessions per intent – traffic is evenly spread (60 to 78 sessions each).", 4.6)
rich("**Intent volume.** Admissions and schedule are the most frequent topics (78 sessions each), followed by fees (77), exams (73), grievance and hostel (67 each) and library (60). No class dominates, so no re-sampling was needed.")
FIGURE("fig_eda_confidence_hist.png", "Distribution of confidence_score (mean 0.797; 26.8 % of sessions below 0.70).", 4.6)
rich("**Confidence.** Scores are spread almost uniformly between 0.60 and 1.00 (skew ≈ 0.01). More than a quarter of sessions fall below 0.70, which means a safety net is needed for uncertain predictions.")
FIGURE("fig_eda_escalation_by_intent.png", "Escalation rate by intent (overall 7.8 %, 39 of 500 sessions).", 4.6)
rich("**Escalation.** Fees (10.4 %) and library (10.0 %) show the highest escalation rates and exams (4.1 %) the lowest. A chi-square test finds the differences **not significant** (χ² = 3.30, p = 0.77): escalation does not depend on topic in this dataset.")
FIGURE("fig_eda_ratings.png", "Rating distribution and mean rating for bot-handled versus escalated sessions.", 6.0)
rich("**Satisfaction.** Ratings are nearly uniform (18–23 % per star), mean 3.08, and only 41.6 % of sessions are satisfied (≥ 4) while 37.8 % are dissatisfied (≤ 2). Escalated sessions have a slightly higher mean rating (3.46 versus 3.05), but the difference is not statistically significant (Mann-Whitney p = 0.09; only 39 escalations).")
FIGURE("fig_eda_confidence_vs_outcome.png", "Escalation and dissatisfaction by confidence band, and rating by confidence band.", 6.0)
rich("**Confidence versus outcomes.** Confidence is essentially uncorrelated with escalation (Spearman ρ = 0.043, p = 0.33) and rating (ρ = 0.034, p = 0.45). Surprisingly the escalation rate is *lower* in the lowest confidence band (6.0 %) than in the highest (9.2 %). **Design implication:** historical escalation did not follow model confidence, so a confidence-only rule would be a poor escalation policy. Abes Assist therefore uses several independent signals (Section 5.4).")
FIGURE("fig_eda_correlation.png", "Spearman correlation matrix and sessions by query type.", 6.0)
rich("**Caveat.** The near-zero correlations between every pair of variables are typical of synthetically generated data (the brief points to a dataset-generation prompt). Findings should be read as illustrative of the method rather than as evidence about real student behaviour.")

# ============ 5 DESIGN ============
H1("5. System Design")
H2("5.1 Architecture")
rich("The system is a pipeline of small, independently testable modules behind a Flask REST API (Figure 7). Every message passes through the same six stages; only anonymous metadata leaves the pipeline.")
FIGURE("fig_architecture_block.png", "Abes Assist system block diagram.", 6.3)
H2("5.2 Data flow (DFD Level 0)")
rich("The context diagram (Figure 8) shows the single process – the chatbot system – and its three external entities: the student (asks questions, receives answers and escalation notices), the human support agent (receives escalation tickets and replies through the student portal) and the university administrator (maintains the FAQ content and supplies new training data).")
FIGURE("fig_dfd_level0.png", "Data Flow Diagram – Level 0.", 6.3)
H2("5.3 Modules")
TABLE([["Stage", "Module (file)", "Responsibility"],
       ["1", "PII redaction (nlp_utils.py)", "Regex removal of e-mail, phone, Aadhaar-style and card numbers; user is told what was removed"],
       ["2", "Small-talk & safety (chatbot.py)", "Greetings / thanks / bye; self-harm and severe-incident detection"],
       ["3", "Intent classifier (train_intent.py)", "TF-IDF (word + char) → Logistic Regression; outputs intent and probability"],
       ["4", "FAQ retriever (chatbot.py)", "TF-IDF cosine over question + paraphrases; small bonus for same-intent FAQs"],
       ["5", "Sentiment (chatbot.py)", "VADER compound score with domain-adjusted lexicon"],
       ["6", "Escalation policy (chatbot.py)", "Combines signals, creates ticket, builds reply with red badge"],
       ["–", "Store (chatbot.py)", "SQLite tables interactions and tickets, anonymous metadata only"],
       ["–", "Web app (app.py, templates/)", "Chat UI, REST endpoints, dashboard, rating and opt-out"]],
      [0.5, 2.2, 3.7], caption="Pipeline modules")
H2("5.4 Escalation policy")
rich("Escalation is decided by independent rules, any of which is sufficient. This makes the behaviour explainable (the reasons are shown to the student and stored in the ticket) and robust to the finding that confidence alone is not predictive.")
FIGURE("fig_escalation_logic.png", "Escalation decision logic.", 6.2)
TABLE([["Signal", "Rule", "Priority"],
       ["Wellbeing", "Self-harm expressions → supportive reply with Tele-MANAS 14416 and 112, plus escalation", "Urgent"],
       ["Safety incident", "First-person reports of ragging / harassment / bullying / threats, or severe terms (assault, blackmail)", "Urgent"],
       ["Explicit request", "“talk to a human”, “real person”, “transfer me to an agent”, …", "Normal"],
       ["Sentiment", f"VADER compound ≤ −0.50 (≤ −0.25 when intent is grievance)", "Normal"],
       ["Repeated confusion", "Confidence < 0.40 or no FAQ match in two consecutive turns", "Normal"]],
      [1.4, 4.2, 0.8], caption="Escalation signals")
rich("When the bot escalates, the student sees a red **“ESCALATED TO HUMAN AGENT”** badge, a ticket number (HT-xxxxxx) and the reason, satisfying the brief’s requirement that escalation be clearly indicated. A relevant FAQ answer is still shown if one matches strongly.")
H2("5.5 Data storage and privacy architecture")
rich("Two SQLite tables exist. **interactions** stores session_id (random, anonymous), timestamp, query type, intent, confidence, escalated flag and rating – exactly the schema of dataset.csv, so live data can later be analysed with the same notebook. **tickets** stores ticket ID, session ID, intent, reason and status. Neither table contains message text, names, e-mail addresses or phone numbers. Conversation state (turn count, low-confidence streak) is kept in memory only and discarded at the end of the session.")
H2("5.6 REST API")
TABLE([["Endpoint", "Method", "Purpose"],
       ["/api/session", "POST", "Create an anonymous session ID"],
       ["/api/chat", "POST", "Send message → reply, intent, confidence, sentiment, escalation info"],
       ["/api/rate", "POST", "Store 1–5 rating for the last interaction (validated)"],
       ["/api/optout", "POST", "Delete all session rows and stop logging"],
       ["/api/end", "POST", "End session and clear in-memory state"],
       ["/api/stats, /dashboard", "GET", "Aggregated anonymous statistics"]],
      [1.9, 0.8, 3.7], caption="API endpoints")

# ============ 6 IMPLEMENTATION ============
H1("6. Implementation")
H2("6.1 Intent classification")
rich("Text is lower-cased, tokenised with a regular expression, stripped of common stop-words and Porter-stemmed (so “paying”, “payment” and “paid” share features). Two TF-IDF representations are concatenated: **word uni/bi-grams** capture phrases such as “hall ticket”, and **character 2–5-grams** capture sub-word patterns, making the model tolerant to typos (“admsion”) and spelling variants. A Logistic Regression (C = 20) outputs class probabilities; the largest probability is the **confidence**. Four classifiers were compared on the same held-out test set (Section 7.1). The shipped model is retrained on all labelled data after evaluation.")
H2("6.2 FAQ retrieval")
rich("Each FAQ is indexed by its canonical question and three paraphrases, vectorised with the same stemming TF-IDF, and compared with the user message by cosine similarity. A small bonus is added when the FAQ belongs to the predicted intent, which resolves ties between similar questions across topics. If the best similarity is below 0.12 the bot treats the question as unanswered.")
H2("6.3 Sentiment analysis")
rich("VADER provides a compound sentiment score in [−1, 1]. Its lexicon was extended with campus-specific negative terms (“useless”, “rude”, “ignored”, “unacceptable”, “harassed”, …) and – after errors were found in testing – routine neutral words that VADER scores as negative (“charges”, “fine”, “failed”, “mess”, “hostel”, …) were set to zero so that ordinary questions such as “how to pay mess charges” do not trigger escalation.")
H2("6.4 Privacy features in code")
B(["**PII redaction** before any processing; the student is told what was removed and reminded not to share personal data.",
   "**No raw text persistence** – only intent, confidence, flags and rating are written to SQLite.",
   "**Opt-out button** – deletes all rows for the session, flags the session and stops all logging; a human can still be requested.",
   "**Random session IDs** (UUID-based) – not linked to a student identity or login.",
   "**Transparent escalation** – the badge, ticket and reasons are shown to the student."])
H2("6.5 User interface")
rich("The web interface is a single page with chat bubbles, quick-reply chips with suggested follow-up questions, a persistent privacy notice, a “Talk to a human” button, an “Opt out of data logging” button, a star rating and automatic light/dark theme. Each bot reply shows the predicted intent, confidence, sentiment and response time for transparency (useful for demonstration; it can be hidden in production). An anonymous dashboard (/dashboard) shows conversation counts, escalation rate, average rating and open tickets.")
H2("6.6 Running the project")
rich("Install dependencies with pip install -r requirements.txt, train the model with python src/train_intent.py, and start the app with python src/app.py, then open http://127.0.0.1:5000. Details are in Appendix A and the README.")

# ============ 7 RESULTS ============
H1("7. Testing and Results")
H2("7.1 Intent classification")
rows = [["Model", "Accuracy", "Macro-F1"]] + [[k, f"{v['accuracy']*100:.1f} %", f"{v['macro_f1']:.3f}"] for k, v in im["model_comparison"].items()]
TABLE(rows, [3.6, 1.4, 1.4], caption=f"Model comparison on {im['n_test']} unseen held-out utterances (8 classes)")
rich(f"Logistic Regression with word + character TF-IDF performed best (**{im['test_accuracy']*100:.1f} % accuracy, macro-F1 {im['test_macro_f1']:.3f}**), meeting objective O1. Five-fold cross-validation on the training utterances (augmentation performed inside each fold to avoid leakage) gave {im['cv_accuracy_mean']*100:.1f} % ± {im['cv_accuracy_std']*100:.1f} %, showing that the estimate has noticeable variance because the corpus is small. Naive Bayes performed poorly with this feature set.")
rows = [["Class", "Precision", "Recall", "F1", "Support"]] + [[k, f"{v['precision']:.2f}", f"{v['recall']:.2f}", f"{v['f1-score']:.2f}", v["support"]] for k, v in im["per_class"].items()]
TABLE(rows, [1.7, 1.1, 1.1, 1.1, 1.1], caption="Per-class results of the chosen model on the held-out test set")
FIGURE("fig_confusion_matrix.png", "Confusion matrix on the held-out test set.", 4.9)
rich("The weakest class is **exams** (F1 0.59), mainly confused with schedule and fees, which share vocabulary (“date”, “fee”, “when”). **Out-of-scope** has precision 1.0 but recall 0.56: some off-topic questions are routed to a campus intent; for these the FAQ-similarity check and the repeated-confusion rule act as a second line of defence.")
H2("7.2 FAQ retrieval")
rich(f"On {sm['faq_retrieval']['n']} paraphrased queries that do not appear verbatim in the knowledge base, the correct FAQ was returned first in **{sm['faq_retrieval']['top1_accuracy']*100:.1f} %** of cases (objective O2 met). The single miss (“is there any aid for freshers”) used a synonym that the vocabulary does not cover, and the bot correctly declined to answer instead of returning a wrong FAQ.")
H2("7.3 Escalation policy")
c = sm["escalation"]["confusion"]
TABLE([["", "Predicted: no escalation", "Predicted: escalation"], ["Actual: no escalation", c[0][0], c[0][1]], ["Actual: escalation needed", c[1][0], c[1][1]]], [2.2, 2.0, 2.0], caption=f"Escalation confusion matrix ({sm['escalation']['n']} labelled messages)")
rich(f"Precision was {sm['escalation']['precision']:.2f}, recall {sm['escalation']['recall']:.2f} and F1 {sm['escalation']['f1']:.2f}. The test set includes 24 messages that must **not** escalate (routine FAQs, an anti-ragging helpline question, small talk, an off-topic question) and 18 that must (human requests, frustration, incident reports, self-harm, blackmail). During testing, one self-harm phrasing (“ending my life”) was initially missed (recall 0.94); the pattern list was widened and the test re-run – a reminder that keyword safety nets need continuous review. **Caution:** these messages were written by the same person who designed the rules, so the scores are optimistic; an independent test set with real student messages is essential before deployment.")
H2("7.4 Response time")
rich(f"Across {sm['latency_ms']['n']} test replies, mean latency was **{sm['latency_ms']['mean']} ms**, 95th percentile {sm['latency_ms']['p95']} ms and maximum {sm['latency_ms']['max']} ms on a CPU – far below the 1 s target (O4). Network and browser time are not included.")
H2("7.5 Privacy audit")
rich(f"A message containing an e-mail address, a phone number and a topic (“hostel wifi not working”) was sent, then every row of both tables was searched for those strings: **found = {sm['privacy']['raw_text_or_pii_found_in_db']}**. After calling opt-out, **{sm['privacy']['rows_left_after_optout']}** rows remained for that session. Both results meet objective O5.")
H2("7.6 Automated tests and sample conversations")
rich("Eleven unit/API tests (tests/test_chatbot.py) cover intent routing, human-request and sentiment escalation, urgent self-harm handling, out-of-scope detection, the two-strikes rule, PII redaction, absence of raw text in the database, opt-out behaviour, and the Flask endpoints including input validation. All pass. Table 11 shows real outputs of the system.")
rows = [["Student message", "Intent (conf.)", "Sent.", "Esc.", "Bot reply (truncated)"]]
for r in dlg:
    rep = r["reply"].replace("\n", " ").replace("**", "")
    rows.append([r["q"], f"{r['intent']} ({r['conf']:.2f})", f"{r['sent']:+.2f}", "YES" if r["esc"] else "no", rep[:150] + ("…" if len(rep) > 150 else "")])
TABLE(rows, [1.55, 1.0, 0.5, 0.45, 2.9], caption="Sample conversations produced by the prototype", size=8.5)
H2("7.7 Summary against objectives")
TABLE([["Objective", "Target", "Result", "Met?"],
       ["O1 intent accuracy", "≥ 80 %", f"{im['test_accuracy']*100:.1f} % (held-out)", "Yes (narrowly)"],
       ["O2 FAQ top-1", "≥ 90 %", f"{sm['faq_retrieval']['top1_accuracy']*100:.1f} %", "Yes"],
       ["O3 escalation recall", "≥ 90 %", f"{sm['escalation']['recall']*100:.0f} % (optimistic test set)", "Yes*"],
       ["O4 latency", "< 1 s", f"{sm['latency_ms']['mean']} ms mean", "Yes"],
       ["O5 privacy", "0 PII/text stored; opt-out works", "Audit passed", "Yes"],
       ["O6 visible escalation", "Badge + ticket", "Implemented in UI/API", "Yes"]],
      [1.7, 1.6, 2.2, 0.9], caption="Objectives versus results (*see caution in 7.3)")

# ============ 8 ETHICS ============
H1("8. Ethical Considerations and Compliance")
TABLE([["Concern", "Mitigation in this project"],
       ["Personal data (PII)", "Redaction before processing; raw text never stored; random anonymous session IDs; only aggregate-able metadata kept."],
       ["Consent and control", "Visible privacy notice; one-click opt-out that deletes the session’s rows and stops logging."],
       ["Transparency", "The bot identifies itself as an AI assistant; shows intent/confidence; escalation reasons are displayed to the student."],
       ["Human oversight", "Clear red escalation indicator, ticket number, ‘Talk to a human’ button available at all times."],
       ["Safety of vulnerable students", "Self-harm and incident keywords produce a supportive message, Tele-MANAS (14416) / 112 details and priority escalation. The bot does not attempt counselling."],
       ["Accuracy of information", "Answers come only from approved FAQ text (no free-text generation). The sample FAQ must be validated by the university before use."],
       ["Fairness", "Keyword and sentiment methods can misread dialects, Hinglish or politely-worded complaints. Sentiment-based escalation errs towards handing over to a human, which is the safer failure mode."],
       ["Legal", "Design aligns with data-minimisation and purpose-limitation principles of India’s Digital Personal Data Protection Act, 2023; a real deployment needs a formal data-protection review, retention policy and grievance contact."],
       ["Dataset licence", "dataset.csv is programme-provided and anonymous; utterances and FAQ were created for this project."],
       ["AI-tool use", "Disclosed in Appendix B."]],
      [1.7, 4.7], caption="Ethical risks and mitigations")

# ============ 9 CHALLENGES ============
H1("9. Challenges Faced and How They Were Resolved")
TABLE([["Challenge", "Resolution"],
       ["dataset.csv contains no message text, so no NLP model can be trained from it.", "Authored a labelled corpus and FAQ base; used dataset.csv for EDA, class definitions and policy design."],
       ["Tiny corpus risks inflated accuracy through leakage from augmented copies.", "Split base utterances first; augmented only training data; reported held-out and cross-validated results with their variance."],
       ["Confidence was uncorrelated with escalation in the data (ρ ≈ 0.04).", "Replaced a single-threshold policy by a multi-signal, explainable rule set."],
       ["Out-of-domain questions (“weather today”) were assigned to a campus intent with high confidence.", "Added an explicit out_of_scope class and a polite redirection message."],
       ["VADER marked routine words (“charges”, “mess”) negative → false escalations.", "Neutralised domain words and added campus-specific negative words; re-tested."],
       ["A frustrated message was answered with an unrelated FAQ (matched on generic words).", "Attach an FAQ to an escalation only if it is from the predicted intent and similarity ≥ 0.45."],
       ["One self-harm phrasing slipped past the keyword list.", "Widened the pattern list; kept the case in the test set; documented the need for ongoing review."]],
      [3.0, 3.4], caption="Challenges and resolutions")

# ============ 10 LIMITS ============
H1("10. Limitations and Future Work")
H2("10.1 Limitations")
B(["**Evaluation data are small and self-authored.** Real student messages will be noisier; accuracy will probably be lower. The escalation test set was written by the rule designer and is optimistic.",
   "**dataset.csv appears synthetic** (almost no correlations), so EDA conclusions are illustrative.",
   "**FAQ content is sample text**, not the policy of any real university.",
   "The bot answers one FAQ per message; it does not track multi-turn context or extract entities (dates, course names).",
   "Keyword/VADER methods are English-centric; Hindi, Hinglish and regional-language support is minimal.",
   "Sessions are stored in process memory and there is no authentication, so the prototype is single-server and not production-hardened. Tickets are stored but not integrated with a real helpdesk system.",
   "user_query_type is not defined in the data dictionary; the live system derives it from message length/structure as an assumption."])
H2("10.2 Future work")
B(["Collect consented, anonymised real queries and retrain; evaluate on an independent test set; add confidence calibration.",
   "Fine-tune a multilingual transformer (e.g., a small BERT variant) for intent detection and compare with the TF-IDF baseline; consider Rasa for multi-turn dialogue and entity slots.",
   "Integrate with the student portal (read-only status look-ups, fee dues, timetable) and a ticketing tool (e-mail/Teams alerts for agents, SLA tracking).",
   "Add a human-agent console, analytics on unanswered questions and a feedback loop to grow the FAQ.",
   "Run usability tests with students, bias/fairness checks across languages, accessibility review (screen readers) and a formal DPDP impact assessment."])

# ============ 11 CONCLUSION ============
H1("11. Conclusion")
rich(f"The project delivered a working, privacy-conscious student-support chatbot that answers routine questions from an approved FAQ base and, just as importantly, knows when to stop. Exploratory analysis showed that escalation in the provided data is not explained by model confidence; the resulting multi-signal policy (explicit request, sentiment, safety, repeated confusion) is explainable and visible to students. On held-out tests the system reached {im['test_accuracy']*100:.0f} % intent accuracy, {sm['faq_retrieval']['top1_accuracy']*100:.0f} % FAQ retrieval accuracy and a few milliseconds of latency, while storing no message text or PII. The principal caveats are the small, self-authored evaluation data and the sample FAQ content; addressing these with real, consented data is the most valuable next step.")

# ============ REFERENCES ============
H1("References")
for i, r in enumerate([
 "Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
 "Hutto, C. J. and Gilbert, E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Proceedings of the 8th International AAAI Conference on Weblogs and Social Media (ICWSM).",
 "Salton, G. and Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. Information Processing & Management, 24(5), 513–523.",
 "Bird, S., Klein, E. and Loper, E. (2009). Natural Language Processing with Python. O’Reilly Media (NLTK).",
 "Government of India (2023). The Digital Personal Data Protection Act, 2023.",
 "Flask documentation. https://flask.palletsprojects.com (accessed 2026).",
 "HCLTech Career Shaper Programme – Project Brief, Project No. 30, Academic Year 2025-26 (provided by the Programme Coordinator).",
 "Mentor to validate and add further links (as stated in the Project Brief)."], 1):
    p = P(f"[{i}] {r}", size=10, after=3); p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.3)

# ============ APPENDICES ============
d.add_page_break(); H1("Appendix A – Project structure and how to run")
rich("```", align=None) if False else None
code = """university_chatbot/
├── data/        dataset.csv (cleaned) · dataset_raw.csv · data_dictionary.csv · faq_knowledge_base.csv · intent_training_data.csv
├── notebooks/   EDA_Notebook.ipynb (executed, 6 visualisations)
├── src/         app.py · chatbot.py · nlp_utils.py · intent_data.py · train_intent.py · evaluate.py · build_faq.py · make_*.py
├── templates/   index.html (chat UI) · dashboard.html
├── models/      intent_model.joblib · intent_metrics.json · system_metrics.json
├── figures/     all charts and diagrams used in this report
├── tests/       test_chatbot.py (11 tests)
└── docs/        Project_Report.docx · demo_script.md · sample_dialogues.json"""
for ln in code.split("\n"):
    p = P(ln, size=8.5, after=0); [setattr(r.font, "name", "Consolas") for r in p.runs]
P("", after=4)
N(["pip install -r requirements.txt", "python src/build_faq.py   (optional – regenerates the FAQ CSV)", "python src/train_intent.py   (trains model, writes metrics and confusion matrix)",
   "python src/evaluate.py   (system evaluation)", "python -m unittest tests.test_chatbot", "python src/app.py   → open http://127.0.0.1:5000"])
H1("Appendix B – Disclosure of AI tools")
rich("An AI assistant (Claude, by Anthropic) was used to help plan the project, generate code, draft the utterance corpus, FAQ knowledge base and this report. The learner is responsible for reviewing, running and understanding all submitted material. [Learner to add any other tools used and review notes.]")
PLACE("[LEARNER: confirm the disclosure above reflects how you actually used AI tools.]")
H1("Appendix C – Mapping to the 4-week plan")
TABLE([["Week", "Planned focus", "Evidence in this project"],
       ["1", "Problem understanding, EDA", "Section 2, Section 4, EDA_Notebook.ipynb"],
       ["2", "Architecture and core implementation", "Section 5, intent model, FAQ retrieval"],
       ["3", "Integration, testing, validation", "Section 7, tests/, evaluate.py, metrics JSON"],
       ["4", "Report, presentation, demo", "This report, demo_script.md, synopsis"]], [0.6, 2.6, 3.2], caption="Mapping to suggested plan")

# footer page numbers
for s in d.sections:
    fp = s.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("AI-Powered Chatbot for University Student Support  |  HCLTech Career Shaper 2025-26  |  Page "); r.font.size = Pt(8.5)
    fld(fp, "PAGE")
    for r in fp.runs: r.font.size = Pt(8.5)
(ROOT / "docs").mkdir(exist_ok=True)
d.save(ROOT / "docs/Project_Report.docx"); print("saved")
