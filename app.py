import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Sahifa sozlamalari
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Dinamik UCG Ssenariysi (RS2 Style)")

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time = st.sidebar.slider("Jarayon vaqti (soat):", 0, 100, 45)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#000000', '#800080']

layers_data = []
total_depth = 0
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
            u = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
        with col2:
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI:", 0, 100, 60, key=f"g_{i}")
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'gsi': g, 
            'color': color, 'z_start': total_depth
        })
        total_depth += thick

# --- Matematik Model ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
thermal_deg = np.exp(-0.005 * time)
current_ucs = avg_ucs * thermal_deg
sub_coeff = np.clip(0.95 - (avg_ucs / 800), 0.1, 0.8)

# Deformatsiya profili (Oq chiziq formulasi)
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 300)
r = total_depth / np.tan(np.radians(35)) # Ta'sir radiusi
s_max = layers_data[-1]['t'] * sub_coeff * (time/100) # Maksimal cho'kish
# Silliq cho'kish profili
subsidence_profile = -s_max * np.exp(-(x_axis**2) / (2 * (r/2)**2)) 

# --- 2D Model ---
grid_x, grid_z = np.meshgrid(np.linspace(-total_depth*1.2, total_depth*1.2, 150), np.linspace(0, total_depth + 20, 100))
cracks_2d = np.zeros_like(grid_x)
source_z = total_depth - (layers_data[-1]['t'] / 2)

sources = {'1': -total_depth/2, '2': 0, '3': total_depth/2}
active_sources = [sources['1']]
if time > 30: active_sources.append(sources['3'])
if time > 60: active_sources.append(sources['2'])

for sx in active_sources:
    dist_sq = (grid_x - sx)**2 + (grid_z - source_z)**2
    radius = 15 + (time * 0.4)
    cracks_2d += np.exp(-dist_sq / (2 * radius**2))

# --- VIZUALIZATSIYA (RS2 STYLE) ---
c1, c2 = st.columns([1, 3])

with c1:
    st.subheader("🧱 Kesim")
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=[''], y=[l['t']], name=l['name'], marker_color=l['color']))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=600, showlegend=False)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🏗️ RS2 Interpret: Vertical Displacement")
    fig_rs2 = go.Figure()

    # 1. Kontur maydoni (Jinslar deformatsiyasi)
    fig_rs2.add_trace(go.Contour(
        z=cracks_2d, x=grid_x[0], y=grid_z[:,0],
        colorscale='Jet',
        contours=dict(start=0, end=1.2, size=0.1, coloring='heatmap', showlines=True),
        line_width=0.5,
        colorbar=dict(title="Displacement (m)", x=1.02)
    ))

    # 2. YER YUZASI DEFORMATSIYA CHIZIG'I (Oq punktir chiziq)
    # y=0 sathidan yuqoriga/pastga deformatsiyani ko'rsatish
    fig_rs2.add_trace(go.Scatter(
        x=x_axis, 
        y=subsidence_profile * 20 - 10, # Masshtab ko'rinishi uchun
        mode='lines',
        line=dict(color='white', width=4, dash='dash'),
        name="Surface Profile"
    ))

    # 3. Strukturaviy chegaralar
    for l in layers_data:
        fig_rs2.add_shape(type="line", x0=min(x_axis), y0=l['z_start'], x1=max(x_axis), y1=l['z_start'],
                          line=dict(color="rgba(255,255,255,0.5)", width=1.5))

    fig_rs2.update_layout(
        template="plotly_dark", height=700,
        xaxis=dict(title="Distance (m)", range=[min(x_axis), max(x_axis)]),
        yaxis=dict(title="Depth (m)", autorange='reversed', range=[total_depth+20, -50]),
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig_rs2, use_container_width=True)
