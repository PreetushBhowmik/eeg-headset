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
        <style>
            body {
                font-family: Arial;
                text-align: center;
                padding: 50px;
                background: #111;
                color: white;
            }

            .box {
                background: #222;
                padding: 30px;
                border-radius: 10px;
                display: inline-block;
            }

            button {
                margin-top: 10px;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
                background: #00c6ff;
                color: white;
                cursor: pointer;
            }

            #result {
                margin-top: 20px;
                font-size: 30px;
            }
        </style>
    </head>

    <body>
        <div class="box">
            <h2>Upload CSV</h2>

            <form id="uploadForm">
                <input type="file" name="file" required><br>
                <button type="submit">Upload</button>
            </form>

            <div id="result"></div>
        </div>

        <script>
            const form = document.getElementById("uploadForm");
            const resultDiv = document.getElementById("result");

            form.addEventListener("submit", async (e) => {
                e.preventDefault();

                const formData = new FormData(form);

                const response = await fetch("/upload", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                console.log(data); // DEBUG

                if (data.score !== undefined) {
                    resultDiv.innerHTML = "Stress Score: " + data.score.toFixed(3);
                } else {
                    resultDiv.innerHTML = "Error: " + JSON.stringify(data);
                }
            });
        </script>
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

        if score > 0.66:
            trigger_piezo_async()

        return {
            "score": float(score)
        }

    except Exception as e:
        return {"error": str(e)}
