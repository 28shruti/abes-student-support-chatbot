# Demo Script (1–2 minutes) – Abes Assist

Record your screen (Windows: Win+G / OBS) with the app running at http://127.0.0.1:5000. Speak over it; ~90 seconds.

| Time | Do | Say |
|---|---|---|
| 0:00 | Show the chat page | "This is Abes Assist, an AI chatbot for university student support. It answers FAQs, and escalates to a human when needed. Note the privacy notice at the top." |
| 0:10 | Type **How do I pay my fees online?** | "It detects the *fees* intent with high confidence, and returns the approved FAQ answer in a few milliseconds." |
| 0:25 | Click a suggested chip, or type **hall ticket kaise download kare / Where can I download my hall ticket?** | "Follow-up suggestions and typo/Hinglish tolerance." |
| 0:35 | Type **what is the weather today** | "Out-of-scope questions are politely redirected." |
| 0:45 | Type **my number is 9876543210 and hostel wifi not working** | "The phone number is removed automatically – PII is never processed or stored." |
| 0:58 | Type **You people are useless, nobody replies to my complaint** | "Strong negative sentiment triggers escalation. See the red badge, ticket number and reason." |
| 1:10 | Type **I was ragged by seniors yesterday** | "Safety incidents are escalated with priority." |
| 1:20 | Click **Opt out of data logging**, then open `/dashboard` | "Students can opt out any time; the dashboard shows only anonymous statistics." |
| 1:30 | Show terminal: `python -m unittest tests.test_chatbot` (11 tests OK) and `models/system_metrics.json` | "Intent accuracy ≈ 82 %, FAQ retrieval ≈ 96 %, escalation F1 ≈ 1.0 on my test set, ~3 ms latency." |

Tip: the numbers above come from `models/intent_metrics.json` and `models/system_metrics.json` – say what your files show.
