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
        <title>Stress Detection Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                color: white;
                text-align: center;
                padding: 50px;
            }

            .container {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                width: 400px;
                margin: auto;
                box-shadow: 0px 10px 25px rgba(0,0,0,0.3);
            }

            h2 {
                margin-bottom: 20px;
            }

            input[type="file"] {
                margin: 15px 0;
            }

            button {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                background: #00c6ff;
                color: white;
                font-size: 16px;
                cursor: pointer;
                transition: 0.3s;
            }

            button:hover {
                background: #0072ff;
            }

            .result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 10px;
                font-size: 18px;
            }

            .low { background: #2ecc71; }
            .medium { background: #f1c40f; }
            .high { background: #e74c3c; }
        </style>
    </head>

    <body>
        <div class="container">
            <h2>Stress Detection System</h2>

            <form id="uploadForm">
                <input type="file" name="file" required><br>
                <button type="submit">Upload CSV</button>
            </form>

            <div id="result" class="result" style="display:none;"></div>
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

        resultDiv.style.display = "block";

        let color = "";
        if (data.score <= 0.33) color = "low";
        else if (data.score <= 0.66) color = "medium";
        else color = "high";

        resultDiv.className = "result " + color;

        resultDiv.innerHTML = `
            <h3>Stress Score</h3>
            <div style="font-size: 32px; font-weight: bold;">
                ${data.score.toFixed(3)}
            </div>
        `;
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
