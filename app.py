from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import io
from PIL import Image
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def preprocess_image(file_bytes):
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img = np.array(img)
    img = cv2.resize(img, (224, 224)) / 255.0
    return img.flatten()

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    ucs: float = Form(80),
    gsi: float = Form(60),
    depth: float = Form(400),
    temp: float = Form(500)
):
    img_bytes = await file.read()
    img_vector = preprocess_image(img_bytes)
    
    # Dummy hisoblash (yoki modelingizni yuklang)
    physics_mpa = ucs * (gsi/100) - (temp*0.04 + depth*0.01)
    crack = min(100, temp * 0.08 + np.random.rand()*3)
    
    return {
        "mpa": round(max(5, physics_mpa), 2),
        "crack_percent": round(crack, 2),
        "confidence": 93.5,
        "status": "SAFE" if physics_mpa > 50 else "WARNING",
        "loss": 0.084
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
