"""
train_model.py — Run once locally or automatically on Render during build.
Usage: python train_model.py
"""
import os, re, joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# Works both locally (d:\FakeNewsProject) and on Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "Telugu_F&R_News")

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
            print(f"  [SKIP] {sub}")
            continue
        for fname in os.listdir(sub):
            fpath = os.path.join(sub, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text:
                    rows.append({"text": text, "label": label})
            except Exception:
                pass

df = pd.DataFrame(rows)
print(f"Total rows: {len(df)}")
print(df["label"].value_counts().to_string())

# ── 2. Clean ──────────────────────────────────────────────────────────────────
def clean_text(text):
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[a-zA-Z0-9]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()

print("Cleaning text...")
df["clean"] = df["text"].apply(clean_text)
df = df[df["clean"].str.len() > 10].reset_index(drop=True)
print(f"Rows after cleaning: {len(df)}")

# ── 3. Split ──────────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    df["clean"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

# ── 4. TF-IDF ─────────────────────────────────────────────────────────────────
print("Fitting TF-IDF...")
tfidf = TfidfVectorizer(max_features=50000, ngram_range=(1, 2), sublinear_tf=True)
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf  = tfidf.transform(X_test)

# ── 5. Train ──────────────────────────────────────────────────────────────────
print("Training Logistic Regression...")
model = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", solver="lbfgs")
model.fit(X_train_tfidf, y_train)

y_pred = model.predict(X_test_tfidf)
acc = accuracy_score(y_test, y_pred)
print(f"Accuracy: {acc:.4f}")
print(classification_report(y_test, y_pred, target_names=["Fake", "Real"]))

# ── 6. Save ───────────────────────────────────────────────────────────────────
os.makedirs(SAVE_DIR, exist_ok=True)
joblib.dump(model, os.path.join(SAVE_DIR, "fake_news_model.pkl"))
joblib.dump(tfidf,  os.path.join(SAVE_DIR, "tfidf_vectorizer.pkl"))
print(f"Saved to: {SAVE_DIR}")
print("Done!")
