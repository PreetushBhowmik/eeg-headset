import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

DATASET_PATH = "C:/Users/preetush/Downloads/minor"

X, y = [], []

def extract_features(df):
    return [
        df.mean().mean(),
        df.std().mean(),
        df.max().mean(),
        df.min().mean()
    ]

for file in os.listdir(DATASET_PATH):
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(DATASET_PATH, file))
        X.append(extract_features(df))
        
        label = 0 if int(file[1:3]) < 18 else 1
        y.append(label)

X = np.array(X)
y = np.array(y)

scaler = StandardScaler()
X = scaler.fit_transform(X)

model = RandomForestClassifier(n_estimators=20)
model.fit(X, y)

joblib.dump(model, "stress_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Model ready!")
