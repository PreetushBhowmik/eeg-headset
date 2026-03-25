from fastapi import FastAPI
import pandas as pd
import numpy as np
import joblib
import RPi.GPIO as GPIO

app = FastAPI()

# GPIO setup
PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

# Load model
model = joblib.load("stress_model.pkl")
scaler = joblib.load("scaler.pkl")

def extract_features(df):
    return [
        df.mean().mean(),
        df.std().mean(),
        df.max().mean(),
        df.min().mean()
    ]

def predict_stress(file_path):
    df = pd.read_csv(file_path)
    features = np.array(extract_features(df)).reshape(1, -1)
    features = scaler.transform(features)
    return model.predict_proba(features)[0][1]

# ---------------- API ----------------

@app.get("/")
def home():
    return {"message": "Stress API running"}

@app.get("/stress")
def get_stress():
    score = predict_stress("test.csv")  # replace later with real data
    
    if score <= 0.33:
        level = "LOW"
    elif score <= 0.66:
        level = "MEDIUM"
    else:
        level = "HIGH"
    
    return {"score": float(score), "level": level}

@app.get("/piezo/on")
def piezo_on():
    GPIO.output(PIN, GPIO.LOW)
    return {"status": "Piezo ON"}

@app.get("/piezo/off")
def piezo_off():
    GPIO.output(PIN, GPIO.HIGH)
    return {"status": "Piezo OFF"}