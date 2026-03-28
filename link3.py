from fastapi import FastAPI, UploadFile, File
import pandas as pd
import numpy as np
import joblib
import RPi.GPIO as GPIO
import time
import threading

app = FastAPI()

# ---------------- GPIO SETUP ----------------
PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)
GPIO.output(PIN, GPIO.HIGH)  # OFF initially

# ---------------- LOAD MODEL ----------------
model = joblib.load("stress_model.pkl")
scaler = joblib.load("scaler.pkl")

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

# ---------------- PIEZO (YOUR LOGIC, NON-BLOCKING) ----------------
def trigger_piezo():
    print("🚨 HIGH STRESS DETECTED → Activating Piezo")

    GPIO.output(PIN, GPIO.LOW)   # ON
    time.sleep(5)
    GPIO.output(PIN, GPIO.HIGH)  # OFF

def trigger_piezo_async():
    threading.Thread(target=trigger_piezo).start()

# ---------------- ROUTE ----------------
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)

    score = predict_stress_df(df)

    print(f"Stress Score: {score:.2f}")  # DEBUG

    if score <= 0.33:
        level = "LOW"

    elif score <= 0.66:
        level = "MEDIUM"

    else:
        level = "HIGH"
        trigger_piezo_async()  # 🔥 THIS IS THE KEY LINE

    return {
        "score": float(score),
        "level": level
    }
