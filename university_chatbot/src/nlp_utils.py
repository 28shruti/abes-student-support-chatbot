"""Shared NLP helpers: tokenizer/stemmer, PII redaction, augmentation."""
import re, random
from nltk.stem import PorterStemmer

_stemmer = PorterStemmer()
_TOKEN = re.compile(r"[a-z0-9']+")
_STOP = {"the","a","an","is","are","am","of","to","in","on","at","for","and","or","do","does","did","my","me","i",
         "you","your","it","this","that","be","can","could","would","will","please","hi","hello","hey","sir","tell","know","want"}

def stem_tokenizer(text: str):
    """lower-case -> regex tokens -> drop stop-words -> Porter stem."""
    toks = _TOKEN.findall(text.lower())
    return [_stemmer.stem(t) for t in toks if t not in _STOP]

# ---------------- PII redaction (ethical requirement: no PII stored beyond session) --------------
PII_PATTERNS = [
    ("email",   re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("aadhaar", re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")),
    ("phone",   re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")),
    ("card",    re.compile(r"\b(?:\d[ -]?){13,16}\b")),
]
def redact_pii(text: str):
    """Return (redacted_text, [types_found])."""
    found = []
    for name, pat in PII_PATTERNS:
        if pat.search(text):
            found.append(name)
            text = pat.sub(f"[{name.upper()}_REMOVED]", text)
    return text, found

# ---------------- data augmentation for the small training corpus ---------------------------------
_PRE = ["hi", "hello", "hey,", "please tell me", "excuse me,", "sir,", "i want to know", "can you help me,", "quick question:", "pls"]
_SUF = ["please", "thanks", "urgent", "?", "kindly reply", "thank you"]

def _typo(s, rng):
    w = s.split()
    cand = [i for i, x in enumerate(w) if len(x) > 4]
    if not cand: return s
    i = rng.choice(cand); x = w[i]; j = rng.randrange(1, len(x) - 2)
    w[i] = x[:j] + x[j + 1] + x[j] + x[j + 2:]
    return " ".join(w)

def augment(text: str, rng: random.Random, n=4):
    out = [text]
    for _ in range(n):
        t = text
        r = rng.random()
        if r < .3: t = f"{rng.choice(_PRE)} {t[0].lower() + t[1:]}"
        elif r < .55: t = f"{t.rstrip('?.')} {rng.choice(_SUF)}"
        elif r < .8: t = _typo(t, rng)
        else: t = t.lower().rstrip("?.")
        out.append(t)
    return list(dict.fromkeys(out))
