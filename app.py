import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress, norm as gaussian_distribution
import time
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
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
import sys
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve
from sklearn.model_selection import KFold
import joblib
from sklearn.preprocessing import StandardScaler
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================== KUTUBXONALARNI TEKSHIRISH ===========================
try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    PYTORCH_AVAILABLE = False
    device = "cpu"

try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

try:
    from pyDOE import lhs
    PYDOE_AVAILABLE = True
except ImportError:
    PYDOE_AVAILABLE = False

try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# =========================== TARJIMALAR (TO‘LIQ) ===========================
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
        'thermal_decay': "Termal shikastlanish koeffitsiyenti (β):",
        'combustion': "🔥 Yonish va Termal",
        'burn_duration': "Kamera yonish muddati (soat):",
        'max_temp': "Maksimal harorat (°C)",
        'timeline': "📅 Loyiha bosqichlari (Timeline)",
        'layer_params': "{num}-qatlam parametrlari",
        'layer_name': "Nomi:",
        'thickness': "Qalinlik (m):",
        'ucs': "UCS (MPa):",
        'density': "Zichlik (kg/m³):",
        'color': "Rangi:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (MPa):",
        'error_thick_positive': "Qalinlik >0 bo'lishi kerak",
        'error_ucs_positive': "UCS >0 MPa bo'lishi kerak",
        'error_density_positive': "Zichlik >0 kg/m³ bo'lishi kerak",
        'error_gsi_range': "GSI 10...100 oralig'ida bo'lishi kerak",
        'error_mi_positive': "mi >0 bo'lishi kerak",
        'error_min_layers': "❌ Kamida 1 ta qatlam kiriting!",
        'warning_pytorch': "⚠️ PyTorch o'rnatilmagan. RandomForest ishlatiladi.",
        'pillar_strength': "Selek mustahkamligi (σp)",
        'plastic_zone': "Plastik zona (y)",
        'cavity_volume': "Kamera Hajmi",
        'max_permeability': "Maks. O'tkazuvchanlik",
        'ai_recommendation': "AI Tavsiya (Selek eni)",
        'monitoring_header': "📊 {obj_name}: Monitoring va Ekspert Xulosasi",
        'subsidence_title': "📉 Yer yuzasi cho'kishi (cm)",
        'thermal_deform_title': "🔥 Termal deformatsiya (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Ilmiy Tahlil",
        'fos_red': "🔴 FOS < 1.0: Buzilish",
        'fos_yellow': "🟡 FOS 1.0–1.5: Beqaror",
        'fos_green': "🟢 FOS > 1.5: Barqaror",
        'tm_field_title': "🔥 TM Maydoni va Selek Interferensiyasi",
        'temp_subplot': "Harorat Maydoni (°C) + Gaz Oqimi",
        'fos_subplot': "FOS + AI Collapse Bashorati (NN) + Yielded Zones",
        'gas_flow': "Gaz oqimi",
        'shear': "Shear",
        'tensile': "Tensile",
        'ai_collapse': "AI Collapse (NN)",
        'monitoring_panel': "📊 {obj_name}: Kompleks Monitoring Paneli",
        'pillar_live': "Selek mustahkamligi",
        'rec_width_live': "Tavsiya: Selek eni",
        'max_subsidence_live': "Maks. Cho'kish",
        'process_stage': "Jarayon bosqichi",
        'stage_active': "Faol",
        'stage_cooling': "Sovish",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'ai_monitor_desc': "Real-vaqt sensor ma'lumotlari va anomaliya aniqlash",
        'ai_steps': "Simulyatsiya qadamlari soni:",
        'ai_run_btn': "▶️ AI Monitoringni Ishga Tushirish",
        'ai_stop_btn': "⏹ To'xtatish",
        'advanced_analysis': "🔍 Chuqurlashtirilgan Dinamik Tahlil va Metodik Asoslash",
        'tab_mass': "🏗️ Massiv Parametrlari",
        'tab_thermal': "🔥 Termal Degradatsiya",
        'tab_stability': "⚖️ Barqarorlik & Manbalar",
        'hb_class': "1. Hoek-Brown (2018) Klassifikatsiyasi",
        'hb_mb': "m_b = {mb:.3f}",
        'hb_s': "s = {s:.4f}",
        'hb_caption_mb': "Massiv ishqalanish burchagi funksiyasi (m_i={mi})",
        'hb_caption_s': "Yoriqlilik darajasi (GSI={gsi})",
        'hb_interpret': "**Ilmiy izoh:** Hoek & Brown (2018) mezoniga ko'ra, GSI={gsi} bo'lishi massiv mustahkamligi laboratoriyaga nisbatan **{perc:.1f}%** ga pastligini anglatadi.",
        'thermal_params': "2. Termo-Mexanik Koeffitsiyentlar Tahlili",
        'param_table_param': "Parametr",
        'param_table_value': "Qiymat",
        'param_table_reason': "Tanlanish sababi",
        'modulus': "Elastiklik Moduli (E)",
        'alpha': "Termal kengayish (α)",
        'temp0': "Boshlang'ich T₀",
        'modulus_reason': "Ko'mir uchun xos o'rtacha deformatsiya koeffitsiyenti.",
        'alpha_reason': "Ko'mirning issiqlikdan chiziqli kengayish ko'rsatkichi (Yang, 2010).",
        'temp0_reason': "Kon qatlamining boshlang'ich tabiiy harorati.",
        'ucs_decay': "**A) Termal UCS pasayishi:**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ MPa}}",
        'ucs_interpret': "**Interpretatsiya:** {temp}°C haroratda jins mustahkamligi {perc:.1f}% ga pasaydi.",
        'thermal_stress': "**B) Termal kuchlanish ($\\sigma_{{th}}$):**",
        'thermal_stress_eq': r"\sigma_{{th}} \approx \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ MPa}}",
        'pillar_stability': "3. Selek Barqarorligi va Bibliografiya",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v}} = {fos:.2f}",
        'pillar_wilson': "**Wilson (1972) Yield Pillar nazariyasiga binoan:** Selek o'lchami $w={w}$ m bo'lganda, uning markaziy yadrosi {sv:.2f} MPa lik geostatik yukni ko'tarishga qodir. Plastik zona: $y = {y:.1f}$ m.",
        'references': "#### 📚 Asosiy Ilmiy Manbalar:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*.",
        'conclusion_danger': "🔴 **Ilmiy Xulosa:** FOS={fos:.2f}. Termal degradatsiya yuqori. Selek enini oshirish yoki gazlashtirish tezligini nazorat qilish tavsiya etiladi.",
        'conclusion_safe': "🟢 **Ilmiy Xulosa:** FOS={fos:.2f}. Tanlangan parametrlar massiv barqarorligini ta'minlaydi.",
        'methodology_expander': "📚 Ilmiy Metodologiya va Manbalar (PhD Research References)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'timeline_table': """
| Bosqich | Vaqti | Tavsif |
|---------|-------|--------|
| **Rejalashtirish** | 2026-04-01 | Validatsiya, xavfsiz bo'lish funksiyalarini ishlab chiqish |
| **Modellarni optimallashtirish** | 2026-05-15 | NN/RF testlash, FDM yaxshilash, keshlashtirish |
| **Integratsiya va testlash** | 2026-06-30 | Unit testlar, yakuniy vizualizatsiya, deploy |
        """,
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Monitoring ma'lumotlarini yuklab olish (CSV)",
        'validation_title': "📑 **Ilmiy Validatsiya (A–E)**",
        'validation_a': "A) FLAC3D yoki RS2 bilan solishtirish",
        'validation_b': "B) Noaniqlik tahlili (Monte Carlo)",
        'validation_c': "C) Sezgirlik tahlili (Sobol / Tornado)",
        'validation_d': "D) Mavjud modellar bilan taqqoslash (Benchmarking)",
        'validation_e': "E) Yangilik da’vosi (Novelty Claim)",
    },
    'en': {
        'app_title': "Universal Surface Deformation Monitoring",
        'app_subtitle': "Thermo-Mechanical (TM) Analysis and Pillar Size Optimization",
        'sidebar_header_params': "⚙️ General Parameters",
        'formula_show': "View formulas:",
        'project_name': "Project name:",
        'process_time': "Process time (hours):",
        'num_layers': "Number of layers:",
        'tensile_model': "Tensile model:",
        'rock_props': "💎 Rock Properties",
        'disturbance': "Disturbance Factor (D):",
        'poisson': "Poisson's ratio (ν):",
        'stress_ratio': "Stress Ratio (k = σh/σv):",
        'tensile_params': "📐 Tension and Pillar",
        'tensile_ratio': "Tensile Ratio (σt0/UCS):",
        'thermal_decay': "Thermal Damage Coefficient (β):",
        'combustion': "🔥 Combustion and Thermal",
        'burn_duration': "Burn duration (hours):",
        'max_temp': "Maximum temperature (°C)",
        'timeline': "📅 Project Timeline",
        'layer_params': "Layer {num} parameters",
        'layer_name': "Name:",
        'thickness': "Thickness (m):",
        'ucs': "UCS (MPa):",
        'density': "Density (kg/m³):",
        'color': "Color:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (MPa):",
        'error_thick_positive': "Thickness must be >0",
        'error_ucs_positive': "UCS must be >0 MPa",
        'error_density_positive': "Density must be >0 kg/m³",
        'error_gsi_range': "GSI must be between 10 and 100",
        'error_mi_positive': "mi must be >0",
        'error_min_layers': "❌ At least 1 layer required!",
        'warning_pytorch': "⚠️ PyTorch not installed. Using RandomForest.",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastic zone (y)",
        'cavity_volume': "Cavity Volume",
        'max_permeability': "Max Permeability",
        'ai_recommendation': "AI Recommendation (Pillar Width)",
        'monitoring_header': "📊 {obj_name}: Monitoring and Expert Summary",
        'subsidence_title': "📉 Surface subsidence (cm)",
        'thermal_deform_title': "🔥 Thermal deformation (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Scientific Analysis",
        'fos_red': "🔴 FOS < 1.0: Failure",
        'fos_yellow': "🟡 FOS 1.0–1.5: Unstable",
        'fos_green': "🟢 FOS > 1.5: Stable",
        'tm_field_title': "🔥 TM Field and Pillar Interference",
        'temp_subplot': "Temperature Field (°C) + Gas Flow",
        'fos_subplot': "FOS + AI Collapse Prediction (NN) + Yielded Zones",
        'gas_flow': "Gas flow",
        'shear': "Shear",
        'tensile': "Tensile",
        'ai_collapse': "AI Collapse (NN)",
        'monitoring_panel': "📊 {obj_name}: Integrated Monitoring Panel",
        'pillar_live': "Pillar Strength",
        'rec_width_live': "Recommended Pillar Width",
        'max_subsidence_live': "Max Subsidence",
        'process_stage': "Process stage",
        'stage_active': "Active",
        'stage_cooling': "Cooling",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'ai_monitor_desc': "Real-time sensor data and anomaly detection",
        'ai_steps': "Simulation steps:",
        'ai_run_btn': "▶️ Run AI Monitoring",
        'ai_stop_btn': "⏹ Stop",
        'advanced_analysis': "🔍 In-depth Dynamic Analysis and Methodological Justification",
        'tab_mass': "🏗️ Rock Mass Parameters",
        'tab_thermal': "🔥 Thermal Degradation",
        'tab_stability': "⚖️ Stability & References",
        'hb_class': "1. Hoek-Brown (2018) Classification",
        'hb_mb': "m_b = {mb:.3f}",
        'hb_s': "s = {s:.4f}",
        'hb_caption_mb': "Mass friction angle function (m_i={mi})",
        'hb_caption_s': "Fracturing degree (GSI={gsi})",
        'hb_interpret': "**Scientific comment:** According to Hoek & Brown (2018), GSI={gsi} means rock mass strength is **{perc:.1f}%** lower than laboratory values.",
        'thermal_params': "2. Thermo-Mechanical Coefficient Analysis",
        'param_table_param': "Parameter",
        'param_table_value': "Value",
        'param_table_reason': "Justification",
        'modulus': "Elastic Modulus (E)",
        'alpha': "Thermal expansion (α)",
        'temp0': "Initial T₀",
        'modulus_reason': "Typical average deformation coefficient for coal.",
        'alpha_reason': "Linear thermal expansion coefficient of coal (Yang, 2010).",
        'temp0_reason': "Initial natural temperature of the coal seam.",
        'ucs_decay': "**A) Thermal UCS reduction:**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ MPa}}",
        'ucs_interpret': "**Interpretation:** At {temp}°C, rock strength decreased by {perc:.1f}%.",
        'thermal_stress': "**B) Thermal stress ($\\sigma_{{th}}$):**",
        'thermal_stress_eq': r"\sigma_{{th}} \approx \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ MPa}}",
        'pillar_stability': "3. Pillar Stability and Bibliography",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v}} = {fos:.2f}",
        'pillar_wilson': "**According to Wilson (1972) Yield Pillar theory:** With pillar width $w={w}$ m, the central core can sustain a geostatic load of {sv:.2f} MPa. Plastic zone: $y = {y:.1f}$ m.",
        'references': "#### 📚 Main Scientific References:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*.",
        'conclusion_danger': "🔴 **Scientific Conclusion:** FOS={fos:.2f}. High thermal degradation. Increase pillar width or control gasification rate.",
        'conclusion_safe': "🟢 **Scientific Conclusion:** FOS={fos:.2f}. The selected parameters ensure mass stability.",
        'methodology_expander': "📚 Scientific Methodology and References (PhD Research)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'timeline_table': """
| Stage | Time | Description |
|-------|------|-------------|
| **Planning** | 2026-04-01 | Validation, develop safety functions |
| **Model optimization** | 2026-05-15 | NN/RF testing, FDM improvement, caching |
| **Integration & testing** | 2026-06-30 | Unit tests, final visualization, deploy |
        """,
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Download monitoring data (CSV)",
        'validation_title': "📑 **Scientific Validation (A–E)**",
        'validation_a': "A) FLAC3D/RS2 Comparison",
        'validation_b': "B) Uncertainty Analysis (Monte Carlo)",
        'validation_c': "C) Sensitivity Analysis (Sobol / Tornado)",
        'validation_d': "D) Benchmarking Against Existing Models",
        'validation_e': "E) Novelty Claim",
    }
}

FORMULA_OPTIONS = {
    'uz': ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"],
    'en': ["Close", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"]
}

def translate(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

EPSILON = 1e-8

st.set_page_config(page_title=translate('app_title'), layout="wide")
st.title(translate('app_title'))
st.markdown(f"### {translate('app_subtitle')}")

if 'language' not in st.session_state:
    st.session_state.language = 'uz'
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English'}
lang = st.sidebar.selectbox("Til / Language", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# QR kod
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilova")
application_url = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app"
@st.cache_data
def generate_qr_code(link):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
qr_image_bytes = generate_qr_code(application_url)
st.sidebar.image(qr_image_bytes, caption="Scan QR", use_container_width=True)

# Sidebar parametrlar
st.sidebar.header(translate('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(translate('formula_show'), formula_opts)
if formula_option != formula_opts[0]:
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == formula_opts[1]:
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.info("**Hoek-Brown:** GSI va Disturbance (D) faktorlari asosida massiv mustahkamligini hisoblash.")
        elif formula_option == formula_opts[2]:
            st.latex(r"D(T) = 1 - \exp(-\beta (T - T_0))")
            st.info("**Termal degradatsiya:** Harorat ta'sirida mustahkamlik pasayishi.")
        elif formula_option == formula_opts[3]:
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu}")
            st.latex(r"\sigma_{t0} = \frac{\sigma_{ci}}{2}\left(m_b - \sqrt{m_b^2 + 4s}\right)")
            st.info("**Termo-mexanika:** Termik kuchlanish va cho'zilish.")
        elif formula_option == formula_opts[4]:
            st.latex(r"S(x) = S_{max} \cdot \exp\left( -\frac{\pi x^2}{r^2} \right)")
            st.info("**Knothe cho‘kish modeli:** Yer yuzasi deformatsiyasi.")

object_name = st.sidebar.text_input(translate('project_name'), value="Angren-UCG-001")
simulation_time_hours = st.sidebar.slider(translate('process_time'), 1, 150, 24)
number_of_layers = st.sidebar.number_input(translate('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode = st.sidebar.selectbox(translate('tensile_model'),
                                    [translate('tensile_empirical'), translate('tensile_hb'), translate('tensile_manual')])

st.sidebar.subheader(translate('rock_props'))
disturbance_factor = st.sidebar.slider(translate('disturbance'), 0.0, 1.0, 0.7)
poisson_ratio = st.sidebar.slider(translate('poisson'), 0.1, 0.4, 0.28)
stress_ratio_k = st.sidebar.slider(translate('stress_ratio'), 0.1, 2.0, 0.5)

st.sidebar.subheader(translate('tensile_params'))
tensile_ratio_value = st.sidebar.slider(translate('tensile_ratio'), 0.03, 0.15, 0.08)
beta_thermal_coefficient = st.sidebar.slider(
    translate('thermal_decay'),
    min_value=0.0005,
    max_value=0.005,
    value=0.002,
    step=0.0001
)

st.sidebar.subheader(translate('combustion'))
burning_duration_hours = st.sidebar.number_input(translate('burn_duration'), value=40)
maximum_temperature = st.sidebar.slider(translate('max_temp'), 600, 1200, 1075)

with st.sidebar.expander(translate('timeline')):
    st.markdown(translate('timeline_table'))

# Qatlam ma'lumotlari
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(number_of_layers)):
    with st.sidebar.expander(translate('layer_params', num=i+1), expanded=(i == int(number_of_layers) - 1)):
        name = st.text_input(translate('layer_name'), value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(translate('thickness'), value=50.0, min_value=0.1, key=f"t_{i}")
        ucs = st.number_input(translate('ucs'), value=40.0, min_value=0.1, key=f"u_{i}")
        density = st.number_input(translate('density'), value=2500.0, min_value=100.0, key=f"rho_{i}")
        color = st.color_picker(translate('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
        gsi = st.slider(translate('gsi'), 10, 100, 60, key=f"g_{i}")
        mi = st.number_input(translate('mi'), value=10.0, min_value=0.1, key=f"m_{i}")
        s_t0_val = st.number_input(translate('manual_st0'), value=3.0, key=f"st_{i}") if tensile_mode == translate('tensile_manual') else 0.0
    layers_data.append({
        'name': name, 'thickness': thick, 'ucs': ucs, 'density': density,
        'gsi': gsi, 'mi': mi, 'color': color, 'depth_top': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

# Validatsiya
errors = []
for layer in layers_data:
    if layer['thickness'] <= 0: errors.append(translate('error_thick_positive'))
    if layer['ucs'] <= 0: errors.append(translate('error_ucs_positive'))
    if layer['density'] <= 0: errors.append(translate('error_density_positive'))
    if not (10 <= layer['gsi'] <= 100): errors.append(translate('error_gsi_range'))
    if layer['mi'] <= 0: errors.append(translate('error_mi_positive'))
if not layers_data: errors.append(translate('error_min_layers'))
if errors:
    for e in errors: st.error(e)
    st.stop()

# =========================== FIZIK MODELLAR ===========================
class ThermalConductionSolver:
    def __init__(self, thermal_diffusivity=1.0e-6):
        self.alpha = thermal_diffusivity
    def laplacian(self, T, dx, dz):
        return ((T[2:,1:-1] - 2*T[1:-1,1:-1] + T[:-2,1:-1]) / dz**2 +
                (T[1:-1,2:] - 2*T[1:-1,1:-1] + T[1:-1,:-2]) / dx**2)
    def step(self, T, dx, dz, dt, heat_source=None):
        T_new = T.copy()
        lap = self.laplacian(T, dx, dz)
        T_new[1:-1,1:-1] += self.alpha * dt * lap
        if heat_source is not None:
            T_new[1:-1,1:-1] += heat_source[1:-1,1:-1] * dt
        return T_new

class HoekBrownParameters:
    def __init__(self, mi, gsi, D):
        self.mi = mi; self.gsi = gsi; self.D = D
    def compute_parameters(self):
        mb = self.mi * np.exp((self.gsi - 100) / (28 - 14*self.D))
        s = np.exp((self.gsi - 100) / (9 - 3*self.D))
        a = 0.5 + (1/6)*(np.exp(-self.gsi/15) - np.exp(-20/3))
        return mb, s, a

def calculate_thermal_damage(temperature, beta=0.002, T_ref=20):
    delta_T = np.maximum(temperature - T_ref, 0)
    damage = 1 - np.exp(-beta * delta_T)
    return np.clip(damage, 0, 0.95)

def effective_modulus(E0, damage):
    return E0 * (1 - damage)

def vertical_stress_from_depth(depth, density):
    return density * 9.81 * depth / 1e6

def hoek_brown_failure_sigma1(sigma3, sigma_ci, mb, s, a):
    sigma_tension_limit = -0.15 * sigma_ci
    sigma3_eff = np.maximum(sigma3, sigma_tension_limit)
    term = mb * sigma3_eff / (sigma_ci + EPSILON) + s
    term = np.maximum(term, EPSILON)
    sigma1_fail = sigma3_eff + sigma_ci * (term ** a)
    return sigma1_fail

def cavity_growth_factor(damage, fos):
    return damage**1.5 * np.maximum(1 - fos, 0)

def permeability_kozeny_carman(porosity, grain_size=1e-4):
    return (grain_size**2 * porosity**3) / (180 * (1 - porosity + EPSILON)**2)

def knothe_subsidence_profile(x_axis, s_max, depth, draw_angle=35):
    r = depth * np.tan(np.radians(draw_angle))
    subsidence = -s_max * np.exp(-(np.pi * x_axis**2) / (r**2 + EPSILON))
    return subsidence, r

# =========================== ASOSIY HISOB-KITOBLAR ===========================
seam_layer = layers_data[-1]
seam_thickness = seam_layer['thickness']
source_depth = total_depth - seam_thickness / 2.0

grid_shape = (80, 100)
x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
z_axis = np.linspace(0, total_depth + 50, grid_shape[0])
dx = x_axis[1] - x_axis[0]
dz = z_axis[1] - z_axis[0]
grid_x, grid_z = np.meshgrid(x_axis, z_axis)

thermal_diffusivity_rock = 1.0e-6
solver = ThermalConductionSolver(thermal_diffusivity_rock)

combustion_sources = [
    {'x0': -total_depth/3, 'start_time': 0, 'moving': False},
    {'x0': 0, 'start_time': 40, 'moving': True, 'velocity': 0.02},
    {'x0': total_depth/3, 'start_time': 80, 'moving': False}
]

temperature_field = np.full_like(grid_x, 25.0)
for src in combustion_sources:
    if simulation_time_hours <= src['start_time']:
        continue
    elapsed = simulation_time_hours - src['start_time']
    dt_sec = elapsed * 3600
    if src.get('moving', False):
        x_center = src['x0'] + src['velocity'] * dt_sec
    else:
        x_center = src['x0']
    pen_depth = np.sqrt(4 * thermal_diffusivity_rock * dt_sec)
    if elapsed <= burning_duration_hours:
        curr_T = maximum_temperature
    else:
        curr_T = 25 + (maximum_temperature - 25) * np.exp(-0.03 * (elapsed - burning_duration_hours))
    dist_sq = (grid_x - x_center)**2 + (grid_z - source_depth)**2
    temperature_field += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

# FDM diffuziya
n_steps_fdm = 20
dt_fdm = (burning_duration_hours * 3600) / n_steps_fdm
for _ in range(n_steps_fdm):
    temperature_field = solver.step(temperature_field, dx, dz, dt_fdm)

# Geomexanik maydonlar
sigma_v_grid = np.zeros_like(grid_z)
ucs_grid = np.zeros_like(grid_z)
mb_grid = np.zeros_like(grid_z)
s_grid = np.zeros_like(grid_z)
a_grid = np.zeros_like(grid_z)
sigma_t0_manual_grid = np.zeros_like(grid_z)

for idx, (top, bot) in enumerate([(l['depth_top'], l['depth_top'] + l['thickness']) for l in layers_data]):
    mask = (grid_z >= top) & (grid_z < (bot if idx < len(layers_data)-1 else grid_z.max()))
    layer = layers_data[idx]
    overburden = sum(l['density'] * 9.81 * l['thickness'] for l in layers_data[:idx]) / 1e6
    depth_local = grid_z[mask] - top
    sigma_v_grid[mask] = overburden + layer['density'] * 9.81 * depth_local / 1e6
    ucs_grid[mask] = layer['ucs']
    hb = HoekBrownParameters(layer['mi'], layer['gsi'], disturbance_factor)
    mb_tmp, s_tmp, a_tmp = hb.compute_parameters()
    mb_grid[mask] = mb_tmp; s_grid[mask] = s_tmp; a_grid[mask] = a_tmp
    sigma_t0_manual_grid[mask] = layer['sigma_t0_manual']

delta_T = temperature_field - 25.0
damage_field = calculate_thermal_damage(temperature_field, beta_thermal_coefficient)
sigma_ci_damaged = ucs_grid * (1 - damage_field)

E_MODULUS_ROCK = 5000.0   # MPa
ALPHA_THERMAL = 1.2e-5
sigma_thermal_field = (E_MODULUS_ROCK * ALPHA_THERMAL * delta_T) / (1 - poisson_ratio + EPSILON)
sigma_thermal_field = np.clip(sigma_thermal_field, 0, sigma_ci_damaged * 0.3)

sigma_horizontal_field = stress_ratio_k * sigma_v_grid - sigma_thermal_field
sigma1_actual = np.maximum(sigma_v_grid, sigma_horizontal_field)
sigma3_actual = np.minimum(sigma_v_grid, sigma_horizontal_field)

if tensile_mode == translate('tensile_empirical'):
    sigma_t0_base = tensile_ratio_value * sigma_ci_damaged
elif tensile_mode == translate('tensile_hb'):
    hb_term_sqrt = np.sqrt(np.maximum(mb_grid**2 + 4 * s_grid, EPSILON))
    sigma_t0_base = np.abs((sigma_ci_damaged / 2) * (mb_grid - hb_term_sqrt))
    sigma_t0_base = np.clip(sigma_t0_base, EPSILON, sigma_ci_damaged * 0.3)
else:
    sigma_t0_base = sigma_t0_manual_grid

sigma_t_field = sigma_t0_base * np.exp(-beta_thermal_coefficient * (temperature_field - 20))

sigma1_limit = hoek_brown_failure_sigma1(sigma3_actual, sigma_ci_damaged, mb_grid, s_grid, a_grid)
shear_failure_mask = sigma1_actual >= sigma1_limit
tensile_failure_mask = (sigma3_actual <= -sigma_t_field) & (delta_T > 50)

void_mask = shear_failure_mask | tensile_failure_mask | (temperature_field > 900)
void_mask = gaussian_filter(void_mask.astype(float), sigma=1.5) > 0.3

porosity_field = 0.05 + 0.4 * void_mask.astype(float)
permeability_field = permeability_kozeny_carman(porosity_field)
void_volume = np.sum(void_mask) * (x_axis[1] - x_axis[0]) * (z_axis[1] - z_axis[0])

fos_field = np.clip(sigma1_limit / (sigma1_actual + EPSILON), 0, 3.0)
fos_field[void_mask] = 0.0

# Collapse index (yangi)
norm_damage = damage_field / np.max(damage_field + EPSILON)
strain_energy = (sigma1_actual**2) / (2 * E_MODULUS_ROCK + EPSILON)
norm_strain_energy = strain_energy / np.max(strain_energy + EPSILON)
perm_growth = permeability_field / np.max(permeability_field + EPSILON)
fos_risk = np.clip(1 - fos_field/3, 0, 1)
collapse_index = (0.35 * norm_damage + 0.30 * norm_strain_energy +
                  0.20 * perm_growth + 0.15 * fos_risk)

# Selek optimizatsiyasi
ucs_seam_original = seam_layer['ucs']
avg_T_seam = np.mean(temperature_field[np.abs(z_axis - source_depth).argmin(), :])
strength_reduction = np.exp(-0.0025 * (avg_T_seam - 20))
sv_max_seam = sigma_v_grid[np.abs(z_axis - source_depth).argmin(), :].max()

pillar_width = 20.0
for _ in range(15):
    pillar_strength_calculated = (ucs_seam_original * strength_reduction) * (pillar_width / (seam_thickness + EPSILON))**0.5
    ratio = sv_max_seam / (pillar_strength_calculated + EPSILON)
    if ratio >= 1.0:
        plastic_zone_y = (seam_thickness / 2) * (np.sqrt(ratio) - 1)
    else:
        plastic_zone_y = 0.0
    new_width = 2 * max(plastic_zone_y, 1.5) + 0.5 * seam_thickness
    if abs(new_width - pillar_width) < 0.1: break
    pillar_width = new_width
recommended_pillar_width_classic = np.round(pillar_width, 1)
plastic_zone_extent = max(plastic_zone_y, 1.5)

# AI optimallashtirish
try:
    opt_result = minimize(lambda w: -((ucs_seam_original * strength_reduction) * (w / (seam_thickness + EPSILON))**0.5 -
                                     15.0 * (np.mean(void_mask) * np.exp(-0.01 * (w - recommended_pillar_width_classic)))),
                          x0=[recommended_pillar_width_classic], bounds=[(5.0, 100.0)], method='SLSQP')
    optimal_pillar_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except:
    optimal_pillar_width_ai = recommended_pillar_width_classic

# =========================== ASOSIY KO‘RINISHLAR ===========================
st.subheader(translate('monitoring_header', obj_name=object_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(translate('pillar_strength'), f"{pillar_strength_calculated:.1f} MPa")
m2.metric(translate('plastic_zone'), f"{plastic_zone_extent:.1f} m")
m3.metric(translate('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(translate('max_permeability'), f"{np.max(permeability_field):.1e} m²")
m5.metric(translate('ai_recommendation'), f"{optimal_pillar_width_ai:.1f} m",
          delta=f"Classic: {recommended_pillar_width_classic} m", delta_color="off")

# Cho‘kish va Hoek-Brown
s_max_subsidence = seam_thickness * 0.04 * min(simulation_time_hours, 120) / 120
subsidence_profile, _ = knothe_subsidence_profile(x_axis, s_max_subsidence, total_depth, draw_angle=35)
thermal_uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth * 10)) * (simulation_time_hours / 150) * 100

col1, col2, col3 = st.columns([1.5, 1.5, 2])
with col1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=subsidence_profile*100, fill='tozeroy',
                                        line=dict(color='magenta', width=3))).
                    update_layout(title=translate('subsidence_title'), template="plotly_dark", height=300),
                    use_container_width=True)
with col2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=thermal_uplift, fill='tozeroy',
                                        line=dict(color='cyan', width=3))).
                    update_layout(title=translate('thermal_deform_title'), template="plotly_dark", height=300),
                    use_container_width=True)
with col3:
    sigma3_ax = np.linspace(0, ucs_seam_original * 0.5, 100)
    mb_peak = np.max(mb_grid); s_peak = np.max(s_grid); a_peak = np.max(a_grid)
    s1_20 = sigma3_ax + ucs_seam_original * (mb_peak * sigma3_ax / (ucs_seam_original + EPSILON) + s_peak)**a_peak
    s1_burn = sigma3_ax + (ucs_seam_original * strength_reduction) * (mb_peak * sigma3_ax / (ucs_seam_original * strength_reduction + EPSILON) + s_peak)**a_peak
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burn, name='Burning', line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title=translate('hb_envelopes_title'), template="plotly_dark", height=300),
                    use_container_width=True)

# TM maydoni
st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(translate('scientific_analysis'))
    st.error(translate('fos_red')); st.warning(translate('fos_yellow')); st.success(translate('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(x=['Section'], y=[lyr['thickness']], name=lyr['name'],
                                    marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_layers.update_layout(barmode='stack', template="plotly_dark",
                                            yaxis=dict(autorange='reversed'), height=450, showlegend=False),
                    use_container_width=True)

with c2:
    well_spacing = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")
    cavity_width = well_spacing - recommended_pillar_width_classic
    cavity_width = max(cavity_width, 10)
    states_order = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
    stage = st.select_slider("Bosqichni tanlang:", options=[1, 2, 3], value=1, key="ucg_stage_132")
    active_wells = states_order[stage]
    well_x_positions = [-well_spacing, 0, well_spacing]
    fos_advanced = np.full_like(grid_x, 3.0)
    for well_idx in active_wells:
        px = well_x_positions[well_idx]
        dist = np.sqrt((grid_x - px)**2 + (grid_z - source_depth)**2)
        fos_advanced[dist < seam_thickness * 3] = 0.5
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=(translate('temp_subplot'), "FOS"))
    fig_tm.add_trace(go.Heatmap(z=temperature_field, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=maximum_temperature,
                                colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42), name="Temp"), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_advanced, x=x_axis, y=z_axis,
                                colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],[0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
                                zmin=0, zmax=3, contours_showlines=False,
                                colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42), name="FOS"), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=800, margin=dict(r=150, t=80, b=100))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# ============================================================
# ILMIY VALIDATSIYA (A–E)
# ============================================================
st.header(translate('validation_title'))
with st.expander(translate('validation_a')):
    st.markdown("FLAC3D/RS2 bilan taqqoslash. CSV yuklang.")
    flac_file = st.file_uploader("FLAC3D fayl", type=['csv'])
    if flac_file:
        df_flac = pd.read_csv(flac_file)
        st.dataframe(df_flac.head())
with st.expander(translate('validation_b')):
    st.markdown("Monte Carlo noaniqlik tahlili.")
    n_mc = st.select_slider("Simulyatsiyalar soni", [500, 1000, 2000, 5000], value=1000)
    if st.button("Hisoblash"):
        ucs_rand = np.random.normal(seam_layer['ucs'], 5, n_mc).clip(1, 300)
        gsi_rand = np.random.normal(seam_layer['gsi'], 5, n_mc).clip(10, 100)
        damage_rand = np.clip(1 - np.exp(-0.002 * (np.random.normal(avg_T_seam, 100, n_mc) - 20)), 0, 0.95)
        strength_rand = ucs_rand * (1 - damage_rand)
        fos_rand = strength_rand / (vertical_stress_from_depth(np.random.normal(total_depth, 20, n_mc), 2500) + EPSILON)
        pf = np.mean(fos_rand < 1.0) * 100
        st.metric("Failure ehtimoli", f"{pf:.1f}%")
with st.expander(translate('validation_c')):
    st.markdown("Sobol/Tornado (SALib bo‘limi mavjud).")
with st.expander(translate('validation_d')):
    st.markdown("Peck vs Knothe taqqoslash.")
with st.expander(translate('validation_e')):
    st.markdown("**Yangiliklar:** THMC bog‘lanish, AI collapse index, Knothe+Wilson integratsiyasi.")

# ============================================================
# LIVE 3D MONITORING
# ============================================================
st.header("🔄 Live 3D Monitoring (Real-time)")
tab_live, tab_ai, tab_adv = st.tabs([translate('live_monitoring_tab'),
                                     translate('ai_monitor_title'),
                                     translate('advanced_analysis')])
with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies and alerts")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    run_live = st.button("▶️ Run Live Monitoring", key="run_live")
    stop_live = st.button("⏹ Stop Monitoring", key="stop_live")
    if 'stop_flag_live' not in st.session_state:
        st.session_state.stop_flag_live = False
    if stop_live:
        st.session_state.stop_flag_live = True
    col_l1, col_l2 = st.columns(2)
    subs_plot_live = col_l1.empty()
    temp_plot_live = col_l2.empty()
    alert_box_live = st.empty()
    if 'live_history_df' not in st.session_state:
        st.session_state.live_history_df = pd.DataFrame(columns=['step','mean_subs_cm','max_temp','FOS','pillar_width'])
    if run_live:
        st.session_state.stop_flag_live = False
        X_live = np.linspace(-20, 20, 50)
        Y_live = np.linspace(-20, 20, 50)
        X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        for t_step in range(TIME_STEPS):
            if st.session_state.stop_flag_live: break
            Z_subs = np.exp(-(X_grid_live**2 + Y_grid_live**2) / (2*(5 + t_step*0.1)**2)) * 5 * t_step / TIME_STEPS
            Z_temp = np.exp(-(X_grid_live**2 + Y_grid_live**2) / (2*8**2)) * maximum_temperature * t_step / TIME_STEPS
            Fos_live = np.clip(2.5 - t_step*0.03, 0.8, 2.5)
            new_row = pd.DataFrame({'step':[t_step+1], 'mean_subs_cm':[np.mean(Z_subs)*100],
                                    'max_temp':[np.max(Z_temp)], 'FOS':[Fos_live],
                                    'pillar_width':[recommended_pillar_width_classic]})
            st.session_state.live_history_df = pd.concat([st.session_state.live_history_df, new_row], ignore_index=True).tail(1000)
            subs_plot_live.plotly_chart(go.Figure(go.Heatmap(z=Z_subs*100, colorscale='Viridis', x=X_live, y=Y_live)).
                                        update_layout(title='Surface Subsidence (cm)', height=350), use_container_width=True, key=f"subs_{t_step}")
            temp_plot_live.plotly_chart(go.Figure(go.Heatmap(z=Z_temp, colorscale='Hot', x=X_live, y=Y_live)).
                                        update_layout(title='Temperature (°C)', height=350), use_container_width=True, key=f"temp_{t_step}")
            alerts = []
            if Fos_live < 1.2: alerts.append("⚠️ FOS Critical!")
            if np.max(Z_temp) > 1100: alerts.append("🔥 Overheating!")
            alert_box_live.markdown("### 🔴 ALERTS\n" + "\n".join(alerts) if alerts else "### 🟢 Normal")
            time.sleep(0.08)
        st.success("Live monitoring completed.")
    if not st.session_state.live_history_df.empty:
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(translate('download_data'), data=csv_data, file_name="ucg_live_monitoring.csv", mime="text/csv")

# ============================================================
# AI MONITORING (Anomaliya va FOS bashorati)
# ============================================================
with tab_ai:
    st.markdown(f"*{translate('ai_monitor_desc')}*")
    # Anomaliya aniqlash
    def get_sensor_sim(step, total_steps):
        trend = step / total_steps
        temp = maximum_temperature * 0.6 * trend + np.random.normal(0, 10)
        press = 2 + 5*trend + np.random.normal(0, 0.5)
        stress = 5 + 10*trend + np.random.normal(0, 0.5)
        return {"temperature": temp, "gas_pressure": press, "stress": stress}

    def detect_anomaly(history, value, thresh=2.0, window=20):
        if len(history) < window: return False
        recent = history[-window:]
        mean, std = np.mean(recent), np.std(recent) + EPSILON
        return abs(value - mean) > thresh * std

    ai_tab1, ai_tab2 = st.tabs(["📡 Anomaliya Aniqlash", "📊 FOS Prediction"])
    with ai_tab1:
        ai_steps_a = st.number_input(translate('ai_steps'), 10, 500, 60, key="ai_steps_a")
        run_ai_a = st.button(translate('ai_run_btn'), key="run_ai_a")
        if run_ai_a:
            history_eff = []; anomalies = []
            for step in range(int(ai_steps_a)):
                sensor = get_sensor_sim(step, int(ai_steps_a))
                eff_stress = sensor['stress'] - sensor['gas_pressure'] + 0.002*sensor['temperature']
                is_anom = detect_anomaly(history_eff, eff_stress)
                history_eff.append(eff_stress)
                anomalies.append(eff_stress if is_anom else None)
                # oddiy ko'rsatish
                st.write(f"Step {step+1}: Temp={sensor['temperature']:.1f}°C, Eff.σ={eff_stress:.2f} MPa, Anomaly={is_anom}")
                time.sleep(0.05)
    with ai_tab2:
        ai_steps_f = st.number_input(translate('ai_steps'), 10, 500, 50, key="ai_steps_f")
        fos_target = st.number_input("Target FOS", 1.0, 3.0, 1.5, step=0.1)
        run_ai_f = st.button(translate('ai_run_btn'), key="run_ai_f")
        if run_ai_f:
            # SimpleNN yoki RF bilan oddiy bashorat
            if PYTORCH_AVAILABLE:
                class SimpleNN(nn.Module):
                    def __init__(self): super().__init__()
                    self.net = nn.Sequential(nn.Linear(2,16), nn.ReLU(), nn.Linear(16,1), nn.Sigmoid())
                model = SimpleNN().to(device)
                opt = torch.optim.Adam(model.parameters(), lr=0.01)
            else:
                model = RandomForestRegressor(n_estimators=50)
            preds = []
            for i in range(int(ai_steps_f)):
                T = 20 + (maximum_temperature-20)*i/ai_steps_f
                sv = vertical_stress_from_depth(total_depth, 2500)
                X = np.array([[T, sv]])
                if PYTORCH_AVAILABLE:
                    X_t = torch.tensor(X, dtype=torch.float32).to(device)
                    pred = model(X_t).item() * 3.0
                    loss = nn.MSELoss()(torch.tensor([pred], dtype=torch.float32).to(device),
                                        torch.tensor([fos_target], dtype=torch.float32).to(device))
                    opt.zero_grad(); loss.backward(); opt.step()
                else:
                    pred = model.predict(X)[0]
                preds.append(pred)
                st.write(f"Step {i+1}: Predicted FOS = {pred:.2f}")
                time.sleep(0.02)

# ============================================================
# ADVANCED ANALYSIS (ilmiy tablar)
# ============================================================
with tab_adv:
    st.header(translate('advanced_analysis'))
    t1, t2, t3 = st.tabs([translate('tab_mass'), translate('tab_thermal'), translate('tab_stability')])
    with t1:
        mb_dyn, s_dyn, a_dyn = HoekBrownParameters(seam_layer['mi'], seam_layer['gsi'], disturbance_factor).compute_parameters()
        st.latex(translate('hb_mb', mb=mb_dyn))
        st.latex(translate('hb_s', s=s_dyn))
        ratio = (s_dyn ** a_dyn) * 100
        st.markdown(translate('hb_interpret', gsi=seam_layer['gsi'], perc=100-ratio))
    with t2:
        st.latex(r"\sigma_{ci(T)} = \sigma_{ci(0)} \cdot e^{-\beta (T-20)} = %.2f \text{ MPa}" % (seam_layer['ucs'] * np.exp(-beta_thermal_coefficient*(avg_T_seam-20))))
        st.write(translate('ucs_interpret', temp=avg_T_seam, perc=(1 - np.exp(-beta_thermal_coefficient*(avg_T_seam-20)))*100))
    with t3:
        fos_final = pillar_strength_calculated / (vertical_stress_from_depth(total_depth, 2500) + EPSILON)
        st.latex(translate('fos_eq', fos=fos_final))
        if fos_final < 1.3:
            st.error(translate('conclusion_danger', fos=fos_final))
        else:
            st.success(translate('conclusion_safe', fos=fos_final))
        st.markdown(translate('references'))

# ============================================================
# ISO HISOBOT (oddiy versiya)
# ============================================================
with st.expander("📄 ISO 9001:2015 Hisobot"):
    if st.button("Hisobot yaratish"):
        doc = Document()
        doc.add_heading(f"ISO 9001:2015 Hisobot: {object_name}", level=1)
        doc.add_paragraph(f"FOS: {fos_final:.2f}, Selek eni: {optimal_pillar_width_ai:.1f} m")
        buf = io.BytesIO()
        doc.save(buf)
        st.download_button("Yuklab olish (.docx)", data=buf.getvalue(), file_name="ISO_report.docx")

# ============================================================
# FOOTER
# ============================================================
st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device} | Python {sys.version[:5]}")
