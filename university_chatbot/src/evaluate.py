"""End-to-end evaluation: escalation policy, FAQ retrieval, latency, privacy audit. Writes models/system_metrics.json"""
import json, time, tempfile, sqlite3, pathlib, statistics as st
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix
from chatbot import AbesAssist, ROOT

# (message, should_escalate) – hand-labelled test messages NOT used for rule design
ESC = [
 ("How do I pay my tuition fees online?",0),("When does the next semester start?",0),("What are the library timings?",0),
 ("How do I download my hall ticket?",0),("Is there a hostel for girls?",0),("What documents are needed for admission?",0),
 ("Can I renew my library book online?",0),("What is the late fee for delayed payment?",0),("Is the mess menu available online?",0),
 ("When will results be declared?",0),("How can I apply for revaluation?",0),("What is the anti-ragging helpline number?",0),
 ("How do I file a complaint?",0),("Where is the complaint box?",0),("What is the refund policy?",0),("How to apply for a scholarship?",0),
 ("Can I get a duplicate marksheet?",0),("hostel gate timing kya hai",0),("What is the passing marks criteria?",0),("when is the diwali break",0),
 ("What is the weather today?",0),("Tell me a joke",0),("thanks a lot",0),("hello",0),
 ("I want to talk to a human agent",1),("Please connect me to a real person",1),("Can I speak to someone from the admin staff?",1),
 ("This chatbot is useless, nobody ever helps me",1),("Worst service ever, I am so frustrated with this university",1),
 ("My complaint was ignored for two months, this is unacceptable",1),("The warden was very rude to me and I want action",1),
 ("I was ragged by my seniors last night",1),("I am being harassed by a classmate",1),("A professor threatened me about my marks",1),
 ("I feel like ending my life",1),("I want to hurt myself",1),("Someone is blackmailing me with my photos",1),
 ("I have been cheated, the fee was deducted twice and nobody replies, pathetic",1),("this is ridiculous, I am fed up of running around for my marksheet",1),
 ("I want to speak to a human about my fee issue",1),("transfer me to an agent",1),("Staff at the accounts office ignored me, horrible behaviour",1),
]
FAQ_Q = [  # (paraphrase, substring that must appear in the expected FAQ question)
 ("where do i apply online for a seat","How do I apply for admission"),("which certificates should i bring for admission","What documents are required for admission"),
 ("how do i track my application","check my application"),("is there any aid for freshers","scholarships available for new"),
 ("where is my timetable","find my class timetable"),("when do the semester dates come out","semester start and end"),
 ("is class cancelled today","class is cancelled or rescheduled"),("what time does the office open","office and working hours"),
 ("how can i pay college fee by upi","pay my tuition fees online"),("is there a penalty for paying fee late","late fee penalty"),
 ("download my fee receipt","fee receipt or fee certificate"),("my money got cut but fee still pending","payment failed but money"),
 ("when is the date sheet coming","exam timetable be released"),("how to get admit card","hall ticket or admit card"),
 ("how to recheck my paper","re-evaluation"),("what attendance do i need for exams","minimum attendance required for exams"),
 ("i failed one paper how to reappear","backlog or supplementary"),("how to report ragging","harassment or ragging"),
 ("what is the grievance resolution time","long does grievance resolution"),("how do i raise a complaint","file a complaint or grievance"),
 ("how to get a hostel room","apply for a hostel room"),("what time does hostel gate shut","hostel gate timings"),
 ("can my parents visit me in the hostel","visitors allowed"),("my hostel wifi is down","maintenance, wifi or water"),
 ("library open hours","library timings"),("how many books can one borrow","how many books can I borrow"),
 ("fine on overdue books","fine for late return"),("how to read ieee papers from home","e-journals and digital resources"),
]
def main():
    bot = AbesAssist(db_path=tempfile.mktemp(suffix=".db"))
    y, p, lat = [], [], []
    for m, lab in ESC:
        sid = bot.new_session(); r = bot.respond(sid, m); y.append(lab); p.append(int(r["escalated"])); lat.append(r["latency_ms"])
    fp = [m for (m, l), pr in zip(ESC, p) if pr and not l]; fn = [m for (m, l), pr in zip(ESC, p) if not pr and l]
    ok = 0; miss = []
    for q, exp in FAQ_Q:
        sid = bot.new_session(); r = bot.respond(sid, q)
        hit = r["faq_id"] and exp.lower() in bot.faq[r["faq_id"]]["question"].lower()
        ok += bool(hit)
        if not hit: miss.append((q, bot.faq[r["faq_id"]]["question"] if r["faq_id"] else None))
        lat.append(r["latency_ms"])
    # privacy audit: log a message with PII, then scan the database for it
    sid = bot.new_session(); bot.respond(sid, "my email is secret.student@uni.edu and phone 9876543210, hostel wifi not working")
    con = sqlite3.connect(bot.store.path); dump = " ".join(str(r) for t in ("interactions", "tickets") for r in con.execute(f"select * from {t}"))
    pii_leak = any(s in dump for s in ("secret.student", "9876543210", "wifi"))
    bot.opt_out(sid); n_after = con.execute("select count(*) from interactions where session_id=?", (sid,)).fetchone()[0]
    res = dict(
        escalation=dict(n=len(ESC), accuracy=round(accuracy_score(y, p), 3), precision=round(precision_score(y, p), 3), recall=round(recall_score(y, p), 3),
                        f1=round(f1_score(y, p), 3), confusion=confusion_matrix(y, p).tolist(), false_positives=fp, false_negatives=fn),
        faq_retrieval=dict(n=len(FAQ_Q), top1_accuracy=round(ok / len(FAQ_Q), 3), misses=miss),
        latency_ms=dict(mean=round(st.mean(lat), 2), p95=round(float(np.percentile(lat, 95)), 2), max=round(max(lat), 2), n=len(lat)),
        privacy=dict(raw_text_or_pii_found_in_db=pii_leak, rows_left_after_optout=n_after))
    (ROOT / "models" / "system_metrics.json").write_text(json.dumps(res, indent=2)); print(json.dumps(res, indent=2))
if __name__ == "__main__": main()
