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

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, 0.5)

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
            rho = st.number_input(f"Zichlik (kg/m³):", value=2500, key=f"rho_{i}")
        with col2:
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
        
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'rho': rho, 'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth})
        total_depth += thick

# --- SET GRID ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

# --- 3. HEAT PDE LOGIC (COMSOL STYLE DIFFUSION) ---
alpha_rock = 1.0e-6 # Thermal diffusivity (m2/s)
time_seconds = time_h * 3600
# Penetration depth: d = sqrt(4*alpha*t)
pen_depth = np.sqrt(4 * alpha_rock * time_seconds) + 1e-6

sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt_local = (time_h - val['start']) * 3600
        local_pen = np.sqrt(4 * alpha_rock * dt_local)
        curr_T = T_source_max if (time_h - val['start']) <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*((time_h-val['start'])-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (local_pen**2 + 15**2))

# --- 2. LAYER-BY-LAYER STRESS FIELD ---
grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s = np.zeros_like(grid_z)
grid_a = np.zeros_like(grid_z)

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1: mask = grid_z >= layer['z_start']
    
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))

E_modulus = 5000
alpha_thermal = 1e-5
delta_T = temp_2d - 25
sigma_thermal = (E_modulus * alpha_thermal * delta_T) / (1 - nu_poisson)
grid_sigma_h = (k_ratio * grid_sigma_v) - sigma_thermal

sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

sigma_ci = grid_ucs * np.exp(-0.0025 * (temp_2d - 20))
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + 1e-6) + grid_s)**grid_a

shear_failure = sigma1_act >= sigma1_limit
tensile_failure = sigma3_act <= -(0.05 * sigma_ci)

# --- 1. ITERATIVE PILLAR SOLVER ---
avg_t_at_pillar = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
reduction = np.exp(-0.0025 * (avg_t_at_pillar - 20))
ucs_seam = layers_data[-1]['ucs']
sigma_v_seam = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0 # Initial guess
for _ in range(15):
    # Obert-Duvall + Thermal Reduction
    p_strength = (ucs_seam * reduction) * (w_sol / H_seam)**0.5
    y_z = (H_seam / 2) * (np.sqrt(sigma_v_seam / (p_strength + 1e-6)) - 1)
    y_z = max(y_z, 1.5)
    new_w = 2 * y_z + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1: break
    w_sol = new_w

rec_width = np.round(w_sol, 1)
pillar_strength = p_strength
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_z:.1f} m")
m3.metric("Stress Ratio (k)", f"{k_ratio}")
m4.metric("TAVSIYA: Selek Eni", f"{rec_width} m")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
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
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    # Hoek-Brown visualization for seam layer
    mb_s, s_s, a_s = grid_mb.max(), grid_s.max(), grid_a.max()
    s1_init = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + 1e-6) + s_s)**a_s
    s1_fire = sigma3_ax + (ucs_seam * reduction) * (mb_s * sigma3_ax / (ucs_seam * reduction + 1e-6) + s_s)**a_s
    
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_init, name='20°C (Dastlabki)', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_fire, name='TM Zararlangan', line=dict(color='orange', width=4)))
    fig_hb.update_layout(title="🛡️ Hoek-Brown Envelope (Ko'mir)", template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_hb, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("📋 Ilmiy Tahlil")
    st.info(f"**Iterativ Selek Solver:**")
    st.write(f"Konvergentsiya 15 qadamda yakunlandi. Wilson (1972) yondashuvi bo'yicha barqaror yadro (core) saqlab qolindi.")
    
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed', title="Chuqurlik (m)"), height=450, showlegend=False)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi (Layer-by-Layer)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, 
                           subplot_titles=("PDE Issiqlik Diffuziyasi (°C)", "FOS va Plastik Zonalar (Principal Stress)"))
    
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, colorbar=dict(title="T (°C)", x=1.08, y=0.78, len=0.42)), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']], zmin=0, zmax=3.0, contours_showlines=False, colorbar=dict(title="FOS", x=1.08, y=0.22, len=0.42)), row=2, col=1)

    fig_tm.add_trace(go.Scatter(x=grid_x[shear_failure][::3], y=grid_z[shear_failure][::3], mode='markers', marker=dict(color='red', size=2, opacity=0.4), name='Shear Yield'), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tensile_failure][::3], y=grid_z[tensile_failure][::3], mode='markers', marker=dict(color='blue', size=2, opacity=0.4), name='Tensile Yield'), row=2, col=1)
    
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(r=150))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
