import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go

# Sahifa sozlamalari
st.set_page_config(page_title="Angren UCG Monitor", layout="wide")

st.title("🏗 Angren UCG: Yer yuzasi deformatsiyasi monitoringi")
st.markdown("### PhD Tadqiqot: Ko'mirni er ostida gazlashtirish jarayoni tahlili")

# Boshqaruv paneli (Sidebar)
st.sidebar.header("⚙️ Model parametrlari")
time = st.sidebar.slider("Yonish vaqti (soat):", 0, 48, 24)
depth = st.sidebar.number_input("Qatlam chuqurligi (m):", value=500)
thickness = st.sidebar.number_input("Ko'mir qalinligi (m):", value=10)

# Matematik hisob-kitoblar
x = np.linspace(-400, 400, 200)

# 1. Termal ko'tarilish (sm da)
uplift = (depth * 1e-5 * (1100 - 35)) * 0.1 * np.exp(-(x**2) / 20000)

# 2. Mexanik cho'kish (m da)
r = depth / np.tan(np.radians(45))
s_max = thickness * 0.75 
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x / r)) - s_max

# --- Grafiklarni chiqarish (Interaktiv Plotly versiyasi) ---
col1, col2 = st.columns(2)

with col1:
    fig_thermal = go.Figure()
    fig_thermal.add_trace(go.Scatter(
        x=x, 
        y=uplift * 100, 
        fill='tozeroy', 
        line=dict(color='orange', width=3),
        name="Ko'tarilish"
    ))
    fig_thermal.update_layout(
        title="🔥 Termal ko'tarilish (cm)", 
        template="plotly_dark",
        xaxis_title="Masofa (m)",
        yaxis_title="Balandlik (cm)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_thermal, use_container_width=True)

with col2:
    fig_subsidence = go.Figure()
    fig_subsidence.add_trace(go.Scatter(
        x=x, 
        y=subsidence, 
        fill='tozeroy', 
        line=dict(color='red', width=3),
        name="Cho'kish"
    ))
    fig_subsidence.update_layout(
        title="📉 Mexanik cho'kish (m)", 
        template="plotly_dark",
        xaxis_title="Masofa (m)",
        yaxis_title="Chuqurlik (m)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_subsidence, use_container_width=True)

# Xulosa qismi
st.divider()
if time < 12:
    st.info(f"Hozirgi holat: {time}-soat. Termal kengayish hisobiga yer yuzasida ko'tarilish kuzatilmoqda.")
else:
    st.warning(f"Diqqat! {time}-soat. Yonish kamerasi kengayishi natijasida mexanik cho'kish xavfi ortmoqda.")

st.sidebar.markdown("---")
st.sidebar.write("Tuzuvchi: Saitov Dilshodbek")
