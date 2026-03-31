import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go

# Sahifa sozlamalari
st.set_page_config(page_title="Angren UCG Monitor", layout="wide")

st.title("🏗 Angren UCG: Yer yuzasi deformatsiyasi monitoringi")
st.markdown("### PhD Tadqiqot: Ko'mirni er ostida gazlashtirish jarayoni tahlili")

# --- Boshqaruv paneli (Sidebar) ---
st.sidebar.header("⚙️ Model parametrlari")

# 1. Geometrik parametrlar
st.sidebar.subheader("📍 Geometriya")
time = st.sidebar.slider("Yonish vaqti (soat):", 0, 48, 24)
depth = st.sidebar.number_input("Qatlam chuqurligi (m):", value=500)
thickness = st.sidebar.number_input("Ko'mir qalinligi (m):", value=10)

# 2. Tog' jinsi parametrlari (Siz yuborgan rasm asosida)
st.sidebar.markdown("---")
st.sidebar.subheader("🪨 Tog' jinsi xususiyatlari (Hoek-Brown)")
ucs = st.sidebar.number_input("Intact UCS (MPa):", value=50.0)
gsi = st.sidebar.slider("Geological Strength Index (GSI):", 0, 100, 65)
mi = st.sidebar.number_input("Intact Rock Constant (mi):", value=10.0)
d_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.0)

# Matematik hisob-kitoblar
x = np.linspace(-400, 400, 200)

# 1. Termal ko'tarilish (sm da)
# Jins qanchalik mustahkam (UCS yuqori) bo'lsa, ko'tarilish effekti shunchalik barqaror bo'ladi
uplift = (depth * 1e-5 * (1100 - 35)) * 0.1 * np.exp(-(x**2) / 20000)

# 2. Mexanik cho'kish (m da)
# Ilmiy mantiq: GSI va UCS past bo'lsa, cho'kish koeffitsiyenti ortadi
# Bu yerda oddiy bog'liqlik yaratdik:
subsidence_coeff = 0.85 - (gsi / 250) - (ucs / 1000)
if subsidence_coeff < 0.1: subsidence_coeff = 0.1 # Minimal chegara

r = depth / np.tan(np.radians(45))
s_max = thickness * subsidence_coeff
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

# Xulosa va Parametrlar haqida ma'lumot
st.divider()
c1, c2 = st.columns(2)
with c1:
    if time < 12:
        st.info(f"Hozirgi holat: {time}-soat. Termal kengayish ustunlik qilmoqda.")
    else:
        st.warning(f"Diqqat! {time}-soat. Mexanik cho'kish xavfi mavjud.")

with c2:
    st.write(f"**Hisoblangan cho'kish koeffitsiyenti:** {subsidence_coeff:.3f}")
    st.write(f"**Jins holati:** {'Mustahkam' if gsi > 60 else 'Zaif/Parchalangan'}")

st.sidebar.markdown("---")
st.sidebar.write("Tuzuvchi: Saitov Dilshodbek")
