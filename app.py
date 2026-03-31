import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go

# Sahifa sozlamalari
st.set_page_config(page_title="Angren UCG Monitor (TM Model)", layout="wide")

st.title("🏗 Angren UCG: Termo-Mexanik Deformatsiya Monitoringi")
st.markdown("### PhD Tadqiqot: Issiqlik ta'sirida jins mustahkamligi o'zgarishini hisobga olgan model")

# --- Boshqaruv paneli (Sidebar) ---
st.sidebar.header("⚙️ Model parametrlari")

# 1. Geometrik va Vaqt parametrlari
st.sidebar.subheader("📍 Geometriya va Vaqt")
time = st.sidebar.slider("Yonish vaqti (soat):", 0, 100, 24)
depth = st.sidebar.number_input("Qatlam chuqurligi (m):", value=500)
thickness = st.sidebar.number_input("Ko'mir qalinligi (m):", value=10)

# 2. Tog' jinsi parametrlari
st.sidebar.markdown("---")
st.sidebar.subheader("🪨 Boshlang'ich jins xususiyatlari")
ucs_0 = st.sidebar.number_input("Boshlang'ich UCS (MPa):", value=50.0)
gsi_0 = st.sidebar.slider("Boshlang'ich GSI:", 0, 100, 65)
mi = st.sidebar.number_input("Intact Rock Constant (mi):", value=10.0)

# --- Termo-Mexanik Bog'liqlik (Scientific Logic) ---
# Harorat va vaqt o'tishi bilan jinsning degradatsiyasi
# 100 soat davomida UCS va GSI taxminan 30-40% gacha kamayishi modellashtirilgan
thermal_degradation = np.exp(-0.005 * time) 
current_ucs = ucs_0 * thermal_degradation
current_gsi = gsi_0 * thermal_degradation

# Matematik hisob-kitoblar
x = np.linspace(-400, 400, 200)

# 1. Termal ko'tarilish (cm da)
# Harorat oshishi (vaqtga bog'liq) ko'tarilishni oshiradi
temp_factor = 1 - np.exp(-0.05 * time)
uplift = (depth * 1e-5 * (1100 - 35)) * 0.1 * np.exp(-(x**2) / 20000) * temp_factor

# 2. Mexanik cho'kish (m da)
# Jins yumshashi (GSI va UCS kamayishi) cho'kish koeffitsiyentini oshiradi
subsidence_coeff = 0.95 - (current_gsi / 200) - (current_ucs / 800)
if subsidence_coeff < 0.1: subsidence_coeff = 0.1
if subsidence_coeff > 0.9: subsidence_coeff = 0.9

r = depth / np.tan(np.radians(45))
s_max = thickness * subsidence_coeff
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x / r)) - s_max

# --- Grafiklarni chiqarish ---
col1, col2 = st.columns(2)

with col1:
    fig_thermal = go.Figure()
    fig_thermal.add_trace(go.Scatter(x=x, y=uplift * 100, fill='tozeroy', 
                                     line=dict(color='orange', width=3), name="Ko'tarilish"))
    fig_thermal.update_layout(title="🔥 Termal ko'tarilish (cm)", template="plotly_dark",
                              xaxis_title="Masofa (m)", yaxis_title="Balandlik (cm)")
    st.plotly_chart(fig_thermal, use_container_width=True)

with col2:
    fig_subsidence = go.Figure()
    fig_subsidence.add_trace(go.Scatter(x=x, y=subsidence, fill='tozeroy', 
                                        line=dict(color='red', width=3), name="Cho'kish"))
    fig_subsidence.update_layout(title="📉 Mexanik cho'kish (m)", template="plotly_dark",
                                 xaxis_title="Masofa (m)", yaxis_title="Chuqurlik (m)")
    st.plotly_chart(fig_subsidence, use_container_width=True)

# --- Ilmiy tahlil paneli ---
st.divider()
st.subheader("📊 Termo-Mexanik tahlil natijalari")
m1, m2, m3 = st.columns(3)

with m1:
    st.metric("Joriy UCS (MPa)", f"{current_ucs:.2f}", f"{current_ucs - ucs_0:.2f} MPa")
    st.caption("Issiqlik ta'sirida mustahkamlikning kamayishi")

with m2:
    st.metric("Joriy GSI", f"{current_gsi:.1f}", f"{current_gsi - gsi_0:.1f}")
    st.caption("Strukturaviy buzilish darajasi")

with m3:
    st.metric("Cho'kish koeffitsiyenti", f"{subsidence_coeff:.3f}")
    st.caption("Jins zaiflashishi hisobiga cho'kishning ortishi")

st.sidebar.markdown("---")
st.sidebar.write("Tuzuvchi: Saitov Dilshodbek")
