import os
import re
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── MongoDB ───────────────────────────────────────────────────────────────────
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    client.server_info()
    db = client["fakenews_db"]
    history_col = db["history"]
    MONGO_OK = True
    print("[INFO] MongoDB connected")
except Exception as e:
    print(f"[WARNING] MongoDB not available: {e}")
    MONGO_OK = False
    history_col = None

# ── Load model ────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Telugu_F&R_News")
model = joblib.load(os.path.join(MODEL_DIR, "fake_news_model.pkl"))
tfidf = joblib.load(os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
print(f"[INFO] Model loaded: {type(model).__name__}  classes={model.classes_}")


def clean_text(text):
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[a-zA-Z0-9]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def predict_label(text):
    """Returns (label, confidence_percent)"""
    cleaned  = clean_text(text)
    features = tfidf.transform([cleaned])

    # predict_proba gives clean 0-1 probabilities, no bias issue
    proba = model.predict_proba(features)[0]   # [prob_fake, prob_real]
    pred  = model.predict(features)[0]         # 0=FAKE, 1=REAL

    label      = "REAL" if int(pred) == 1 else "FAKE"
    confidence = round(float(max(proba)) * 100, 1)
    return label, confidence


@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True, silent=True)
    text = (data or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    cleaned = clean_text(text)
    if len(cleaned) < 10:
        return jsonify({"error": "Text too short — please paste a longer news article in Hindi / Telugu / Marathi / Gujarati"}), 400

    label, confidence = predict_label(text)

    record = {
        "text":       text[:500],
        "label":      label,
        "confidence": confidence,
        "timestamp":  datetime.now(timezone.utc),
    }
    doc_id = None
    if MONGO_OK and history_col is not None:
        try:
            doc_id = str(history_col.insert_one(record).inserted_id)
        except Exception as e:
            print(f"[WARNING] MongoDB insert failed: {e}")

    return jsonify({"label": label, "confidence": confidence, "id": doc_id})


@app.route("/api/history", methods=["GET"])
def get_history():
    if not MONGO_OK or history_col is None:
        return jsonify([])
    limit = int(request.args.get("limit", 30))
    try:
        docs = list(history_col.find().sort("timestamp", -1).limit(limit))
    except Exception:
        return jsonify([])
    return jsonify([{
        "id":         str(d["_id"]),
        "text":       d["text"],
        "label":      d["label"],
        "confidence": d.get("confidence"),
        "timestamp":  d["timestamp"].isoformat(),
    } for d in docs])


@app.route("/api/history/<doc_id>", methods=["DELETE"])
def delete_history(doc_id):
    if MONGO_OK and history_col is not None:
        from bson import ObjectId
        try:
            history_col.delete_one({"_id": ObjectId(doc_id)})
        except Exception:
            pass
    return jsonify({"ok": True})


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    if MONGO_OK and history_col is not None:
        try:
            history_col.delete_many({})
        except Exception:
            pass
    return jsonify({"ok": True})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mongo": MONGO_OK, "model": type(model).__name__})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
