# Abes Assist – AI-Powered Chatbot for University Student Support
HCLTech Career Shaper Programme · Project 30 · Python / Flask / scikit-learn / VADER / SQLite

**What it does:** classifies a student's message into 7 helpdesk intents (+ out-of-scope), returns the best FAQ answer, scores sentiment, and **escalates to a human agent** (red badge + ticket) when the student asks, is very unhappy, reports an incident/safety issue, or the bot repeatedly fails. PII is redacted; message text is never stored; opt-out is built in.

## Quick start
```bash
pip install -r requirements.txt
python src/train_intent.py      # trains model -> models/intent_model.joblib (+ metrics, confusion matrix)
python src/evaluate.py          # escalation / FAQ / latency / privacy evaluation
python -m unittest tests.test_chatbot   # 11 tests
python src/app.py               # open http://127.0.0.1:5000   (dashboard: /dashboard)
```
`python src/make_notebook.py` + running `notebooks/EDA_Notebook.ipynb` reproduces the EDA, the cleaned `data/dataset.csv` and the extended `data/data_dictionary.csv`.

## Folder map
| Path | Content |
|---|---|
| `data/dataset.csv` | cleaned & feature-engineered dataset (500 × 11); original in `dataset_raw.csv` |
| `data/data_dictionary.csv` | all columns described (original + 5 engineered) |
| `data/faq_knowledge_base.csv` | 57 **sample** FAQs – replace with your university's real policies |
| `data/intent_training_data.csv` | 288 labelled utterances with train/test split flag |
| `notebooks/EDA_Notebook.ipynb` | executed EDA, 6 visualisations, statistical tests |
| `src/` | app.py, chatbot.py (engine), nlp_utils.py, train_intent.py, evaluate.py, … |
| `docs/Project_Report.docx` | 18-page project report |
| `Project_Synopsis_[YourName]_[RollNo].docx` | filled synopsis (rename + add your details) |

## Honest notes
* `dataset.csv` has no message text → the NLP corpus and FAQ base were authored for this project. Test sets are small and self-authored; expect lower accuracy on real student messages.
* The FAQ answers are generic sample content (flagged in the CSV).
* Prototype only: in-memory sessions, no authentication, tickets not connected to a real helpdesk tool.
