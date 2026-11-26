"""Flask web app + REST API for Abes Assist.  Run:  python src/app.py   ->  http://127.0.0.1:5000"""
import pathlib, sys
from flask import Flask, jsonify, request, render_template
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chatbot import AbesAssist, ROOT

def create_app(db_path=None, live=True):
    app = Flask(__name__, template_folder=str(ROOT / "templates"))
    bot = AbesAssist(db_path=db_path, live=live)
    app.bot = bot

    @app.get("/")
    def index(): return render_template("index.html")

    @app.get("/dashboard")
    def dashboard(): return render_template("dashboard.html")

    @app.post("/api/session")
    def session(): return jsonify(session_id=bot.new_session())

    @app.post("/api/chat")
    def chat():
        d = request.get_json(silent=True) or {}
        msg = (d.get("message") or "").strip()
        if not msg: return jsonify(error="message is required"), 400
        sid = d.get("session_id") or bot.new_session()
        r = bot.respond(sid, msg)
        return jsonify(r)

    @app.post("/api/rate")
    def rate():
        d = request.get_json(silent=True) or {}
        try: rating = int(d.get("rating"))
        except (TypeError, ValueError): return jsonify(error="rating 1-5 required"), 400
        if not 1 <= rating <= 5: return jsonify(error="rating 1-5 required"), 400
        sid = d.get("session_id")
        if sid and not bot.sessions.get(sid, {}).get("opt_out"): bot.store.rate(sid, rating)
        return jsonify(ok=True)

    @app.post("/api/optout")
    def optout():
        sid = (request.get_json(silent=True) or {}).get("session_id")
        if sid: bot.opt_out(sid)
        return jsonify(ok=True, message="Opted out: your session data was deleted and nothing further will be logged.")

    @app.post("/api/end")
    def end():
        sid = (request.get_json(silent=True) or {}).get("session_id")
        bot.end_session(sid); return jsonify(ok=True)

    @app.get("/api/site-status")
    def site_status(): return jsonify(bot.site.meta)

    @app.get("/api/stats")
    def stats(): return jsonify(bot.store.stats())

    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
