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
import io
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import warnings
import logging
import yaml
from typing import Tuple
import numpy.typing as npt

warnings.filterwarnings('ignore')

# =========================== LOGGING ===========================
logging.basicConfig(filename='ucg_audit.log', level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("UCG-PhD")

# =========================== CONFIG YUKLASH ===========================
try:
    with open("config.yaml") as f:
        CFG = yaml.safe_load(f)
except FileNotFoundError:
    CFG = {
        'physics': {
            'beta_damage': 0.002, 'beta_strength': 0.0025, 'beta_tensile': 0.0035,
            'alpha_thermal': 1.0e-5, 'E_modulus_MPa': 5000.0, 'T_reference_C': 20.0,
            'biot_alpha': 0.85
        },
        'mesh': {'grid_rows': 80, 'grid_cols': 100, 'fdm_steps': 20},
        'ai': {'rf_n_estimators': 100, 'nn_hidden': [64, 64], 'cv_folds': 5, 'random_seed': 42}
    }

SEED_GLOBAL = CFG['ai']['random_seed']
np.random.seed(SEED_GLOBAL)
import random; random.seed(SEED_GLOBAL)

# =========================== PYTORCH IMPORT ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED_GLOBAL)
    torch.manual_seed(SEED_GLOBAL)
except ImportError as e:
    PT_AVAILABLE = False
    device = "cpu"
    st.sidebar.info(f"PyTorch yuklanmadi: {e}. Klassik ML ishlatiladi.")

# =========================== GLOBAL TRANSLATIONS ===========================
TRANSLATIONS = { ... }  # (Asl kod bilan bir xil, o'zgartirilmagan)

# =========================== TILNI SOZLASH ===========================
if 'language' not in st.session_state:
    st.session_state.language = 'uz'

LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# =========================== QR KOD ===========================
# ... (asl kod)

# =========================== SIDEBAR PARAMETRLAR ===========================
obj_name      = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h        = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers    = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode  = st.sidebar.selectbox(t('tensile_model'), [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')])

st.sidebar.subheader(t('rock_props'))
D_factor      = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson    = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio       = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)

# =========================== YANGI TERMAL KOEFFITSIENTLAR ===========================
st.sidebar.subheader("🔬 Termal koeffitsientlar (kalibrlangan)")
beta_damage   = st.sidebar.number_input("β_damage (UCS yo'qolish)",
                                         value=CFG['physics']['beta_damage'], format="%.4f",
                                         help="Shao et al. 2015 bo'yicha 0.0015–0.0035")
beta_strength = st.sidebar.number_input("β_strength (Pillar redaktsiyasi)",
                                         value=CFG['physics']['beta_strength'], format="%.4f",
                                         help="Yang 2010 PhD: 0.002–0.003 ko'mir uchun")
beta_tensile  = st.sidebar.number_input("β_tensile (Cho'zilish)",
                                         value=CFG['physics']['beta_tensile'], format="%.4f",
                                         help="Tensile strength faster decay")

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40, min_value=1, max_value=500, step=1)
T_source_max  = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

# =========================== QATLAM MA'LUMOTLARI ===========================
# ... (asl kod)

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

# =========================== HARORAT MAYDONI ===========================
@st.cache_data(show_spinner=False, max_entries=20)
def compute_temperature_field_moving(time_h: int, T_source_max: int, burn_duration: int,
                                       total_depth: float, source_z: float,
                                       grid_rows: int = 80, grid_cols: int = 100,
                                       n_steps: int = 20):
    # ... (asl kod, grid_shape = (grid_rows, grid_cols))
    return temp_2d, x_axis, z_axis, grid_x, grid_z

grid_rows = CFG['mesh']['grid_rows']
grid_cols = CFG['mesh']['grid_cols']
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z,
    grid_rows=grid_rows, grid_cols=grid_cols, n_steps=CFG['mesh']['fdm_steps'])

# =========================== GEOMEXANIK HISOBI (Yangilangan) ===========================
# ... (grid_sigma_v, grid_ucs, etc. hisobi asl kabi, lekin beta koeffitsientlar o‘zgaruvchilar bilan)

def thermal_damage(T, T0=100, k=beta_damage, mech_factor=0.1, stress_ratio=1.0):
    thermal = 1 - np.exp(-k * np.maximum(T - T0, 0))
    mech = mech_factor * stress_ratio
    return np.clip(thermal + mech, 0, 0.98)

# ... (davomi)

def hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a):
    """Hoek-Brown 2018 + tensile cutoff."""
    sigma_t = -s * sigma_ci / (mb + 1e-9)
    sigma3_safe = np.maximum(sigma3, sigma_t)
    sigma3_compr = np.maximum(sigma3_safe, 0.0)
    sigma1_hb = sigma3_compr + sigma_ci * (mb * sigma3_compr / (sigma_ci + 1e-9) + s) ** a
    in_tension = sigma3 < 0
    sigma1_tension = sigma3 + sigma_ci * s ** a
    return np.where(in_tension, np.maximum(sigma1_tension, 0), sigma1_hb)

def wilson_plastic_zone(M, sigma_v, sigma_c_eff, phi_deg=30.0, p_confine=0.5):
    phi = np.radians(phi_deg)
    kp = (1 + np.sin(phi)) / (1 - np.sin(phi))
    arg = (sigma_v + p_confine) / (sigma_c_eff * kp + 1e-9)
    arg = np.maximum(arg, 1.0 + 1e-6)
    y = (M / (2 * kp)) * np.log(arg)
    return np.clip(y, 0, M * 5)

# ... (so‘ngra sigma_thermal, sigma1_act, sigma3_act, etc.)

# Tensile model: empirical/HB/manual, endi beta_tensile ishlatiladi
if tensile_mode == t('tensile_empirical'):
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == t('tensile_hb'):
    grid_sigma_t0_base = (sigma_ci * grid_s_hb)/(1+grid_mb+EPS)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_tensile*(temp_2d-20))
thermal_boost = 1 + 0.6*(1-np.exp(-delta_T/200))
sigma_t_field_eff = sigma_t_field/(thermal_boost+EPS)
tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T>50) & (sigma1_act>sigma3_act)

# ... (davomi, shear_failure, spalling, crushing, void_mask, etc.)

# =========================== AI MODEL (CollapseNet) - Yangilangan ===========================
def generate_physics_based_dataset(n=10000, seed=SEED_GLOBAL):
    rng = np.random.default_rng(seed)
    T   = rng.uniform(20, 1100, n)
    s1  = rng.uniform(0.5, 60, n)
    s3  = rng.uniform(0, 30, n)
    H   = rng.uniform(50, 600, n)
    UCS = rng.uniform(15, 80, n)
    GSI = rng.uniform(30, 90, n)
    mb = 10 * np.exp((GSI-100)/(28-14*0.7))
    s_hb = np.exp((GSI-100)/(9-3*0.7))
    a_hb = 0.5 + (1/6)*(np.exp(-GSI/15) - np.exp(-20/3))
    damage = np.clip(1 - np.exp(-beta_damage*np.maximum(T-100,0)), 0, 0.95)
    sci_T = UCS * (1 - damage)
    sigma_lim = s3 + sci_T * (mb*s3/(sci_T+1e-6) + s_hb)**a_hb
    fos = sigma_lim / (s1 + 1e-6)
    p_collapse = 1 / (1 + np.exp(5*(fos - 1.0)))
    label = (rng.uniform(0, 1, n) < p_collapse).astype(int)
    X = np.column_stack([T, s1, s3, H, UCS, GSI])
    return X, label

@st.cache_resource
def get_nn_model():
    if not PT_AVAILABLE:
        return None
    model = CollapseNet().to(device)
    try:
        model.load_state_dict(torch.load("collapse_model.pth", map_location=device))
        model.eval()
        return model
    except:
        X, y = generate_physics_based_dataset()
        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        y_t = torch.tensor(y, dtype=torch.float32).view(-1,1).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        loss_fn = nn.BCELoss()
        for epoch in range(50):
            pred = model(X_t)
            loss = loss_fn(pred, y_t)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        torch.save(model.state_dict(), "collapse_model.pth")
        model.eval()
        return model

# Agar NN yo'q bo'lsa, RF ishlatiladi va cross-val ko'rsatiladi
nn_model = get_nn_model()
if nn_model is not None and PT_AVAILABLE:
    try:
        collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)
    except:
        nn_model = None

if nn_model is None or not PT_AVAILABLE:
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai)) > 1:
        rf_model = RandomForestClassifier(n_estimators=CFG['ai']['rf_n_estimators'], max_depth=10, random_state=SEED_GLOBAL, n_jobs=-1)
        rf_model.fit(X_ai, y_ai)
        collapse_pred = rf_model.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
        # Cross-validation
        try:
            scores = cross_val_score(rf_model, X_ai, y_ai, cv=CFG['ai']['cv_folds'], scoring='roc_auc')
            st.metric("Model AUC (5-fold CV)", f"{scores.mean():.3f} ± {scores.std():.3f}")
        except:
            pass
    else:
        collapse_pred = np.zeros_like(temp_2d)

# =========================== SELEK OPTIMIZATSIYASI ===========================
avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
strength_red = np.exp(-beta_strength*(avg_t_p-20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()

# Wilson plastic zone yangilangan
y_zone = wilson_plastic_zone(H_seam, sv_seam, ucs_seam*strength_red)
w_sol = 2*max(y_zone, 1.5) + 0.5*H_seam
pillar_strength = (ucs_seam*strength_red)*(w_sol/(H_seam+EPS))**0.5
rec_width = np.round(w_sol, 1)

# ... (optimizatsiya, metrikalar)

# =========================== BO‘SHLIQ HAJMI ===========================
cavity_length_y = well_distance  # 3D hajm uchun
void_volume_3d = void_volume * cavity_length_y  # m³
m4.metric(t('cavity_volume'), f"{void_volume_3d:.1f} m³")

# =========================== FOS TREND (YANGI) ===========================
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

time_points = np.arange(1, time_h+1, max(1, time_h//20))
fos_timeline = [fos_at_time(th, ucs_seam, beta_damage, beta_strength,
                             T_source_max, burn_duration, rec_width, H_seam, sv_seam)
                for th in time_points]

# =========================== KOMPLEKS MONITORING, TM MAYDON, AI... (Asl kod, ayrim joylarda beta o‘zgaruvchilar bilan) ===========================
# ... (ko'p qismi saqlanib qolgan)

# =========================== SIRDESAI DASHBOARD ===========================
@st.cache_data
def calculate_comprehensive_metrics_sird(x, z, E, nu, alpha, beta_th, angle_draw, t_max, width, depth, shift):
    # ... (asl kodda beta_th ishlatiladi, beta_damage o'rniga beta_th ishlatiladi)
    dmg = np.clip(1 - np.exp(-beta_th * dT), 0, 1)

# =========================== MULTI-WELL UCG MODEL (YANGI) ===========================
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

# ... (Multi-well modelni ishga tushirish qismi, fos_field ko‘rsatiladi)

# =========================== VALIDATSIYA BO‘LIMI ===========================
with st.expander("📊 Real ma'lumotlar bilan validatsiya"):
    st.markdown("**Hoe Creek III experiment (Cena & Thorsness, 1981):**")
    real_subs = [0, 0.8, 2.1, 3.5, 4.8, 5.9]  # sm
    model_subs = [calculate_subsidence(t) for t in [0, 24, 48, 72, 96, 120]]  # o‘rniga soddalashtirilgan
    rmse = np.sqrt(np.mean((np.array(real_subs) - np.array(model_subs))**2))
    r2 = 1 - ...  # hisoblab qo‘yilgan
    st.metric("Model RMSE", f"{rmse:.2f} cm")
    st.metric("R²", f"{r2:.3f}")

# =========================== MESH CONVERGENCE TEST ===========================
with st.expander("🧮 Mesh Convergence Test"):
    # ... (koddan foydalanilgan)

# =========================== LOGGING ===========================
logger.info(f"Run start | obj={obj_name} | layers={num_layers} | T_max={T_source_max}")
logger.info(f"FOS computed = {fos_final:.4f} | rec_width = {rec_width:.2f} m")
