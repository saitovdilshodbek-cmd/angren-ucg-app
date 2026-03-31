import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Sahifa sozlamalari
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Professional Geomechanical Monitor (RS2 Style)")
st.markdown("### Angren UCG: Termo-Mexanik (TM) Strukturaviy Tahlil")

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Loyiha Sozlamalari")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-Sector-01")
time = st.sidebar.slider("Jarayon vaqti (soat):", 0, 100, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=4)

# --- Qatlamlar ma'lumotlarini yig'ish ---
layers_data = []
total_depth = 0
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"n_{i}")
            thick = st.number_input(f"Qalinlik (m):", value=100.0 if i < 3 else 20.0, key=f"t_{i}")
        with col2:
            color = st.color_picker(f"Rangi:", '#2c3e50', key=f"c_{i}")
        
        layers_data.append({'name': name, 't': thick, 'color': color, 'z_start': total_depth})
        total_depth += thick

# --- Matematik Model (Dinamik Hisob) ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 300)
grid_x, grid_z = np.meshgrid(np.linspace(-total_depth*1.2, total_depth*1.2, 120), np.linspace(0, total_depth + 50, 100))

# Subsidence (Cho'kish) hisobi
r = total_depth / np.tan(np.radians(45))
s_max = (layers_data[-1]['t'] * 0.4) * (1 - np.exp(-0.03 * time))
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x_axis / r)) - s_max

# Yoriqlanish va Harorat (Contour data)
temp_2d = np.ones_like(grid_x) * 25
cracks_2d = np.zeros_like(grid_x)
source_z = total_depth - (layers_data[-1]['t'] / 2)

sources = {'1': -total_depth/3, '2': 0, '3': total_depth/3}
for i, (k, sx) in enumerate(sources.items()):
    active_time = max(0, time - (i * 20))
    if active_time > 0:
        rad = 15 + (active_time * 0.4)
        dist_sq = (grid_x - sx)**2 + (grid_z - source_z)**2
        temp_2d += 1000 * np.exp(-dist_sq / (2 * rad**2))
        cracks_2d += 1.2 * np.exp(-dist_sq / (2 * (rad*1.5)**2))

# --- VIZUALIZATSIYA ---
c1, c2 = st.columns([1, 3])

with c1:
    st.subheader("🧱 Geologik Ustun")
    fig_col = go.Figure()
    for l in layers_data:
        fig_col.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color']))
    fig_col.update_layout(template="plotly_dark", barmode='stack', yaxis=dict(autorange='reversed', title="Chuqurlik (m)"), showlegend=False, height=700)
    st.plotly_chart(fig_col, use_container_width=True)

with c2:
    st.subheader("📊 RS2 Style: Deformatsiya va Harorat Konturi")
    
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                           subplot_titles=("Termal Maydon (°C)", "Jinslar Deformatsiyasi va Yer yuzasi Cho'kishi"))

    # 1. Heatmap (Harorat)
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=grid_x[0], y=grid_z[:,0], colorscale='Hot', zmin=25, zmax=1100,
                                 colorbar=dict(title="°C", x=1.02, y=0.78, len=0.4)), row=1, col=1)

    # 2. Contour (Deformatsiya - RS2 Style)
    fig_tm.add_trace(go.Contour(z=cracks_2d, x=grid_x[0], y=grid_z[:,0], colorscale='Jet',
                                 contours=dict(coloring='heatmap', showlines=True),
                                 line_width=0.5, zmin=0, zmax=1.2,
                                 colorbar=dict(title="Zichlik", x=1.02, y=0.22, len=0.4)), row=2, col=1)

    # 3. Yer yuzasi deformatsiyasi (Oq nuqtali chiziq)
    fig_tm.add_trace(go.Scatter(x=x_axis, y=subsidence * 15, mode='lines', 
                                 line=dict(color='white', width=4, dash='dash'), name="Yer yuzasi"), row=2, col=1)

    # Qatlamlar chegarasini (Horizontal lines) grafik ustiga qo'shish
    for layer in layers_data:
        fig_tm.add_shape(type="line", x0=min(x_axis), y0=layer['z_start'], x1=max(x_axis), y1=layer['z_start'],
                         line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dot"), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(l=20, r=80, t=40, b=20), showlegend=False)
    fig_tm.update_yaxes(autorange='reversed')
    st.plotly_chart(fig_tm, use_container_width=True)

# Natijalar paneli
st.divider()
cols = st.columns(4)
cols[0].metric("Maksimal cho'kish", f"{abs(subsidence.min()):.2f} m")
cols[1].metric("Kamera harorati", f"{temp_2d.max():.0f} °C")
cols[2].metric("Umumiy chuqurlik", f"{total_depth} m")
cols[3].metric("Ssenariya", "Faol" if time > 0 else "Kutish")

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
