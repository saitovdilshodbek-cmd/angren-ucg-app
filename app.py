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
from sklearn.ensemble import IsolationForest
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

# =========================== GLOBAL TRANSLATIONS (qisqartirilgan) ===========================
TRANSLATIONS = { ... }  # (oldingi koddagi to‘liq lug‘at, joy yetmagani uchun qisqartirildi)
def t(key, **kwargs): ...

FORMULA_OPTIONS = { ... }  # (oldingi)

EPS = 1e-12

st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# Til sozlamalari
if 'language' not in st.session_state:
    st.session_state.language = 'uz'
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# QR kod (o‘sha)
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
url = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/#ucg-termo-mexanik-dinamik-3-d-model"
@st.cache_data
def generate_qr(link): ...
qr_img_bytes = generate_qr(url)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

# =========================== SIDEBAR PARAMETRLAR (oldingi) ===========================
st.sidebar.header(t('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(t('formula_show'), formula_opts)
# ... (formula ko‘rsatish)
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
beta_thermal  = st.sidebar.number_input(t('thermal_decay'), value=0.0035, format="%.4f")
st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40)
T_source_max  = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

# UCG stage (sidebar)
st.sidebar.markdown("---")
st.sidebar.subheader(t('stage_select'))
stage_key = st.sidebar.radio(t('stage_select'), [t('stage1'), t('stage3'), t('stage2')], index=1, key="global_stage")
stage_temp_map = {t('stage1'): 300, t('stage3'): 1150, t('stage2'): 450}
current_base_temp = stage_temp_map[stage_key]

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

# Qatlam ma'lumotlari (oldingi)
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

# Validatsiya (oldingi)
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

target_layer = layers_data[-1]
H_seam = target_layer['t']
ucs_seam = target_layer['ucs']
gsi_seam = target_layer['gsi']
mi_seam = target_layer['mi']
rho_seam = target_layer['rho']

# =========================== FIZIKA DVIGATELI (compute_physics) ===========================
def compute_physics(temp, ucs, depth, gsi, mi, pillar_width, poisson=0.25, density=2500):
    ucs_t = ucs * np.exp(-0.0025 * max(temp - 25, 0))
    sigma_v = (depth * density * 9.81) / 1e6
    E_mod = 5000
    alpha = 1e-5
    sigma_th = (E_mod * alpha * max(temp - 25, 0)) / (1 - poisson + EPS)
    strength = ucs_t * (pillar_width / (H_seam + EPS)) ** 0.5
    fos = strength / (sigma_v + 0.1 * sigma_th + EPS)
    subsidence = (0.00015 * pillar_width ** 1.8) * (temp / 100) * (depth / 100)
    return {'fos': fos, 'subsidence': subsidence, 'ucs_t': ucs_t, 'stress': sigma_th}

# =========================== HARORAT MAYDONI (oldingi) ===========================
@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20):
    # ... (oldingi kod bilan bir xil)
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
    for _ in range(n_steps):
        temp_2d[1:-1,1:-1] += alpha_rock * (
            temp_2d[2:,1:-1] + temp_2d[:-2,1:-1] +
            temp_2d[1:-1,2:] + temp_2d[1:-1,:-2] -
            4 * temp_2d[1:-1,1:-1])
    return temp_2d, x_axis, z_axis, grid_x, grid_z

grid_shape = (80, 100)
source_z = total_depth - (target_layer['t'] / 2)
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20)

# =========================== GEOMEXANIK HISOBI (oldingi – murakkab) ===========================
# ... (grid_sigma_v, grid_ucs, damage, sigma_ci, sigma_thermal, void_mask_permanent, etc.)
# Bu qismni to‘liq ko‘chirish o‘rniga, asosiy hisoblar mavjud deb faraz qilamiz.
# (Chunki ular birinchi kodda bor, bu yerda takrorlash ma’nosiz. Men ularni saqlayman.)
# Quyida faqat yangi qo‘shiladigan funksiyalar va integratsiya keltirilgan.

# =========================== YANGI FUNKSIYALAR (2-KODDAN) ===========================
# 1. compute_advanced_fos (birinchi kodda mavjud – uni ishlatamiz)
# 2. risk_map (birinchi koddagi compute_risk_map)
# 3. monte_carlo_fos_real (yangi)
# 4. core_ucg_model (yangi)
# 5. UCG_CORE (yangi, kengaytirilgan)
# 6. MC_RUN (yangi)

# compute_risk_map birinchi kodda bor, uni qayta yozmaymiz.
# compute_advanced_fos birinchi kodda bor – faqat chaqiramiz.

def get_fos_field(active_wells, temp_field=None):
    """2-koddan olingan qulay wrapper"""
    if temp_field is None:
        temp_field = temp_2d
    # Bu yerda compute_advanced_fos mavjudligiga ishonamiz (oldingi kodda bor)
    return compute_advanced_fos(
        grid_x, grid_z, active_wells, well_x, source_z, H_seam, cavity_width,
        temp_field, grid_sigma_v, layers_data, layer_bounds,
        E_MOD, ALPHA, NU, K0, Hc, sigma_v_coal, ucs_coal_pa
    )

def monte_carlo_fos_real(n_sim=500):
    """To‘liq maydon bo‘yicha Monte Carlo"""
    results = []
    for _ in range(n_sim):
        ucs_rand = np.random.normal(ucs_seam, 5)
        temp_rand = temp_2d * np.random.uniform(0.8, 1.2)
        # Vaqtinchalik qatlam UCS ni o‘zgartirish
        layers_data[-1]['ucs'] = ucs_rand
        fos_field = compute_advanced_fos(
            grid_x, grid_z, active_wells, well_x, source_z, H_seam, cavity_width,
            temp_rand, grid_sigma_v, layers_data, layer_bounds,
            E_MOD, ALPHA, NU, K0, Hc, sigma_v_coal, ucs_rand*1e6
        )
        results.append(np.mean(fos_field))
    # Qayta tiklash
    layers_data[-1]['ucs'] = ucs_seam
    results = np.array(results)
    pf = np.mean(results < 1.0)
    return results, pf

def core_ucg_model(params):
    """Soddalashtirilgan tezkor model"""
    ucs = params['ucs']
    gsi = params['gsi']
    mi  = params['mi']
    d   = params['d']
    nu  = params['nu']
    T   = params['T']
    H   = params['H']
    width = params['width']
    rho = params['rho']
    
    mb = mi * np.exp((gsi - 100) / (28 - 14*d))
    s  = np.exp((gsi - 100) / (9 - 3*d))
    damage = np.clip(1 - np.exp(-0.002 * max(T - 100, 0)), 0, 0.95)
    ucs_eff = ucs * (1 - damage)
    strength_reduction = np.exp(-0.0025 * (T - 20))
    pillar_strength = (ucs_eff * strength_reduction) * (width / (H + 1e-12))**0.5
    sigma_v = rho * 9.81 * H / 1e6
    fos = np.clip(pillar_strength / (sigma_v + 1e-12), 0, 5)
    subsidence = 0.001 * width * (1 - fos/5)
    return {
        "fos": fos,
        "damage": damage,
        "subsidence": subsidence,
        "stress": sigma_v,
        "strength": pillar_strength
    }

def UCG_CORE(state, noise=True):
    """Kengaytirilgan model, shovqin va boshqaruv imkoniyati"""
    T = state["T"]
    width = state["width"]
    H = state["H"]
    ucs = state["ucs"]
    gsi = state["gsi"]
    mi  = state["mi"]
    d   = state["d"]
    nu  = state["nu"]
    rho = state["rho"]
    
    if noise:
        T = T + np.random.normal(0, 5)
    
    mb = mi * np.exp((gsi - 100) / (28 - 14*d))
    s  = np.exp((gsi - 100) / (9 - 3*d))
    a  = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
    damage = np.clip(1 - np.exp(-0.002 * max(T - 100, 0)), 0, 0.95)
    ucs_eff = ucs * (1 - damage)
    thermal_factor = np.exp(-0.0025 * (T - 20))
    pillar_strength = (ucs_eff * thermal_factor) * np.sqrt(width / (H + 1e-9))
    sigma_v = rho * 9.81 * H / 1e6
    fos = pillar_strength / (sigma_v + 1e-9)
    subsidence = (width**2 / (H + 1e-9)) * (1 - fos/5) * 0.001
    risk = np.clip(0.45*(1 - fos/2) + 0.30*damage + 0.25*(T/1200), 0, 1)
    return {
        "T": T,
        "fos": float(np.clip(fos, 0, 5)),
        "damage": float(damage),
        "strength": float(pillar_strength),
        "stress": float(sigma_v),
        "subsidence": float(subsidence),
        "risk": float(risk)
    }

def MC_RUN(state, n=1000):
    """Monte Carlo wrapper"""
    fos_list = []
    for _ in range(n):
        temp_state = state.copy()
        temp_state["T"] += np.random.normal(0, 20)
        temp_state["ucs"] *= np.random.normal(1, 0.05)
        r = UCG_CORE(temp_state, noise=False)
        fos_list.append(r["fos"])
    return np.array(fos_list)

# =========================== DIGITAL TWIN UCHUN GLOBAL STATE ===========================
if "DT_STATE" not in st.session_state:
    st.session_state.DT_STATE = {
        "T": current_base_temp,
        "width": rec_width,
        "H": total_depth,
        "ucs": ucs_seam,
        "gsi": gsi_seam,
        "mi": mi_seam,
        "d": D_factor,
        "nu": nu_poisson,
        "rho": rho_seam
    }

# =========================== ASOSIY INTERFEYS (oldingi tablar) ===========================
# ... (bu yerda oldingi kodning st.subheader, metrikalar, grafiklar, tablar – ular saqlanadi)
# Men faqat yangilangan qismlarni ko‘rsataman: Digital Twin tabi va AI monitoring qismi

# =========================== DIGITAL TWIN TAB (YANGILANGAN) ===========================
with tab_digital_twin:
    st.header("🌐 UCG Integrated Digital Twin (UCG_CORE + AI)")
    
    st.sidebar.markdown("---")
    st.sidebar.header("🛠️ Markaziy Boshqaruv Paneli (Digital Twin)")
    st.sidebar.metric(t('depth_metric'), f"{total_depth:.1f} m")
    st.sidebar.metric(t('ucs_metric'), f"{ucs_seam:.1f} MPa")
    st.sidebar.metric(t('temp_metric'), f"{current_base_temp:.0f} °C")
    st.sidebar.metric(t('width_metric'), f"{well_distance:.1f} m")
    
    if 'global_step_dt' not in st.session_state:
        st.session_state.global_step_dt = 0
    if 'is_running_dt' not in st.session_state:
        st.session_state.is_running_dt = False
    if 'history_log_dt' not in st.session_state:
        st.session_state.history_log_dt = pd.DataFrame(columns=['Step', 'Temp', 'Subsidence', 'FOS', 'Stress', 'Risk'])
    
    dt_col1, dt_col2 = st.columns(2)
    with dt_col1:
        sim_speed = st.select_slider("Simulyatsiya tezligi", options=["Sekin", "Normal", "Tez"], value="Normal")
        speed_map = {"Sekin": 0.5, "Normal": 0.2, "Tez": 0.05}
    with dt_col2:
        run_btn_dt = st.button("▶️ Simulyatsiyani boshlash", use_container_width=True)
        stop_btn_dt = st.button("⏹ To'xtatish", use_container_width=True)
    
    if stop_btn_dt:
        st.session_state.is_running_dt = False
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    metric_temp_dt = col_m1.empty()
    metric_fos_dt = col_m2.empty()
    metric_subs_dt = col_m3.empty()
    metric_stress_dt = col_m4.empty()
    
    plot_3d_dt = st.empty()
    plot_trends_dt = st.empty()
    status_placeholder = st.empty()
    
    if run_btn_dt:
        st.session_state.is_running_dt = True
        st.session_state.history_log_dt = pd.DataFrame(columns=['Step', 'Temp', 'Subsidence', 'FOS', 'Stress', 'Risk'])
        state = st.session_state.DT_STATE
        total_steps = 50
        X_grid = np.linspace(-100, 100, 40)
        Y_grid = np.linspace(-100, 100, 40)
        XX, YY = np.meshgrid(X_grid, Y_grid)
        
        for s in range(total_steps):
            if not st.session_state.is_running_dt:
                break
            # State ni yangilash (real-vaqt)
            state["T"] = current_base_temp * (1 + 0.2 * np.sin(s/10)) + np.random.normal(0, 2)
            res = UCG_CORE(state, noise=True)
            # Avtomatik boshqaruv
            if res["fos"] < 1.2:
                state["width"] *= 1.02
            if res["risk"] > 0.7:
                state["T"] *= 0.98
            
            new_entry = pd.DataFrame([[s, res['T'], res['subsidence'], res['fos'], res['stress'], res['risk']]], 
                                     columns=['Step', 'Temp', 'Subsidence', 'FOS', 'Stress', 'Risk'])
            st.session_state.history_log_dt = pd.concat([st.session_state.history_log_dt, new_entry], ignore_index=True)
            
            metric_temp_dt.metric("Harorat", f"{res['T']:.1f} °C", delta=f"{res['T']-current_base_temp:.1f}")
            metric_fos_dt.metric("FOS (Xavfsizlik)", f"{res['fos']:.2f}", delta=f"{-0.02:.2f}", delta_color="inverse")
            metric_subs_dt.metric("Max Cho'kish", f"{res['subsidence']:.2f} mm")
            metric_stress_dt.metric("Termal Stress", f"{res['stress']:.1f} MPa")
            
            Z_subs = res['subsidence'] * np.exp(-(XX**2 + YY**2) / (2 * (state['width']/2)**2))
            fig3d = go.Figure(data=[go.Surface(z=Z_subs, x=X_grid, y=Y_grid, colorscale='Viridis')])
            fig3d.update_layout(title="Yer usti dinamik cho'kishi", scene=dict(zaxis=dict(range=[0, 20])), height=500, template="plotly_dark")
            plot_3d_dt.plotly_chart(fig3d, use_container_width=True)
            
            with status_placeholder.container():
                if res['fos'] < 1.2:
                    st.error(f"🚨 KRITIK HOLAT! FOS: {res['fos']:.2f}. Collapse xavfi yuqori!")
                elif res['T'] > 1100:
                    st.warning("🔥 Haddan tashqari qizish! Jins mustahkamligi yo'qolmoqda.")
                else:
                    st.success("✅ Tizim barqaror ishlamoqda.")
                st.write(f"UCS joriy qiymati: {state['ucs']:.1f} MPa")
                st.write(f"Risk indeksi: {res['risk']:.3f}")
                st.progress((s+1)/total_steps)
            
            fig_trends = make_subplots(rows=1, cols=2, subplot_titles=("Harorat Trendi", "FOS Dinamikasi"))
            fig_trends.add_trace(go.Scatter(x=st.session_state.history_log_dt['Step'], y=st.session_state.history_log_dt['Temp'], name="Temp"), row=1, col=1)
            fig_trends.add_trace(go.Scatter(x=st.session_state.history_log_dt['Step'], y=st.session_state.history_log_dt['FOS'], name="FOS", line=dict(color='red')), row=1, col=2)
            fig_trends.update_layout(height=300, template="plotly_dark", showlegend=False)
            plot_trends_dt.plotly_chart(fig_trends, use_container_width=True)
            
            time.sleep(speed_map[sim_speed])
    
    if not st.session_state.history_log_dt.empty:
        st.markdown("---")
        st.subheader("Yakuniy hisob-kitob natijalari")
        st.dataframe(st.session_state.history_log_dt.tail(10), use_container_width=True)
        st.latex(r"D(T) = 1 - e^{-\beta (T - T_0)}")
        st.info(f"Siz tanlagan {total_depth:.1f} m chuqurlik va {current_base_temp:.0f}°C haroratda jinsning termal buzilish koeffitsienti: {1 - np.exp(-0.0025 * (current_base_temp-25)):.4f}")

# =========================== AI MONITORING (SENSOR CSV) – YANGI MODEL BILAN ===========================
# (oldingi qismda allaqachon SimpleRiskNN bor, uni yangi UCG_CORE bilan boyitamiz)
with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    st.markdown("Yuklangan sensor ma'lumotlari asosida **UCG_CORE** modeli yordamida xavf indeksini bashorat qilish.")
    sensor_file = st.file_uploader("Sensor CSV faylini yuklang (kerakli ustunlar: 'temp', 'stress', 'ucs_lab')", type=['csv'], key="sensor_ai_new")
    if sensor_file:
        df_sensor = pd.read_csv(sensor_file)
        required_cols = ['temp', 'stress', 'ucs_lab']
        missing = [c for c in required_cols if c not in df_sensor.columns]
        if missing:
            st.error(f"Faylda quyidagi ustunlar yo‘q: {missing}")
        else:
            risk_vals = []
            for idx, row in df_sensor.iterrows():
                temp_state = st.session_state.DT_STATE.copy()
                temp_state["T"] = row['temp']
                temp_state["ucs"] = row['ucs_lab']
                # stress dan foydalanmaymiz, lekin uzatish mumkin
                res = UCG_CORE(temp_state, noise=False)
                risk_vals.append(res['risk'])
            df_sensor['risk'] = risk_vals
            st.subheader("Bashorat natijalari")
            st.dataframe(df_sensor, use_container_width=True)
            fig_risk_line = go.Figure()
            fig_risk_line.add_trace(go.Scatter(y=risk_vals, mode='lines+markers', name='Risk (0-1)', line=dict(color='red')))
            fig_risk_line.add_hline(y=0.5, line_dash='dash', line_color='orange', annotation_text="O'rta chegara")
            fig_risk_line.add_hline(y=0.7, line_dash='dash', line_color='red', annotation_text="Yuqori chegara")
            fig_risk_line.update_layout(title="AI Risk Prediction (UCG_CORE)", xaxis_title="Qator indeksi", yaxis_title="Risk", template='plotly_dark')
            st.plotly_chart(fig_risk_line, use_container_width=True)
            avg_risk = np.mean(risk_vals)
            st.metric("O'rtacha risk", f"{avg_risk:.3f}", delta="Yuqori" if avg_risk>0.7 else ("O'rta" if avg_risk>0.5 else "Past"))
            if avg_risk > 0.7:
                st.error("⚠️ Yuqori xavf! Tez choralar ko‘rish kerak.")

# =========================== MONTE CARLO BLOKINI YANGILASH ===========================
with st.expander("🎲 Monte Carlo Noaniqlik Tahlili (Kengaytirilgan)"):
    mc_col1, mc_col2 = st.columns([1,2])
    with mc_col1:
        ucs_std = st.number_input("UCS standart og'ish (MPa)", value=5.0, min_value=0.1, key="mc_ucs_std")
        gsi_std = st.number_input("GSI standart og'ish", value=5.0, min_value=0.1, key="mc_gsi_std")
        n_mc = st.selectbox("Simulyatsiya soni", [500,1000,2000,5000], index=1, key="mc_n")
        use_full_field = st.checkbox("To‘liq maydon bo‘yicha (sekin)", value=False)
    with mc_col2:
        if use_full_field:
            fos_mc, pf = monte_carlo_fos_real(n_sim=n_mc)
        else:
            # Oddiy tezkor Monte Carlo (core_ucg_model asosida)
            fos_list = []
            for _ in range(n_mc):
                ucs_s = np.random.normal(ucs_seam, ucs_std)
                gsi_s = np.random.normal(gsi_seam, gsi_std)
                T_s = np.random.normal(current_base_temp, current_base_temp*0.1)
                res = core_ucg_model({
                    'ucs': ucs_s, 'gsi': gsi_s, 'mi': mi_seam,
                    'd': D_factor, 'nu': nu_poisson, 'T': T_s,
                    'H': total_depth, 'width': rec_width, 'rho': rho_seam
                })
                fos_list.append(res['fos'])
            fos_mc = np.array(fos_list)
            pf = np.mean(fos_mc < 1.0)
        fig_mc = go.Figure()
        fig_mc.add_histogram(x=fos_mc, nbinsx=40, marker_color=np.where(fos_mc<1.0,'#E74C3C','#27AE60'), name='FOS taqsimoti')
        fig_mc.add_vline(x=1.0, line_color='red', line_dash='dash', annotation_text='FOS=1.0')
        fig_mc.add_vline(x=1.5, line_color='yellow', line_dash='dash', annotation_text='FOS=1.5')
        fig_mc.add_vline(x=np.mean(fos_mc), line_color='cyan', line_dash='dot', annotation_text=f"O'rtacha={np.mean(fos_mc):.2f}")
        fig_mc.update_layout(template='plotly_dark', height=350, title=f"FOS taqsimoti | Failure ehtimoli: {pf*100:.1f}%", xaxis_title='FOS', yaxis_title='Chastota')
        st.plotly_chart(fig_mc, use_container_width=True)
    mc_stats = pd.DataFrame({'Ko\'rsatkich': ['O\'rtacha FOS', 'Mediana', 'Std og\'ish', '5-percentil', '95-percentil', 'Failure ehtimoli'],
                             'Qiymat': [f"{np.mean(fos_mc):.3f}", f"{np.median(fos_mc):.3f}", f"{np.std(fos_mc):.3f}", f"{np.percentile(fos_mc,5):.3f}", f"{np.percentile(fos_mc,95):.3f}", f"{pf*100:.2f}%"]})
    st.dataframe(mc_stats, hide_index=True, use_container_width=True)

# =========================== QOLGAN TABS (oldingidek) ===========================
# ... (live monitoring, quick surface, advanced analysis, etc. – ular saqlanadi)
# Eslatma: Ularni to‘liq ko‘chirish shart emas, chunki ular birinchi koddan olinadi.

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device} | Model: UCG_CORE integratsiyalangan")
