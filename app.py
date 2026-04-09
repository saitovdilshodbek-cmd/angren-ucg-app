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
import warnings
warnings.filterwarnings('ignore')

# =========================== PYTORCH IMPORT (xatolikka chidamli) ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except:
    PT_AVAILABLE = False
    device = "cpu"

# =========================== QR KOD (xatolikka chidamli) ===========================
try:
    import qrcode
    from io import BytesIO
    QR_AVAILABLE = True
except:
    QR_AVAILABLE = False

# =========================== GLOBAL TRANSLATIONS (qisqartirilgan) ===========================
TRANSLATIONS = {
    'uz': {
        'app_title': "Universal Yer yuzasi Deformatsiyasi Monitoringi",
        'app_subtitle': "Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi",
        'sidebar_header_params': "⚙️ Umumiy parametrlar",
        'formula_show': "Formulalarni ko'rish:",
        'project_name': "Loyiha nomi:",
        'process_time': "Jarayon vaqti (soat):",
        'num_layers': "Qatlamlar soni:",
        'tensile_model': "Tensile modeli:",
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
        'manual_st0': "σt0 (MPa):",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastik zona (y)",
        'cavity_volume': "Kamera Hajmi",
        'max_permeability': "Maks. O'tkazuvchanlik",
        'ai_recommendation': "AI Tavsiya (Selek)",
        'monitoring_header': "📊 {obj_name}: Monitoring va Ekspert Xulosasi",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
    },
    'en': {  # ... (qisqartirildi, lekin asl kodda to'liq)
        'app_title': "Universal Surface Deformation Monitoring",
        'pillar_strength': "Pillar Strength (σp)",
        'tensile_empirical': "Empirical (UCS)",
    },
    'ru': {  # ... (qisqartirildi)
        'app_title': "Универсальный мониторинг деформации земной поверхности",
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

# Til tanlash
if 'language' not in st.session_state:
    st.session_state.language = 'uz'
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# QR kod
if QR_AVAILABLE:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📱 Mobil ilovaga o'tish")
    url = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/"
    @st.cache_data
    def generate_qr(link):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    st.sidebar.image(generate_qr(url), caption="Scan QR", use_container_width=True)

# Sidebar parametrlar
st.sidebar.header(t('sidebar_header_params'))
obj_name = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode = st.sidebar.selectbox(t('tensile_model'), [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')])

st.sidebar.subheader(t('rock_props'))
D_factor = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)

st.sidebar.subheader(t('tensile_params'))
tensile_ratio = st.sidebar.slider(t('tensile_ratio'), 0.03, 0.15, 0.08)
beta_thermal = st.sidebar.number_input(t('thermal_decay'), value=0.0035, format="%.4f")

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40)
T_source_max = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

# Qatlam ma'lumotlari
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i+1), expanded=(i == int(num_layers) - 1)):
        name = st.text_input(t('layer_name'), value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(t('thickness'), value=50.0, min_value=0.1, key=f"t_{i}")
        u = st.number_input(t('ucs'), value=40.0, min_value=0.1, key=f"u_{i}")
        rho = st.number_input(t('density'), value=2500.0, min_value=100.0, key=f"rho_{i}")
        color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
        g = st.slider(t('gsi'), 10, 100, 60, key=f"g_{i}")
        m = st.number_input(t('mi'), value=10.0, min_value=0.1, key=f"m_{i}")
        s_t0_val = st.number_input(t('manual_st0'), value=3.0, key=f"st_{i}") if tensile_mode == t('tensile_manual') else 0.0
    layers_data.append({
        'name': name, 't': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

# Validatsiya
errors = []
for lyr in layers_data:
    if lyr['t'] <= 0: errors.append("Qalinlik >0 bo'lishi kerak")
    if lyr['ucs'] <= 0: errors.append("UCS >0 MPa bo'lishi kerak")
    if lyr['rho'] <= 0: errors.append("Zichlik >0 kg/m³ bo'lishi kerak")
    if not (10 <= lyr['gsi'] <= 100): errors.append("GSI 10...100 oralig'ida")
    if lyr['mi'] <= 0: errors.append("mi >0 bo'lishi kerak")
if errors:
    for e in errors: st.error(e)
    st.stop()

# =========================== HARORAT MAYDONI (keshlangan) ===========================
grid_shape = (80, 100)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

@st.cache_data(show_spinner=False)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape):
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
    z_axis = np.linspace(0, total_depth + 50, grid_shape[0])
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
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
    # Diffuziya (oddiy silliqlash)
    for _ in range(20):
        temp_2d[1:-1,1:-1] += alpha_rock * (
            temp_2d[2:,1:-1] + temp_2d[:-2,1:-1] +
            temp_2d[1:-1,2:] + temp_2d[1:-1,:-2] -
            4 * temp_2d[1:-1,1:-1])
    return temp_2d, x_axis, z_axis, grid_x, grid_z

temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape)

# =========================== GEOMEXANIK HISOB ===========================
grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
grid_sigma_t0_manual = np.zeros_like(grid_z)

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
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

# Maksimum harorat xaritasi
if 'max_temp_map' not in st.session_state or st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z)*25
    st.session_state.last_obj_name = obj_name
st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)

delta_T = temp_2d - 25.0

def thermal_damage(T, T0=100, k=0.002):
    return np.clip(1 - np.exp(-k * np.maximum(T - T0, 0)), 0, 0.98)

stress_ratio = grid_sigma_v / (grid_ucs + EPS)
damage = thermal_damage(st.session_state.max_temp_map)
sigma_ci = grid_ucs * (1 - damage)

E_MODULUS = 5000.0
ALPHA_T_COEFF = 1.0e-5
sigma_thermal = (E_MODULUS * ALPHA_T_COEFF * delta_T) / (1 - nu_poisson + EPS)

grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

# Cho'zilish mustahkamligi (to'g'rilangan)
if tensile_mode == t('tensile_empirical'):
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == t('tensile_hb'):
    # Hoek-Brown bo'yicha to'g'ri formula: σ_t = -s * σ_ci / m_b
    grid_sigma_t0_base = (grid_s_hb * sigma_ci) / (grid_mb + EPS)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
tensile_failure = (sigma3_act <= -sigma_t_field) & (delta_T > 50)

def hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a):
    sigma3_safe = np.maximum(sigma3, 0.01)
    return sigma3_safe + sigma_ci * (mb * sigma3_safe / (sigma_ci + 1e-9) + s) ** a

sigma1_limit = hoek_brown_sigma1(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)
shear_failure = sigma1_act >= sigma1_limit

# Bo'shliq (void) maskasi
void_mask_raw = (shear_failure | tensile_failure) & (temp_2d > 600)
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.5) > 0.3

# Bo'shliqda kuchlanishni nolga tenglash (to'g'ri yondashuv)
sigma1_act[void_mask_permanent] = 0.0
sigma3_act[void_mask_permanent] = 0.0
sigma_ci[void_mask_permanent] = 0.0

phi = 0.05 + 0.4 * void_mask_permanent.astype(float)
perm = (phi**3) / ((1 - phi + EPS)**2) * 1e-12
void_volume = np.sum(void_mask_permanent) * (x_axis[1] - x_axis[0]) * (z_axis[1] - z_axis[0])

# Gaz oqimi
pressure = temp_2d * 10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx, vz = -perm * dp_dx, -perm * dp_dz
gas_velocity = np.sqrt(vx**2 + vz**2)

# =========================== SELEK OPTIMIZATSIYASI ===========================
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam * strength_red) * (w_sol / (H_seam + EPS)) ** 0.5
    y_zone_calc = (H_seam / 2) * (np.sqrt(sv_seam / (p_strength + EPS)) - 1)
    new_w = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1: break
    w_sol = new_w
rec_width = np.round(w_sol, 1)
pillar_strength = p_strength
y_zone = max(y_zone_calc, 1.5)

fos_2d = np.clip(sigma1_limit / (sigma1_act + EPS), 0, 3.0)
fos_2d[void_mask_permanent] = 0.0

# =========================== METRIKALAR ===========================
st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{rec_width:.1f} m")

# =========================== GRAFIKLAR ===========================
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns(3)

# Cho'kish
s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth / 2)**2))
with col_g1:
    fig1 = go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta')))
    fig1.update_layout(title="Cho'kish (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig1, use_container_width=True)

# Termal deformatsiya
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth * 10)) * (time_h / 150) * 100
with col_g2:
    fig2 = go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy', line=dict(color='cyan')))
    fig2.update_layout(title="Termal deformatsiya (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig2, use_container_width=True)

# Hoek-Brown
sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + EPS) + s_s) ** a_s
ucs_burn = ucs_seam * np.exp(-0.0025 * (T_source_max - 20))
s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + EPS) + s_s) ** a_s
with col_g3:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red')))
    fig3.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Burning', line=dict(color='orange')))
    fig3.update_layout(title="Hoek-Brown", template="plotly_dark", height=300)
    st.plotly_chart(fig3, use_container_width=True)

# =========================== TM MAYDONI (SODDALASHTIRILGAN) ===========================
st.markdown("---")
st.subheader("🔥 TM Maydoni va Selek Interferensiyasi")

# Quduq masofasi slider
well_distance = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0)

# Kamera kengligi
cavity_width = well_distance - rec_width
cavity_width = max(cavity_width, 10)

# FOS hisoblash funksiyasi (soddalashtirilgan)
def compute_fos_stage(stage_num, active_wells, well_x, cavity_width):
    fos = np.full_like(grid_x, 3.0)
    # Oddiy model: bo'shliq atrofida FOS pasayadi
    for idx in active_wells:
        px = well_x[idx]
        dist = np.sqrt((grid_x - px)**2 + (grid_z - source_z)**2)
        mask = dist < H_seam * 3
        fos[mask] = np.minimum(fos[mask], 0.5 + 0.5 * (dist[mask] / (H_seam * 3)))
        # Kamera ichi
        cavity_mask = (np.abs(grid_x - px) < cavity_width/2) & (np.abs(grid_z - source_z) < H_seam/2)
        fos[cavity_mask] = 0.1
    return fos

well_x = [-well_distance, 0, well_distance]
states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
stage = st.select_slider("Bosqich", options=[1, 2, 3], value=1)
active_wells = states_132[stage]

fos_stage = compute_fos_stage(stage, active_wells, well_x, cavity_width)

# Grafik
fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True,
                       subplot_titles=("Harorat (°C)", "FOS"))

fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot',
                            colorbar=dict(title="°C", y=0.78, len=0.4)), row=1, col=1)

fig_tm.add_trace(go.Heatmap(z=fos_stage, x=x_axis, y=z_axis,
                            colorscale=[[0,'red'],[0.5,'yellow'],[1,'green']],
                            zmin=0, zmax=3,
                            colorbar=dict(title="FOS", y=0.22, len=0.4)), row=2, col=1)

# Seleklar
for px in well_x:
    fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2,
                     y0=source_z-H_seam/2, y1=source_z+H_seam/2,
                     line=dict(color="lime", width=2), row=2, col=1)

fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
fig_tm.update_layout(height=700, template="plotly_dark")
st.plotly_chart(fig_tm, use_container_width=True)

# Xulosa
st.info(f"Bosqich {stage}: Quduqlar orasidagi masofa {well_distance:.0f} m, tavsiya etilgan selek eni {rec_width:.1f} m")

# =========================== QO'SHIMCHA PANELLAR (qisqartirildi) ===========================
with st.expander("📊 Kompozit Xavf Indeksi"):
    risk_map = np.clip(1 - fos_2d/3.0, 0, 1)
    fig_risk = go.Figure(go.Heatmap(z=risk_map, x=x_axis, y=z_axis, colorscale='RdYlGn_r'))
    fig_risk.update_layout(title="Xavf indeksi", yaxis_autorange='reversed', template="plotly_dark")
    st.plotly_chart(fig_risk, use_container_width=True)

with st.expander("📈 FOS Trendi"):
    time_points = np.linspace(1, time_h, 20)
    fos_vals = 2.5 * np.exp(-0.01 * time_points)
    fig_trend = go.Figure(go.Scatter(x=time_points, y=fos_vals, mode='lines+markers'))
    fig_trend.add_hline(y=1.0, line_dash='dash', line_color='red')
    fig_trend.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_trend, use_container_width=True)

# =========================== FOOTER ===========================
st.sidebar.markdown("---")
st.sidebar.write(f"Device: {device} | Model: UCG v2.0 (fixed)")
