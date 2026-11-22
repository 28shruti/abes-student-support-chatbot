"""Train + evaluate the intent classifier. Honest evaluation: split BASE utterances first, augment only the train part."""
import json, random, pathlib, sys
import numpy as np, joblib, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from intent_data import UTTERANCES
from nlp_utils import stem_tokenizer, augment

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = 42; rng = random.Random(SEED)

def features():
    return FeatureUnion([
        ("word", TfidfVectorizer(tokenizer=stem_tokenizer, token_pattern=None, lowercase=False, ngram_range=(1, 2), sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)),
    ])

def make(clf): return Pipeline([("feat", features()), ("clf", clf)])

def split_base():
    tr, te = [], []
    for intent, utts in UTTERANCES.items():
        u = utts[:]; rng.shuffle(u); k = int(round(len(u) * 0.25))
        te += [(x, intent) for x in u[:k]]; tr += [(x, intent) for x in u[k:]]
    return tr, te

def expand(pairs):
    X, y = [], []
    for t, l in pairs:
        for a in augment(t, rng): X.append(a); y.append(l)
    return X, y

if __name__ == "__main__":
    train, test = split_base()
    Xtr, ytr = expand(train); Xte, yte = [t for t, _ in test], [l for _, l in test]
    print(f"base train {len(train)} -> augmented {len(Xtr)} | held-out test {len(Xte)} (unaugmented, unseen)")
    models = {
        "Logistic Regression (word+char TF-IDF)": LogisticRegression(C=20, max_iter=2000),
        "Linear SVM": LinearSVC(C=1.0),
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.05),
        "Random Forest": RandomForestClassifier(n_estimators=300, random_state=SEED),
    }
    res = {}
    for name, clf in models.items():
        p = make(clf)
        # NB needs non-negative features (TF-IDF is fine)
        p.fit(Xtr, ytr); pred = p.predict(Xte)
        res[name] = dict(accuracy=round(accuracy_score(yte, pred), 4), macro_f1=round(f1_score(yte, pred, average="macro"), 4))
        print(name, res[name])
    best = "Logistic Regression (word+char TF-IDF)"
    p = make(models[best]).fit(Xtr, ytr); pred = p.predict(Xte); proba = p.predict_proba(Xte)
    labels = sorted(UTTERANCES)
    rep = classification_report(yte, pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(yte, pred, labels=labels)

    # 5-fold CV on base train utterances (augment inside each fold -> no leakage)
    base_X = np.array([t for t, _ in train], dtype=object); base_y = np.array([l for _, l in train])
    cv = []
    for a, b in StratifiedKFold(5, shuffle=True, random_state=SEED).split(base_X, base_y):
        Xa, ya = expand(list(zip(base_X[a], base_y[a])))
        m = make(LogisticRegression(C=20, max_iter=2000)).fit(Xa, ya)
        cv.append(accuracy_score(base_y[b], m.predict(list(base_X[b]))))
    # confidence behaviour: in-domain vs out-of-scope
    OOS = ["is it hot outside right now", "who scored the winning goal", "how do i install java", "what is the best laptop under 50000", "tell me a funny story", "what is the capital of france", "best pizza place nearby", "how to book a flight ticket",
           "explain quantum physics", "asdf qwer zxcv", "recommend a good movie", "what is bitcoin price", "how do I cook pasta",
           "play some music", "who is the prime minister", "what is the meaning of life"]
    conf_in = proba.max(axis=1); po = p.predict_proba(OOS); conf_oos = po.max(axis=1)
    oos_caught = float(np.mean([(p.classes_[i] == "out_of_scope") or (c < 0.40) for i, c in zip(po.argmax(1), conf_oos)]))
    thr = {}
    for t in (0.30, 0.35, 0.40, 0.45, 0.50):
        thr[str(t)] = dict(in_domain_accepted=round(float((conf_in >= t).mean()), 3), oos_rejected=round(float((conf_oos < t).mean()), 3))
    print("threshold table", thr)

    final = make(LogisticRegression(C=20, max_iter=2000))
    allX, ally = expand([(t, l) for l, us in UTTERANCES.items() for t in us])
    final.fit(allX, ally)
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump(final, ROOT / "models" / "intent_model.joblib")

    # write labelled corpus for transparency
    import csv
    with open(ROOT / "data" / "intent_training_data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["utterance", "intent", "split"])
        tr_set = {t for t, _ in train}
        for l, us in UTTERANCES.items():
            for t in us: w.writerow([t, l, "train" if t in tr_set else "test"])

    metrics = dict(n_base=sum(len(v) for v in UTTERANCES.values()), n_train_base=len(train), n_train_aug=len(Xtr), n_test=len(Xte),
                   model_comparison=res, chosen=best, test_accuracy=res[best]["accuracy"], test_macro_f1=res[best]["macro_f1"],
                   cv_accuracy_mean=round(float(np.mean(cv)), 4), cv_accuracy_std=round(float(np.std(cv)), 4),
                   per_class={k: {m: round(v[m], 3) for m in ("precision", "recall", "f1-score")} | {"support": int(v["support"])} for k, v in rep.items() if k in labels},
                   confidence_in_domain_mean=round(float(conf_in.mean()), 3), confidence_oos_mean=round(float(conf_oos.mean()), 3),
                   threshold_table=thr, oos_caught_by_class_or_threshold=round(oos_caught,3), confusion_matrix=cm.tolist(), labels=labels)
    (ROOT / "models" / "intent_metrics.json").write_text(json.dumps(metrics, indent=2))
    fig, ax = plt.subplots(figsize=(6.2, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=40, ha="right"); ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)): ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xlabel("Predicted intent"); ax.set_ylabel("True intent"); ax.set_title("Intent classifier – confusion matrix (held-out test)")
    plt.tight_layout(); plt.savefig(ROOT / "figures" / "fig_confusion_matrix.png", dpi=160); plt.close()
    print(json.dumps({k: metrics[k] for k in ("test_accuracy", "test_macro_f1", "cv_accuracy_mean", "cv_accuracy_std", "confidence_in_domain_mean", "confidence_oos_mean")}, indent=1))
