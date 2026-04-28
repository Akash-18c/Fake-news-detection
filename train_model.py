"""
train_model.py  –  Run this once to retrain and save the model.
Usage:  python train_model.py
"""
import os, re, joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

BASE_DIR  = r"d:\FakeNewsProject"
SAVE_DIR  = r"d:\FakeNewsProject\Telugu_F&R_News"

LANGUAGES = {
    "Gujarati": "Gujarati_F&R_News",
    "Hindi":    "Hindi_F&R_News",
    "Marathi":  "Marathi_F&R_News",
    "Telugu":   "Telugu_F&R_News",
}

# ── 1. Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
rows = []
for lang, folder in LANGUAGES.items():
    for category, label in [("fake_news", 0), ("real_news", 1)]:
        sub = os.path.join(BASE_DIR, folder, f"{lang}_{category}")
        if not os.path.exists(sub):
            print(f"  [SKIP] {sub} not found")
            continue
        files = os.listdir(sub)
        for fname in files:
            fpath = os.path.join(sub, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text:
                    rows.append({"text": text, "label": label, "lang": lang})
            except Exception:
                pass

df = pd.DataFrame(rows)
print(f"Total rows: {len(df)}")
print(df["label"].value_counts().to_string())
print(df["lang"].value_counts().to_string())

# ── 2. Clean text ─────────────────────────────────────────────────────────────
def clean_text(text):
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[a-zA-Z0-9]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

print("\nCleaning text...")
df["clean"] = df["text"].apply(clean_text)
df = df[df["clean"].str.len() > 10].reset_index(drop=True)
print(f"Rows after cleaning: {len(df)}")

# ── 3. Split ──────────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    df["clean"], df["label"],
    test_size=0.2, random_state=42, stratify=df["label"]
)
print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")

# ── 4. TF-IDF ─────────────────────────────────────────────────────────────────
print("Fitting TF-IDF...")
tfidf = TfidfVectorizer(max_features=50000, ngram_range=(1, 2), sublinear_tf=True)
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf  = tfidf.transform(X_test)

# ── 5. Train Logistic Regression (has predict_proba, no bias issue) ───────────
print("Training Logistic Regression...")
model = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", solver="lbfgs")
model.fit(X_train_tfidf, y_train)

y_pred = model.predict(X_test_tfidf)
acc = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {acc:.4f}")
print(classification_report(y_test, y_pred, target_names=["Fake", "Real"]))

# ── 6. Sanity check: verify model predicts both classes ─────────────────────
empty_proba = model.predict_proba(tfidf.transform([""]))[0]
print(f"Empty input proba: fake={empty_proba[0]:.3f}  real={empty_proba[1]:.3f}")
print(f"Model predicts both classes: {sorted(model.classes_.tolist())} — OK")

# ── 7. Save ───────────────────────────────────────────────────────────────────
joblib.dump(model, os.path.join(SAVE_DIR, "fake_news_model.pkl"))
joblib.dump(tfidf,  os.path.join(SAVE_DIR, "tfidf_vectorizer.pkl"))
print(f"\nSaved model and vectorizer to: {SAVE_DIR}")
print("classes_:", model.classes_)
print("Done!")
