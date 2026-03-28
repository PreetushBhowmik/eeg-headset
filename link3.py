from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
import joblib
import RPi.GPIO as GPIO
import time
import threading
import os

app = FastAPI()

# ---------------- GPIO SETUP ----------------
PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)
GPIO.output(PIN, GPIO.HIGH)  # OFF initially

# ---------------- LOAD MODEL ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "stress_model.pkl"))
scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))

# ---------------- FEATURE EXTRACTION ----------------
def extract_features(df):
    return [
        df.mean().mean(),
        df.std().mean(),
        df.max().mean(),
        df.min().mean()
    ]

# ---------------- PREDICTION ----------------
def predict_stress_df(df):
    features = np.array(extract_features(df)).reshape(1, -1)
    features = scaler.transform(features)
    return model.predict_proba(features)[0][1]

# ---------------- PIEZO (YOUR LOGIC) ----------------
def trigger_piezo():
    print("🚨 HIGH STRESS DETECTED → Activating Piezo")

    GPIO.output(PIN, GPIO.LOW)   # ON
    time.sleep(5)
    GPIO.output(PIN, GPIO.HIGH)  # OFF

def trigger_piezo_async():
    threading.Thread(target=trigger_piezo).start()

# ---------------- WEB UI ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Stress Detection</title>
        </head>
        <body>
            <h2>Upload CSV File</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button type="submit">Upload</button>
            </form>
        </body>
    </html>
    """

# ---------------- FILE UPLOAD ----------------
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)

        score = predict_stress_df(df)
        print(f"Stress Score: {score:.2f}")

        if score <= 0.33:
            level = "LOW"

        elif score <= 0.66:
            level = "MEDIUM"

        else:
            level = "HIGH"
            trigger_piezo_async()  # 🔥 PIEZO TRIGGER

        return {
            "score": float(score),
            "level": level
        }

    except Exception as e:
        return {"error": str(e)}
