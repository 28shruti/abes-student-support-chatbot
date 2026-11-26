import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import pathlib
FIG = pathlib.Path(__file__).resolve().parent.parent / "figures"

def box(ax, x, y, w, h, t, fc="#e8efff", ec="#1f4fd8", fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal", wrap=True)
def arr(ax, p, q, t="", off=(0, 0.1), color="#333", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13, lw=1.3, color=color, linestyle=ls))
    if t: ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], t, fontsize=7.5, ha="center", color=color)

# ---- System block diagram ----
fig, ax = plt.subplots(figsize=(12, 6.3)); ax.set_xlim(0, 12); ax.set_ylim(0, 6.3); ax.axis("off")
ax.set_title("Figure 1 – Abes Assist system block diagram", fontsize=13, weight="bold")
box(ax, 0.2, 2.6, 1.7, 1.1, "Student\n(Web chat UI)\nHTML / JS", "#fff4d6", "#b7791f", bold=True)
box(ax, 2.5, 2.6, 1.7, 1.1, "Flask REST API\n/api/chat\n/api/rate /optout", "#e8efff", bold=True)
box(ax, 4.8, 4.5, 1.9, 1.0, "1. PII redaction\n(regex: e-mail, phone,\nAadhaar, card)", "#e6f6ec", "#2f855a")
box(ax, 4.8, 3.2, 1.9, 1.0, "2. Small-talk &\nsafety rules\n(greeting / self-harm)", "#e6f6ec", "#2f855a")
box(ax, 4.8, 1.9, 1.9, 1.0, "3. Intent classifier\nTF-IDF word+char\n+ Logistic Regression", "#e6f6ec", "#2f855a")
box(ax, 4.8, 0.6, 1.9, 1.0, "4. FAQ retrieval\nTF-IDF cosine\nsimilarity (57 FAQs)", "#e6f6ec", "#2f855a")
box(ax, 7.3, 3.4, 1.9, 1.2, "5. Sentiment analysis\nVADER + domain\nlexicon", "#fdeaea", "#c53030")
box(ax, 7.3, 1.6, 1.9, 1.5, "6. Escalation policy\nhuman request,\nnegative sentiment,\nsafety, 2x low conf.", "#fdeaea", "#c53030", bold=True)
box(ax, 7.3, 0.3, 1.9, 0.9, "FAQ knowledge base\n(CSV)", "#f1f1f1", "#555")
box(ax, 9.8, 2.0, 2.0, 1.2, "SQLite\nanonymous metadata only\n(no message text)", "#f1f1f1", "#555")
box(ax, 9.8, 0.4, 2.0, 1.0, "Human support queue\n(tickets HT-xxxx)", "#fff4d6", "#b7791f", bold=True)
arr(ax, (1.9, 3.15), (2.5, 3.15)); arr(ax, (4.2, 3.15), (4.8, 4.9)); arr(ax, (5.75, 4.5), (5.75, 4.2)); arr(ax, (5.75, 3.2), (5.75, 2.9)); arr(ax, (5.75, 1.9), (5.75, 1.6))
arr(ax, (6.7, 2.4), (7.3, 2.4)); arr(ax, (6.7, 4.0), (7.3, 3.9)); arr(ax, (8.25, 3.4), (8.25, 3.1))
arr(ax, (9.2, 2.3), (9.8, 2.5), "log", (0, .12)); arr(ax, (9.2, 1.9), (9.8, 1.0), "ticket", (0.1, -.25), "#c53030")
arr(ax, (7.3, 0.8), (6.7, 1.0), "lookup", (0, -0.28), "#555", "--")
arr(ax, (3.35, 2.6), (3.35, 0.8), "", (0, 0)); ax.text(3.35, 0.5, "reply + escalation badge\nback to student", ha="center", fontsize=8, color="#333")
plt.tight_layout(); plt.savefig(FIG / "fig_architecture_block.png", dpi=170); plt.close()

# ---- DFD level 0 ----
fig, ax = plt.subplots(figsize=(11, 5.4)); ax.set_xlim(0, 11); ax.set_ylim(0, 5.4); ax.axis("off")
ax.set_title("Figure 2 – Data Flow Diagram, Level 0 (context diagram)", fontsize=13, weight="bold")
box(ax, 0.3, 2.0, 2.0, 1.3, "STUDENT\n(external entity)", "#fff4d6", "#b7791f", bold=True)
box(ax, 8.6, 3.6, 2.1, 1.2, "HUMAN SUPPORT\nAGENT\n(external entity)", "#fff4d6", "#b7791f", bold=True)
box(ax, 8.6, 0.5, 2.1, 1.2, "UNIVERSITY ADMIN\n(maintains FAQ content)", "#fff4d6", "#b7791f", bold=True)
ax.add_patch(Circle((5.4, 2.65), 1.55, fc="#e8efff", ec="#1f4fd8", lw=2)); ax.text(5.4, 2.65, "0\nAI Chatbot\nStudent Support\nSystem", ha="center", va="center", fontsize=11, weight="bold")
arr(ax, (2.3, 2.9), (3.9, 2.9), "question (text)", (0, .15)); arr(ax, (3.9, 2.4), (2.3, 2.4), "answer / FAQ link /\nescalation notice", (0, -.45))
arr(ax, (6.5, 3.75), (8.6, 4.1), "escalation ticket\n(intent, reason)", (0, .25), "#c53030"); arr(ax, (8.6, 3.7), (6.8, 3.4), "agent reply via portal", (.3, -.3), "#c53030", "--")
arr(ax, (8.6, 1.3), (6.7, 1.8), "FAQ updates /\nretraining data", (0.2, -.5))
arr(ax, (4.5, 1.15), (4.5, 0.45), "", (0, 0)); ax.text(4.5, 0.15, "anonymous metrics (no PII) → dashboard", ha="center", fontsize=8)
ax.text(0.3, 0.7, "Privacy rule: raw message text and PII\nare never stored; only anonymous\nintent / confidence / rating / flags.", fontsize=8.5, color="#2f855a", va="center")
plt.tight_layout(); plt.savefig(FIG / "fig_dfd_level0.png", dpi=170); plt.close()

# ---- Escalation flowchart ----
fig, ax = plt.subplots(figsize=(11, 4.4)); ax.set_xlim(0, 11); ax.set_ylim(0, 4.4); ax.axis("off")
ax.set_title("Figure 3 – Escalation decision logic", fontsize=13, weight="bold")
box(ax, 0.1, 1.7, 1.5, 1.0, "Student\nmessage", "#fff4d6", "#b7791f")
box(ax, 2.0, 1.7, 1.6, 1.0, "Redact PII\nPredict intent\nScore sentiment", "#e6f6ec", "#2f855a")
rules = ["Self-harm / assault keywords  →  URGENT + helpline", "Incident report (\"I was ragged / harassed\")  →  URGENT", "Student asks for a human  →  ESCALATE",
         "Sentiment ≤ −0.50  (≤ −0.25 for grievance)  →  ESCALATE", "Low confidence (<0.40) twice in a row  →  ESCALATE"]
for i, r in enumerate(rules): box(ax, 4.1, 3.5 - i * 0.78, 4.3, 0.6, r, "#fdeaea", "#c53030", fs=8)
box(ax, 8.9, 2.5, 2.0, 1.1, "YES → ticket created,\nred badge shown,\nFAQ answer attached", "#fdeaea", "#c53030", bold=True)
box(ax, 8.9, 0.6, 2.0, 1.1, "NO → bot answers\nfrom FAQ KB (or asks\nto rephrase once)", "#e6f6ec", "#2f855a", bold=True)
arr(ax, (1.6, 2.2), (2.0, 2.2)); arr(ax, (3.6, 2.2), (4.1, 2.2)); arr(ax, (8.4, 3.0), (8.9, 3.0)); arr(ax, (8.4, 1.4), (8.9, 1.1), "none fire", (0, -.25))
plt.tight_layout(); plt.savefig(FIG / "fig_escalation_logic.png", dpi=170); plt.close(); print("ok")
