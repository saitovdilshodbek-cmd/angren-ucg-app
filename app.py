import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

# ==============================================================================
# --- 🌍 GEOTECHNICAL DATABASE INTEGRATION (NEW) ---
# ==============================================================================
geo_db = {
    "Angren (Uzbekistan)": {"E": 5500, "phi": 28, "c": 2.2, "alpha_T": 1.2e-5, "rho": 1350, "ucs": 15, "gsi": 55, "mi": 10},
    "Shivee Ovoo (Mongolia)": {"E": 3200, "phi": 24, "c": 1.8, "alpha_T": 1.5e-5, "rho": 1250, "ucs": 10, "gsi": 45, "mi": 8},
    "Custom": {"E": 4000, "phi": 25, "c": 2.0, "alpha_T": 1.2e-5, "rho": 1500, "ucs": 20, "gsi": 50, "mi": 10}
}

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Ko'p Modelli Optimizatsiya")

# ==============================================================================
# --- 🧮 TO'LIQ MATEMATIK METODOLOGIYA ---
# ==============================================================================
st.sidebar.header("🧮 Metodologiya & Mode")
selected_field = st.sidebar.selectbox("Kon ma'lumotlar bazasi:", list(geo_db.keys()))
f_params = geo_db[selected_field]

# NEW: Dimensionless va Failure Model tanlovi
display_mode = st.sidebar.selectbox("Vizualizatsiya rejimi:", ["Standard (Metric)", "Universal (Dimensionless)"])
failure_model = st.sidebar.selectbox("Plastiklik modeli:", ["Hoek-Brown", "Mohr-Coulomb", "Drucker-Prager"])

formula_option = st.sidebar.selectbox(
    "Formulalarni ko'rish:",
    ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability", "3. Thermal Stress & Tension", "4. Pillar & Subsidence"]
)

if formula_option != "Yopish":
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == "1. Hoek-Brown Failure (2018)":
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.info("**Hoek-Brown:** GSI va Disturbance (D) faktorlari asosida massiv mustahkamligi.")
        elif formula_option == "2. Thermal Damage & Permeability":
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
        elif formula_option == "3. Thermal Stress & Tension":
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu}")
        elif formula_option == "4. Pillar & Subsidence":
            st.latex(r"\sigma_{p} = (UCS \cdot \eta) \cdot (w/H)^{0.5}")

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value=f"{selected_field.split()[0]}-UCG")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 48)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

tensile_mode = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.5)
nu_poisson = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, 0.5)

st.sidebar.subheader("🔥 Yonish va Termal")
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)

# Layers Data Generation
layers_data = []
total_depth = 0
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        # DB dan defolt qiymatlarni olish
        def_ucs = f_params['ucs'] if i == int(num_layers)-1 else 40.0
        def_gsi = f_params['gsi'] if i == int(num_layers)-1 else 60.0
        
        name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
        u = st.number_input(f"UCS (MPa):", value=float(def_ucs), key=f"u_{i}")
        rho = st.number_input(f"Zichlik (kg/m³):", value=f_params['rho'] if i == int(num_layers)-1 else 2500, key=f"rho_{i}")
        g = st.slider(f"GSI:", 10, 100, int(def_gsi), key=f"g_{i}")
        m = st.number_input(f"mi:", value=float(f_params['mi']), key=f"m_{i}")
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'rho': rho, 
            'gsi': g, 'mi': m, 'color': strata_colors[i % 5], 'z_start': total_depth
        })
        total_depth += thick

# --- HISOB-KITOBLAR ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

# Gridlarni tayyorlash
grid_sigma_v, grid_ucs, grid_mb, grid_s_hb, grid_a_hb = [np.zeros_like(grid_z) for _ in range(5)]

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1: mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))

# Termal PDE Solver (Fourier logic)
alpha_rock = f_params['alpha_T'] * 1e5
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec = (time_h - val['start'])
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec) 
        curr_T = T_source_max if dt_sec <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(dt_sec-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

# Stress & Damage
damage = 1 - np.exp(-0.002 * np.maximum(temp_2d - 100, 0))
sigma_ci = grid_ucs * (1 - np.clip(damage, 0, 0.9))
sigma_thermal = 0.7 * (f_params['E'] * f_params['alpha_T'] * (temp_2d - 25)) / (1 - nu_poisson)

grid_sigma_h = (k_ratio * grid_sigma_v) - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

# Failure Calculation (Multi-model)
def get_limit(s3, model):
    if model == "Mohr-Coulomb":
        phi_rad = np.radians(f_params['phi'])
        ka = (1 + np.sin(phi_rad)) / (1 - np.sin(phi_rad))
        return s3 * ka + 2 * f_params['c'] * np.sqrt(ka)
    elif model == "Drucker-Prager":
        return s3 * 1.5 + 2.5
    else: # Hoek-Brown
        s3_safe = np.maximum(s3, 0.01)
        return s3_safe + sigma_ci * (grid_mb * s3_safe / (sigma_ci + 1e-6) + grid_s_hb)**grid_a_hb

sigma1_limit = get_limit(sigma3_act, failure_model)
shear_failure = sigma1_act >= sigma1_limit
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)

# Void & Permanent Changes
void_mask = (temp_2d > 950) | (shear_failure & (temp_2d > 600))
void_mask_permanent = gaussian_filter(void_mask.astype(float), sigma=1.2) > 0.4
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)

# Selek Optimizatsiyasi
strength_red = np.exp(-0.0025 * (np.mean(temp_2d[np.abs(z_axis-source_z).argmin(),:]) - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()
w_sol = 20.0
for _ in range(10):
    p_str = (ucs_seam * strength_red) * (w_sol / H_seam)**0.5
    y_zone = (H_seam / 2) * (np.sqrt(sv_seam / (p_str + 1e-6)) - 1)
    w_sol = 2 * max(y_zone, 2.0) + 0.5 * H_seam

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name} ({selected_field}) Monitoring")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Selek Mustahkamligi", f"{p_str:.1f} MPa")
m2.metric("Plastik zona (y)", f"{max(y_zone, 2.0):.1f} m")
m3.metric("Maks. Harorat", f"{np.max(temp_2d):.0f} °C")
m4.metric("Failure Model", failure_model)
m5.metric("TAVSIYA: Selek Eni", f"{np.round(w_sol, 1)} m")

# Subsidence Plots
st.markdown("---")
col_g1, col_g2 = st.columns(2)
s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta'))).update_layout(title="📉 Cho'kish (cm)", template="plotly_dark", height=250), use_container_width=True)
with col_g2:
    # Hoek-Brown Envelope
    s3_ax = np.linspace(0, ucs_seam, 50)
    s1_env = s3_ax + ucs_seam * (f_params['mi'] * s3_ax / ucs_seam + 1)**0.5
    st.plotly_chart(go.Figure(go.Scatter(x=s3_ax, y=s1_env, name="Chegara")).update_layout(title="🛡️ Failure Envelope", template="plotly_dark", height=250), use_container_width=True)

# Main RS2 Heatmaps
st.markdown("---")
c1, c2 = st.columns([1, 3])
with c1:
    st.subheader("📋 Kesim")
    fig_s = go.Figure()
    for l in layers_data: fig_s.add_trace(go.Bar(x=['Section'], y=[l['t']], name=l['name'], marker_color=l['color']))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=600), use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va FOS (RS2 Style)")
    # Dimensionless logic for plotting
    if display_mode == "Universal (Dimensionless)":
        p_x, p_z = grid_x / total_depth, grid_z / total_depth
        p_t = (temp_2d - 25) / (T_source_max - 25)
    else:
        p_x, p_z, p_t = grid_x, grid_z, temp_2d

    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=("Harorat Maydoni", "Safety Factor (FOS)"))
    
    fig_tm.add_trace(go.Heatmap(z=p_t, x=x_axis, y=z_axis, colorscale='Hot'), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale='RdYlGn', zmin=0, zmax=3), row=2, col=1)
    
    # Yielded markers
    y_idx, x_idx = np.where(shear_failure == True)
    fig_tm.add_trace(go.Scatter(x=x_axis[x_idx[::4]], y=z_axis[y_idx[::4]], mode='markers', marker=dict(color='black', size=2, symbol='x'), name="Yield"), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=800)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1); fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | {selected_field}")
