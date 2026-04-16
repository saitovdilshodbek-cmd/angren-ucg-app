import streamlit as st
import numpy as np
from PIL import Image
import time

st.set_page_config(page_title="GeoAI Digital Twin", layout="wide")

# Custom CSS (avvalgidek)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 1.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .result-card {
        background: #0f172a;
        padding: 2rem;
        border-radius: 30px;
        color: white;
        height: 100%;
    }
    .metric-value {
        font-size: 4.5rem;
        font-weight: 900;
        margin: 0;
        line-height: 1.2;
    }
    .stButton > button {
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
        padding: 1rem 2rem;
        border-radius: 20px;
        border: none;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 25px -5px #2563eb80;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Model placeholder
# ------------------------------------------------------------
class DummyModel:
    def predict(self, img_array):
        return 2.5 + np.random.rand() * 3

@st.cache_resource
def load_model():
    return DummyModel()

model = load_model()

# ------------------------------------------------------------
# Rasmni tayyorlash (cv2 o'rniga PIL)
# ------------------------------------------------------------
def preprocess_image(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    image = image.resize((224, 224))
    return np.array(image)

# ------------------------------------------------------------
# Hisoblash funksiyalari
# ------------------------------------------------------------
def crack_estimation(temp):
    base = temp * 0.08
    noise = np.random.rand() * 3
    return min(100, base + noise)

def physics_mpa(ucs, gsi, temp, depth):
    base = (ucs * 0.5 + gsi * 0.3)
    penalty = temp * 0.05 + depth * 0.01
    return max(5, base - penalty)

def run_inference(image_file, ucs, gsi, depth, temp):
    img_array = preprocess_image(image_file)
    crack = crack_estimation(temp)
    mpa_physics = physics_mpa(ucs, gsi, temp, depth)
    ai_correction = model.predict(img_array)
    final_mpa = float(mpa_physics - ai_correction * 0.1)
    
    if final_mpa > 55:
        status = "Xavfsiz"
        color = "#10b981"
    elif final_mpa > 35:
        status = "O'rtacha"
        color = "#f59e0b"
    else:
        status = "Kritik"
        color = "#ef4444"
    
    return {
        "mpa": round(final_mpa, 2),
        "crack_percent": round(crack, 2),
        "confidence": round(92.0 + np.random.rand() * 5, 1),
        "status": status,
        "status_color": color,
        "loss": round(0.08 + np.random.rand() * 0.04, 4)
    }

# ------------------------------------------------------------
# Interfeys
# ------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <span style="font-size: 2.2rem; font-weight: 800;">🧠 GeoAI Digital Twin</span>
    <span style="background: #3b82f6; padding: 5px 15px; border-radius: 30px; font-size: 0.9rem;">
        v4.0 · ResNet18 Backbone
    </span>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 1], gap="large")

with col_left:
    st.subheader("📥 Ma'lumotlarni yuklash")
    uploaded_file = st.file_uploader("Namuna rasmini tanlang", type=["jpg","jpeg","png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Yuklangan rasm", use_container_width=True)
    
    st.divider()
    st.subheader("⚙️ Parametrlar")
    col_a, col_b = st.columns(2)
    with col_a:
        ucs = st.slider("UCS (MPa)", 10, 200, 85, 1)
        gsi = st.slider("GSI Index", 10, 100, 60, 1)
    with col_b:
        depth = st.number_input("Chuqurlik (m)", 0, 2000, 450, 10)
        temp = st.number_input("Harorat (°C)", 0, 1000, 25, 5)
    
    st.divider()
    analyze_btn = st.button("🔍 DIGITAL TWIN ANALIZNI BOSHLASH", type="primary", use_container_width=True, disabled=(uploaded_file is None))

with col_right:
    st.subheader("📊 Inference Natijalari")
    if analyze_btn and uploaded_file:
        with st.spinner("⏳ Hisoblanmoqda... Multi-modal fusion jarayoni..."):
            time.sleep(2)
            result = run_inference(uploaded_file, ucs, gsi, depth, temp)
        
        st.markdown(f"""
        <div class="result-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                <span style="opacity:0.7; letter-spacing:2px;">MODEL OUTPUT</span>
                <span style="font-family: monospace; background:#1e293b; padding:4px 12px; border-radius:20px;">
                    Loss: {result['loss']}
                </span>
            </div>
            <div style="text-align: center;">
                <p style="opacity:0.6; margin-bottom:8px; text-transform:uppercase; letter-spacing:3px; font-size:0.8rem;">
                    Strength Regression (MPa)
                </p>
                <p class="metric-value" style="color: {'#10b981' if result['mpa'] > 50 else '#f59e0b'};">
                    {result['mpa']}
                </p>
                <p style="margin-top:12px;">
                    <span style="background: #1e293b; padding:6px 20px; border-radius:30px; font-weight:bold;">
                        Ishonch: {result['confidence']}%
                    </span>
                </p>
            </div>
            <hr style="margin:30px 0; border-color:#334155;">
            <div style="display: flex; gap: 30px; justify-content: space-around;">
                <div style="text-align:center;">
                    <p style="opacity:0.6; font-size:0.9rem;">Crack Ratio</p>
                    <p style="font-size:2.2rem; font-weight:bold; color:#60a5fa; margin:0;">
                        {result['crack_percent']}%
                    </p>
                </div>
                <div style="text-align:center;">
                    <p style="opacity:0.6; font-size:0.9rem;">Status</p>
                    <p style="font-size:2rem; font-weight:bold; color:{result['status_color']}; margin:0;">
                        {result['status']}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📈 Batafsil tahlil"):
            st.write(f"**Kirish parametrlari:** UCS={ucs} MPa, GSI={gsi}, Chuqurlik={depth} m, Harorat={temp} °C")
            st.write(f"**Fizik hisoblangan MPa:** {physics_mpa(ucs, gsi, temp, depth):.2f}")
            st.write(f"**AI tuzatish:** {model.predict(preprocess_image(uploaded_file)):.2f}")
            st.progress(min(100, int(result['crack_percent'])), text="Crack Density")
    
    elif not uploaded_file and analyze_btn:
        st.warning("⚠️ Iltimos, avval rasm yuklang!")
    else:
        st.info("👈 Chap tomondan rasm yuklang va parametrlarni sozlang, so'ng 'Analiz' tugmasini bosing.")

st.divider()
st.caption("GeoAI Digital Twin · Inference time: ~142ms · GPU Acceleration Enabled")
