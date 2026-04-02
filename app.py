import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("🔥 Yonish va Termal")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

# --- Qatlamlar ma'lumotlarini yig'ish ---
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
            g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
        
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth})
        total_depth += thick

# --- ILMIY HISOB-KITOBLAR (HOEK-BROWN) ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / (total_depth + 1e-6)
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / (total_depth + 1e-6)
avg_mi = sum(l['mi'] * l['t'] for l in layers_data) / (total_depth + 1e-6)

mb = avg_mi * np.exp((avg_gsi - 100) / 28)
s_hb = np.exp((avg_gsi - 100) / 9)
a_hb = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H = layers_data[-1]['t']

# Issiqlik manbalari
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt = time_h - val['start']
        radius = 15 + (min(dt, burn_duration) * 0.5)
        curr_T = T_source_max if dt <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(dt-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (2 * radius**2))

# --- STRESS FIELD & RS2 FAILURE LOGIC (ENHANCED) ---
E_modulus = 5000  
alpha_thermal = 1e-5  
delta_T = temp_2d - 25

sigma_v = 0.027 * grid_z
sigma_thermal = E_modulus * alpha_thermal * delta_T
bending_effect = 2.0 * np.exp(-((grid_x / (total_depth + 1e-6))**2)) 

# Yangi sigma_h (Termal va bending hisobga olingan)
sigma_h = (0.5 * sigma_v) - sigma_thermal - bending_effect

# Termal UCS va Hoek-Brown chegarasi
sigma_ci = avg_ucs * np.exp(-0.0025 * (temp_2d - 20))
sigma3_safe = np.maximum(sigma_h, 0.01)
sigma1_limit = sigma3_safe + sigma_ci * (mb * sigma3_safe / (sigma_ci + 1e-6) + s_hb)**a_hb

# Failure tahlili
shear_failure = sigma_v >= sigma1_limit
sigma_t_limit = 0.05 * sigma_ci  
tensile_failure = sigma_h <= -sigma_t_limit

# --- WILSON PILLAR STRENGTH ---
avg_t_at_pillar = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red_factor = np.exp(-0.0025 * (avg_t_at_pillar - 20))
pillar_strength = 0.6 * (avg_ucs * strength_red_factor)
y_zone = max((H / 2) * (np.sqrt((0.027 * source_z) / (pillar_strength + 1e-6)) - 1), 1.5)
stable_core = 0.5 * H
rec_width = np.round(2 * y_zone + stable_core, 1)

# FOS maydoni
fos_2d = sigma1_limit / (sigma_v + 1e-6)
fos_2d = np.clip(fos_2d, 0, 3.0)

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Stable Core (0.5H)", f"{stable_core:.1f} m")
m4.metric("TAVSIYA: Selek Eni", f"{rec_width} m")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

s_max = (layers_data[-1]['t'] * 0.04) * (min(time_h, 120) / 120)
subsidence_profile = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
uplift_vals = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*10)) * (time_h/150) * 100

with col_g1:
    fig1 = go.Figure(go.Scatter(x=x_axis, y=subsidence_profile * 100, fill='tozeroy', line=dict(color='magenta', width=3)))
    fig1.update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    fig2 = go.Figure(go.Scatter(x=x_axis, y=uplift_vals, fill='tozeroy', line=dict(color='cyan', width=3)))
    fig2.update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig2, use_container_width=True)

with col_g3:
    sigma3_ax = np.linspace(0, avg_ucs * 0.5, 100)
    red_h = strength_red_factor 
    red_fire = np.exp(-0.0035 * (T_source_max - 20)) 
    s1_init = sigma3_ax + avg_ucs * (mb * sigma3_ax / (avg_ucs + 1e-6) + s_hb)**a_hb
    s1_hot = sigma3_ax + (avg_ucs * red_h) * (mb * sigma3_ax / (avg_ucs * red_h + 1e-6) + s_hb)**a_hb
    s1_fire = sigma3_ax + (avg_ucs * red_fire) * (mb * sigma3_ax / (avg_ucs * red_fire + 1e-6) + s_hb)**a_hb
    
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_init, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_hot, name='Sovugandagi Zarar', line=dict(color='cyan', dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_fire, name='Yonayotgan payt', line=dict(color='orange', width=4)))
    fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_hb, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("📋 Ilmiy Tahlil")
    st.info(f"**Wilson (1972) & FOS talablari:**")
    st.error("🔴 FOS < 1.0: Failure")
    st.warning("🟡 FOS 1.0 - 1.5: Unstable")
    st.success("🟢 FOS > 1.5: Stable")
    
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi (RS2)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=("Harorat (°C)", "Xavfsizlik Koeffitsiyenti (FOS) & Yielded Zones"))
    
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
        colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.4)
    ), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=fos_2d, x=x_axis, y=z_axis, 
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']],
        zmin=0, zmax=3.0, contours_showlines=False,
        colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.4)
    ), row=2, col=1)

    fig_tm.add_trace(go.Scatter(
        x=grid_x[shear_failure][::2], y=grid_z[shear_failure][::2], 
        mode='markers', marker=dict(color='red', size=2, symbol='x', opacity=0.4),
        name='Shear Failure'
    ), row=2, col=1)

    fig_tm.add_trace(go.Scatter(
        x=grid_x[tensile_failure][::2], y=grid_z[tensile_failure][::2],
        mode='markers', marker=dict(color='blue', size=2, symbol='cross', opacity=0.4),
        name='Tensile Failure'
    ), row=2, col=1)
    
    p_x1 = (sources['1']['x'] + sources['2']['x']) / 2
    p_x2 = (sources['2']['x'] + sources['3']['x']) / 2
    for px in [p_x1, p_x2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H/2, y1=source_z+H/2, 
                         line=dict(color="lime", width=3, dash='dot'), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=800, showlegend=True, margin=dict(r=100))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Diana Meiram/ Saitov Dilshodbek")
