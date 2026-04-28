import os
import re
import joblib

SAVE_DIR = r"d:\FakeNewsProject\Telugu_F&R_News"

def clean_text(text):
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)
    text = re.sub(r"[a-zA-Z0-9]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

model   = joblib.load(os.path.join(SAVE_DIR, "fake_news_model.pkl"))
tfidf   = joblib.load(os.path.join(SAVE_DIR, "tfidf_vectorizer.pkl"))

# Verify label mapping by checking model.classes_
# fake_news=0, real_news=1  (as labeled during training)
# model.classes_ tells us the actual order sklearn used
print("Model classes:", model.classes_)

def predict(text):
    cleaned  = clean_text(text)
    features = tfidf.transform([cleaned])
    pred     = model.predict(features)[0]
    # 0 = fake, 1 = real  (matches training labels)
    return "REAL" if pred == 1 else "FAKE"

if __name__ == "__main__":
    test_cases = [
        "एका व्यक्तीने 15 वर्षे झोप न घेता जगल्याचा दावा केला।",
        "భారత ప్రభుత్వం కొత్త విద్యా విధానాన్ని ప్రకటించింది.",
    ]
    for news in test_cases:
        print(f"Text: {news[:60]}...")
        print(f"Prediction: {predict(news)}\n")
