import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="UCG Scientific Monitor", layout="wide")

st.title("🌐 UCG Geomechanical Monitor (Final Scientific Version)")

# ===================== SIDEBAR =====================
st.sidebar.header("⚙️ Model Parametrlari")

# GEOLOGY
st.sidebar.subheader("🧱 Geologiya")
num_layers = st.sidebar.slider("Qatlamlar soni", 1, 5, 3)

layers = []
total_depth = 0

for i in range(num_layers):
    with st.sidebar.expander(f"Qatlam {i+1}"):
        t = st.number_input("Qalinlik (m)", 10.0, 200.0, 50.0, key=f"t{i}")
        ucs = st.number_input("UCS (MPa)", 5.0, 150.0, 40.0, key=f"ucs{i}")
        gsi = st.slider("GSI", 10, 100, 60, key=f"gsi{i}")
        mi = st.number_input("mi", 5.0, 30.0, 10.0, key=f"mi{i}")

        layers.append({"t": t, "ucs": ucs, "gsi": gsi, "mi": mi, "z": total_depth})
        total_depth += t

# THERMAL
st.sidebar.subheader("🔥 Termal")
T_source = st.sidebar.slider("Yonish harorati (°C)", 600, 1200, 1000)
alpha = st.sidebar.selectbox("Diffuziya", [1e-7, 1e-6, 1e-5])
burn_duration = st.sidebar.slider("Yonish vaqti", 10, 100, 40)
cooling = st.sidebar.slider("Sovish", 0.01, 0.05, 0.03)

# MECHANICAL
st.sidebar.subheader("💥 Mexanik")
phi = st.sidebar.slider("Phi (°)", 20, 45, 30)
cohesion = st.sidebar.slider("C (MPa)", 0.1, 20.0, 5.0)
gamma = st.sidebar.slider("Stress gradient", 0.02, 0.03, 0.027)

# SUBSIDENCE
st.sidebar.subheader("📉 Cho‘kish")
subs_factor = st.sidebar.slider("Koeff", 0.005, 0.05, 0.01)
angle = st.sidebar.slider("Burchak", 20, 45, 35)

# TIME
time = st.sidebar.slider("Vaqt", 1, 150, 24)

# ===================== CALCULATIONS =====================

# averages
avg_ucs = sum(l['ucs'] * l['t'] for l in layers) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers) / total_depth
avg_mi = sum(l['mi'] * l['t'] for l in layers) / total_depth

# Hoek-Brown
mb = avg_mi * np.exp((avg_gsi - 100) / 28)
s = np.exp((avg_gsi - 100) / 9)
a = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

# GRID
x = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z = np.linspace(0, total_depth+50, 120)
X, Z = np.meshgrid(x, z)

# TEMPERATURE FIELD
dist = (X)**2 + (Z - total_depth + 20)**2
T = 25 + T_source * np.exp(-dist / (4 * alpha * (time*3600)))

# STRENGTH REDUCTION
strength = avg_ucs * np.exp(-0.002 * (T - 25))

# STRESS FIELD
sigma_v = gamma * Z

# FAILURE (Mohr-Coulomb)
shear = sigma_v * np.tan(np.radians(phi))
failure = shear / (cohesion + 1e-6)

# SUBSIDENCE
r = total_depth / np.tan(np.radians(angle))
Smax = total_depth * subs_factor * (time/100)
subsidence = -Smax * np.exp(-(x**2)/(2*(r/2.5)**2))

# ===================== VISUAL =====================
st.subheader("📊 Natijalar")

fig = make_subplots(rows=2, cols=2,
                    subplot_titles=("Temperature", "Stress", "Failure", "Subsidence"))

fig.add_trace(go.Heatmap(z=T, x=x, y=z, colorscale='Hot'), 1, 1)
fig.add_trace(go.Heatmap(z=sigma_v, x=x, y=z, colorscale='Viridis'), 1, 2)
fig.add_trace(go.Heatmap(z=failure, x=x, y=z, colorscale='Jet'), 2, 1)

fig.add_trace(go.Scatter(x=x, y=subsidence, fill='tozeroy'), 2, 2)

fig.update_layout(height=900, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# ===================== OUTPUT =====================
st.subheader("📄 Hisobot")

st.table({
    "Parametr": ["mb", "s", "a", "Max Temp", "Max Failure"],
    "Qiymat": [
        f"{mb:.2f}",
        f"{s:.4f}",
        f"{a:.3f}",
        f"{np.max(T):.1f} °C",
        f"{np.max(failure):.2f}"
    ]
})

st.success("✅ Final ilmiy model tayyor")
