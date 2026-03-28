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
PIN = 18  # use stable pin
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.OUT)
GPIO.output(PIN, GPIO.LOW)  # OFF initially

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

# ---------------- RELAY CONTROL ----------------
def trigger_relay():
    print("🚨 HIGH STRESS → RELAY ON")

    GPIO.output(PIN, GPIO.HIGH)  # ON
    time.sleep(5)
    GPIO.output(PIN, GPIO.LOW)   # OFF

def trigger_relay_async():
    threading.Thread(target=trigger_relay, daemon=True).start()

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
                background: #111;
                color: white;
                text-align: center;
                padding-top: 100px;
            }

            .box {
                background: #222;
                padding: 30px;
                border-radius: 15px;
                display: inline-block;
                box-shadow: 0px 10px 30px rgba(0,0,0,0.5);
            }

            button {
                padding: 10px 20px;
                margin-top: 15px;
                border: none;
                border-radius: 8px;
                background: #00c6ff;
                color: white;
                cursor: pointer;
                font-size: 16px;
            }

            button:hover {
                background: #0072ff;
            }

            #result {
                margin-top: 20px;
                font-size: 32px;
                font-weight: bold;
                color: #00ffcc;
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

                console.log(data);

                if (data.score !== undefined) {
                    resultDiv.innerHTML = data.score.toFixed(3);
                } else {
                    resultDiv.innerHTML = "Error: " + JSON.stringify(data);
                }
            });
        </script>
    </body>
    </html>
    """

# ---------------- FILE UPLOAD ----------------
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)

        score = predict_stress_df(df)
        print(f"Stress Score: {score:.3f}")

        if score > 0.66:
            trigger_relay_async()

        return {
            "score": float(score)
        }

    except Exception as e:
        return {"error": str(e)}
