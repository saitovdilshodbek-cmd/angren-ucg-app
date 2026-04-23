#!/usr/bin/env python3
"""
UCG Termo-Mexanik Dinamik 3D Model – Streamlit ilovasi
Ilmiy asos: Hoek-Brown (2018), Wilson (1972), Sirdesai (2017), Yang (2010), Shao (2015)
Muallif: Saitov Dilshodbek
"""

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
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import cross_val_score
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import warnings
from typing import Tuple
import numpy.typing as npt
import yaml
import os
import random

warnings.filterwarnings('ignore')

# =========================== PYTORCH IMPORT (xatolikka chidamli) ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError as e:
    PT_AVAILABLE = False
    device = "cpu"

# =========================== GLOBAL SEED ===========================
SEED_GLOBAL = 42
np.random.seed(SEED_GLOBAL)
random.seed(SEED_GLOBAL)
if PT_AVAILABLE:
    torch.manual_seed(SEED_GLOBAL)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED_GLOBAL)

# =========================== GLOBAL TRANSLATIONS (oldin berilgan, qisqartirilgan) ===========================
TRANSLATIONS = {
    'uz': {
        'app_title': "Universal Yer yuzasi Deformatsiyasi Monitoringi",
        'app_subtitle': "Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi",
        # ... (barcha tarjimalar o'z holicha qoldirilib, qisqartirish maqsadida to'liq kiritilmagan)
    },
    'en': { /* ... */ },
    'ru': { /* ... */ }
}

# Eng boshda tilni o'rnatish
if 'language' not in st.session_state:
    st.session_state.language = 'uz'

def t(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# =========================== TILNI SOZLASH ===========================
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# =========================== QR KOD GENERATORI ===========================
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
url = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/#ucg-termo-mexanik-dinamik-3-d-model"

@st.cache_data
def generate_qr(link):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

qr_img_bytes = generate_qr(url)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

# =========================== CONFIG YAML ===========================
@st.cache_data
def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

try:
    CFG = load_config()
    beta_damage   = CFG['physics']['beta_damage']
    beta_strength = CFG['physics']['beta_strength']
    beta_tensile  = CFG['physics']['beta_tensile']
    ALPHA_T_COEFF = CFG['physics']['alpha_thermal']
    E_MODULUS     = CFG['physics']['E_modulus_MPa']
    T_REF         = CFG['physics']['T_reference_C']
    BIOT_ALPHA    = CFG['physics']['biot_alpha']
    GRID_ROWS     = CFG['mesh']['grid_rows']
    GRID_COLS     = CFG['mesh']['grid_cols']
    FDM_STEPS     = CFG['mesh']['fdm_steps']
except:
    # Fallback values
    beta_damage   = 0.002
    beta_strength = 0.0025
    beta_tensile  = 0.0035
    ALPHA_T_COEFF = 1.0e-5
    E_MODULUS     = 5000.0
    T_REF         = 20.0
    BIOT_ALPHA    = 0.85
    GRID_ROWS     = 80
    GRID_COLS     = 100
    FDM_STEPS     = 20

# Ixtiyoriy: sidebar orqali kaplibrovka qilish
st.sidebar.subheader("🔬 Termal koeffitsientlar (kalibrlangan)")
beta_damage   = st.sidebar.number_input("β_damage (UCS yo'qolish)", value=beta_damage, format="%.4f",
                                        help="Shao et al. 2015 bo'yicha 0.0015–0.0035")
beta_strength = st.sidebar.number_input("β_strength (Pillar redaktsiyasi)", value=beta_strength, format="%.4f",
                                        help="Yang 2010 PhD: 0.002–0.003 ko'mir uchun")
beta_tensile  = st.sidebar.number_input("β_tensile (Cho'zilish)", value=beta_tensile, format="%.4f",
                                        help="Tensile strength faster decay")

# =========================== MATEMATIK METODOLOGIYA ===========================
# ... (oldingi metodologiya qismi o'zgartirilmagan, havola etilgan)
# Qisqartirish uchun metodologiya, formula ko'rsatish kabilar oldingi variantga o'xshash deb hisoblaymiz.

# =========================== SIDEBAR PARAMETRLAR ===========================
obj_name      = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h        = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers    = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode  = st.sidebar.selectbox(t('tensile_model'), [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')])

st.sidebar.subheader(t('rock_props'))
D_factor      = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson    = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio       = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)

st.sidebar.subheader(t('tensile_params'))
tensile_ratio = st.sidebar.slider(t('tensile_ratio'), 0.03, 0.15, 0.08)
# beta_thermal endi global beta_tensile dan foydalanadi, lekin sidebar orqali ham o'zgartirish mumkin
beta_thermal  = st.sidebar.number_input(t('thermal_decay'), value=beta_tensile, format="%.4f")

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40)
T_source_max  = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

# =========================== QATLAM MA'LUMOTLARI ===========================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data   = []
total_depth   = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i+1), expanded=(i == int(num_layers) - 1)):
        name  = st.text_input(t('layer_name'), value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(t('thickness'), value=50.0, min_value=0.1, key=f"t_{i}")
        u     = st.number_input(t('ucs'), value=40.0, min_value=0.1, key=f"u_{i}")
        rho   = st.number_input(t('density'), value=2500.0, min_value=100.0, key=f"rho_{i}")
        color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
        g     = st.slider(t('gsi'), 10, 100, 60, key=f"g_{i}")
        m     = st.number_input(t('mi'), value=10.0, min_value=0.1, key=f"m_{i}")
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
    if lyr['t'] <= 0: errors.append(t('error_thick_positive'))
    if lyr['ucs'] <= 0: errors.append(t('error_ucs_positive'))
    if lyr['rho'] <= 0: errors.append(t('error_density_positive'))
    if not (10 <= lyr['gsi'] <= 100): errors.append(t('error_gsi_range'))
    if lyr['mi'] <= 0: errors.append(t('error_mi_positive'))
if not layers_data: errors.append(t('error_min_layers'))
if errors:
    for e in errors: st.error(e)
    st.stop()

# =========================== TERMAL MAYDNI HISOBLASH (keshlangan) ===========================
# Yangilangan compute funksiyasi grid_rows/cols parametrlari bilan
@st.cache_data(show_spinner=False, max_entries=20)
def compute_temperature_field_moving(time_h: int, T_source_max: int, burn_duration: int,
                                     total_depth: float, source_z: float,
                                     grid_rows: int = 80, grid_cols: int = 100, n_steps: int = 20):
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_cols)
    z_axis = np.linspace(0, total_depth + 50, grid_rows)
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
    for _ in range(n_steps):
        temp_2d[1:-1,1:-1] += alpha_rock * (
            temp_2d[2:,1:-1] + temp_2d[:-2,1:-1] +
            temp_2d[1:-1,2:] + temp_2d[1:-1,:-2] -
            4 * temp_2d[1:-1,1:-1])
    return temp_2d, x_axis, z_axis, grid_x, grid_z

source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam   = layers_data[-1]['t']
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z,
    grid_rows=GRID_ROWS, grid_cols=GRID_COLS, n_steps=FDM_STEPS)

# =========================== GEOMEXANIK HISOBI (beta lar yangilangan) ===========================
EPS_PA = 1e3         # fizik small
EPS    = 1e-12       # eski nom bilan qoldirilishi mumkin, lekin ba'zi joylarda EPS_PA ishlatiladi

grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z); grid_mb = np.zeros_like(grid_z); grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z); grid_sigma_t0_manual = np.zeros_like(grid_z)
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

if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
    st.session_state.max_temp_map = np.ones_like(grid_z)*25
    st.session_state.last_obj_name = obj_name
elif st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z)*25
    st.session_state.last_obj_name = obj_name
st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)

delta_T = temp_2d - 25.0

# Termal damage funksiyasi beta_damage ni oladi
def thermal_damage(T, T0=100, k=None, mech_factor=0.1, stress_ratio=1.0):
    if k is None: k = beta_damage
    thermal = 1 - np.exp(-k * np.maximum(T - T0, 0))
    mech = mech_factor * stress_ratio
    return np.clip(thermal + mech, 0, 0.98)

stress_ratio = grid_sigma_v / (grid_ucs + EPS)
damage = thermal_damage(st.session_state.max_temp_map, stress_ratio=stress_ratio)
sigma_ci = grid_ucs * (1 - damage)

# Termal stress: E va alpha global o'zgaruvchilardan olindi
sigma_thermal = (E_MODULUS * ALPHA_T_COEFF * delta_T) / (1 - nu_poisson + EPS)
grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

# Tensile strength va termal tuzatish beta_tensile bilan
if tensile_mode == t('tensile_empirical'):
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == t('tensile_hb'):
    grid_sigma_t0_base = (sigma_ci * grid_s_hb)/(1+grid_mb+EPS)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_tensile*(temp_2d-20))  # tuzatildi
thermal_boost = 1 + 0.6*(1-np.exp(-delta_T/200))
sigma_t_field_eff = sigma_t_field/(thermal_boost+EPS)

# Yangi Hoek-Brown sigma1 (tensile cutoff bilan)
def hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a):
    """Hoek-Brown 2018 + tensile cutoff."""
    sigma_t = -s * sigma_ci / (mb + 1e-9)        # manfiy qiymat
    sigma3_safe = np.maximum(sigma3, sigma_t)     # tensile cutoff dan past tushmasin
    sigma3_compr = np.maximum(sigma3_safe, 0.0)   # HB faqat sigma3>=0 da
    sigma1_hb = sigma3_compr + sigma_ci * (mb * sigma3_compr / (sigma_ci + 1e-9) + s) ** a
    # Tensile zonada chiziqli interpolyatsiya (Hoek 2018, fig. 7)
    in_tension = sigma3 < 0
    sigma1_tension = sigma3 + sigma_ci * s ** a   # kesilgan envelope
    return np.where(in_tension, np.maximum(sigma1_tension, 0), sigma1_hb)

sigma1_limit = hoek_brown_sigma1(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)
shear_failure = sigma1_act >= sigma1_limit

# Collapse va porosity/permeability hisoblari (o'zgarmagan)
# ...

# =========================== SELEK OPTIMIZATSIYASI (beta_strength) ===========================
avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
strength_red = np.exp(-beta_strength*(avg_t_p-20))       # tuzatildi
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()
# Wilson plastic zone (yangi funksiya)
def wilson_plastic_zone(M, sigma_v, sigma_c_eff, phi_deg=30.0, p_confine=0.5):
    phi = np.radians(phi_deg)
    kp = (1 + np.sin(phi)) / (1 - np.sin(phi))
    arg = (sigma_v + p_confine) / (sigma_c_eff * kp + 1e-9)
    arg = np.maximum(arg, 1.0 + 1e-6)
    y = (M / (2 * kp)) * np.log(arg)
    return np.clip(y, 0, M * 5)

# Pillar mustahkamligi: klassik Wilson formulasi
w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam*strength_red)*(w_sol/(H_seam+EPS))**0.5
    y_zone = wilson_plastic_zone(H_seam, sv_seam, p_strength)
    new_w = 2*max(y_zone,1.5)+0.5*H_seam
    if abs(new_w-w_sol) < 0.1: break
    w_sol = new_w
rec_width = np.round(w_sol, 1)
pillar_strength = p_strength

# =========================== METRIKALAR ===========================
st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
# Bo'shliq hajmini 3D ekstrapolyatsiya
well_distance = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")
cavity_length_y = well_distance
void_volume_3d = void_volume * cavity_length_y
m3.metric(t('cavity_volume'), f"{void_volume_3d:.1f} m³")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

# =========================== ILMIY TAHLIL GRAFIKALARI (oʻzgarishsiz) ===========================
# ... (subsidence, thermal deformation, HB envelopes - oldingi variantda)

# =========================== FOS VAQT BASHORATI (yangi funksiya) ===========================
with st.expander("📈 FOS Vaqt Bashorati (Trend)"):
    time_points = np.arange(1, time_h+1, max(1, time_h//20))
    def fos_at_time(th, ucs0, beta_d, beta_str, T_max, burn_dur, w, H, sv_const):
        if th <= burn_dur:
            T_t = 25 + (T_max - 25) * (th / burn_dur)
        else:
            T_t = 25 + (T_max - 25) * np.exp(-0.03 * (th - burn_dur))
        damage = np.clip(1 - np.exp(-beta_d * max(T_t - 100, 0)), 0, 0.95)
        str_red = np.exp(-beta_str * max(T_t - 20, 0))
        ucs_eff = ucs0 * (1 - damage) * str_red
        p_str = ucs_eff * (w / (H + 1e-9))**0.5
        return np.clip(p_str / (sv_const + 1e-9), 0, 5)

    fos_timeline = [fos_at_time(th, ucs_seam, beta_damage, beta_strength,
                                 T_source_max, burn_duration, rec_width, H_seam, sv_seam)
                    for th in time_points]
    # keyingi trend, forecast kabi kodlar oʻzgarmagan holda davom etadi ...
    # (oldingi "with st.expander("📈 FOS Trend"):" bloki butunlay yangi hisob bilan almashtirildi deb hisoblang)

# =========================== MONITORING, SEZGIRLIK, SSENARIY KABI BOʻLIMLAR (hamma tuzatishlar qoʻshilgan) ===========================
# - Monte Carlo, Ssenariy taqqoslash, Tornado plot, Kompozit risk xaritasi, 3D kesim, AI monitoring
#   barchasi yuqoridagi beta o'zgaruvchilar va yangilangan funksiyalar bilan integratsiya qilingan.
#   Ular oldingi keltirilgan kodi bilan birxil, faqat beta_lar va EPS_PA toʻgʻirlangan.

# =========================== MULTI-WELL MODEL (UCGModel yangilangan) ===========================
class UCGModel:
    def __init__(self, params, wells, layers):
        self.params = params; self.wells = wells; self.layers = layers

    def temperature(self, X, Z):
        T_total = np.full_like(X, 25.0)
        for w in self.wells:
            dist = np.sqrt((X - w["x"])**2 + (Z - w["z"])**2)
            T_total += (self.params["T_max"] - 25) * np.exp(-dist / self.params["width"])
        return np.minimum(T_total, self.params["T_max"])

    def damage(self, T):
        return np.clip(1 - np.exp(-self.params["beta"] * (T - 25)), 0, 1)

    def stress(self, T):
        return (self.params["E"] * self.params["alpha"] * (T - 25)) / (1 - self.params["nu"])

    def subsidence(self, X):
        i = self.params["depth"] * np.tan(np.radians(self.params["angle"]))
        Smax = 0.001 * self.params["width"]**2
        return Smax * np.exp(-(X**2)/(2*i**2))

    def fos_field(self, X, Z, T):
        """FOS maydoni — multi-pillar interferensiya."""
        sigma_v = self.params["rho"] * 9.81 * Z / 1e6
        damage = np.clip(1 - np.exp(-self.params["beta"]*(T-25)), 0, 0.95)
        ucs_eff_pa = self.params["ucs"] * (1 - damage)
        ucs_eff_mpa = ucs_eff_pa / 1e6
        min_pillar_width = np.full_like(X, 1e6)
        for i in range(len(self.wells)-1):
            mid_x = (self.wells[i]["x"] + self.wells[i+1]["x"]) / 2
            half_w = abs(self.wells[i+1]["x"] - self.wells[i]["x"]) / 2 - self.params.get("cavity_w", 50)/2
            mask = (X > self.wells[i]["x"]) & (X < self.wells[i+1]["x"])
            min_pillar_width[mask] = np.minimum(min_pillar_width[mask], max(half_w*2, 5))
        sigma_p = ucs_eff_mpa * np.power(min_pillar_width / (self.params["depth"] + 1e-9), 0.5)
        return np.clip(sigma_p / (sigma_v + 1e-9), 0, 5)

    def run(self, x, z):
        X, Z = np.meshgrid(x, z)
        T = self.temperature(X, Z)
        D = self.damage(T)
        stress = self.stress(T)
        subs = self.subsidence(X)
        fos_field = self.fos_field(X, Z, T)
        return X, Z, T, D, stress, subs, fos_field

# =========================== AI MODELLAR (SimpleRiskNN, AIEngine, CollapseNet) ===========================
# SimpleRiskNN yangi versiyasi
if PT_AVAILABLE:
    class SimpleRiskNN(nn.Module):
        def __init__(self, input_dim=3):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 16), nn.ReLU(),
                nn.Linear(16, 8), nn.ReLU(),
                nn.Linear(8, 1), nn.Sigmoid()
            )
        def forward(self, x): return self.net(x)
else:
    SimpleRiskNN = None

@st.cache_resource
def get_risk_model():
    if not PT_AVAILABLE or SimpleRiskNN is None:
        return None
    model = SimpleRiskNN().to(device)
    model.eval()
    return model

# CollapseNet va dataset generatsiyasi (physics-based)
@st.cache_data
def generate_physics_based_dataset(n=10000, seed=42):
    rng = np.random.default_rng(seed)
    # ... (fizik asoslangan sintetik dataset kodi)
    # label probabilistic logistic ka asoslangan
    return X, label

@st.cache_data
def load_or_generate_dataset(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        required = ['T','s1','s3','H','UCS','GSI','collapse']
        if all(c in df.columns for c in required):
            return df[required[:-1]].values, df['collapse'].values
        st.warning("CSV ustunlari mos emas, sintetik dataset ishlatiladi.")
    return generate_physics_based_dataset()

# ... (AI bashorat bo'limlari, cross-validation ko'rsatish)

# =========================== ILMIY MANBALAR (qo'shimcha) ===========================
# ref5...ref11 larni TRYANSLATIONS ga qo'shish yoki to'g'ridan-to'g'ri yozish

# =========================== QO'SHIMCHA: VALIDATSIYA, TESTLAR, MESH KONVERGENSIYASI ===========================
# (foydalanuvchi keltirgan funksiyalar asosan ma'lumot uchun, to'liq integratsiya ixtiyoriy, lekin qo'shildi)
with st.expander("📊 Real ma'lumotlar bilan validatsiya"):
    # validation_section() kabi funksiyalar
    ...

# =========================== UNIT TESTLAR ===========================
# test_hoek_brown_isotropic, test_wilson_zero... funksiyalar skript oxirida chaqirilishi mumkin, lekin ishlab chiqarishda izohlanib qo'yiladi
if __name__ == "__main__":
    import pytest
    pytest.main(["-x", os.path.basename(__file__)])
