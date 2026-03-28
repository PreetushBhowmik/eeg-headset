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
                background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                color: white;
                text-align: center;
                padding-top: 80px;
            }

            .box {
                background: rgba(255,255,255,0.08);
                padding: 40px;
                border-radius: 20px;
                display: inline-block;
                box-shadow: 0px 10px 40px rgba(0,0,0,0.6);
                backdrop-filter: blur(10px);
                width: 350px;
            }

            h2 {
                margin-bottom: 20px;
            }

            button {
                padding: 12px 25px;
                margin-top: 15px;
                border: none;
                border-radius: 10px;
                background: #00c6ff;
                color: white;
                cursor: pointer;
                font-size: 16px;
                transition: 0.3s;
            }

            button:hover {
                background: #0072ff;
            }

            .score {
                margin-top: 25px;
                font-size: 42px;
                font-weight: bold;
                color: #00ffcc;
            }

            .level {
                font-size: 20px;
                margin-top: 10px;
                opacity: 0.9;
            }

            .low { color: #2ecc71; }
            .medium { color: #f1c40f; }
            .high { color: #e74c3c; }
        </style>
    </head>

    <body>
        <div class="box">
            <h2>Stress Detection</h2>

            <form id="uploadForm">
                <input type="file" name="file" required><br>
                <button type="submit">Upload</button>
            </form>

            <div id="score" class="score"></div>
            <div id="level" class="level"></div>
        </div>

        <script>
            const form = document.getElementById("uploadForm");
            const scoreDiv = document.getElementById("score");
            const levelDiv = document.getElementById("level");

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
                    scoreDiv.innerHTML = data.score.toFixed(3);

                    levelDiv.innerHTML = data.level;

                    levelDiv.className = "level " + data.level.toLowerCase();
                } else {
                    scoreDiv.innerHTML = "Error";
                    levelDiv.innerHTML = JSON.stringify(data);
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

        if score <= 0.33:
            level = "LOW"
        elif score <= 0.66:
            level = "MEDIUM"
        else:
            level = "HIGH"
            trigger_relay_async()

        return {
            "score": float(score),
            "level": level
        }

    except Exception as e:
        return {"error": str(e)}
