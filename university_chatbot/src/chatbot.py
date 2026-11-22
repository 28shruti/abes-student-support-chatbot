"""Core chatbot engine: PII redaction -> small-talk -> intent classification -> FAQ retrieval -> sentiment -> escalation policy.
Privacy by design: raw user text is NEVER written to disk; only anonymous metadata (intent, confidence, flags, rating)."""
import re, time, uuid, sqlite3, pathlib, csv, threading
import joblib, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nlp_utils import stem_tokenizer, redact_pii
from live_site import LiveSite   # noqa: F401  (stem_tokenizer needed to unpickle the model)

ROOT = pathlib.Path(__file__).resolve().parent.parent

CONF_THRESHOLD = 0.40         # below this the bot does not trust its intent prediction
FAQ_MIN_SIM = 0.12            # below this no FAQ is considered a match
SENT_ESCALATE = -0.50         # strongly negative message -> human
SENT_GRIEVANCE = -0.25        # milder negativity is enough when the topic is a grievance
FAQ_STRONG = 0.30             # above this the FAQ is treated as a clear match
MAX_LOW_CONF_TURNS = 2
HINGLISH = {"kab": "when", "kitni": "how many", "kitna": "how much", "kitne": "how many", "kaise": "how", "kahan": "where", "kaha": "where",
            "kya": "what", "kyun": "why", "mujhe": "i", "chahiye": "need", "milega": "get", "milti": "get", "milta": "get", "mil": "get",
            "sakti": "can", "sakta": "can", "khuli": "open", "khulti": "open", "khulta": "open", "band": "closed", "shikayat": "complaint",
            "bharni": "pay", "bharna": "fill", "jama": "pay", "karna": "do", "kare": "do", "kar": "do", "baje": "time", "din": "day", "ko": "",
            "hai": "", "hain": "", "ka": "", "ki": "", "ke": "", "mein": "in", "me": "in", "se": "from", "liye": "for", "aayega": "declared",
            "aata": "declared", "hoga": "", "honge": "", "shuru": "start", "darj": "file", "lagti": "", "lagta": ""}
_WORD = re.compile(r"[a-z']+")
def normalise(text):
    """Replace common Hinglish words by English ones (used for FAQ search only)."""
    return " ".join(w for w in (HINGLISH.get(x, x) for x in _WORD.findall(text.lower())) if w)        # bot asks to rephrase once, then hands over

HUMAN_REQUEST = re.compile(r"\b(talk|speak|connect|chat|transfer)\b.{0,25}\b(human|person|agent|someone|staff|representative|officer|counsel+or)\b|"
                           r"\b(human|real person|live agent|customer care|helpdesk staff)\b|\bnot a bot\b|\bkisi insaan\b", re.I)
SELF_HARM = re.compile(r"\b(suicide|suicidal|kill myself|(end|ending|take|taking) (my|my own) life|end it all|want to die|self[- ]?harm|hurt myself|no reason to live)\b", re.I)
SEVERE = re.compile(r"\b(assault(ed)?|molest(ed|ation)?|rape[d]?|blackmail(ed|ing)?|sexual(ly)? harass\w*)\b", re.I)
INCIDENT = re.compile(r"\b(i|we|me|my)\b.{0,40}\b(was|am|been|being|got|get|getting)\b.{0,15}\b(ragged|harass\w*|bullied|abused|threat\w*|stalk\w*|beaten|discriminat\w*)\b|"
                      r"\b(ragged|harass\w*|bullied|threatened|stalked)\b.{0,15}\b(me|us)\b|\bragging\b.{0,20}\b(happening|going on)\b", re.I)

SMALLTALK = [
 (re.compile(r"^\s*(hi+|hello+|hey+|namaste|good (morning|afternoon|evening))\b[\s!.,]*$", re.I),
  "Hello! 👋 I'm UniBot, the university student-support assistant. I can help with admissions, timetable & schedule, fees, exams, hostel, library and complaints. What would you like to know?"),
 (re.compile(r"^\s*(thanks?|thank you|thx|ok thanks|shukriya|dhanyavad)\b.*$", re.I), "You're welcome! 😊 Is there anything else I can help you with?"),
 (re.compile(r"^\s*(bye|goodbye|see you|that'?s all|no more|nothing else)\b.*$", re.I), "Goodbye! Take care. You can rate this chat below. Session data is cleared when you close the chat."),
 (re.compile(r"^\s*(how are you|how r u|kaise ho|kya haal)\b.*$", re.I), "I'm doing well, thank you! 😊 I'm an AI assistant for university queries. What would you like to know — fees, exams, hostel, library, admissions?"),
 (re.compile(r"\b(who are you|what can you do|what is your name|help me$|^help$)\b", re.I),
  "I'm UniBot, an AI assistant for university students. I answer FAQs on admissions, schedule, fees, exams, grievance, hostel and library, and I hand you over to a human agent when I can't help or when you ask me to."),
]

def _vader():
    s = SentimentIntensityAnalyzer()
    s.lexicon.update({"useless": -2.6, "pathetic": -2.8, "worst": -3.0, "fed": -1.0, "ridiculous": -2.2, "unacceptable": -2.6,
                      "rude": -2.4, "harassed": -3.0, "harassment": -3.0, "ragged": -3.0, "ragging": -2.8, "nobody": -1.2, "ignored": -2.2,
                      "frustrated": -2.5, "frustrating": -2.5, "waste": -2.0, "pathetic": -2.8, "cheated": -2.8, "fraud": -3.0,
                      "stressed": -1.8, "irresponsible": -2.4, "unfair": -2.4, "disgusting": -3.0, "horrible": -3.0, "terrible": -3.0,
                      "complaint": -0.8, "complain": -0.8, "wrongly": -1.5, "harsh": -1.5})
    # domain neutralisation: these are routine words in fee/exam queries, not emotional negativity
    s.lexicon.update({w: 0.0 for w in ("charge", "charges", "charged", "fine", "fines", "penalty", "fail", "failed", "failure", "stuck",
                                      "deducted", "refund", "lost", "damage", "damaged", "broken", "problem", "issue", "pending", "late", "delay", "delayed", "cancel", "cancelled", "detention", "backlog", "stress", "stressed", "mess", "hostel", "exam", "exams", "interrupt")})
    s.lexicon.update({"stressed": -1.0})
    return s

class Store:
    """SQLite store of anonymous metadata. No raw text, no names, no contact data."""
    def __init__(self, path):
        self.path = str(path); self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript("""CREATE TABLE IF NOT EXISTS interactions(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, ts TEXT,
                user_query_type TEXT, intent TEXT, confidence_score REAL, escalated INTEGER, user_rating INTEGER);
                CREATE TABLE IF NOT EXISTS tickets(ticket_id TEXT PRIMARY KEY, session_id TEXT, ts TEXT, intent TEXT, reason TEXT, status TEXT DEFAULT 'OPEN');""")
    def _conn(self): return sqlite3.connect(self.path, check_same_thread=False)
    def log(self, sid, qtype, intent, conf, esc):
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO interactions(session_id,ts,user_query_type,intent,confidence_score,escalated) VALUES(?,datetime('now'),?,?,?,?)", (sid, qtype, intent, round(float(conf), 3), int(esc)))
    def ticket(self, sid, intent, reason):
        tid = "HT-" + uuid.uuid4().hex[:6].upper()
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO tickets(ticket_id,session_id,ts,intent,reason) VALUES(?,?,datetime('now'),?,?)", (tid, sid, intent, reason))
        return tid
    def rate(self, sid, rating):
        with self._lock, self._conn() as c:
            c.execute("UPDATE interactions SET user_rating=? WHERE id=(SELECT MAX(id) FROM interactions WHERE session_id=?)", (int(rating), sid))
    def delete_session(self, sid):
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM interactions WHERE session_id=?", (sid,)); c.execute("DELETE FROM tickets WHERE session_id=?", (sid,))
    def stats(self):
        with self._conn() as c:
            n, e, r = c.execute("SELECT COUNT(*), COALESCE(SUM(escalated),0), AVG(user_rating) FROM interactions").fetchone()
            by = c.execute("SELECT intent, COUNT(*), SUM(escalated), AVG(confidence_score) FROM interactions GROUP BY intent ORDER BY 2 DESC").fetchall()
            tk = c.execute("SELECT COUNT(*) FROM tickets WHERE status='OPEN'").fetchone()[0]
        return dict(total=n, escalated=int(e), escalation_rate=round(e / n, 3) if n else 0, avg_rating=round(r, 2) if r else None, open_tickets=tk,
                    by_intent=[dict(intent=i, count=cn, escalated=int(es or 0), avg_conf=round(a, 3)) for i, cn, es, a in by])

# FAQs whose answer is rebuilt from the college website (question prefix -> composer name in live_site.py)
LIVE_ANSWERS = {
    "What is the fee structure": "fees",
    "How do I pay my tuition fees online": "payment",
    "What is the hostel fee": "hostel_fee",
    "How many hostel seats": None,
    "What documents are required for admission": "documents",
    "What is the refund policy": "refund",
    "How do I cancel or withdraw my admission": "refund",
    "Which courses does ABES offer": "programs",
    "How do I apply for admission": "admission",
}

class UniBot:
    def __init__(self, db_path=None, model_path=None, faq_path=None, live=False):
        self.model = joblib.load(model_path or ROOT / "models" / "intent_model.joblib")
        self.sent = _vader()
        self.store = Store(db_path or ROOT / "data" / "chatbot_log.db")
        self._load_faq(faq_path or ROOT / "data" / "faq_knowledge_base.csv")
        self.sessions = {}          # in-memory only; wiped on end_session / opt-out
        self.site = LiveSite(auto_refresh=live)     # college-website data (live if reachable, else saved copy)

    # ---------- FAQ retrieval (TF-IDF cosine over question + paraphrases) ----------
    def _load_faq(self, path):
        self.faq, docs, owner = {}, [], []
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.faq[r["faq_id"]] = r
                for q in [r["question"]] + [a for a in r["alt_questions"].split("|") if a]:
                    docs.append(normalise(q)); owner.append(r["faq_id"])
        self.faq_owner = owner
        self.vec = TfidfVectorizer(tokenizer=stem_tokenizer, token_pattern=None, lowercase=False, ngram_range=(1, 2), sublinear_tf=True)
        self.faq_mat = self.vec.fit_transform(docs)

    def retrieve(self, text, intent, conf=0.0):
        """Search inside the predicted topic first (when the classifier is fairly sure); otherwise search all FAQs."""
        sims = cosine_similarity(self.vec.transform([normalise(text)]), self.faq_mat)[0]
        best = {}
        for s, fid in zip(sims, self.faq_owner):
            same = self.faq[fid]["intent"] == intent
            if conf >= 0.5 and intent != "out_of_scope" and not same: continue      # stay inside the topic
            best[fid] = max(best.get(fid, 0), s + (0.05 if same and s > 0 else 0))
        if not best: return None, 0.0, 0.0
        fid = max(best, key=best.get)
        raw = max(s for s, o in zip(sims, self.faq_owner) if o == fid)
        return fid, float(raw), float(best[fid])

    # ---------- helpers ----------
    @staticmethod
    def query_type(text):
        """Taxonomy used for the 'user_query_type' column (assumption – see docs): by word count / structure."""
        n = len(text.split()); sent = len(re.findall(r"[.!?]+", text))
        if n <= 3: return "query_type_1"
        if n <= 6: return "query_type_2"
        if n <= 10: return "query_type_3"
        if n <= 15 and sent <= 1: return "query_type_4"
        return "query_type_5"

    def live_answer(self, fid, text=""):
        """If this FAQ is backed by the college website, build the answer from the synced data."""
        q = self.faq[fid]["question"]
        for prefix, name in LIVE_ANSWERS.items():
            if name and q.startswith(prefix): return self.site.compose(name, text)
        return None

    def new_session(self):
        sid = "S" + uuid.uuid4().hex[:10]
        self.sessions[sid] = dict(low_streak=0, turns=0, opt_out=False)
        return sid

    def opt_out(self, sid):
        self.sessions.setdefault(sid, dict(low_streak=0, turns=0))["opt_out"] = True
        self.store.delete_session(sid)

    def end_session(self, sid, delete_logs=False):
        self.sessions.pop(sid, None)
        if delete_logs: self.store.delete_session(sid)

    def decide_escalation(self, text, intent, conf, sentiment, faq_raw, state):
        """Rule-based policy. Returns (escalate, reasons, urgent)."""
        reasons, urgent = [], False
        if SELF_HARM.search(text): reasons.append("wellbeing concern"); urgent = True
        if SEVERE.search(text): reasons.append("serious safety / harassment report"); urgent = True
        if INCIDENT.search(text): reasons.append("incident report (harassment / ragging)"); urgent = True
        if HUMAN_REQUEST.search(text): reasons.append("student asked for a human agent")
        if sentiment <= SENT_ESCALATE: reasons.append(f"strongly negative sentiment ({sentiment:+.2f})")
        elif intent == "grievance" and sentiment <= SENT_GRIEVANCE: reasons.append(f"grievance with negative sentiment ({sentiment:+.2f})")
        low = conf < CONF_THRESHOLD or faq_raw < FAQ_MIN_SIM
        if low and state["low_streak"] + 1 >= MAX_LOW_CONF_TURNS: reasons.append("bot could not understand the question twice")
        return bool(reasons), reasons, urgent

    # ---------- main entry ----------
    def respond(self, sid, message):
        t0 = time.perf_counter()
        state = self.sessions.setdefault(sid, dict(low_streak=0, turns=0, opt_out=False))
        state["turns"] += 1
        text, pii = redact_pii(message.strip()[:1000])
        out = dict(session_id=sid, intent=None, confidence=0.0, sentiment=0.0, escalated=False, reasons=[], ticket_id=None,
                   faq_id=None, faq_score=0.0, pii_detected=pii, suggestions=[], smalltalk=False)
        if not text:
            out["reply"] = "Please type your question and I'll do my best to help."; return out
        for pat, ans in SMALLTALK:
            if pat.search(text) and len(text.split()) <= 8 and not HUMAN_REQUEST.search(text):
                out.update(reply=ans, smalltalk=True, latency_ms=round((time.perf_counter() - t0) * 1000, 1)); return out

        proba = self.model.predict_proba([text])[0]
        k = int(np.argmax(proba)); intent, conf = str(self.model.classes_[k]), float(proba[k])
        sentiment = self.sent.polarity_scores(text)["compound"]
        fid, faq_raw, _ = self.retrieve(text, intent, conf)
        esc, reasons, urgent = self.decide_escalation(text, intent, conf, sentiment, faq_raw, state)
        if conf < 0.5 and faq_raw >= 0.55 and fid:          # classifier unsure but the FAQ match is very strong -> trust the FAQ's topic
            intent = self.faq[fid]["intent"]; conf = max(conf, 0.5)
        oos = intent == "out_of_scope"
        menu = len(text.split()) <= 2 and conf >= 0.6 and not oos and faq_raw < 0.6      # just a keyword like "fees" or "hostel"
        low = conf < CONF_THRESHOLD or faq_raw < FAQ_MIN_SIM or (conf < 0.5 and faq_raw < 0.5)      # genuine misunderstanding (out-of-scope is handled separately)
        if menu: low = False
        low = low and not oos or (oos and conf < CONF_THRESHOLD)
        state["low_streak"] = state["low_streak"] + 1 if low else 0

        pre = ""
        if pii: pre = "🔒 I removed personal details (" + ", ".join(pii) + ") from your message — please don't share such information here.\n\n"
        if SELF_HARM.search(text):
            body = ("I'm really sorry you're feeling this way, and I'm glad you reached out. You don't have to face this alone. "
                    "Please talk to someone right now: **Tele-MANAS 14416** (free, 24×7, India) or call **112** in an emergency. "
                    "I'm also alerting a human counsellor from the university.")
        elif menu and not esc:
            body = f"Here are some common questions about **{intent}** — tap one, or type your own question:"
            out["suggestions"] = [self.faq[f]["question"] for f in self.faq if self.faq[f]["intent"] == intent][:5]
        elif oos and not esc:
            body = ("That looks outside what I can help with — I only handle university student-support topics: **admissions, schedule, fees, "
                    "exams, grievance, hostel and library**. Please ask me about one of these, or type *talk to a human*.")
        elif low and not esc:
            if not oos and conf >= 0.4:
                out["suggestions"] = [self.faq[f]["question"] for f in self.faq if self.faq[f]["intent"] == intent][:4]
            body = ("I'm not sure I understood that. Could you rephrase your question? You can ask about **admissions, schedule, fees, exams, "
                    "grievance, hostel or library** — or type *talk to a human*.")
        else:
            if not oos and fid and faq_raw >= (FAQ_MIN_SIM if not esc else 0.45) and (not esc or self.faq[fid]["intent"] == intent):
                body = self.live_answer(fid, text) or self.faq[fid]["answer"]; out["faq_id"] = fid
                if faq_raw < FAQ_STRONG and not esc:
                    body = "I'm not 100% sure I got that, but this might be what you're looking for:\n\n" + body
            else:
                body = "I'm sorry you're facing this — I understand it's frustrating." if sentiment < -0.2 else "Sure, I'll bring a human agent into this chat."
            pass
            out["suggestions"] = [self.faq[f]["question"] for f in self.faq if self.faq[f]["intent"] == intent and f != fid][:3] if out["faq_id"] else []
        if esc:
            tid = self.store.ticket(sid, intent, "; ".join(reasons)) if not state.get("opt_out") else "HT-OPTOUT"
            body += (f"\n\n🔴 **Escalated to a human support agent** — ticket **{tid}**. Reason: {', '.join(reasons)}. "
                     "A staff member will contact you through the student portal" + (" as a priority." if urgent else " within one working day."))
            out["ticket_id"] = tid
        out.update(reply=pre + body, intent=intent, confidence=round(conf, 3), sentiment=round(sentiment, 3), escalated=esc,
                   reasons=reasons, faq_score=round(faq_raw, 3), query_type=self.query_type(text), urgent=urgent)
        if not state.get("opt_out"):
            self.store.log(sid, out["query_type"], intent, conf, esc)
        out["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return out
