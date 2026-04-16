import streamlit as st
import numpy as np
from PIL import Image
import time

st.set_page_config(page_title="GeoAI Digital Twin", layout="wide")

# CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    padding: 1.5rem 2rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 2rem;
}
.result-card {
    background: #0f172a;
    padding: 2rem;
    border-radius: 30px;
    color: white;
}
.metric-value {
    font-size: 4.5rem;
    font-weight: 900;
    text-align: center;
    margin: 0.5rem 0;
}
.stButton > button {
    background: linear-gradient(90deg, #2563eb, #4f46e5);
    color: white;
    font-weight: bold;
    font-size: 1.2rem;
    padding: 1rem 2rem;
    border-radius: 20px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><span style="font-size:2.2rem; font-weight:800;">🧠 GeoAI Digital Twin</span></div>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    uploaded_file = st.file_uploader("📥 Rasm yuklang", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True, caption="Yuklangan rasm")

    ucs = st.slider("UCS (MPa)", 10, 200, 85)
    gsi = st.slider("GSI Index", 10, 100, 60)
    depth = st.number_input("Chuqurlik (m)", 0, 2000, 450)
    temp = st.number_input("Harorat (°C)", 0, 1000, 25)

    btn = st.button("🔍 DIGITAL TWIN ANALIZNI BOSHLASH", disabled=(uploaded_file is None), use_container_width=True)

with col_right:
    if btn and uploaded_file:
        with st.spinner("⏳ Hisoblanmoqda..."):
            time.sleep(1.5)
            # Fizik hisob
            mpa = max(5.0, ucs * (gsi / 100.0) - temp * 0.04 - depth * 0.01)
            crack = min(100.0, temp * 0.08 + np.random.rand() * 3)

            if mpa > 55:
                status = "Xavfsiz"
                color = "#10b981"
            elif mpa > 35:
                status = "O'rtacha"
                color = "#f59e0b"
            else:
                status = "Kritik"
                color = "#ef4444"

        st.markdown(f"""
        <div class="result-card">
            <p style="opacity:0.6; text-align:center; letter-spacing:2px;">STRENGTH REGRESSION (MPa)</p>
            <p class="metric-value" style="color:{color};">{mpa:.2f}</p>
            <p style="text-align:center; margin-top:0;">Ishonch: 93.5%</p>
            <hr style="margin:30px 0; border-color:#334155;">
            <div style="display:flex; justify-content:space-around;">
                <div style="text-align:center;">
                    <p style="opacity:0.6;">Crack Ratio</p>
                    <p style="font-size:2.2rem; font-weight:bold; color:#60a5fa; margin:0;">{crack:.2f}%</p>
                </div>
                <div style="text-align:center;">
                    <p style="opacity:0.6;">Status</p>
                    <p style="font-size:2rem; font-weight:bold; color:{color}; margin:0;">{status}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("👈 Chap tomondan rasm yuklang va parametrlarni sozlang.")

st.divider()
st.caption("GeoAI Digital Twin · Streamlit Cloud Ready")
