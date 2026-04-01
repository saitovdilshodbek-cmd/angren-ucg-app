import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="UCG Void Interaction Monitor", layout="wide")

st.title("🌐 UCG Bo'shliqlararo Ta'sir Monitoringi")
st.markdown("### Ko'p kamerali tizimda Shear (X) va Tension (O) zonalari tahlili")

# --- Sidebar ---
st.sidebar.header("⚙️ Parametrlar")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 200, 150)
dist_between = st.sidebar.slider("Kameralar orasidagi masofa (m):", 30, 150, 70)
T_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1000)

# Qatlam ma'lumotlari (Soddalashtirilgan)
avg_ucs = 40.0
total_depth = 300.0

# --- MATEMATIK MODEL ---
x_axis = np.linspace(-200, 200, 200)
z_axis = np.linspace(0, 350, 150)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)

source_z = 280  # Yonish chuqurligi
temp_2d = np.ones_like(grid_x) * 20
strength_2d = np.ones_like(grid_x) * avg_ucs
sigma_v = 0.027 * grid_z

# 3 ta kamera (bo'shliqlar) koordinatasi
sources_x = [-dist_between, 0, dist_between]
void_radius = 18 

# Bo'shliqlarni hisoblash
void_mask_total = np.zeros_like(grid_x, dtype=bool)
for sx in sources_x:
    dist = np.sqrt((grid_x - sx)**2 + (grid_z - source_z)**2)
    # Harorat ta'siri (sovigandan keyin ham qolgan termal zona)
    temp_2d += (T_max * 0.2) * np.exp(-dist**2 / (2 * 40**2)) 
    
    mask = dist <= void_radius
    void_mask_total = void_mask_total | mask
    strength_2d[mask] = 0

# --- FAILURE ANALYSIS (X va O belgilari uchun) ---
# Shear va Tension nuqtalarini yig'ish
shear_x, shear_z = [], []
tension_x, tension_z = [], []

# Soddalashtirilgan Shear/Tension kriteriyasi
for i in range(0, len(z_axis), 4): # Har 4 nuqtada bir tekshirish (vizual qulaylik uchun)
    for j in range(0, len(x_axis), 4):
        curr_x, curr_z = x_axis[j], z_axis[i]
        
        if void_mask_total[i, j]: continue
        
        # Stress ratio
        s_v = 0.027 * curr_z
        # Bo'shliqlar orasidagi masofa kam bo'lsa stress ortadi (Concentration factor)
        stress_factor = 1.0
        for sx in sources_x:
            d = np.sqrt((curr_x - sx)**2 + (curr_z - source_z)**2)
            if d < void_radius * 3:
                stress_factor += (void_radius / d)**2
        
        actual_stress = s_v * stress_factor
        curr_str = strength_2d[i, j]
        
        # 1. Shear Failure (X) - Siqilish va siljish
        if actual_stress > curr_str * 0.7:
            shear_x.append(curr_x)
            shear_z.append(curr_z)
        
        # 2. Tension Failure (O) - Bo'shliq tepasida (Roof)
        elif curr_z < source_z and actual_stress > curr_str * 0.4:
            tension_x.append(curr_x)
            tension_z.append(curr_z)

# --- VIZUALIZATSIYA ---
fig = go.Figure()

# 1. Background (Strength yoki Stress field)
fig.add_trace(go.Heatmap(
    z=strength_2d, x=x_axis, y=z_axis,
    colorscale='Viridis', showscale=False, opacity=0.3
))

# 2. Bo'shliqlar (Voids)
for sx in sources_x:
    fig.add_shape(type="circle",
        xref="x", yref="y",
        x0=sx-void_radius, y0=source_z-void_radius,
        x1=sx+void_radius, y1=source_z+void_radius,
        fillcolor="black", line_color="white")

# 3. Shear Points (X) - Qizil
fig.add_trace(go.Scatter(
    x=shear_x, y=shear_z,
    mode='markers',
    marker=dict(symbol='x', color='red', size=7),
    name='Shear (Siljish)'
))

# 4. Tension Points (O) - Olovrang/Sariq
fig.add_trace(go.Scatter(
    x=tension_x, y=tension_z,
    mode='markers',
    marker=dict(symbol='circle-open', color='orange', size=7),
    name='Tension (Yorilish)'
))

# Grafik sozlamalari
fig.update_layout(
    title=f"Bo'shliqlararo ta'sir: {dist_between}m masofada",
    template="plotly_dark",
    height=700,
    xaxis_title="Masofa (m)",
    yaxis_title="Chuqurlik (m)",
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

st.info("💡 **Tahlil:** Bo'shliqlar bir-biriga yaqinlashsa (masofa kamaysa), ular orasidagi 'ustun' (pillar) qismida Shear (X) zonalari ko'payishini va xavf ortishini ko'rishingiz mumkin.")
