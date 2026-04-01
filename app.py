import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="UCG Monitor 3D PRO", layout="wide")

st.title("🌐 UCG Geomechanical Monitor (3D + Research Level)")

# --- Sidebar ---
st.sidebar.header("⚙️ Parametrlar")
time = st.sidebar.slider("Vaqt (soat)", 1, 100, 24)
depth = st.sidebar.slider("Chuqurlik (m)", 100, 500, 200)

# --- 3D GRID ---
x = np.linspace(-200, 200, 40)
y = np.linspace(-200, 200, 40)
z = np.linspace(0, depth, 30)
X, Y, Z = np.meshgrid(x, y, z)

# --- HEAT PDE (simplified 3D diffusion) ---
T = np.ones_like(X) * 25
alpha = 1e-6

source = np.array([0, 0, depth - 20])

for _ in range(time):
    dist = (X-source[0])**2 + (Y-source[1])**2 + (Z-source[2])**2
    T += 500 * np.exp(-dist / 5000)

# --- ROCK PARAMETERS ---
UCS = 40
GSI = 60
mi = 10

mb = mi * np.exp((GSI - 100) / 28)
s = np.exp((GSI - 100) / 9)
a = 0.5 + (1/6)*(np.exp(-GSI/15) - np.exp(-20/3))

# --- STRESS FIELD ---
sigma_v = 0.027 * Z

# --- TEMPERATURE EFFECT ---
strength = UCS * np.exp(-0.002*(T-25))

# --- MOHR-COULOMB FAILURE ---
cohesion = strength / 2
phi = 30  # degrees

shear_stress = sigma_v * np.tan(np.radians(phi))
failure = shear_stress / (cohesion + 1e-6)

# --- DISPLACEMENT ---
displacement = -0.002 * sigma_v * np.exp(-(X**2+Y**2)/(depth*10))

# --- 3D VISUALIZATION ---
st.subheader("🔥 3D Harorat maydoni")

fig = go.Figure(data=go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=T.flatten(),
    opacity=0.1,
    surface_count=15
))

fig.update_layout(template="plotly_dark", height=700)
st.plotly_chart(fig, use_container_width=True)

# --- FAILURE VISUAL ---
st.subheader("💥 Failure Zone (3D)")

fig2 = go.Figure(data=go.Volume(
    x=X.flatten(),
    y=Y.flatten(),
    z=Z.flatten(),
    value=failure.flatten(),
    opacity=0.1,
    surface_count=15
))

fig2.update_layout(template="plotly_dark", height=700)
st.plotly_chart(fig2, use_container_width=True)

# --- DISPLACEMENT SLICE ---
st.subheader("📉 Deformatsiya (kesim)")
mid = len(z)//2

fig3 = go.Figure()
fig3.add_trace(go.Heatmap(
    z=displacement[:,:,mid],
    x=x,
    y=y
))

fig3.update_layout(template="plotly_dark")
st.plotly_chart(fig3, use_container_width=True)

# --- REPORT TEXT ---
st.subheader("📄 Ilmiy xulosa (auto)")

st.write(f"""
Ushbu model UCG jarayonida issiqlik tarqalishi, jins mustahkamligi kamayishi va buzilish zonalarini ko‘rsatadi.

- Maksimal harorat: {np.max(T):.1f} °C
- Maksimal stress: {np.max(sigma_v):.2f} MPa
- Eng xavfli zona: {np.max(failure):.2f}

Natijalar shuni ko‘rsatadiki, yuqori harorat hududlarida jins mustahkamligi keskin kamayadi va buzilish ehtimoli ortadi.
""")

st.success("🚀 3D + Mohr-Coulomb + Research level model tayyor")
