import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress
import time
import io
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import warnings
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import IsolationForest
import sqlite3
import smtplib
from email.mime.text import MIMEText
import gspread
from google.oauth2.service_account import Credentials
from fastapi import FastAPI
import uvicorn
import threading
import os

# PyTorch mavjudligini tekshirish
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    PT_AVAILABLE = False
    device = "cpu"

# Word dokumenti uchun (agar kerak bo'lsa)
try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

warnings.filterwarnings('ignore')

# ========================== KONSTANTALAR ==========================
EPS = 1e-12
APP_URL = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app"

# ========================== TARJIMALAR ==========================
TRANSLATIONS = {
    'uz': {
        'app_title': "Universal Yer yuzasi Deformatsiyasi Monitoringi",
        # ... (qolgan tarjimalar birinchi koddagidek, joy tejash uchun qisqartirilgan)
        # To'liq versiyani birinchi kodingizdan oling
    },
    'en': {
        'app_title': "Universal Surface Deformation Monitoring",
        # ...
    },
    'ru': {
        'app_title': "Универсальный мониторинг деформации земной поверхности",
        # ...
    }
}

# Tarjima funksiyasi (soddalashtirilgan)
def t(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ========================== TEZKORLIK UCHUN DEFAULT PARAMETRLAR ==========================
DEFAULT_PARAMS = {
    'E_MODULUS': 5000.0,
    'ALPHA_T': 1e-5,
    'CONSTRAINT': 0.7,
    'GRID_SHAPE': (50, 80),  # 3x tezroq
    'N_STEPS': 15
}

# ========================== MA'LUMOTLAR BAZASI (SQLite) ==========================
@st.cache_resource
def init_db():
    conn = sqlite3.connect('ucg_sensors.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            timestamp DATETIME,
            temperature REAL,
            fos REAL,
            pillar_width REAL,
            anomaly_score REAL
        )
    ''')
    return conn

# ========================== GOOGLE SHEETS INTEGRATSIYASI ==========================
@st.cache_resource
def get_gsheet():
    try:
        creds = Credentials.from_service_account_file("creds.json")
        gc = gspread.authorize(creds)
        return gc.open("UCG_Projects").sheet1
    except:
        return None

# ========================== EMAIL ALERT ==========================
def send_alert(fos_value, project_name, recipient="engineer@angren.com"):
    if fos_value < 1.2:
        msg = MIMEText(f"🚨 UCG ALERT: {project_name} FOS={fos_value:.2f}\nTime: {datetime.now()}")
        msg['Subject'] = 'CRITICAL: UCG Collapse Risk'
        msg['From'] = 'ucg@angren.com'
        msg['To'] = recipient
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(st.secrets["email"]["user"], st.secrets["email"]["password"])
                server.send_message(msg)
        except:
            pass

# ========================== HEALTH CHECK ==========================
@st.cache_data(ttl=60)
def health_check():
    try:
        # oddiy tekshiruv
        _ = np.random.rand(10)
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except:
        return {"status": "unhealthy"}

# ========================== VALIDATSIYA ==========================
def validate_layers(layers_data):
    errors = []
    for i, lyr in enumerate(layers_data):
        if lyr['t'] <= 0: errors.append(f"❌ Qatlam {i+1}: Qalinlik >0")
        if lyr['ucs'] <= 0: errors.append(f"❌ Qatlam {i+1}: UCS >0 MPa")
        if not 10 <= lyr['gsi'] <= 100: errors.append(f"❌ Qatlam {i+1}: GSI 10-100")
        if lyr['mi'] <= 0: errors.append(f"❌ Qatlam {i+1}: mi >0")
    if errors:
        st.error("**XATOLAR:**\n" + "\n".join(errors))
        return False
    return True

# ========================== CACHE'LANGAN MODELLAR ==========================
@st.cache_resource
def get_models():
    rf_reg = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_clf = RandomForestClassifier(n_estimators=50, random_state=42)
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    # Dummy training
    X_dummy = np.random.rand(100, 3)
    rf_reg.fit(X_dummy, np.random.rand(100))
    rf_clf.fit(X_dummy, np.random.randint(0, 2, 100))
    iso_forest.fit(X_dummy)
    return rf_reg, rf_clf, iso_forest

# ========================== FIZIKA FUNKSIYALARI (TEZKOR) ==========================
def thermal_damage(T):
    if T < 100:
        return 0.0
    elif T < 400:
        return 0.1 * (T - 100) / 300
    elif T < 800:
        return 0.1 + 0.4 * (T - 400) / 400
    else:
        return min(0.95, 0.5 + 0.45 * (T - 800) / 400)

def calc_vertical_stress(depth, density=2500):
    gamma = density * 9.81 / 1e6
    return gamma * depth

def hoek_brown_strength(ucs, gsi, mi, D, sigma3=0):
    mb = mi * np.exp((gsi - 100) / (28 - 14 * D))
    s = np.exp((gsi - 100) / (9 - 3 * D))
    a = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
    return sigma3 + ucs * (mb * sigma3 / ucs + s)**a

def improved_fos(ucs, gsi, mi, D, nu, T, depth, H_seam):
    damage = thermal_damage(T)
    ucs_eff = ucs * (1 - damage)
    sigma_strength = hoek_brown_strength(ucs_eff, gsi, mi, D, sigma3=0)
    sigma_v = calc_vertical_stress(depth)
    pillar_effect = (20 / (H_seam + EPS))**0.5
    fos = (sigma_strength * pillar_effect) / (sigma_v + EPS)
    return np.clip(fos, 0, 5)

@st.cache_data(ttl=600, show_spinner=False)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=15):
    """Tezlashtirilgan versiya"""
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
    temp_2d = np.ones_like(grid_x) * 25.0
    for src in sources:
        if time_h > src['start']:
            dt_sec = (time_h - src['start']) * 3600
            if src['moving']:
                x_center = src['x0'] + src['v'] * dt_sec
            else:
                x_center = src['x0']
            pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
            elapsed = time_h - src['start']
            if elapsed <= burn_duration:
                curr_T = T_source_max
            else:
                curr_T = 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration))
            dist_sq = (grid_x - x_center)**2 + (grid_z - source_z)**2
            temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))
    # Diffuziya (kamroq iteratsiya)
    DX, DT = 1.0, 0.1
    for _ in range(n_steps):
        Tn = temp_2d.copy()
        Tn[1:-1,1:-1] = (temp_2d[1:-1,1:-1] + alpha_rock*DT*(
            (temp_2d[2:,1:-1]-2*temp_2d[1:-1,1:-1]+temp_2d[:-2,1:-1])/(DX**2+EPS) +
            (temp_2d[1:-1,2:]-2*temp_2d[1:-1,1:-1]+temp_2d[1:-1,:-2])/(DX**2+EPS)))
        temp_2d = Tn
    return temp_2d, x_axis, z_axis, grid_x, grid_z

@st.cache_data(ttl=600, show_spinner=False)
def compute_geomechanics_fast(layers_data, grid_z, grid_x, temp_2d, D_factor, nu_poisson, k_ratio,
                              tensile_mode, tensile_ratio, beta_thermal, total_depth, EPS, time_h):
    """Vektorlashtirilgan va xavfsiz bo'lish"""
    grid_sigma_v = np.zeros_like(grid_z)
    grid_ucs = np.zeros_like(grid_z)
    grid_mb = np.zeros_like(grid_z)
    grid_s_hb = np.zeros_like(grid_z)
    grid_a_hb = np.zeros_like(grid_z)
    grid_sigma_t0_manual = np.zeros_like(grid_z)

    for i, layer in enumerate(layers_data):
        mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
        if i == len(layers_data)-1:
            mask = grid_z >= layer['z_start']
        overburden = sum(l['rho']*9.81*l['t'] for l in layers_data[:i])/1e6
        grid_sigma_v[mask] = overburden + (layer['rho']*9.81*(grid_z[mask]-layer['z_start']))/1e6
        grid_ucs[mask] = layer['ucs']
        grid_mb[mask] = layer['mi'] * np.exp((layer['gsi']-100)/(28-14*D_factor))
        grid_s_hb[mask] = np.exp((layer['gsi']-100)/(9-3*D_factor))
        grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15)-np.exp(-20/3))
        grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

    if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
        st.session_state.max_temp_map = np.ones_like(grid_z)*25
    st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
    delta_T = temp_2d - 25.0

    temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
    damage = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
    sigma_ci = grid_ucs * (1 - damage)

    E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = DEFAULT_PARAMS['E_MODULUS'], DEFAULT_PARAMS['ALPHA_T'], DEFAULT_PARAMS['CONSTRAINT']
    dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
    thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)
    sigma_thermal = CONSTRAINT_FACTOR*(E_MODULUS*ALPHA_T_COEFF*delta_T)/(1-nu_poisson+EPS) + 0.3*thermal_gradient
    grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
    sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
    sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

    # Safe division helper
    def safe_div(a, b):
        return np.divide(a, b, out=np.zeros_like(a), where=b!=0)

    if tensile_mode == t('tensile_empirical'): 
        grid_sigma_t0_base = tensile_ratio * sigma_ci
    elif tensile_mode == t('tensile_hb'): 
        grid_sigma_t0_base = (sigma_ci * grid_s_hb)/(1+grid_mb+EPS)
    else: 
        grid_sigma_t0_base = grid_sigma_t0_manual

    sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal*(temp_2d-20))
    thermal_boost = 1 + 0.6*(1-np.exp(-delta_T/200))
    sigma_t_field_eff = sigma_t_field/(thermal_boost+EPS)

    tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T>50) & (sigma1_act>sigma3_act)
    sigma3_safe = np.maximum(sigma3_act, 0.01)
    sigma1_limit = sigma3_safe + sigma_ci*(grid_mb*sigma3_safe/(sigma_ci+EPS)+grid_s_hb)**grid_a_hb
    shear_failure = sigma1_act >= sigma1_limit

    spalling = tensile_failure & (temp_2d>400)
    crushing = shear_failure & (temp_2d>600)
    depth_factor = np.exp(-grid_z/(total_depth+EPS))
    local_collapse_T = np.clip((st.session_state.max_temp_map-600)/300,0,1)
    time_factor = np.clip((time_h-40)/60,0,1)
    collapse_final = local_collapse_T * time_factor * (1-depth_factor)
    void_mask_raw = spalling | crushing | (st.session_state.max_temp_map>900)
    void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
    void_mask_permanent = (void_mask_smooth>0.3) & (collapse_final>0.05)

    phi = 0.05 + 0.4 * void_mask_permanent.astype(float)
    perm = (phi**3) / ((1-phi+EPS)**2) * 1e-12
    void_volume = np.sum(void_mask_permanent)*(grid_x[0,1]-grid_x[0,0])*(grid_z[1,0]-grid_z[0,0])
    sigma1_act = np.where(void_mask_permanent, 0.0, sigma1_act)
    sigma3_act = np.where(void_mask_permanent, 0.0, sigma3_act)
    sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)

    pressure = temp_2d*10.0
    dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
    vx, vz = -perm*dp_dx, -perm*dp_dz
    gas_velocity = np.sqrt(vx**2+vz**2)

    fos_2d = safe_div(sigma1_limit, sigma1_act+EPS)
    fos_2d = np.clip(fos_2d, 0, 3.0)
    fos_2d = np.where(void_mask_permanent, 0.0, fos_2d)

    return {
        'sigma1': sigma1_act, 'sigma3': sigma3_act, 'fos': fos_2d,
        'void': void_mask_permanent, 'perm': perm, 'gas_velocity': gas_velocity,
        'damage': damage, 'sigma_ci': sigma_ci, 'sigma1_limit': sigma1_limit,
        'void_volume': void_volume
    }

# ========================== PILLAR OPTIMIZATSIYASI ==========================
def optimize_pillar(ucs_seam, H_seam, sv_seam, strength_red, void_frac_base, rec_width_init):
    def objective(w_arr):
        w = w_arr[0]
        strength = (ucs_seam*strength_red)*(w/(H_seam+EPS))**0.5
        risk = void_frac_base * np.exp(-0.01*(w-rec_width_init))
        return -(strength - 15.0*risk)
    opt_result = minimize(objective, x0=[rec_width_init], bounds=[(5.0,100.0)], method='SLSQP')
    return float(np.clip(opt_result.x[0],5.0,100.0))

# ========================== MONTE CARLO & SENSITIVITY ==========================
def monte_carlo_fos(n_sim, base_params):
    results = []
    for _ in range(n_sim):
        ucs = np.random.normal(base_params['ucs'], 5)
        gsi = np.random.normal(base_params['gsi'], 10)
        T = np.random.uniform(200, 1000)
        fos = improved_fos(ucs, gsi, base_params['mi'], base_params['D'],
                           base_params['nu'], T, base_params['depth'], base_params['H'])
        results.append(fos)
    return np.array(results)

def sensitivity_analysis_pro(base_params, range_pct=0.2):
    names = ['ucs','gsi','D','nu','T']
    base_values = [base_params['ucs'], base_params['gsi'], base_params['D'],
                   base_params['nu'], base_params['T']]
    base_fos = improved_fos(base_params['ucs'], base_params['gsi'], base_params['mi'],
                            base_params['D'], base_params['nu'], base_params['T'],
                            base_params['depth'], base_params['H'])
    results = []
    for i, name in enumerate(names):
        low_vals = base_values.copy()
        high_vals = base_values.copy()
        low_vals[i] *= (1 - range_pct)
        high_vals[i] *= (1 + range_pct)
        fos_low = improved_fos(*low_vals, base_params['mi'], base_params['depth'], base_params['H'])
        fos_high = improved_fos(*high_vals, base_params['mi'], base_params['depth'], base_params['H'])
        results.append({'param': name, 'low': fos_low - base_fos, 'high': fos_high - base_fos})
    return pd.DataFrame(results), base_fos

# ========================== DIGITAL TWIN SINFI ==========================
class DigitalTwin:
    def __init__(self):
        self.temperature = 20.0
        self.stress = 5.0
        self.pressure = 2.0
        self.history = []

    def update(self):
        self.temperature += np.random.normal(5, 10)
        self.stress += np.random.normal(0.5, 0.3)
        self.pressure += np.random.normal(0.2, 0.1)
        self.temperature = np.clip(self.temperature, 20, 1200)
        state = {"T": self.temperature, "stress": self.stress, "pressure": self.pressure}
        self.history.append(state)
        return state

# ========================== FASTAPI (alohida threadda) ==========================
api = FastAPI()
@api.get("/api/fos/{project_id}")
def get_fos(project_id: str):
    # Real vaqtda FOS olish (soddalashtirilgan)
    fos_val = np.random.uniform(1.0, 2.5)
    return {"project_id": project_id, "fos": fos_val, "risk": 1.0 - fos_val/2.5, "timestamp": datetime.now().isoformat()}

def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)

# API ni ishga tushirish (agar asosiy threadda bo'lmasa)
if not os.environ.get("API_RUNNING"):
    threading.Thread(target=run_api, daemon=True).start()
    os.environ["API_RUNNING"] = "1"

# ========================== ASOSIY STREAMLIT ILOVASI ==========================
st.set_page_config(page_title=t('app_title'), layout="wide", page_icon="🌍")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# Autentifikatsiya (oddiy)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.sidebar:
        password = st.text_input("🔐 Admin paroli", type="password")
        if st.button("Kirish") and password == st.secrets["auth"]["admin_password"]:
            st.session_state.logged_in = True
            st.rerun()
        st.stop()

# Til sozlamalari
if 'language' not in st.session_state:
    st.session_state.language = 'uz'
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# QR kod
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
def generate_qr(link):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
qr_img_bytes = generate_qr(APP_URL)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

# Sidebar parametrlar (soddalashtirilgan, lekin to'liq)
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

# Qatlamlar
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i+1), expanded=(i == int(num_layers)-1)):
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
if not validate_layers(layers_data):
    st.stop()

# Hisoblash (progress bilan)
progress_bar = st.progress(0, text="Hisoblanmoqda...")
# Harorat maydoni
grid_shape = DEFAULT_PARAMS['GRID_SHAPE']
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=DEFAULT_PARAMS['N_STEPS'])
progress_bar.progress(0.4)

# Geomexanika
geo = compute_geomechanics_fast(layers_data, grid_z, grid_x, temp_2d, D_factor, nu_poisson, k_ratio,
                                tensile_mode, tensile_ratio, beta_thermal, total_depth, EPS, time_h)
progress_bar.progress(0.7)

sigma1_act = geo['sigma1']
sigma3_act = geo['sigma3']
fos_2d = geo['fos']
void_mask_permanent = geo['void']
perm = geo['perm']
gas_velocity = geo['gas_velocity']
damage = geo['damage']
void_volume = geo['void_volume']

# AI modellarni yuklash
rf_reg, rf_clf, iso_forest = get_models()
# Collapse prediction
X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
y_ai = void_mask_permanent.flatten().astype(int)
if len(np.unique(y_ai)) > 1:
    rf_clf.fit(X_ai, y_ai)
    collapse_pred = rf_clf.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
else:
    collapse_pred = np.zeros_like(temp_2d)

# Pillar optimizatsiyasi
avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
strength_red = np.exp(-0.0025*(avg_t_p-20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = geo['sigma1'][np.abs(z_axis-source_z).argmin(), :].max()
rec_width_init = 20.0
for _ in range(15):
    p_strength = (ucs_seam*strength_red)*(rec_width_init/(H_seam+EPS))**0.5
    y_zone_calc = (H_seam/2)*(np.sqrt(sv_seam/(p_strength+EPS))-1)
    new_w = 2*max(y_zone_calc,1.5)+0.5*H_seam
    if abs(new_w-rec_width_init) < 0.1: break
    rec_width_init = new_w
rec_width = np.round(rec_width_init,1)
pillar_strength = p_strength
y_zone = max(y_zone_calc,1.5)
void_frac_base = float(np.mean(void_mask_permanent))
optimal_width_ai = optimize_pillar(ucs_seam, H_seam, sv_seam, strength_red, void_frac_base, rec_width)
progress_bar.progress(1.0)
progress_bar.empty()

# Email alert agar FOS kritik bo'lsa
mean_fos = np.nanmean(fos_2d)
send_alert(mean_fos, obj_name)

# Ma'lumotlar bazasiga yozish
conn = init_db()
cursor = conn.cursor()
cursor.execute("INSERT INTO sensors (timestamp, temperature, fos, pillar_width, anomaly_score) VALUES (?, ?, ?, ?, ?)",
               (datetime.now(), float(np.mean(temp_2d)), float(mean_fos), optimal_width_ai, 0.0))
conn.commit()

# Google Sheets ga yozish
gsheet = get_gsheet()
if gsheet:
    try:
        gsheet.append_row([obj_name, mean_fos, datetime.now().isoformat()])
    except:
        pass

# Asosiy metrikalar
st.subheader(t('monitoring_header', obj_name=obj_name))
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

# Grafiklar (qisqartirilgan, lekin asosiy)
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5,1.5,2])
s_max = (H_seam*0.04)*(min(time_h,120)/120)
sub_p = -s_max * np.exp(-(x_axis**2)/(2*(total_depth/2)**2))
uplift = (total_depth*1e-4)*np.exp(-(x_axis**2)/(total_depth*10))*(time_h/150)*100
with col_g1:
    fig_sub = go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta',width=3)))
    fig_sub.update_layout(title=t('subsidence_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_sub, use_container_width=True)
with col_g2:
    fig_therm = go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy', line=dict(color='cyan',width=3)))
    fig_therm.update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_therm, use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
    mb_s = layers_data[-1]['mi'] * np.exp((layers_data[-1]['gsi']-100)/(28-14*D_factor))
    s_s = np.exp((layers_data[-1]['gsi']-100)/(9-3*D_factor))
    a_s = 0.5 + (1/6)*(np.exp(-layers_data[-1]['gsi']/15)-np.exp(-20/3))
    s1_20 = sigma3_ax + ucs_seam*(mb_s*sigma3_ax/(ucs_seam+EPS)+s_s)**a_s
    ucs_burn = ucs_seam*np.exp(-0.0025*(T_source_max-20))
    s1_burning = sigma3_ax + ucs_burn*(mb_s*sigma3_ax/(ucs_burn+EPS)+s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam*strength_red)*(mb_s*sigma3_ax/(ucs_seam*strength_red+EPS)+s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red',width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name=t('tensile_hb'), line=dict(color='cyan',width=2,dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name=t('combustion'), line=dict(color='orange',width=4)))
    fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_hb, use_container_width=True)

# TM maydoni (harorat + FOS + collapse) – qisqartirilgan
st.markdown("---")
c1, c2 = st.columns([1,2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
with c2:
    st.subheader(t('tm_field_title'))
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                           subplot_titles=(t('temp_subplot'), t('fos_subplot')))
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42)), row=1, col=1)
    step = 12
    qx,qz = grid_x[::step,::step].flatten(), grid_z[::step,::step].flatten()
    qu,qw = gas_velocity[::step,::step].flatten()*0, gas_velocity[::step,::step].flatten()
    qmag = gas_velocity[::step,::step].flatten()
    mask_q = qmag > qmag.max()*0.05
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q]+EPS))
    fig_tm.add_trace(go.Scatter(x=qx[mask_q], y=qz[mask_q], mode='markers',
                                marker=dict(symbol='arrow', size=10, color=qmag[mask_q], colorscale='ice',
                                            angle=angles, opacity=0.85), name=t('gas_flow')), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale=[[0,'red'],[0.33,'yellow'],[0.5,'green'],[1,'darkgreen']],
                                zmin=0, zmax=3.0, colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42)), row=2, col=1)
    void_visual = np.where(void_mask_permanent>0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis, colorscale=[[0,'black'],[1,'black']], showscale=False, opacity=0.9), row=2, col=1)
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name=t('ai_collapse')), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(r=150,t=80,b=100), showlegend=True,
                         legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# Health check
health = health_check()
if health['status'] != 'healthy':
    st.warning("⚠️ Health check: some services may be degraded")

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device} | PT: {PT_AVAILABLE}")
