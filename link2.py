from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
import joblib
import RPi.GPIO as GPIO

app = FastAPI()

# ---------------- GPIO SETUP ----------------
PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)

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

def predict_stress_df(df):
    features = np.array(extract_features(df)).reshape(1, -1)
    features = scaler.transform(features)
    return model.predict_proba(features)[0][1]

# ---------------- WEB PAGE ----------------
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
    df = pd.read_csv(file.file)

    score = predict_stress_df(df)

    if score <= 0.33:
        level = "LOW"
    elif score <= 0.66:
        level = "MEDIUM"
    else:
        level = "HIGH"
        GPIO.output(PIN, GPIO.LOW)  # Trigger piezo

    return {
        "score": float(score),
        "level": level
    }

# ---------------- OPTIONAL APIs ----------------
@app.get("/piezo/on")
def piezo_on():
    GPIO.output(PIN, GPIO.LOW)
    return {"status": "Piezo ON"}

@app.get("/piezo/off")
def piezo_off():
    GPIO.output(PIN, GPIO.HIGH)
    return {"status": "Piezo OFF"}
