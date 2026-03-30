import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erf

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
# Formula: chuqurlik * kengayish * harorat farqi
uplift = (depth * 1e-5 * (1100 - 35)) * 0.1 * np.exp(-(x**2) / 20000)

# 2. Mexanik cho'kish (m da)
# Formula: S(x) = S_max * 0.5 * (1 + erf(sqrt(pi)*x/r))
r = depth / np.tan(np.radians(45))
s_max = thickness * 0.75  # Cho'kish koeffitsiyenti
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x / r)) - s_max

# Grafiklarni chiqarish
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Termal ko'tarilish (cm)")
    fig1, ax1 = plt.subplots()
    ax1.plot(x, uplift * 100, color='orange', linewidth=2, label="Ko'tarilish")
    ax1.fill_between(x, uplift * 100, color='orange', alpha=0.2)
    ax1.set_xlabel("Masofa (m)")
    ax1.set_ylabel("Balandlik (cm)")
    ax1.grid(True, linestyle=':')
    st.pyplot(fig1)

with col2:
    st.subheader("📉 Mexanik cho'kish (m)")
    fig2, ax2 = plt.subplots()
    ax2.plot(x, subsidence, color='red', linewidth=2, label="Cho'kish")
    ax2.fill_between(x, subsidence, color='red', alpha=0.2)
    ax2.set_xlabel("Masofa (m)")
    ax2.set_ylabel("Chuqurlik (m)")
    ax2.grid(True, linestyle=':')
    st.pyplot(fig2)

# Xulosa qismi
st.divider()
if time < 12:
    st.info(f"Hozirgi holat: {time}-soat. Termal kengayish hisobiga yer yuzasida ko'tarilish kuzatilmoqda.")
else:
    st.warning(f"Diqqat! {time}-soat. Yonish kamerasi kengayishi natijasida mexanik cho'kish xavfi ortmoqda.")

st.sidebar.markdown("---")
st.sidebar.write("Tuzuvchi: Saitov Dilshodbek")
