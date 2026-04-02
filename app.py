import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

# CSS orqali interfeysni biroz jozibador qilish
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4253; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil: Seleklar Barqarorligi")

# --- Sidebar: Parametrlar ---
with st.sidebar:
    st.header("⚙️ Umumiy parametrlar")
    obj_name = st.text_input("Loyiha nomi:", value="Angren-UCG-001")
    time_h = st.slider("Jarayon vaqti (soat):", 1, 150, 24)
    num_layers = st.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

    st.subheader("🔥 Yonish va Termal")
    burn_duration = st.number_input("Kamera yonish muddati (soat):", value=40)
    T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

    strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
    layers_data = []
    total_depth = 0
    for i in range(int(num_layers)):
        with st.expander(f"{i+1}-qatlam", expanded=(i == int(num_layers)-1)):
            c1, c2 = st.columns(2)
            name = c1.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"n_{i}")
            thick = c2.number_input(f"Qalinlik:", value=50.0, key=f"t_{i}")
            u = c1.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
            g = c2.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
            layers_data.append({'name': name, 't': thick, 'ucs': u, 'gsi': g, 'z_start': total_depth, 'color': strata_colors[i%5]})
            total_depth += thick

# --- HISOB-KITOBLAR (Faqat mantiq) ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth
mb = 10 * np.exp((avg_gsi - 100) / 28)
s_hb = np.exp((avg_gsi - 100) / 9)
a_hb = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)

sources = {'1': {'x': -total_depth/2.5, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/2.5, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
plastic_mask = np.zeros_like(grid_x)

for k, v in sources.items():
    if time_h > v['start']:
        dt = time_h - v['start']
        r = 15 + (min(dt, burn_duration) * 0.5)
        curr_T = T_source_max if dt <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(dt-burn_duration))
        dist_sq = (grid_x - v['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (2 * r**2))
        plastic_mask = np.maximum(plastic_mask, np.exp(-dist_sq / (2 * (r*1.3)**2)))

failure_2d = (0.027 * grid_z) / (avg_ucs * np.exp(-0.002 * (temp_2d - 20)) + 1e-6)

# --- ASOSIY INTERFEYS (TARTIBLANGAN) ---
top_col1, top_col2, top_col3 = st.columns([1, 1, 1.5])

with top_col1:
    st.subheader("📉 Cho'kish (cm)")
    s_max = (layers_data[-1]['t'] * 0.04) * (min(time_h, 120) / 120)
    sub_y = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
    fig1 = go.Figure(go.Scatter(x=x_axis, y=sub_y*100, fill='tozeroy', line=dict(color='magenta')))
    fig1.update_layout(template="plotly_dark", height=250, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig1, use_container_width=True)

with top_col2:
    st.subheader("🛡️ Mustahkamlik")
    s3 = np.linspace(0, avg_ucs*0.4, 100)
    s1 = s3 + avg_ucs * (mb * s3 / avg_ucs + s_hb)**a_hb
    fig2 = go.Figure(go.Scatter(x=s3, y=s1, name='HB Envelope', line=dict(color='red')))
    fig2.update_layout(template="plotly_dark", height=250, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

with top_col3:
    st.subheader("🏗️ Seleklar Holati")
    m_col1, m_col2 = st.columns(2)
    # Selek nuqtalarini tekshirish
    for i, px in enumerate([ -total_depth/5, total_depth/5 ]):
        idx_x = np.abs(x_axis - px).argmin()
        t_p = temp_2d[np.abs(z_axis - source_z).argmin(), idx_x]
        safety = np.exp(-0.002 * (t_p - 20))
        target_col = m_col1 if i == 0 else m_col2
        target_col.metric(f"{i+1}-Selek", f"{t_p:.0f} °C", f"{safety*100:.1f}%")

st.divider()

# Markaziy Grafik: RS2 Interpret uslubida
st.subheader("🔍 Geomexanik Kesim va TM Maydoni (RS2 Interpret Simulation)")
fig_main = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                         subplot_titles=("Harorat Distributsiyasi", "Buzilish zonalari (Failure)"))

fig_main.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max), row=1, col=1)
fig_main.add_trace(go.Contour(z=failure_2d, x=x_axis, y=z_axis, colorscale='Jet', contours_showlines=False), row=2, col=1)

# Plastik nuqtalar (Shear Failure)
m = plastic_mask > 0.65
fig_main.add_trace(go.Scatter(x=grid_x[m], y=grid_z[m], mode='markers', 
                             marker=dict(symbol='x', color='red', size=3, opacity=0.4)), row=2, col=1)

fig_main.update_layout(template="plotly_dark", height=700, margin=dict(t=50, b=50))
fig_main.update_yaxes(autorange='reversed', title="Chuqurlik (m)")
st.plotly_chart(fig_main, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
