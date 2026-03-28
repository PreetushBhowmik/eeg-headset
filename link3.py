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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stress Detection</title>

        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f7fa;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }

            .container {
                background: #ffffff;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
                text-align: center;
                width: 350px;
            }

            h2 {
                margin-bottom: 20px;
                color: #333;
                font-weight: 600;
            }

            input[type="file"] {
                margin-bottom: 20px;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 6px;
                width: 100%;
                background-color: #fafafa;
                cursor: pointer;
            }

            button {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            button:hover {
                background-color: #357abd;
            }

            button:active {
                transform: scale(0.98);
            }
        </style>
    </head>

    <body>
        <div class="container">
            <h2>Upload CSV File</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <br>
                <button type="submit">Upload</button>
            </form>
        </div>
    </body>
    </html>
    """


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()

    # For now, just confirm upload
    return {"filename": file.filename, "message": "File uploaded successfully"}

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
