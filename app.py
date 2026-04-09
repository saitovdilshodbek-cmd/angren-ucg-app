import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress
import time
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
import qrcode
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# =========================== PYTORCH IMPORT ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except:
    PT_AVAILABLE = False
    device = "cpu"

# =========================== TRANSLATIONS (qisqartirilgan) ===========================
TRANSLATIONS = {
    'uz': {
        'app_title': "Universal Yer yuzasi Deformatsiyasi Monitoringi",
        'app_subtitle': "Termo-Mexanik tahlil va Selek Optimizatsiyasi",
        'sidebar_header_params': "⚙️ Umumiy parametrlar",
        'project_name': "Loyiha nomi:",
        'process_time': "Jarayon vaqti (soat):",
        'num_layers': "Qatlamlar soni:",
        'rock_props': "💎 Jins Xususiyatlari",
        'disturbance': "Disturbance Factor (D):",
        'poisson': "Poisson koeffitsiyenti (ν):",
        'stress_ratio': "Stress Ratio (k = σh/σv):",
        'tensile_params': "📐 Cho'zilish va Selek",
        'tensile_ratio': "Tensile Ratio (σt0/UCS):",
        'thermal_decay': "Thermal Decay (β):",
        'combustion': "🔥 Yonish va Termal",
        'burn_duration': "Kamera yonish muddati (soat):",
        'max_temp': "Maksimal harorat (°C)",
        'layer_params': "{num}-qatlam parametrlari",
        'layer_name': "Nomi:",
        'thickness': "Qalinlik (m):",
        'ucs': "UCS (MPa):",
        'density': "Zichlik (kg/m³):",
        'color': "Rangi:",
        'gsi': "GSI:",
        'mi': "mi:",
        'error_thick_positive': "Qalinlik >0 bo'lishi kerak",
        'error_ucs_positive': "UCS >0 MPa bo'lishi kerak",
        'error_density_positive': "Zichlik >0 kg/m³ bo'lishi kerak",
        'error_gsi_range': "GSI 10...100 oralig'ida bo'lishi kerak",
        'error_mi_positive': "mi >0 bo'lishi kerak",
        'error_min_layers': "❌ Kamida 1 ta qatlam kiriting!",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastik zona (y)",
        'cavity_volume': "Kamera Hajmi",
        'max_permeability': "Maks. O'tkazuvchanlik",
        'ai_recommendation': "AI Tavsiya (Selek)",
        'monitoring_header': "📊 {obj_name}: Monitoring va Ekspert Xulosasi",
        'subsidence_title': "📉 Yer yuzasi cho'kishi (cm)",
        'thermal_deform_title': "🔥 Termal deformatsiya (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Ilmiy Tahlil",
        'fos_red': "🔴 FOS < 1.0: Failure",
        'fos_yellow': "🟡 FOS 1.0–1.5: Unstable",
        'fos_green': "🟢 FOS > 1.5: Stable",
        'temp_subplot': "Harorat Maydoni (°C)",
        'gas_flow': "Gaz oqimi",
        'shear': "Shear",
        'tensile': "Tensile",
        'ai_collapse': "AI Collapse",
        'monitoring_panel': "📊 {obj_name}: Kompleks Monitoring Paneli",
        'pillar_live': "Pillar Strength",
        'rec_width_live': "Tavsiya: Selek Eni",
        'max_subsidence_live': "Maks. Cho'kish",
        'process_stage': "Jarayon bosqichi",
        'stage_active': "Faol",
        'stage_cooling': "Sovish",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'advanced_analysis': "🔍 Chuqurlashtirilgan Dinamik Tahlil",
    },
    'en': {
        'app_title': "Universal Surface Deformation Monitoring",
        'app_subtitle': "Thermo-Mechanical Analysis and Pillar Optimization",
        'sidebar_header_params': "⚙️ General Parameters",
        'project_name': "Project name:",
        'process_time': "Process time (hours):",
        'num_layers': "Number of layers:",
        'rock_props': "💎 Rock Properties",
        'disturbance': "Disturbance Factor (D):",
        'poisson': "Poisson's ratio (ν):",
        'stress_ratio': "Stress Ratio (k = σh/σv):",
        'tensile_params': "📐 Tension and Pillar",
        'tensile_ratio': "Tensile Ratio (σt0/UCS):",
        'thermal_decay': "Thermal Decay (β):",
        'combustion': "🔥 Combustion and Thermal",
        'burn_duration': "Burn duration (hours):",
        'max_temp': "Maximum temperature (°C)",
        'layer_params': "Layer {num} parameters",
        'layer_name': "Name:",
        'thickness': "Thickness (m):",
        'ucs': "UCS (MPa):",
        'density': "Density (kg/m³):",
        'color': "Color:",
        'gsi': "GSI:",
        'mi': "mi:",
        'error_thick_positive': "Thickness must be >0",
        'error_ucs_positive': "UCS must be >0 MPa",
        'error_density_positive': "Density must be >0 kg/m³",
        'error_gsi_range': "GSI must be between 10 and 100",
        'error_mi_positive': "mi must be >0",
        'error_min_layers': "❌ At least 1 layer required!",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastic zone (y)",
        'cavity_volume': "Cavity Volume",
        'max_permeability': "Max Permeability",
        'ai_recommendation': "AI Recommendation (Pillar)",
        'monitoring_header': "📊 {obj_name}: Monitoring and Expert Summary",
        'subsidence_title': "📉 Surface subsidence (cm)",
        'thermal_deform_title': "🔥 Thermal deformation (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Scientific Analysis",
        'fos_red': "🔴 FOS < 1.0: Failure",
        'fos_yellow': "🟡 FOS 1.0–1.5: Unstable",
        'fos_green': "🟢 FOS > 1.5: Stable",
        'temp_subplot': "Temperature Field (°C)",
        'gas_flow': "Gas flow",
        'shear': "Shear",
        'tensile': "Tensile",
        'ai_collapse': "AI Collapse",
        'monitoring_panel': "📊 {obj_name}: Integrated Monitoring Panel",
        'pillar_live': "Pillar Strength",
        'rec_width_live': "Recommended Pillar Width",
        'max_subsidence_live': "Max Subsidence",
        'process_stage': "Process stage",
        'stage_active': "Active",
        'stage_cooling': "Cooling",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'advanced_analysis': "🔍 In-depth Dynamic Analysis",
    }
}

def t(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

EPS = 1e-12

st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# =========================== TILNI SOZLASH ===========================
if 'language' not in st.session_state:
    st.session_state.language = 'uz'

LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English'}
lang = st.sidebar.selectbox("Til / Language", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# =========================== QR KOD ===========================
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
url = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/"
@st.cache_data
def generate_qr(link):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
st.sidebar.image(generate_qr(url), caption="Scan QR", use_container_width=True)

# =========================== SIDEBAR PARAMETRLAR ===========================
st.sidebar.header(t('sidebar_header_params'))
obj_name      = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h        = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers    = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)

st.sidebar.subheader(t('rock_props'))
D_factor      = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson    = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio       = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)

st.sidebar.subheader(t('tensile_params'))
tensile_ratio = st.sidebar.slider(t('tensile_ratio'), 0.03, 0.15, 0.08)
beta_thermal  = st.sidebar.number_input(t('thermal_decay'), value=0.0035, format="%.4f")

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40)
T_source_max  = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

# Quduqlar masofasi
well_distance = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0)

# =========================== QATLAM MA'LUMOTLARI ===========================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i+1), expanded=(i == int(num_layers)-1)):
        name  = st.text_input(t('layer_name'), value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(t('thickness'), value=50.0, min_value=0.1, key=f"t_{i}")
        u     = st.number_input(t('ucs'), value=40.0, min_value=0.1, key=f"u_{i}")
        rho   = st.number_input(t('density'), value=2500.0, min_value=100.0, key=f"rho_{i}")
        color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
        g     = st.slider(t('gsi'), 10, 100, 60, key=f"g_{i}")
        m     = st.number_input(t('mi'), value=10.0, min_value=0.1, key=f"m_{i}")
    layers_data.append({
        'name': name, 't': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
    })
    total_depth += thick

# Validatsiya
errors = []
for lyr in layers_data:
    if lyr['t'] <= 0: errors.append(t('error_thick_positive'))
    if lyr['ucs'] <= 0: errors.append(t('error_ucs_positive'))
    if lyr['rho'] <= 0: errors.append(t('error_density_positive'))
    if not (10 <= lyr['gsi'] <= 100): errors.append(t('error_gsi_range'))
    if lyr['mi'] <= 0: errors.append(t('error_mi_positive'))
if not layers_data: errors.append(t('error_min_layers'))
if errors:
    for e in errors: st.error(e)
    st.stop()

# =========================== ASOSIY HISOB FUNKSIYASI (barcha natijalarni qaytaradi) ===========================
def compute_all_results(time_h, T_source_max, burn_duration, total_depth, layers_data,
                        D_factor, nu_poisson, k_ratio, beta_thermal, well_distance):
    # Grid yaratish
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, 100)
    z_axis = np.linspace(0, total_depth + 50, 80)
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
    H_seam = layers_data[-1]['t']
    source_z = total_depth - (H_seam / 2)

    # 1. Harorat maydoni (soddalashtirilgan, lekin vaqtga bog'liq)
    # Asl koddagi murakkab harorat hisobini qisqacha bajaramiz
    alpha_rock = 1.0e-6
    v_burn = 0.02
    sources = [
        {'x0': -total_depth/3, 'start': 0, 'moving': False},
        {'x0': 0, 'start': 40, 'moving': True, 'v': v_burn},
        {'x0': total_depth/3, 'start': 80, 'moving': False}
    ]
    temp_2d = np.full_like(grid_x, 25.0)
    for src in sources:
        if time_h <= src['start']: continue
        dt_sec = (time_h - src['start']) * 3600
        if src['moving']: x_center = src['x0'] + src['v'] * dt_sec
        else: x_center = src['x0']
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
        elapsed = time_h - src['start']
        if elapsed <= burn_duration: curr_T = T_source_max
        else: curr_T = 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration))
        dist_sq = (grid_x - x_center)**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))
    # Diffuziya
    for _ in range(20):
        temp_2d[1:-1,1:-1] += alpha_rock * (
            temp_2d[2:,1:-1] + temp_2d[:-2,1:-1] +
            temp_2d[1:-1,2:] + temp_2d[1:-1,:-2] -
            4 * temp_2d[1:-1,1:-1])
    # Maksimal haroratni saqlash
    max_temp_map = np.maximum(temp_2d, 25)

    # 2. Geomexanik hisoblar
    grid_sigma_v = np.zeros_like(grid_z)
    grid_ucs = np.zeros_like(grid_z)
    grid_mb = np.zeros_like(grid_z)
    grid_s_hb = np.zeros_like(grid_z)
    grid_a_hb = np.zeros_like(grid_z)
    layer_bounds = [(l['z_start'], l['z_start'] + l['t']) for l in layers_data]
    for i, (z0, z1) in enumerate(layer_bounds):
        mask = (grid_z >= z0) & (grid_z < z1 if i < len(layer_bounds)-1 else True)
        layer = layers_data[i]
        overburden = sum(l['rho']*9.81*l['t'] for l in layers_data[:i]) / 1e6
        depth_local = grid_z[mask] - z0
        grid_sigma_v[mask] = overburden + (layer['rho']*9.81*depth_local) / 1e6
        grid_ucs[mask] = layer['ucs']
        exp_gsi = (layer['gsi'] - 100)
        grid_mb[mask] = layer['mi'] * np.exp(exp_gsi / (28 - 14*D_factor))
        grid_s_hb[mask] = np.exp(exp_gsi / (9 - 3*D_factor))
        grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    
    delta_T = temp_2d - 25.0
    # Termal zarar
    def thermal_damage(T, T0=100, k=0.002):
        return np.clip(1 - np.exp(-k * np.maximum(T - T0, 0)), 0, 0.98)
    damage = thermal_damage(max_temp_map)
    sigma_ci = grid_ucs * (1 - damage)
    
    # Kuchlanishlar
    E_MOD = 5000.0
    ALPHA_T = 1.0e-5
    sigma_thermal = (E_MOD * ALPHA_T * delta_T) / (1 - nu_poisson + EPS)
    grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
    sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
    sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)
    
    # Hoek-Brown limit
    def hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a):
        sigma3_safe = np.maximum(sigma3, 0.01)
        return sigma3_safe + sigma_ci * (mb * sigma3_safe / (sigma_ci + 1e-9) + s) ** a
    sigma1_limit = hoek_brown_sigma1(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)
    fos_2d = np.clip(sigma1_limit/(sigma1_act+EPS), 0, 3)
    
    # Bo'shliq (void) maydoni
    tensile_failure = (sigma3_act <= -0.5) & (delta_T>50)
    shear_failure = sigma1_act >= sigma1_limit
    void_mask = tensile_failure | shear_failure | (max_temp_map>900)
    void_mask_smooth = gaussian_filter(void_mask.astype(float), sigma=1.0)
    void_mask_permanent = void_mask_smooth > 0.3
    
    # Gaz oqimi
    perm = 1e-12 * (void_mask_permanent.astype(float) * 0.1 + 0.01)
    pressure = temp_2d * 10.0
    dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
    vx, vz = -perm*dp_dx, -perm*dp_dz
    gas_velocity = np.sqrt(vx**2+vz**2)
    
    # Selek optimizatsiyasi
    avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
    strength_red = np.exp(-0.0025*(avg_t_p-20))
    ucs_seam = layers_data[-1]['ucs']
    sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()
    w_sol = 20.0
    for _ in range(15):
        p_strength = (ucs_seam*strength_red)*(w_sol/(H_seam+EPS))**0.5
        y_zone_calc = (H_seam/2)*(np.sqrt(sv_seam/(p_strength+EPS))-1)
        new_w = 2*max(y_zone_calc,1.5)+0.5*H_seam
        if abs(new_w-w_sol) < 0.1: break
        w_sol = new_w
    rec_width = np.round(w_sol, 1)
    pillar_strength = p_strength
    y_zone = max(y_zone_calc, 1.5)
    
    # AI Collapse (oddiy RandomForest)
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai)) > 1:
        rf_collapse = RandomForestClassifier(n_estimators=30, random_state=42)
        rf_collapse.fit(X_ai, y_ai)
        collapse_pred = rf_collapse.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
    else:
        collapse_pred = np.zeros_like(temp_2d)
    
    # Cho'kish va termal deformatsiya
    s_max = (H_seam*0.04)*(min(time_h,120)/120)
    sub_p = -s_max * np.exp(-(x_axis**2)/(2*(total_depth/2)**2))
    uplift = (total_depth*1e-4)*np.exp(-(x_axis**2)/(total_depth*10))*(time_h/150)*100
    
    # Hoek-Brown envelopelar
    sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
    mb_s = grid_mb.max()
    s_s = grid_s_hb.max()
    a_s = grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam*(mb_s*sigma3_ax/(ucs_seam+EPS)+s_s)**a_s
    ucs_burn = ucs_seam*np.exp(-0.0025*(T_source_max-20))
    s1_burning = sigma3_ax + ucs_burn*(mb_s*sigma3_ax/(ucs_burn+EPS)+s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam*strength_red)*(mb_s*sigma3_ax/(ucs_seam*strength_red+EPS)+s_s)**a_s
    
    # FOS vaqt trendi (soddalashtirilgan)
    time_points = np.arange(1, min(time_h, 150)+1, max(1, time_h//20))
    fos_timeline = []
    for th in time_points:
        str_red_t = np.exp(-0.0025*(T_source_max*min(th,burn_duration)/burn_duration - 20))
        p_str_t = (ucs_seam*str_red_t)*(rec_width/(H_seam+EPS))**0.5
        sv_t = sv_seam*(1+0.001*th)
        fos_t = np.clip(p_str_t/(sv_t+EPS),0,3)
        fos_timeline.append(fos_t)
    if len(time_points) > 1:
        slope, intercept, r_value, _, _ = linregress(time_points, fos_timeline)
    else:
        slope, intercept, r_value = 0, fos_timeline[0], 0
    
    # 3D litologik kesim uchun ma'lumotlar
    # (soddalashtirilgan)
    
    # Natijalarni lug'atda qaytarish
    results = {
        'x_axis': x_axis, 'z_axis': z_axis, 'grid_x': grid_x, 'grid_z': grid_z,
        'temp_2d': temp_2d, 'damage': damage, 'fos_2d': fos_2d,
        'gas_velocity': gas_velocity, 'collapse_pred': collapse_pred,
        'void_mask_permanent': void_mask_permanent,
        'sub_p': sub_p, 'uplift': uplift, 's1_20': s1_20, 's1_burning': s1_burning, 's1_sov': s1_sov,
        'sigma3_ax': sigma3_ax, 'pillar_strength': pillar_strength, 'y_zone': y_zone,
        'rec_width': rec_width, 'fos_timeline': fos_timeline, 'time_points': time_points,
        'slope': slope, 'intercept': intercept, 'r_value': r_value,
        'total_depth': total_depth, 'H_seam': H_seam, 'source_z': source_z,
        'well_x': [-well_distance, 0, well_distance],
        'layers_data': layers_data, 'layer_bounds': layer_bounds,
        'sigma_v_coal': sv_seam, 'ucs_coal_pa': ucs_seam * 1e6,
        'E_MOD': 25e9, 'ALPHA': 1e-5, 'NU': nu_poisson, 'K0': nu_poisson/(1-nu_poisson+EPS),
        'Hc': H_seam * np.sqrt(sv_seam/(ucs_seam+1e-5)),
    }
    return results

# =========================== ASOSIY HISOB ===========================
with st.spinner("Hisoblash davom etmoqda..."):
    results = compute_all_results(time_h, T_source_max, burn_duration, total_depth, layers_data,
                                  D_factor, nu_poisson, k_ratio, beta_thermal, well_distance)

# =========================== NATIJALARNI VIZUALIZATSIYA ===========================
st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4 = st.columns(4)
m1.metric(t('pillar_strength'), f"{results['pillar_strength']:.1f} MPa")
m2.metric(t('plastic_zone'), f"{results['y_zone']:.1f} m")
m3.metric(t('max_permeability'), f"{np.max(results['gas_velocity']):.1e} m/s")
m4.metric(t('ai_recommendation'), f"{results['rec_width']:.1f} m")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5,1.5,2])
with col_g1:
    fig_subs = go.Figure(go.Scatter(x=results['x_axis'], y=results['sub_p']*100, fill='tozeroy', line=dict(color='magenta',width=3)))
    fig_subs.update_layout(title=t('subsidence_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_subs, use_container_width=True)
with col_g2:
    fig_uplift = go.Figure(go.Scatter(x=results['x_axis'], y=results['uplift'], fill='tozeroy', line=dict(color='cyan',width=3)))
    fig_uplift.update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_uplift, use_container_width=True)
with col_g3:
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=results['sigma3_ax'], y=results['s1_20'], name='20°C', line=dict(color='red',width=2)))
    fig_hb.add_trace(go.Scatter(x=results['sigma3_ax'], y=results['s1_sov'], name='After cooling', line=dict(color='cyan',width=2,dash='dash')))
    fig_hb.add_trace(go.Scatter(x=results['sigma3_ax'], y=results['s1_burning'], name='Burning', line=dict(color='orange',width=4)))
    fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_hb, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in results['layers_data']:
        fig_layers.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    fig_layers.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False)
    st.plotly_chart(fig_layers, use_container_width=True)

with c2:
    st.subheader("TM Maydoni va FOS")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=(t('temp_subplot'), "FOS + AI Collapse"))
    fig_tm.add_trace(go.Heatmap(z=results['temp_2d'], x=results['x_axis'], y=results['z_axis'], colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42)), row=1, col=1)
    step = 12
    qx, qz = results['grid_x'][::step, ::step].flatten(), results['grid_z'][::step, ::step].flatten()
    vx_plot, vz_plot = results['gas_velocity'][::step, ::step] * np.cos(np.pi/4), results['gas_velocity'][::step, ::step] * np.sin(np.pi/4)
    fig_tm.add_trace(go.Scatter(x=qx, y=qz, mode='markers', marker=dict(symbol='arrow', size=8, color='cyan', opacity=0.6), name=t('gas_flow')), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=results['fos_2d'], x=results['x_axis'], y=results['z_axis'],
                                colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],[0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
                                zmin=0, zmax=3, contours_showlines=False, colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42)), row=2, col=1)
    fig_tm.add_trace(go.Heatmap(z=results['collapse_pred'], x=results['x_axis'], y=results['z_axis'], colorscale='Viridis', opacity=0.4, showscale=False), row=2, col=1)
    void_vis = np.where(results['void_mask_permanent']>0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_vis, x=results['x_axis'], y=results['z_axis'], colorscale=[[0,'black'],[1,'black']], showscale=False, opacity=0.8), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=700, margin=dict(r=150))
    fig_tm.update_yaxes(autorange='reversed', row=1); fig_tm.update_yaxes(autorange='reversed', row=2)
    st.plotly_chart(fig_tm, use_container_width=True)

# Kompleks monitoring paneli
st.header(t('monitoring_panel', obj_name=obj_name))
p_str_live = results['pillar_strength']
t_now = results['temp_2d'].max()
s_max_3d = np.max(-results['sub_p'])*100
mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric(t('pillar_live'), f"{p_str_live:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric(t('rec_width_live'), f"{results['rec_width']:.1f} m")
mk3.metric(t('max_subsidence_live'), f"{s_max_3d:.1f} cm")
mk4.metric(t('process_stage'), t('stage_active') if time_h<100 else t('stage_cooling'))

# FOS trendi
with st.expander("📈 FOS Vaqt Bashorati (Trend)"):
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=results['time_points'], y=results['fos_timeline'], mode='lines+markers', name='FOS', line=dict(color='cyan')))
    trend_line = results['intercept'] + results['slope'] * np.array(results['time_points'])
    fig_trend.add_trace(go.Scatter(x=results['time_points'], y=trend_line, mode='lines', name=f'Trend (R²={results["r_value"]**2:.3f})', line=dict(color='yellow', dash='dot')))
    fig_trend.add_hline(y=1.5, line_color='green', line_dash='dash', annotation_text='Barqaror')
    fig_trend.add_hline(y=1.0, line_color='red', line_dash='dash', annotation_text='Kritik')
    fig_trend.update_layout(template='plotly_dark', height=400, title="FOS vaqt bashorati")
    st.plotly_chart(fig_trend, use_container_width=True)
    st.metric("Trend", f"{results['slope']:+.4f} FOS/soat")
    if results['slope'] < 0:
        st.warning("FOS kamaymoqda, ehtiyot bo'ling!")

# AI Risk Prediction (sensor CSV) – soddalashtirilgan
with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    st.markdown("Sensor ma'lumotlari asosida xavf indeksini bashorat qilish.")
    sensor_file = st.file_uploader("CSV fayl (ustunlar: temp, stress, ucs_lab)", type=['csv'])
    if sensor_file:
        df = pd.read_csv(sensor_file)
        if all(c in df.columns for c in ['temp','stress','ucs_lab']):
            # Oddiy risk modeli
            risk = (df['temp']/1000 + df['stress']/50) / 2
            df['risk'] = np.clip(risk, 0, 1)
            st.dataframe(df)
            fig_risk = go.Figure(go.Scatter(y=df['risk'], mode='lines+markers'))
            fig_risk.update_layout(title="Risk Prediction", template='plotly_dark')
            st.plotly_chart(fig_risk, use_container_width=True)
            avg_risk = df['risk'].mean()
            if avg_risk > 0.7: st.error("Yuqori xavf!")
            elif avg_risk > 0.5: st.warning("O'rta xavf")
            else: st.success("Xavf past")
        else:
            st.error("Kerakli ustunlar topilmadi")

# 3D Litologik kesim
with st.expander("🌍 3D Litologik Kesim"):
    fig_3d = go.Figure()
    y_3d = np.linspace(-results['total_depth']*0.5, results['total_depth']*0.5, 30)
    for layer in results['layers_data']:
        z_top = layer['z_start']
        x_3d = np.linspace(results['x_axis'].min(), results['x_axis'].max(), 30)
        X3, Y3 = np.meshgrid(x_3d, y_3d)
        Z_top = np.full_like(X3, z_top)
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_top, colorscale=[[0,layer['color']],[1,layer['color']]], showscale=False, opacity=0.7, name=layer['name']))
    fig_3d.update_layout(scene=dict(zaxis=dict(autorange='reversed')), template='plotly_dark', height=600)
    st.plotly_chart(fig_3d, use_container_width=True)

# Advanced analysis (qisqacha)
with st.expander("📚 Ilmiy Metodologiya va Manbalar"):
    st.markdown("""
    **Hoek-Brown (2018)**, **Wilson (1972) pillar theory**, **termal degradatsiya** modellari asosida hisoblangan.
    - FOS < 1.0: Yemirilish
    - FOS 1.0–1.5: Beqaror
    - FOS > 1.5: Barqaror
    """)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")
