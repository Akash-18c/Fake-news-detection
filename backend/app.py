import os
import re
import jwt
import bcrypt
import joblib
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

JWT_SECRET = os.getenv("JWT_SECRET", "fakelens_secret")

# ── MongoDB Atlas ─────────────────────────────────────────────────────────────
try:
    client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client["fakenews_db"]
    users_col   = db["users"]
    history_col = db["history"]
    # indexes
    users_col.create_index("email", unique=True)
    history_col.create_index("user_id")
    MONGO_OK = True
    print("[INFO] MongoDB Atlas connected")
except Exception as e:
    print(f"[ERROR] MongoDB connection failed: {e}")
    MONGO_OK = False

# ── Load ML model ─────────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Telugu_F&R_News")
model = joblib.load(os.path.join(MODEL_DIR, "fake_news_model.pkl"))
tfidf = joblib.load(os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
print(f"[INFO] Model loaded: {type(model).__name__}")


# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_text(text):
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[a-zA-Z0-9]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def make_token(user_id, name):
    return jwt.encode(
        {"user_id": str(user_id), "name": name,
         "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        JWT_SECRET, algorithm="HS256"
    )


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            request.user_id = data["user_id"]
            request.user_name = data["name"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired, please login again"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    result = users_col.insert_one({
        "name": name, "email": email,
        "password": hashed,
        "created_at": datetime.now(timezone.utc)
    })
    token = make_token(result.inserted_id, name)
    return jsonify({"token": token, "name": name, "email": email}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = users_col.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = make_token(user["_id"], user["name"])
    return jsonify({"token": token, "name": user["name"], "email": email})


@app.route("/api/auth/me", methods=["GET"])
@token_required
def me():
    return jsonify({"name": request.user_name, "user_id": request.user_id})


# ── Predict ───────────────────────────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
@token_required
def predict():
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    cleaned = clean_text(text)
    if len(cleaned) < 10:
        return jsonify({"error": "Text too short — paste a longer news article"}), 400

    features   = tfidf.transform([cleaned])
    proba      = model.predict_proba(features)[0]
    pred       = model.predict(features)[0]
    label      = "REAL" if int(pred) == 1 else "FAKE"
    confidence = round(float(max(proba)) * 100, 1)

    doc_id = None
    if MONGO_OK:
        try:
            res = history_col.insert_one({
                "user_id":    request.user_id,
                "text":       text[:500],
                "label":      label,
                "confidence": confidence,
                "timestamp":  datetime.now(timezone.utc),
            })
            doc_id = str(res.inserted_id)
        except Exception as e:
            print(f"[WARNING] Insert failed: {e}")

    return jsonify({"label": label, "confidence": confidence, "id": doc_id})


# ── History (per user) ────────────────────────────────────────────────────────
@app.route("/api/history", methods=["GET"])
@token_required
def get_history():
    if not MONGO_OK:
        return jsonify([])
    limit = int(request.args.get("limit", 30))
    docs = list(
        history_col.find({"user_id": request.user_id})
        .sort("timestamp", -1).limit(limit)
    )
    return jsonify([{
        "id":         str(d["_id"]),
        "text":       d["text"],
        "label":      d["label"],
        "confidence": d.get("confidence"),
        "timestamp":  d["timestamp"].isoformat(),
    } for d in docs])


@app.route("/api/history/<doc_id>", methods=["DELETE"])
@token_required
def delete_one(doc_id):
    if MONGO_OK:
        history_col.delete_one({"_id": ObjectId(doc_id), "user_id": request.user_id})
    return jsonify({"ok": True})


@app.route("/api/history", methods=["DELETE"])
@token_required
def clear_history():
    if MONGO_OK:
        history_col.delete_many({"user_id": request.user_id})
    return jsonify({"ok": True})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mongo": MONGO_OK})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
