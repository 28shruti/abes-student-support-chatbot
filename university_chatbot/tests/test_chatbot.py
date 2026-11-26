import sys, pathlib, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from chatbot import AbesAssist
from nlp_utils import redact_pii
from app import create_app

class TestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.bot = AbesAssist(db_path=tempfile.mktemp(suffix=".db"))
    def ask(self, m): return self.bot.respond(self.bot.new_session(), m)
    def test_fee_intent(self):
        r = self.ask("How do I pay my fees online?"); self.assertEqual(r["intent"], "fees"); self.assertFalse(r["escalated"])
    def test_human_request_escalates(self): self.assertTrue(self.ask("please connect me to a human agent")["escalated"])
    def test_negative_sentiment_escalates(self): self.assertTrue(self.ask("This is the worst, useless service. Nobody helps me")["escalated"])
    def test_self_harm_urgent(self):
        r = self.ask("I want to end my life"); self.assertTrue(r["escalated"]); self.assertIn("14416", r["reply"])
    def test_out_of_scope(self): self.assertEqual(self.ask("what is the weather today")["intent"], "out_of_scope")
    def test_two_low_confidence_turns_escalate(self):
        sid = self.bot.new_session(); self.bot.respond(sid, "qwerty zxcv"); r = self.bot.respond(sid, "lkjh poiu")
        self.assertTrue(r["escalated"])
    def test_smalltalk(self): self.assertTrue(self.ask("hello")["smalltalk"])
    def test_pii_redaction(self):
        t, f = redact_pii("mail me at a.b@x.com or call 9876543210, aadhaar 1234 5678 9012")
        self.assertNotIn("9876543210", t); self.assertNotIn("a.b@x.com", t); self.assertEqual(set(f), {"email", "phone", "aadhaar"})
    def test_no_raw_text_in_db(self):
        sid = self.bot.new_session(); self.bot.respond(sid, "my hostel wifi is broken, call 9876543210")
        import sqlite3; rows = sqlite3.connect(self.bot.store.path).execute("select * from interactions where session_id=?", (sid,)).fetchall()
        self.assertTrue(rows); self.assertNotIn("wifi", str(rows)); self.assertNotIn("9876543210", str(rows))
    def test_opt_out_deletes_and_stops_logging(self):
        sid = self.bot.new_session(); self.bot.respond(sid, "library timings"); self.bot.opt_out(sid); self.bot.respond(sid, "library timings")
        import sqlite3; self.assertEqual(sqlite3.connect(self.bot.store.path).execute("select count(*) from interactions where session_id=?", (sid,)).fetchone()[0], 0)

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.c = create_app(db_path=tempfile.mktemp(suffix=".db")).test_client()
    def test_flow(self):
        sid = self.c.post("/api/session").get_json()["session_id"]
        r = self.c.post("/api/chat", json={"session_id": sid, "message": "library timings please"}).get_json()
        self.assertEqual(r["intent"], "library"); self.assertEqual(self.c.post("/api/rate", json={"session_id": sid, "rating": 5}).status_code, 200)
        self.assertEqual(self.c.post("/api/rate", json={"session_id": sid, "rating": 9}).status_code, 400)
        self.assertEqual(self.c.post("/api/chat", json={"message": ""}).status_code, 400)
        self.assertGreaterEqual(self.c.get("/api/stats").get_json()["total"], 1)
        self.assertEqual(self.c.get("/").status_code, 200); self.assertEqual(self.c.get("/dashboard").status_code, 200)
if __name__ == "__main__": unittest.main()

# ---------------- live website sync ----------------
from live_site import extract_facts, valid, LiveSite, inr, money
FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "courses_offered_sample.html"

class TestLiveSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.facts = extract_facts(FIX.read_text(encoding="utf-8"))
    def test_parse_valid(self): self.assertTrue(valid(self.facts))
    def test_fee_numbers(self):
        f = self.facts["fee"]; self.assertEqual(f["total"], 181200); self.assertEqual(dict(f["heads"])["Tuition Fee"], 110000); self.assertEqual(f["session"], "2026-27")
    def test_fee_heads_add_up(self): self.assertEqual(sum(a for _, a in self.facts["fee"]["heads"]), self.facts["fee"]["total"])
    def test_tab_mapping_when_page_has_tabs(self):
        from live_site import fee_tabs_from_html
        tabs = fee_tabs_from_html((FIX.parent / "fee_tabs_demo.html").read_text(encoding="utf-8"))
        self.assertEqual({k: v["total"] for k, v in tabs.items()}, {"B.Tech": 1000, "B.Tech-LE": 2000, "M.Tech": 3000, "MCA": 4000, "BCA": 5000, "B.Tech-WP": 6000})
        self.assertEqual(tabs["B.Tech-WP"]["extras"], [["Examination Fees(Both Sem)", 700]])
    def test_no_tabs_found_means_no_mapping(self): self.assertEqual(self.facts.get("fee_tabs"), {})
    def test_hostel_columns(self): self.assertEqual(len(self.facts["hostel_boys"]), 6); self.assertEqual(len(self.facts["hostel_girls"]), 3)
    def test_programs_deduplicated(self): self.assertEqual(sum(p["name"] == "MCA" for p in self.facts["programs"]), 1)
    def test_bank_account_never_repeated(self):
        import json; self.assertNotRegex(json.dumps(self.facts), r"\d{10,}(?!.*Enquiry)" if False else r"0674009300045914")
    def test_inr_format(self): self.assertEqual(inr(181200), "Rs. 1,81,200"); self.assertEqual(inr(5000), "Rs. 5,000"); self.assertEqual(money("110000.00"), 110000)
    def test_bad_page_keeps_old_data(self):
        site = LiveSite(auto_refresh=False); before = dict(site.facts)
        import live_site; orig = live_site.fetch_html
        live_site.fetch_html = lambda *a, **k: "<html><body>Under maintenance</body></html>"
        try: self.assertFalse(site.refresh())
        finally: live_site.fetch_html = orig
        self.assertEqual(site.facts, before); self.assertIsNotNone(site.meta["error"])
    def test_network_failure_keeps_old_data(self):
        site = LiveSite(auto_refresh=False); import live_site; orig = live_site.fetch_html
        def boom(*a, **k): raise ConnectionError("offline")
        live_site.fetch_html = boom
        try: self.assertFalse(site.refresh())
        finally: live_site.fetch_html = orig
        self.assertTrue(valid(site.facts))
    def test_url_allow_list(self):
        import live_site
        with self.assertRaises(ValueError): live_site.fetch_html("https://evil.example.com/x")
        with self.assertRaises(ValueError): live_site.fetch_html("http://www.abes.ac.in/x")

class TestBotUsesWebsiteData(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.bot = AbesAssist(db_path=tempfile.mktemp(suffix=".db"))
    def ask(self, m): return self.bot.respond(self.bot.new_session(), m)["reply"]
    def test_fee_question_shows_real_numbers(self): self.assertIn("1,81,200", self.ask("what is the fee structure"))
    def test_hostel_fee_numbers(self): r = self.ask("what is the hostel fee"); self.assertIn("1,36,500", r); self.assertIn("1,77,500", r)
    def test_seats(self): self.assertIn("900", self.ask("which courses does abes offer and how many seats"))
    def test_bca_fee_never_shows_btech_numbers(self):
        r = self.ask("what's the bca fee structure"); self.assertNotIn("1,81,200", r.split("(For reference")[0]); self.assertIn("BCA", r)
    def test_btech_fee_still_answered(self): self.assertIn("1,81,200", self.ask("btech fee"))
    def test_programme_tab_used_when_known(self):
        b = AbesAssist(db_path=tempfile.mktemp(suffix=".db")); b.site.facts["fee_tabs"] = {"BCA": {"heads": [["Tuition Fee", 5000]], "extras": [], "total": 5000}}
        r = b.respond(b.new_session(), "bca fee structure")["reply"]; self.assertIn("Rs. 5,000", r); self.assertNotIn("1,81,200", r)
    def test_identical_table_gets_a_confirm_note(self):
        b = AbesAssist(db_path=tempfile.mktemp(suffix=".db")); same = b.site.facts["fee"]
        b.site.facts["fee_tabs"] = {"M.Tech": dict(same), "BCA": {"heads": [["Tuition Fee", 95000]], "extras": [], "total": 95000}}
        self.assertIn("exactly the same fee table", b.respond(b.new_session(), "m.tech fee")["reply"])
        self.assertNotIn("exactly the same fee table", b.respond(b.new_session(), "bca fee")["reply"])
    def test_reply_names_source(self): self.assertIn("abes.ac.in", self.ask("what is the fee structure"))
