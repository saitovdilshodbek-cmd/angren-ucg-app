import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

# ==============================================================================
# --- 🌍 GEOTECHNICAL DATABASE (NEW INTEGRATION) ---
# ==============================================================================
geo_db = {
    "Angren (Uzbekistan)": {"E": 5500, "phi": 28, "c": 2.2, "alpha_T": 1.2e-5, "rho": 1350, "ucs": 15, "gsi": 55, "mi": 10},
    "Zonguldak (Turkey)": {"E": 7500, "phi": 32, "c": 4.5, "alpha_T": 1.0e-5, "rho": 1450, "ucs": 35, "gsi": 65, "mi": 12},
    "Shivee Ovoo (Mongolia)": {"E": 3200, "phi": 24, "c": 1.8, "alpha_T": 1.5e-5, "rho": 1250, "ucs": 10, "gsi": 45, "mi": 8},
    "Custom": {"E": 5000, "phi": 25, "c": 2.0, "alpha_T": 1.0e-5, "rho": 2500, "ucs": 40, "gsi": 60, "mi": 10}
}

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# --- 🧮 TO'LIQ MATEMATIK METODOLOGIYA (PHD LEVEL) ---
# ==============================================================================
st.sidebar.header("🧮 Matematik Metodologiya")

# NEW: Ma'lumotlar bazasi va Rejim tanlovi
selected_field = st.sidebar.selectbox("Kon ma'lumotlar bazasi:", list(geo_db.keys()))
f_params = geo_db[selected_field]

display_mode = st.sidebar.selectbox("Vizualizatsiya rejimi:", ["Standard (Metric)", "Universal (Dimensionless)"])
failure_model = st.sidebar.selectbox("Plastiklik modeli (Failure Criteria):", ["Hoek-Brown (2018)", "Mohr-Coulomb", "Drucker-Prager"])

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
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

tensile_mode = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, 0.5)

st.sidebar.subheader("📐 Cho'zilish va Selek")
tensile_ratio = st.sidebar.slider("Tensile Ratio (σt0/UCS):", 0.03, 0.15, 0.08)
beta_thermal = st.sidebar.number_input("Thermal Decay (β):", value=0.0035, format="%.4f")

st.sidebar.subheader("🔥 Yonish va Termal")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

layers_data = []
total_depth = 0
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        # DB dan defolt qiymatlarni olish (faqat oxirgi qatlam/ko'mir uchun)
        is_seam = (i == int(num_layers)-1)
        def_ucs = f_params['ucs'] if is_seam else 40.0
        def_gsi = f_params['gsi'] if is_seam else 60.0
        def_rho = f_params['rho'] if is_seam else 2500

        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
            u = st.number_input(f"UCS (MPa):", value=float(def_ucs), key=f"u_{i}")
            rho = st.number_input(f"Zichlik (kg/m³):", value=int(def_rho), key=f"rho_{i}")
        with col2:
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI:", 10, 100, int(def_gsi), key=f"g_{i}")
            m = st.number_input(f"mi:", value=float(f_params['mi']) if is_seam else 10.0, key=f"m_{i}")
            
        s_t0_val = st.number_input(f"σt0 (MPa):", value=3.0, key=f"st_{i}") if tensile_mode == "Manual" else 0.0
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'rho': rho, 
            'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
            'sigma_t0_manual': s_t0_val
        })
        total_depth += thick

# --- HISOB-KITOBLAR (ALGORITM ASOSI) ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

grid_sigma_v, grid_ucs, grid_mb, grid_s_hb, grid_a_hb, grid_sigma_t0_manual = [np.zeros_like(grid_z) for _ in range(6)]

if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
if 'last_obj_name' not in st.session_state or st.session_state.last_obj_name != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1: mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

alpha_rock = f_params['alpha_T'] * 1e5 # Ma'lumotlar bazasidan issiqlik o'tkazuvchanlik
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * 1e-6 * dt_sec) 
        curr_T = T_source_max if (time_h - val['start']) <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*((time_h-val['start'])-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25

# --- TM ANALIZ: Stress va Damage ---
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage = 1 - np.exp(-0.002 * temp_eff)
damage = np.clip(damage, 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

E_mod = f_params['E'] 
alpha_T_coeff = f_params['alpha_T']
constraint_factor = 0.7 

sigma_thermal = constraint_factor * (E_mod * alpha_T_coeff * delta_T) / (1 - nu_poisson)

grid_sigma_h = (k_ratio * grid_sigma_v) - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

# --- PLASTIKLIK MODELLARI INTEGRATSIYASI ---
def get_sigma1_limit(s3, model_type):
    if model_type == "Mohr-Coulomb":
        phi_rad = np.radians(f_params['phi'])
        ka = (1 + np.sin(phi_rad)) / (1 - np.sin(phi_rad))
        return s3 * ka + 2 * f_params['c'] * np.sqrt(ka)
    elif model_type == "Drucker-Prager":
        # Simplified DP for rock masses
        return s3 * 1.8 + (sigma_ci * 0.4)
    else: # Hoek-Brown
        s3_safe = np.maximum(s3, 0.01)
        return s3_safe + sigma_ci * (grid_mb * s3_safe / (sigma_ci + 1e-6) + grid_s_hb)**grid_a_hb

sigma1_limit = get_sigma1_limit(sigma3_act, failure_model)

# --- FAILURE DETECTION ---
if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
sigma_t_field_eff = sigma_t_field / (1 + 0.6 * (1 - np.exp(-delta_T / 200)))

tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50)
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > 400)
crushing = shear_failure & (temp_2d > 600)

void_mask_raw = (spalling | crushing | (st.session_state.max_temp_map > 900))
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.5) > 0.3

# --- Permeability va Selek ---
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])

# Selek Optimizatsiyasi
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam * strength_red) * (w_sol / H_seam)**0.5
    y_zone_calc = (H_seam / 2) * (np.sqrt(sv_seam / (p_strength + 1e-6)) - 1)
    new_w = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1: break
    w_sol = new_w

rec_width, pillar_strength, y_zone = np.round(w_sol, 1), p_strength, max(y_zone_calc, 1.5)
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0, fos_2d)

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name} ({selected_field}): Monitoring")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Failure Model", failure_model.split('(')[0])
m4.metric("Kamera Hajmi", f"{void_volume:.1f} m³")
m5.metric("TAVSIYA: Selek Eni", f"{rec_width} m")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])
s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*10)) * (time_h/150) * 100

with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta', width=3))).update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy', line=dict(color='cyan', width=3))).update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    # Hoek-Brown Envelopes
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    s1_20 = sigma3_ax + ucs_seam * (f_params['mi'] * sigma3_ax / (ucs_seam + 1e-6) + 1)**0.5
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='Massiv (20°C)', line=dict(color='red')))
    st.plotly_chart(fig_hb.update_layout(title="🛡️ Failure Envelope", template="plotly_dark", height=300), use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader("📋 Kesim")
    fig_s = go.Figure()
    for l in layers_data: fig_s.add_trace(go.Bar(x=['Section'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

with c2:
    st.subheader(f"🔥 TM Maydoni va Selek Interferensiyasi ({display_mode})")
    
    # Dimensionless logic
    if display_mode == "Universal (Dimensionless)":
        p_x, p_z = grid_x / total_depth, grid_z / total_depth
        p_t = (temp_2d - 25) / (T_source_max - 25)
        x_label, z_label = "X / H", "Z / H"
    else:
        p_x, p_z, p_t = grid_x, grid_z, temp_2d
        x_label, z_label = "Masofa (m)", "Chuqurlik (m)"

    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=("Harorat Maydoni", "FOS & Yielded Zones"))
    
    fig_tm.add_trace(go.Heatmap(z=p_t, x=x_axis if display_mode=="Standard (Metric)" else x_axis/total_depth, y=z_axis if display_mode=="Standard (Metric)" else z_axis/total_depth, colorscale='Hot'), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis if display_mode=="Standard (Metric)" else x_axis/total_depth, y=z_axis if display_mode=="Standard (Metric)" else z_axis/total_depth, colorscale='RdYlGn', zmin=0, zmax=3.0, contours_showlines=False), row=2, col=1)

    # RS2 Yielded Markers
    y_idx, x_idx = np.where(shear_failure == True)
    fig_tm.add_trace(go.Scatter(x=p_x[y_idx[::5], x_idx[::5]], y=p_z[y_idx[::5], x_idx[::5]], mode='markers', marker=dict(color='black', size=2, symbol='x'), name='Shear Yield'), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=850, showlegend=True)
    fig_tm.update_yaxes(autorange='reversed', title=z_label, row=1, col=1); fig_tm.update_yaxes(autorange='reversed', title=z_label, row=2, col=1)
    fig_tm.update_xaxes(title=x_label, row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# --- MANBALAR ---
st.markdown("---")
with st.expander("📚 PhD Research References"):
    st.write("1. Hoek-Brown Failure Criterion (2018 Edition).")
    st.write("2. Thermal-Mechanical Coupling in UCG Stability (Yang, 2010).")
    st.write("3. Angren Coal Mine Geomechanical Properties Database.")

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | {selected_field}")
