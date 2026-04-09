from fastapi import FastAPI
import numpy as np
import pickle

app = FastAPI()

# Agar siz modelni saqlagan bo‘lsangiz, yuklash mumkin
# with open("model.pkl", "rb") as f:
#     model = pickle.load(f)

@app.get("/")
def home():
    return {"message": "UCG AI API is running"}

@app.get("/predict")
def predict(fos: float, damage: float, temp: float, subs: float):
    # Bu yerda AIEngine predictni chaqirish mumkin
    risk = 1 if fos < 1.2 or damage > 0.6 else 0
    prob = 0.7 if risk else 0.2
    future = 0.5
    return {"risk": risk, "probability": prob, "future_index": future}
