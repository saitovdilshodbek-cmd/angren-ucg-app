import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

# --- SAHITA SOZLAMALARI ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# --- SIDEBAR: PARAMETRLAR ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

tensile_mode = st.sidebar.selectbox(
    "Tensile modeli:",
    ["Empirical (UCS)", "HB-based (auto)", "Manual"]
)

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
            
        s_t0_val = st.number_input(f"σt0 (MPa):", value=3.0, key=f"st_{i}") if tensile_mode == "Manual" else 0.0
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'rho': rho, 
            'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
            'sigma_t0_manual': s_t0_val
        })
        total_depth += thick

# --- ILMIY MANBALAR (METODOLOGIYA) ---
# 1. Hoek-Brown Criterion: https://rocscience.com/help/rs2/theory/hoek-brown-failure-criterion
# 2. Thermal Stress Theory: Timoshenko & Goodier, "Theory of Elasticity", 3rd Ed.
# 3. UCG Subsidence & Stability: Yang et al. (2010), "Stability analysis of UCG"
# 4. Permeability Evolution: Cui et al. (2017), DOI: 10.1007/s40789-017-0171-4

# --- HISOB-KITOBLAR ---
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
    # Vertical Stress calculation (PZ = rho * g * h)
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    # GSI to HB Parameters conversion (Hoek et al., 2002)
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

# Heat conduction (Fourier's Law approximation)
alpha_rock = 1.0e-6 
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec) 
        curr_T = T_source_max if (time_h - val['start']) <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*((time_h-val['start'])-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25

# --- TM ANALIZ: Stress va Damage ---
# Thermal Damage model: D_t = 1 - exp(-k * (T - T_crit))
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage = 1 - np.exp(-0.002 * temp_eff)
damage = np.clip(damage, 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

E = 5000 
alpha_T_coeff = 1e-5
constraint_factor = 0.7 

dT_dx = np.gradient(temp_2d, axis=1)
dT_dz = np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)

# Linear Elastic Thermal Stress (Plane Strain condition)
sigma_thermal = constraint_factor * (E * alpha_T_coeff * delta_T) / (1 - nu_poisson)
sigma_thermal += 0.3 * thermal_gradient

grid_sigma_h = (k_ratio * grid_sigma_v) - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
thermal_tension_boost = 1 + 0.6 * (1 - np.exp(-delta_T / 200))
sigma_t_field_eff = sigma_t_field / thermal_tension_boost

# --- FAILURE DETECTION & VOID ---
# Tensile failure if sigma3 <= -sigma_t
tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50) & (sigma1_act > sigma3_act)
sigma3_safe = np.maximum(sigma3_act, 0.01)
# Hoek-Brown Failure Envelope formula (sigma1 = sigma3 + sigma_ci * (mb * sigma3 / sigma_ci + s)^a)
sigma1_limit = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + 1e-6) + grid_s_hb)**grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > 400)
crushing = shear_failure & (temp_2d > 600)

depth_factor = np.exp(-grid_z / total_depth)
local_collapse_T = np.clip((st.session_state.max_temp_map - 600) / 300, 0, 1)
time_factor = np.clip((time_h - 40) / 60, 0, 1)
collapse_final = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw = (spalling | crushing | (st.session_state.max_temp_map > 900))
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_permanent > 0.3) & (collapse_final > 0.05)

# --- HYDRAULIC: Permeability va Void Volume ---
# Permeability evolution based on stress-induced damage (Cui et al., 2017)
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])

# Stress reset inside voids
sigma1_act = np.where(void_mask_permanent, 0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0, sigma3_act)
sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)

# --- SELEK (PILLAR) OPTIMIZATSIYASI ---
# Pillar strength formula: sigma_p = sigma_ci * (w/h)^0.5 (Obert & Duvall)
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
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi", f"{void_volume:.1f} m³")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("TAVSIYA: Selek Eni", f"{rec_width} m")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])
# Surface Subsidence calculation (Gaussian distribution theory)
s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*10)) * (time_h/150) * 100

with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta', width=3))).update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy', line=dict(color='cyan', width=3))).update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + 1e-6) + s_s)**a_s
    strength_red_burning = np.exp(-0.0025 * (T_source_max - 20))
    ucs_burning = ucs_seam * strength_red_burning
    s1_burning = sigma3_ax + ucs_burning * (mb_s * sigma3_ax / (ucs_burning + 1e-6) + s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam * strength_red) * (mb_s * sigma3_ax / (ucs_seam * strength_red + 1e-6) + s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name='Zararlangan', line=dict(color='cyan', dash='dash', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish payti', line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300, 
                                        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")), use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader("📋 Ilmiy Tahlil")
    st.error("🔴 FOS < 1.0: Failure")
    st.warning("🟡 FOS 1.0 - 1.5: Unstable")
    st.success("🟢 FOS > 1.5: Stable")
    fig_s = go.Figure()
    for l in layers_data: fig_s.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi (RS2)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=("Harorat Maydoni (°C)", "Xavfsizlik Koeffitsiyenti (FOS) & Yielded Zones"))
    
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, 
        colorbar=dict(title="T (°C)", title_side="top", x=1.05, y=0.78, len=0.42, thickness=15)
    ), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=fos_2d, x=x_axis, y=z_axis, 
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']], 
        zmin=0, zmax=3.0, contours_showlines=False, 
        colorbar=dict(title="FOS", title_side="top", x=1.05, y=0.22, len=0.42, thickness=15)
    ), row=2, col=1)

    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=void_visual, x=x_axis, y=z_axis,
        colorscale=[[0, 'black'], [1, 'black']], 
        showscale=False, opacity=0.9, hoverinfo='skip'
    ), row=2, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=void_mask_permanent.astype(int),
        x=x_axis, y=z_axis,
        showscale=False,
        contours=dict(coloring='lines'),
        line=dict(color='white', width=2),
        hoverinfo='skip'
    ), row=2, col=1)
    
    shear_disp = np.copy(shear_failure)
    shear_disp[void_mask_permanent] = False
    tens_disp = np.copy(tensile_failure)
    tens_disp[void_mask_permanent] = False

    fig_tm.add_trace(go.Scatter(x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2], mode='markers', marker=dict(color='red', size=3, symbol='x'), name='Shear'), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2], mode='markers', marker=dict(color='blue', size=3, symbol='cross'), name='Tensile'), row=2, col=1)
    
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)
    
    fig_tm.update_layout(
        template="plotly_dark", height=850, margin=dict(r=150, t=80, b=100),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1); fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
