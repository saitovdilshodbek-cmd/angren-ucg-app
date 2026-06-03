import streamlit as st
st.set_page_config(page_title="UCG SCI-Grade Platform", layout="wide", initial_sidebar_state="expanded")
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.stats import linregress, t as t_dist
import io
import time
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import qrcode
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import logging
from scipy.signal import savgol_filter
import hashlib
from dataclasses import dataclass
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    PT_AVAILABLE = False
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

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
if PT_AVAILABLE:
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(RANDOM_SEED)

EPS = 1e-6
GEOM_EPS = 1e-3
T_REF_AMBIENT = 20.0

WILSON_C1 = 0.64
WILSON_C2 = 0.36

if "language" not in st.session_state:
    st.session_state.language = "uz"
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "live_history_df" not in st.session_state:
    st.session_state.live_history_df = pd.DataFrame(columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m'])

@dataclass(frozen=True)
class UCGPhysicsParams:
    phi_deg: float = 35.0
    cohesion: float = 5e6
    alpha_thermal: float = 3e-5
    gas_temp: int = 1100
    subsidence_rate: float = 0.012
    thermal_damage_beta: float = 0.002
    extraction_ratio: float = 0.6
    E_mass: float = 25e9
    CONFINEMENT: float = 0.65
    RELAX: float = 0.15
    THERMAL_DIFFUSIVITY: float = 8.5e-7
    GAS_VISCOSITY: float = 3e-5
    MOLAR_MASS_GAS: float = 0.028
    R_UNIVERSAL: float = 8.314
    K_VOID: float = 0.35
    CREEP_A: float = 0.05
    CREEP_N: float = 0.3

PARAMS = UCGPhysicsParams()

APP_URL = os.environ.get("UCG_APP_URL", "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/")

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
        'thermal_decay_label': "Termal Degradatsiya (β):",
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
        'warning_pytorch': "⚠️ PyTorch o'rnatilmagan. RandomForestClassifier ishlatiladi.",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastik zona (y)",
        'cavity_volume': "Kamera Hajmi",
        'max_permeability': "Maks. O'tkazuvchanlik",
        'ai_recommendation': "Analitik Tavsiya (Selek)",
        'monitoring_header': "📊 {obj_name}: Monitoring va Ekspert Xulosasi",
        'subsidence_title': "📉 Yer yuzasi cho'kishi (cm)",
        'thermal_deform_title': "🔥 Gorizontal siljish (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Ilmiy Tahlil",
        'fos_red': "🔴 FOS < 1.0: Failure",
        'fos_yellow': "🟡 FOS 1.0–1.5: Unstable",
        'fos_green': "🟢 FOS > 1.5: Stable",
        'tm_field_title': "🔥 TM Maydoni va Selek Interferensiyasi",
        'temp_subplot': "Harorat Maydoni (°C) + Gaz Oqimi",
        'fos_subplot': "FOS + AI Collapse Prediction (NN) + Yielded Zones",
        'gas_flow': "Gaz oqimi",
        'shear': "Shear",
        'tensile': "Tensile",
        'ai_collapse': "AI Collapse (NN)",
        'monitoring_panel': "📊 {obj_name}: Kompleks Monitoring Paneli",
        'pillar_live': "Pillar Strength",
        'rec_width_live': "Tavsiya: Selek Eni",
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
        'dip_angle_label': "Qatlam qiyaligi (Dip - °)",
        'timeline_table': """
| Bosqich | Vaqti | Tavsif |
|---------|-------|--------|
| **Rejalashtirish** | 2026-04-01 | Validatsiya, xavfsiz bo'lish funksiyalarini ishlab chiqish |
| **Modellarni optimallashtirish** | 2026-05-15 | NN/RF testlash, FDM yaxshilash, keshlashtirish |
| **Integratsiya va testlash** | 2026-06-30 | Unit testlar, yakuniy vizualizatsiya, deploy |
        """,
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Monitoring ma'lumotlarini yuklab olish (CSV)",
        'well_config': "Quduqlar konfiguratsiyasi",
        'well_distance': "Quduqlar orasidagi masofa (m):",
        'warning_cavity_width': "Ogohlantirish: Selek kengligi quduqlar masofasidan katta. cavity_width=1m deb olindi.",
        'ucg_stages_title': "UCG Yonish Bosqichlari (1-2-3 sxemasi) – Yangi Ilmiy Model",
        'select_stage': "Bosqichni tanlang:",
        'geomech_state': "Geomexanik Holat (Yangi Ilmiy Model)",
        'auto_animation': "Avtomatik animatsiya (1→2→3 bosqichlar)",
        'animation_done': "Animatsiya yakunlandi.",
        'pillar_annotation': "HIMOYA SELEGI (PILLAR)",
        'system_entropy': "Tizim entropiyasi (noaniqlik)",
        'pin_approx': "**Eslatma:** Kirsch yechimi kvazistatik yaqinlashuv. Katta deformatsiyalar uchun FEM remeshing talab qilinadi.",
        'phase_field_info': "**Fazaviy maydon modeli (Bourdin et al., 2000 asosida):**",
        'uq_info': "Noaniqlik miqdoriy tahlili (Monte-Carlo):",
        'shap_info': "SHAP interpretatsiyasi (Lundberg & Lee, 2017):",
        'sobol_info': "Global sezgirlik (Sobol', 2001):",
        'lhs_info': "Latin Hypercube Sampling (McKay, 1979):",
        'validation_info': "Eksperimental validatsiya:",
        'experimental_note': "CSV faylida 'x' (m) va 'subsidence_cm' ustunlari bo'lishi shart.",
        'case_study_title': "🏭 UCG Case Studies: Model Verification",
        'gas_risk_title': "🛢️ Gaz ko'chish xavfi xaritasi",
        'water_risk_title': "💧 Suv bosish xavfi",
        'uncertainty_title': "📏 Analitik noaniqlik tarqalishi",
        'creep_info': "⏳ Piller Creep (vaqt bo'yicha pasayish)",
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
        'thermal_decay_label': "Thermal Degradation (β):",
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
        'warning_pytorch': "⚠️ PyTorch not installed. Using RandomForestClassifier.",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastic zone (y)",
        'cavity_volume': "Cavity Volume",
        'max_permeability': "Max Permeability",
        'ai_recommendation': "Analytical Recommendation (Pillar)",
        'monitoring_header': "📊 {obj_name}: Monitoring and Expert Summary",
        'subsidence_title': "📉 Surface subsidence (cm)",
        'thermal_deform_title': "🔥 Horizontal displacement (cm)",
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
        'dip_angle_label': "Dip angle (°)",
        'timeline_table': """
| Stage | Time | Description |
|-------|------|-------------|
| **Planning** | 2026-04-01 | Validation, develop safety functions |
| **Model optimization** | 2026-05-15 | NN/RF testing, FDM improvement, caching |
| **Integration & testing** | 2026-06-30 | Unit tests, final visualization, deploy |
        """,
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Download monitoring data (CSV)",
        'well_config': "Well Configuration",
        'well_distance': "Distance between wells (m):",
        'warning_cavity_width': "Warning: Pillar width exceeds well distance. cavity_width set to 1m.",
        'ucg_stages_title': "UCG Burning Stages (1-2-3 scheme) – New Scientific Model",
        'select_stage': "Select stage:",
        'geomech_state': "Geomechanical State (New Scientific Model)",
        'auto_animation': "Auto animation (1→2→3 stages)",
        'animation_done': "Animation finished.",
        'pillar_annotation': "PROTECTIVE PILLAR",
        'system_entropy': "System entropy (uncertainty)",
        'pin_approx': "**Note:** Kirsch solution is quasi-static. FEM remeshing required for large deformations.",
        'phase_field_info': "**Phase-field model (based on Bourdin et al., 2000):**",
        'uq_info': "Uncertainty Quantification (Monte-Carlo):",
        'shap_info': "SHAP interpretation (Lundberg & Lee, 2017):",
        'sobol_info': "Global sensitivity (Sobol', 2001):",
        'lhs_info': "Latin Hypercube Sampling (McKay, 1979):",
        'validation_info': "Experimental validation:",
        'experimental_note': "CSV must contain 'x' (m) and 'subsidence_cm' columns.",
        'case_study_title': "🏭 UCG Case Studies: Model Verification",
        'gas_risk_title': "🛢️ Gas Migration Risk Map",
        'water_risk_title': "💧 Water Inrush Risk",
        'uncertainty_title': "📏 Analytical Uncertainty Propagation",
        'creep_info': "⏳ Pillar Creep (time-dependent reduction)",
    },
    'ru': {
        'app_title': "Универсальный мониторинг деформаций поверхности",
        'app_subtitle': "Термомеханический (TM) анализ и оптимизация размеров целиков",
        'sidebar_header_params': "⚙️ Общие параметры",
        'formula_show': "Показать формулы:",
        'project_name': "Название проекта:",
        'process_time': "Время процесса (часы):",
        'num_layers': "Количество слоёв:",
        'tensile_model': "Модель растяжения:",
        'rock_props': "💎 Свойства породы",
        'disturbance': "Фактор нарушенности (D):",
        'poisson': "Коэффициент Пуассона (ν):",
        'stress_ratio': "Соотношение напряжений (k = σh/σv):",
        'tensile_params': "📐 Растяжение и целик",
        'thermal_decay_label': "Термическая деградация (β):",
        'combustion': "🔥 Горение и термическое воздействие",
        'burn_duration': "Продолжительность горения (часы):",
        'max_temp': "Максимальная температура (°C)",
        'timeline': "📅 Хронология проекта",
        'layer_params': "Параметры слоя {num}",
        'layer_name': "Название:",
        'thickness': "Толщина (м):",
        'ucs': "UCS (МПа):",
        'density': "Плотность (кг/м³):",
        'color': "Цвет:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (МПа):",
        'error_thick_positive': "Толщина должна быть >0",
        'error_ucs_positive': "UCS должен быть >0 МПа",
        'error_density_positive': "Плотность должна быть >0 кг/м³",
        'error_gsi_range': "GSI должен быть в пределах 10...100",
        'error_mi_positive': "mi должен быть >0",
        'error_min_layers': "❌ Требуется хотя бы 1 слой!",
        'warning_pytorch': "⚠️ PyTorch не установлен. Используется RandomForestClassifier.",
        'pillar_strength': "Прочность целика (σp)",
        'plastic_zone': "Пластическая зона (y)",
        'cavity_volume': "Объём полости",
        'max_permeability': "Макс. проницаемость",
        'ai_recommendation': "Аналитическая рекомендация (Целик)",
        'monitoring_header': "📊 {obj_name}: Мониторинг и экспертное заключение",
        'subsidence_title': "📉 Оседание поверхности (см)",
        'thermal_deform_title': "🔥 Горизонтальное смещение (см)",
        'hb_envelopes_title': "🛡️ Огибающие Хука-Брауна",
        'scientific_analysis': "📋 Научный анализ",
        'fos_red': "🔴 FOS < 1.0: Разрушение",
        'fos_yellow': "🟡 FOS 1.0–1.5: Неустойчивость",
        'fos_green': "🟢 FOS > 1.5: Стабильность",
        'tm_field_title': "🔥 ТМ поле и интерференция целиков",
        'temp_subplot': "Температурное поле (°C) + Газовый поток",
        'fos_subplot': "FOS + Прогноз обрушения ИИ (NN) + Зоны пластичности",
        'gas_flow': "Газовый поток",
        'shear': "Сдвиг",
        'tensile': "Растяжение",
        'ai_collapse': "ИИ обрушение (NN)",
        'monitoring_panel': "📊 {obj_name}: Комплексная панель мониторинга",
        'pillar_live': "Прочность целика",
        'rec_width_live': "Рек. ширина целика",
        'max_subsidence_live': "Макс. оседание",
        'process_stage': "Стадия процесса",
        'stage_active': "Активная",
        'stage_cooling': "Остывание",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'ai_monitor_desc': "Данные датчиков в реальном времени и обнаружение аномалий",
        'ai_steps': "Количество шагов симуляции:",
        'ai_run_btn': "▶️ Запустить AI мониторинг",
        'ai_stop_btn': "⏹ Стоп",
        'advanced_analysis': "🔍 Углубленный динамический анализ и методологическое обоснование",
        'tab_mass': "🏗️ Параметры массива",
        'tab_thermal': "🔥 Термическая деградация",
        'tab_stability': "⚖️ Устойчивость и источники",
        'hb_class': "1. Классификация Хука-Брауна (2018)",
        'hb_mb': "m_b = {mb:.3f}",
        'hb_s': "s = {s:.4f}",
        'hb_caption_mb': "Функция угла трения массива (m_i={mi})",
        'hb_caption_s': "Степень трещиноватости (GSI={gsi})",
        'hb_interpret': "**Научный комментарий:** Согласно Хуку и Брауну (2018), GSI={gsi} означает, что прочность массива на **{perc:.1f}%** ниже лабораторных значений.",
        'thermal_params': "2. Анализ термомеханических коэффициентов",
        'param_table_param': "Параметр",
        'param_table_value': "Значение",
        'param_table_reason': "Обоснование",
        'modulus': "Модуль упругости (E)",
        'alpha': "Тепловое расширение (α)",
        'temp0': "Начальная T₀",
        'modulus_reason': "Типичный средний коэффициент деформации угля.",
        'alpha_reason': "Коэффициент линейного теплового расширения угля (Yang, 2010).",
        'temp0_reason': "Начальная естественная температура угольного пласта.",
        'ucs_decay': "**A) Снижение UCS от температуры:**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ МПа}}",
        'ucs_interpret': "**Интерпретация:** При {temp}°C прочность породы снизилась на {perc:.1f}%.",
        'thermal_stress': "**B) Термическое напряжение ($\\sigma_{{th}}$):**",
        'thermal_stress_eq': r"\sigma_{{th}} \approx \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ МПа}}",
        'pillar_stability': "3. Устойчивость целика и библиография",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v}} = {fos:.2f}",
        'pillar_wilson': "**Согласно теории Wilson (1972):** При ширине целика $w={w}$ м, центральное ядро выдерживает геостатическую нагрузку {sv:.2f} МПа. Пластическая зона: $y = {y:.1f}$ м.",
        'references': "#### 📚 Основные научные источники:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*.",
        'conclusion_danger': "🔴 **Научное заключение:** FOS={fos:.2f}. Высокая термическая деградация. Рекомендуется увеличить ширину целика или контролировать скорость газификации.",
        'conclusion_safe': "🟢 **Научное заключение:** FOS={fos:.2f}. Выбранные параметры обеспечивают устойчивость массива.",
        'methodology_expander': "📚 Научная методология и ссылки (PhD Research)",
        'tensile_empirical': "Эмпирический (UCS)",
        'tensile_hb': "На основе HB (авто)",
        'tensile_manual': "Ручной ввод",
        'dip_angle_label': "Угол падения пласта (°)",
        'timeline_table': """
| Этап | Время | Описание |
|-------|------|-------------|
| **Планирование** | 2026-04-01 | Валидация, разработка функций безопасности |
| **Оптимизация моделей** | 2026-05-15 | Тестирование NN/RF, улучшение FDM, кэширование |
| **Интеграция и тестирование** | 2026-06-30 | Юнит-тесты, финальная визуализация, развертывание |
        """,
        'live_monitoring_tab': "🔄 Живой 3D мониторинг",
        'download_data': "📥 Скачать данные мониторинга (CSV)",
        'well_config': "Конфигурация скважин",
        'well_distance': "Расстояние между скважинами (м):",
        'warning_cavity_width': "Предупреждение: ширина целика превышает расстояние между скважинами. cavity_width=1м.",
        'ucg_stages_title': "Стадии горения UCG (схема 1-2-3) – Новая научная модель",
        'select_stage': "Выберите стадию:",
        'geomech_state': "Геомеханическое состояние (Новая научная модель)",
        'auto_animation': "Авто анимация (1→2→3 стадии)",
        'animation_done': "Анимация завершена.",
        'pillar_annotation': "ЗАЩИТНЫЙ ЦЕЛИК",
        'system_entropy': "Системная энтропия (неопределённость)",
        'pin_approx': "**Примечание:** решение Кирша квазистатическое. Для больших деформаций требуется перестройка сетки МКЭ.",
        'phase_field_info': "**Фазовая модель поля (основана на Bourdin и др., 2000):**",
        'uq_info': "Количественная оценка неопределённости (Монте-Карло):",
        'shap_info': "Интерпретация SHAP (Lundberg & Lee, 2017):",
        'sobol_info': "Глобальная чувствительность (Соболь, 2001):",
        'lhs_info': "Латинский гиперкуб (McKay, 1979):",
        'validation_info': "Экспериментальная валидация:",
        'experimental_note': "CSV должен содержать столбцы 'x' (м) и 'subsidence_cm'.",
        'case_study_title': "🏭 UCG Case Studies: Проверка модели",
        'gas_risk_title': "🛢️ Карта риска миграции газа",
        'water_risk_title': "💧 Риск прорыва воды",
        'uncertainty_title': "📏 Аналитическое распространение неопределенности",
        'creep_info': "⏳ Ползучесть целика (снижение со временем)",
    }
}

FORMULA_OPTIONS = {
    'uz': ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"],
    'en': ["Close", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"],
    'ru': ["Закрыть", "1. Разрушение Хука-Брауна (2018)", "2. Термическое повреждение и проницаемость",
           "3. Термическое напряжение и растяжение", "4. Целик и оседание"]
}

def translate(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

t = translate

def von_mises_stress(sigma_x, sigma_z, tau_xz, nu=None):
    if nu is not None:
        sigma_y = nu * (sigma_x + sigma_z)
    else:
        sigma_y = sigma_z
    return np.sqrt(np.maximum(sigma_x**2 - sigma_x*sigma_y + sigma_y**2 + 3*tau_xz**2, 0.0))

def hoek_brown_params(gsi, mi, D):
    mb = mi * np.exp((gsi - 100.0) / (28.0 - 14.0 * D))
    if isinstance(gsi, (int, float)):
        if gsi > 25:
            s = np.exp((gsi - 100.0) / (9.0 - 3.0 * D))
        else:
            s = 0.0
    else:
        s = np.where(np.asarray(gsi) > 25,
                     np.exp((np.asarray(gsi) - 100.0) / (9.0 - 3.0 * D)),
                     0.0)
    a = 0.5 + (1.0/6.0) * (np.exp(-np.asarray(gsi)/15.0) - np.exp(-20.0/3.0))
    return mb, s, a

def hoek_brown(sigma3, sigma_ci, mb, s, a):
    sigma3_eff = np.maximum(sigma3, 0.0)
    term = mb * (sigma3_eff / (sigma_ci + EPS)) + s
    term = np.maximum(term, 0.0)
    sigma1 = sigma3_eff + sigma_ci * term**a
    return sigma1

def compute_demand_capacity_ratio(sigma1_applied, sigma3_confining, sigma_ci, mb, s, a):
    sigma3_eff = np.maximum(sigma3_confining, 0.0)
    sigma1_failure = sigma3_eff + sigma_ci * (np.maximum(mb * (sigma3_eff / (sigma_ci + EPS)) + s, 0.0) ** a)
    return sigma1_applied / (sigma1_failure + EPS)

def thermal_damage(T, beta, T_ref=T_REF_AMBIENT):
    return 1.0 - np.exp(-beta * np.maximum(T - T_ref, 0.0))

def apply_thermal_degradation(ucs0, T, beta):
    dmg = thermal_damage(T, beta)
    ucs_T = ucs0 * (1 - dmg)
    return np.clip(ucs_T, 0.5, None)

def thermal_conductivity(T, k0=2.5):
    k = k0 * (1 - 0.0004 * (T - T_REF_AMBIENT))
    return np.clip(k, 0.5, None)

def specific_heat(T):
    cp = 960 + 0.14 * T
    return np.clip(cp, 900, 2200)

def density_temperature(rho0, T):
    T_clamped = np.clip(T, T_REF_AMBIENT, 1200.0)
    alpha_v = 3.6e-5
    rho_T = rho0 * (1.0 - alpha_v * (T_clamped - T_REF_AMBIENT))
    return np.clip(rho_T, 0.80 * rho0, rho0)

def young_modulus_temperature(T, E0=None):
    E0_val = E0 if E0 is not None else PARAMS.E_mass
    c_E = 0.0018
    E_T = E0_val * np.exp(-c_E * np.maximum(T - T_REF_AMBIENT, 0.0))
    return np.clip(E_T, 0.10 * E0_val, E0_val)

def thermal_expansion_temperature(T):
    T = np.clip(T, T_REF_AMBIENT, 1200)
    alpha_T = PARAMS.alpha_thermal * (1 + 0.002 * (T - T_REF_AMBIENT) + 1e-6 * (T - T_REF_AMBIENT)**2)
    return alpha_T

def vertical_stress(depth, density):
    return density * 9.81 * depth / 1e6

def solve_heat_equation_dynamic(T, Q, rho_field, cp_field, k_field, dx, dz, total_time, T_air, h=10.0):
    alpha_field = k_field / (rho_field * cp_field)
    alpha_max = np.max(alpha_field)
    dt_max = 1.0 / (2 * alpha_max * (1/dx**2 + 1/dz**2))
    dt_candidate = 0.8 * dt_max
    n_steps = max(int(np.ceil(total_time / dt_candidate)), 1)
    dt = total_time / n_steps
    if dt > dt_max * 1.01:
        dt = dt_max * 0.99
        n_steps = max(int(np.ceil(total_time / dt)), 1)
        dt = total_time / n_steps
    for _ in range(n_steps):
        T_old = T.copy()
        Txx = (T_old[1:-1, 2:] - 2 * T_old[1:-1, 1:-1] + T_old[1:-1, :-2]) / dx**2
        Tzz = (T_old[2:, 1:-1] - 2 * T_old[1:-1, 1:-1] + T_old[:-2, 1:-1]) / dz**2
        T_new = T_old.copy()
        T_new[1:-1, 1:-1] = (T_old[1:-1, 1:-1] +
                              dt * (alpha_field[1:-1, 1:-1] * (Txx + Tzz) +
                                    Q[1:-1, 1:-1] / (rho_field[1:-1, 1:-1] * cp_field[1:-1, 1:-1])))
        T_new[:, 0] = T_new[:, 1]
        T_new[:, -1] = T_new[:, -2]
        T_new[-1, :] = T_new[-2, :]
        k_surface = k_field[0, :]
        T_new[0, :] = (k_surface * T_new[1, :] + dz * h * T_air) / (k_surface + dz * h)
        T = T_new.copy()
    return T

def principal_stresses(sx, sy, txy):
    avg = (sx + sy) / 2
    radius = np.sqrt(((sx - sy) / 2) ** 2 + txy ** 2)
    s1 = avg + radius
    s2 = avg - radius
    return s1, s2

def evolving_cavity_radius(time_h, T_field, beta, grid_z, source_z, H_seam):
    source_mask = np.abs(grid_z - source_z) < 1.5 * H_seam
    if not np.any(source_mask):
        return 5.0
    T_source = T_field[source_mask]
    thermal_dam_local = thermal_damage(T_source, beta)
    growth_rate = 0.015 * np.mean(thermal_dam_local)
    radius = 5.0 + growth_rate * time_h
    return float(np.clip(radius, 5.0, 40.0))

def kirsch_stress_field(x, z, sigma_H, sigma_h, cavity_radius, pore_pressure=0.0):
    r = np.sqrt(x**2 + z**2)
    r = np.maximum(r, cavity_radius + GEOM_EPS)
    theta = np.arctan2(z, x)
    a2_r2 = (cavity_radius**2) / (r**2)
    a4_r4 = (cavity_radius**4) / (r**4)
    sigma_rr = ((sigma_H + sigma_h)/2 * (1 - a2_r2) +
                (sigma_H - sigma_h)/2 * (1 - 4*a2_r2 + 3*a4_r4) * np.cos(2*theta))
    sigma_tt = ((sigma_H + sigma_h)/2 * (1 + a2_r2) -
                (sigma_H - sigma_h)/2 * (1 + 3*a4_r4) * np.cos(2*theta))
    tau_rt = -(sigma_H - sigma_h)/2 * (1 + 2*a2_r2 - 3*a4_r4) * np.sin(2*theta)
    sigma_rr -= pore_pressure
    sigma_tt -= pore_pressure
    return sigma_rr, sigma_tt, tau_rt

def pore_pressure_field(T, depth, water_table=20.0, rho_water=1000.0):
    h_water = np.maximum(depth - water_table, 0.0)
    P_hydro = rho_water * 9.81 * h_water / 1e6
    T_kelvin = np.maximum(T + 273.15, 293.15)
    P_gas = (101325.0 * T_kelvin / 293.15) / 1e6
    return P_hydro + P_gas

def monte_carlo_fos(ucs_mean, ucs_std, gsi_mean, gsi_std, mi_val, D, T_avg, H_seam, depth, density, rec_width, beta_th, n_sim=1000, random_seed=RANDOM_SEED):
    rng = np.random.default_rng(seed=random_seed)
    cov = np.array([[ucs_std**2, 0.3*ucs_std*gsi_std],
                    [0.3*ucs_std*gsi_std, gsi_std**2]])
    min_eig = np.min(np.linalg.eigvalsh(cov))
    if min_eig < 0:
        cov -= np.eye(2) * min_eig * 1.01
    samples = rng.multivariate_normal([ucs_mean, gsi_mean], cov, n_sim)
    ucs_samples = samples[:, 0]
    gsi_samples = np.clip(samples[:, 1], 10, 100)
    fos = []
    for ucs, gsi in zip(ucs_samples, gsi_samples):
        mb, s, a = hoek_brown_params(gsi, mi_val, D)
        ucs_T = apply_thermal_degradation(ucs, T_avg, beta_th)
        sigma_cm = ucs_T * (s ** a)
        pillar_strength = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS))
        sv = density * 9.81 * depth / 1e6
        fos_val = np.clip(pillar_strength / (sv + EPS), 0, 3)
        fos.append(fos_val)
    fos = np.array(fos)
    pf = np.mean(fos < 1.0)
    return fos, pf

def _array_hash(*arrays) -> str:
    h = hashlib.md5()
    for arr in arrays:
        h.update(arr.tobytes())
        h.update(str(arr.shape).encode())
    return h.hexdigest()

@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape):
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
    z_axis = np.linspace(0, total_depth + 50, grid_shape[0])
    dx = x_axis[1] - x_axis[0]
    dz = z_axis[1] - z_axis[0]
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
    temp_2d = np.full_like(grid_x, 25.0)
    rho_field = np.full_like(temp_2d, 1400.0)
    cp_field = specific_heat(temp_2d)
    k_field = thermal_conductivity(temp_2d)
    total_time = max(burn_duration, time_h) * 3600
    sources = [
        {'x0': -total_depth/3, 'start': 0, 'moving': False},
        {'x0': 0, 'start': 40, 'moving': True, 'v': 0.02},
        {'x0': total_depth/3, 'start': 80, 'moving': False}
    ]
    current_time_h = 0.0
    time_step = 3600.0
    n_steps = max(int(total_time / time_step), 1)
    time_step = total_time / n_steps
    source_mask_local = np.abs(grid_z - source_z) < 10.0
    if np.any(source_mask_local):
        rho_cp_ref = np.mean((rho_field * cp_field)[source_mask_local])
    else:
        rho_cp_ref = 1400.0 * 960.0
    for step in range(n_steps):
        current_time_h += time_step / 3600.0
        Q_source = np.zeros_like(temp_2d)
        for src in sources:
            if current_time_h <= src['start']:
                continue
            dt_sec = (current_time_h - src['start']) * 3600
            if src['moving']:
                x_center = src['x0'] + src['v'] * dt_sec
            else:
                x_center = src['x0']
            elapsed = current_time_h - src['start']
            if elapsed <= burn_duration:
                curr_T = T_source_max
            else:
                curr_T = 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration))
            pen_depth = np.sqrt(4 * PARAMS.THERMAL_DIFFUSIVITY * max(dt_sec, 3600)) + 15
            dist_sq = (grid_x - x_center)**2 + (grid_z - source_z)**2
            dt_source = 3600.0
            Q_source += rho_cp_ref * (curr_T - 25) / dt_source * np.exp(-dist_sq / (pen_depth**2))
        temp_2d = solve_heat_equation_dynamic(
            T=temp_2d, Q=Q_source, rho_field=rho_field, cp_field=cp_field,
            k_field=k_field, dx=dx, dz=dz, total_time=time_step, T_air=25.0
        )
    return temp_2d, x_axis, z_axis, grid_x, grid_z

def subsidence_inclined_seam(depth, dip_deg, phi_deg):
    dip_rad = np.radians(dip_deg)
    phi_rad = np.radians(phi_deg)
    shift = depth * np.tan(dip_rad) * np.tan(phi_rad/2)
    return shift

def pillar_creep_strength(sigma_p0, time_h, A_creep=PARAMS.CREEP_A, n_creep=PARAMS.CREEP_N):
    reduction = A_creep * (time_h ** n_creep)
    reduction = min(reduction, 0.40)
    return sigma_p0 * (1.0 - reduction)

def gas_migration_risk(T_field, perm_field, fos_field):
    T_threshold = 300.0
    perm_threshold = 1e-14
    thermal_path = T_field > T_threshold
    perm_path = perm_field > perm_threshold
    structural_fail = fos_field < 1.5
    risk = (thermal_path & perm_path & structural_fail).astype(float)
    return gaussian_filter(risk, sigma=2.0)

def water_inrush_risk(void_volume, aquifer_depth, depth_seam, fos_min):
    height_to_aquifer = abs(aquifer_depth - depth_seam)
    h_critical = 0.0015 * void_volume**0.5
    if height_to_aquifer < h_critical and fos_min < 1.2:
        return "CRITICAL", 0.9
    elif height_to_aquifer < h_critical * 1.5:
        return "HIGH", 0.6
    else:
        return "LOW", 0.1

def propagate_uncertainty_analytical(ucs_mean, ucs_cov, gsi_mean, gsi_cov, T_mean, T_cov, H_seam, rec_width):
    eps = 0.01
    def quick_fos(u, g, t, h, w):
        mb, s, a = hoek_brown_params(g, 10, 0.7)
        u_T = apply_thermal_degradation(u, t, PARAMS.thermal_damage_beta)
        sigma_cm = u_T * (s ** a)
        p_strength = sigma_cm * (WILSON_C1 + WILSON_C2 * w / (h + EPS))
        sv = 2500 * 9.81 * 200 / 1e6
        return p_strength / (sv + EPS)
    fos_base = quick_fos(ucs_mean, gsi_mean, T_mean, H_seam, rec_width)
    dfos_ducs = (quick_fos(ucs_mean+eps*ucs_mean, gsi_mean, T_mean, H_seam, rec_width) - fos_base) / (eps*ucs_mean)
    dfos_dgsi = (quick_fos(ucs_mean, gsi_mean+eps*gsi_mean, T_mean, H_seam, rec_width) - fos_base) / (eps*gsi_mean)
    dfos_dT = (quick_fos(ucs_mean, gsi_mean, T_mean+eps*T_mean, H_seam, rec_width) - fos_base) / (eps*T_mean)
    var_fos = (dfos_ducs * ucs_mean * ucs_cov)**2 + \
              (dfos_dgsi * gsi_mean * gsi_cov)**2 + \
              (dfos_dT * T_mean * T_cov)**2
    return fos_base, np.sqrt(var_fos)

st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
@st.cache_data
def generate_qr(link: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
qr_img_bytes = generate_qr(APP_URL)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

st.sidebar.header(t('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
if "formula_idx" not in st.session_state:
    st.session_state.formula_idx = 0
formula_option = st.sidebar.selectbox(t('formula_show'), formula_opts, index=st.session_state.formula_idx)
st.session_state.formula_idx = formula_opts.index(formula_option) if formula_option in formula_opts else 0

if formula_option != formula_opts[0]:
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == formula_opts[1]:
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.latex(r"m_b = m_i \exp\left(\frac{GSI-100}{28-14D}\right); \quad s = \exp\left(\frac{GSI-100}{9-3D}\right)")
            st.latex(r"a = \frac{1}{2} + \frac{1}{6} \left( e^{-GSI/15} - e^{-20/3} \right)")
        elif formula_option == formula_opts[2]:
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
            st.latex(r"\sigma_{ci(T)} = \sigma_{ci} \cdot (1 - D(T))")
            st.latex(r"k = k_0 \exp(8D(T)) (1 + 25 \epsilon_v)")
        elif formula_option == formula_opts[3]:
            st.latex(r"\sigma_{th} = \eta_c \frac{E \alpha \Delta T}{1-\nu} - \lambda_r \nabla T")
            st.latex(r"\sigma_{t0} = \frac{\sigma_{ci}}{2}\left(m_b - \sqrt{m_b^2 + 4s}\right) \quad \text{(Hoek-Brown 2002)}")
            st.latex(r"\sigma_{t(T)} = \sigma_{t0} \cdot \exp\left(-\beta_{th} (T - 20)\right)")
        elif formula_option == formula_opts[4]:
            st.latex(r"\sigma_{p} = \sigma_{ci} \cdot \left(0.64 + 0.36 \frac{w}{H}\right) \quad \text{(Wilson, 1972)}")
            st.latex(r"y = \frac{H}{2} \left( \sqrt{\frac{\sigma_v}{\sigma_p}} - 1 \right)")
            st.latex(r"S(x) = S_{max} \cdot \exp\left( -\frac{x^2}{2i^2} \right), \quad i = 0.45 H_{tot}")
            st.latex(r"u_h(x) = -\frac{x}{i} \cdot S(x)")

obj_name = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode = st.sidebar.selectbox(t('tensile_model'), [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')])
st.sidebar.subheader(t('rock_props'))
D_factor = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)
st.sidebar.subheader(t('tensile_params'))
beta_thermal = st.sidebar.slider(t('thermal_decay_label'), min_value=0.0005, max_value=0.02, value=PARAMS.thermal_damage_beta, step=0.0005)
st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40, min_value=1)
T_source_max = st.sidebar.slider(t('max_temp'), 600, 1200, PARAMS.gas_temp)
with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i+1), expanded=(i == int(num_layers) - 1)):
        name = st.text_input(t('layer_name'), value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(t('thickness'), value=50.0, min_value=0.1, key=f"thick_{i}")
        u = st.number_input(t('ucs'), value=40.0, min_value=0.1, key=f"ucs_{i}")
        rho = st.number_input(t('density'), value=2500.0, min_value=100.0, key=f"rho_{i}")
        color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
        g = st.slider(t('gsi'), 10, 100, 60, key=f"gsi_{i}")
        m = st.number_input(t('mi'), value=10.0, min_value=0.1, key=f"mi_{i}")
        s_t0_val = st.number_input(t('manual_st0'), value=3.0, key=f"st_{i}") if tensile_mode == t('tensile_manual') else 0.0
    layers_data.append({
        'name': name, 'thickness': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

errors = []
for lyr in layers_data:
    if lyr['thickness'] <= 0: errors.append(t('error_thick_positive'))
    if lyr['ucs'] <= 0: errors.append(t('error_ucs_positive'))
    if lyr['rho'] <= 0: errors.append(t('error_density_positive'))
    if not (10 <= lyr['gsi'] <= 100): errors.append(t('error_gsi_range'))
    if lyr['mi'] <= 0: errors.append(t('error_mi_positive'))
if not layers_data: errors.append(t('error_min_layers'))
if errors:
    for e in errors: st.error(e)
    st.stop()

depth_seam = sum(l['thickness'] for l in layers_data[:-1]) + layers_data[-1]['thickness'] / 2
avg_rho = np.mean([l['rho'] for l in layers_data])
H_seam = layers_data[-1]['thickness']
source_z = total_depth - H_seam / 2

grid_shape = (80, 100)
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape)

dx_val = x_axis[1] - x_axis[0]
dz_val = z_axis[1] - z_axis[0]

E_field = young_modulus_temperature(temp_2d)
alpha_field = thermal_expansion_temperature(temp_2d)

grid_rho = np.zeros_like(temp_2d)
layer_bounds_full = [(l['z_start'], l['z_start'] + l['thickness'], l) for l in layers_data]
for z0, z1, layer in layer_bounds_full:
    mask = (grid_z >= z0) & (grid_z < z1 if layer != layers_data[-1] else True)
    grid_rho[mask] = density_temperature(layer['rho'], temp_2d[mask])

grid_sigma_v = np.zeros((len(z_axis), len(x_axis)))
for i in range(1, len(z_axis)):
    dz_i = z_axis[i] - z_axis[i-1]
    grid_sigma_v[i,:] = grid_sigma_v[i-1,:] + grid_rho[i,:] * 9.81 * dz_i / 1e6
grid_sigma_h = k_ratio * grid_sigma_v

cavity_radius = evolving_cavity_radius(time_h, temp_2d, beta_thermal, grid_z, source_z, H_seam)
pore_pressure = pore_pressure_field(temp_2d, grid_z)
sigma_rr, sigma_tt, tau_rt = kirsch_stress_field(grid_x, grid_z - source_z,
                                                 grid_sigma_h, grid_sigma_v,
                                                 cavity_radius, pore_pressure)

delta_T = np.maximum(temp_2d - T_REF_AMBIENT, 0)
sigma_thermal_pa = E_field * alpha_field * delta_T / (1.0 - nu_poisson + EPS)
sigma_thermal = sigma_thermal_pa / 1e6

dT_dx, dT_dz = np.gradient(temp_2d, dx_val, dz_val)
dT_deviatoric = (dT_dx - dT_dz) / 2.0
tau_thermal = (E_field * alpha_field * dT_deviatoric * nu_poisson) / \
              (2.0 * (1.0 - nu_poisson**2) + EPS) / 1e6
tau_rt += tau_thermal

sigma_x_total = sigma_rr - sigma_thermal
sigma_z_total = sigma_tt - sigma_thermal

sigma1_act, sigma3_act = principal_stresses(sigma_x_total, sigma_z_total, tau_rt)

grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
for z0, z1, layer in layer_bounds_full:
    mask = (grid_z >= z0) & (grid_z < z1 if layer != layers_data[-1] else True)
    grid_ucs[mask] = layer['ucs']
    mb, s, a = hoek_brown_params(layer['gsi'], layer['mi'], D_factor)
    grid_mb[mask] = mb
    grid_s_hb[mask] = s
    grid_a_hb[mask] = a

ucs_field_degraded = apply_thermal_degradation(grid_ucs, temp_2d, beta_thermal)
overstress = compute_demand_capacity_ratio(sigma1_act, sigma3_act, ucs_field_degraded, grid_mb, grid_s_hb, grid_a_hb)

void_fraction = gaussian_filter(overstress * (temp_2d > 600), sigma=2)
void_mask_permanent = void_fraction > 0.5
void_volume = np.sum(void_mask_permanent) * dx_val * dz_val

volumetric_strain = (sigma_thermal * 1e6) / (E_field + EPS)
perm = 1e-15 * np.exp(np.clip(8*overstress + 12*volumetric_strain, -20, 20))
perm_x = perm * 5
perm_z = perm
perm = np.clip(perm, 1e-16, 1e-10)

T_kelvin = temp_2d + 273.15
pressure_field = 1e5 + 50 * (T_kelvin - 293.15)
gas_density = (pressure_field * PARAMS.MOLAR_MASS_GAS) / (PARAMS.R_UNIVERSAL * T_kelvin)
dp_dx, dp_dz = np.gradient(pressure_field, dx_val, dz_val)
mu_gas = PARAMS.GAS_VISCOSITY
vx = -perm_x * dp_dx / mu_gas
vz = -perm_z * dp_dz / mu_gas
gas_velocity = np.sqrt(vx**2 + vz**2)

phi_rad = np.radians(PARAMS.phi_deg)
angle_of_draw = np.radians(45.0 - PARAMS.phi_deg / 2.0)
influence_radius = total_depth * np.tan(angle_of_draw)
i_oreilly = 0.45 * total_depth
logger.info(f"Influence radius: Peck={influence_radius:.1f}m, O'Reilly={i_oreilly:.1f}m")

c_subs = PARAMS.subsidence_rate
Smax = H_seam * 0.04
subsidence_t = Smax * (1 - np.exp(-c_subs * time_h))
shift_dip = subsidence_inclined_seam(total_depth, dip_angle, PARAMS.phi_deg)
x_axis_shifted = x_axis + shift_dip
subsidence_raw = -subsidence_t * np.exp(-(x_axis_shifted**2) / (2 * influence_radius**2))
win_len = min(11, len(x_axis)-1)
if win_len % 2 == 0:
    win_len -= 1
subsidence_raw = savgol_filter(subsidence_raw, window_length=win_len, polyorder=3)

void_correction_factor = 1.0 + PARAMS.K_VOID * float(np.mean(void_mask_permanent))
sub_p = subsidence_raw * void_correction_factor

def horizontal_displacement_oreilly(x, S_x, i_inflection):
    return -(x / (i_inflection + EPS)) * S_x

horizontal_disp_m = horizontal_displacement_oreilly(x_axis, sub_p, influence_radius)
horizontal_disp_cm = horizontal_disp_m * 100.0

idx_closest = np.abs(z_axis - source_z).argmin()
avg_t_p = np.mean(temp_2d[idx_closest, :])
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[idx_closest, :].max()
target_layer = layers_data[-1]
mb_dyn, s_dyn, a_dyn = hoek_brown_params(target_layer['gsi'], target_layer['mi'], D_factor)
ucs_t_dyn = apply_thermal_degradation(ucs_seam, avg_t_p, beta_thermal)
sigma_cm = ucs_t_dyn * (s_dyn ** a_dyn)

w_sol = 20.0
E_MIN_CORE = 0.5 * H_seam
w_prev = w_sol
for iteration in range(50):
    p_strength = sigma_cm * (WILSON_C1 + WILSON_C2 * w_sol / (H_seam + EPS))
    ratio = sv_seam / (p_strength + EPS)
    y_zone_calc = (H_seam / 2.0) * (np.sqrt(ratio) - 1.0) if ratio >= 1.0 else 0.0
    new_w = 2.0 * max(y_zone_calc, 1.5) + E_MIN_CORE
    w_sol = 0.6 * new_w + 0.4 * w_sol
    if abs(w_sol - w_prev) < 0.01:
        break
    w_prev = w_sol
rec_width = np.round(w_sol, 1)
pillar_strength = p_strength
y_zone = max(y_zone_calc, 1.5)

rock_factor = (target_layer['gsi']/100) * (target_layer['mi']/20) * (1 - D_factor)
thermal_factor = np.exp(-0.002 * avg_t_p)
analytical_width = 4 + 0.12 * ucs_seam * rock_factor * thermal_factor * (1 + nu_poisson) * np.sqrt(k_ratio)
analytical_width = np.clip(analytical_width, 5, 100)

pillar_strength_creep = pillar_creep_strength(pillar_strength, time_h)

avg_pore_p = float(np.mean(pore_pressure[idx_closest, :]))
def fos_with_pore_pressure(pillar_strength, sigma_v, pore_pressure, B_skempton=0.9):
    sigma_v_eff = max(sigma_v - B_skempton * pore_pressure, 0.01)
    return pillar_strength / sigma_v_eff
fos_final = fos_with_pore_pressure(pillar_strength_creep, vertical_stress(depth_seam, avg_rho), avg_pore_p)

fos_analytic, fos_std_analytic = propagate_uncertainty_analytical(
    ucs_seam, 0.1, target_layer['gsi'], 0.05, T_source_max, 0.05, H_seam, rec_width
)

st.info(t('pin_approx'))

st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength_creep:.1f} MPa", delta=t('creep_info'))
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{analytical_width:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")
st.markdown("---")

col_g1, col_g2, col_g3 = st.columns([1.5,1.5,2])
with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta',width=3))).update_layout(title=t('subsidence_title'), template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=horizontal_disp_cm, fill='tozeroy', line=dict(color='cyan',width=3))).update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    fig_hb = go.Figure()
    for lyr in layers_data:
        ucs_i = lyr['ucs']
        gsi_i = lyr['gsi']
        mi_i = lyr['mi']
        mb_i, s_i, a_i = hoek_brown_params(gsi_i, mi_i, D_factor)
        sigma3_ax = np.linspace(0, ucs_i*0.5, 100)
        layer_mask = (grid_z >= lyr['z_start']) & (grid_z < lyr['z_start'] + lyr['thickness'])
        local_T = temp_2d[layer_mask].mean() if np.any(layer_mask) else 25.0
        ucs_T_i = apply_thermal_degradation(ucs_i, local_T, beta_thermal)
        sigma1_i = sigma3_ax + ucs_T_i*(mb_i*sigma3_ax/(ucs_T_i+EPS)+s_i)**a_i
        fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=sigma1_i, name=lyr['name'], line=dict(width=2)))
    st.plotly_chart(fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")), use_container_width=True)
st.markdown("---")

c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(x=['Kesim'], y=[lyr['thickness']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_layers.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader(t('well_config'))
well_distance = st.sidebar.slider(t('well_distance'), 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")
dip_angle = st.sidebar.slider(t('dip_angle_label'), 0, 90, 0, 5, key="dip_angle_slider")
cavity_width_global = well_distance - rec_width
if cavity_width_global < 1.0:
    st.warning(t('warning_cavity_width'))
    cavity_width_global = 1.0

CONFINEMENT = PARAMS.CONFINEMENT
RELAX = PARAMS.RELAX
sigma_v_coal = 0.0
for l in layers_data[:-1]:
    sigma_v_coal += l['rho'] * 9.81 * l['thickness']
sigma_v_coal += layers_data[-1]['rho'] * 9.81 * (H_seam / 2)
sigma_v_coal = sigma_v_coal / 1e6
Hc = H_seam * np.sqrt(sigma_v_coal / (layers_data[-1]['ucs'] + EPS))
Hc = np.clip(Hc, H_seam, H_seam * 4)

def compute_advanced_fos(grid_x, grid_z, active_wells_tuple, well_x_tuple, source_z_val, h_seam, cavity_width,
                         temp_field, sigma_v_field, layers_data_tuple, layer_bounds_full,
                         E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn):
    fos = np.full_like(grid_x, 3.0)
    for px_idx in active_wells_tuple:
        px = well_x_tuple[px_idx]
        dist = np.sqrt((grid_x - px)**2 + (grid_z - source_z_val)**2)
        delta_z_local = source_z_val - grid_z
        T = temp_field
        delta_T = np.maximum(T - T_REF_AMBIENT, 0)
        thermal_zone = dist < (h_seam * 3)
        for top, bot, layer in layer_bounds_full:
            mask = (grid_z >= top) & (grid_z < bot)
            if not np.any(mask): continue
            ucs_l = layer['ucs']
            gsi = layer['gsi']; mi = layer['mi']
            mb, s_hb, a_hb = hoek_brown_params(gsi, mi, D_factor)
            sigma_v = sigma_v_field[mask]
            delta_T_m = delta_T[mask]
            sigma_ci_T = apply_thermal_degradation(ucs_l, delta_T_m, beta_th)
            sigma_3 = K0 * sigma_v * (0.6 + 0.4 * (1 - thermal_damage(delta_T_m, beta_th)))
            sigma_th = np.zeros_like(sigma_v)
            local_thermal = thermal_zone[mask]
            if np.any(local_thermal):
                grad_T_local = np.sqrt(
                    np.gradient(T, axis=1, edge_order=2)[mask]**2 +
                    np.gradient(T, axis=0, edge_order=2)[mask]**2
                )
                th_vals = (CONFINEMENT * E * alpha * delta_T_m[local_thermal]) / (1 - nu) - RELAX * grad_T_local[local_thermal]
                sigma_th[local_thermal] = np.clip(th_vals, 0, sigma_ci_T[local_thermal] * 0.35)
            sigma_1 = sigma_v + sigma_th
            sigma_limit = hoek_brown(sigma_3, sigma_ci_T, mb, s_hb, a_hb)
            fos_val = np.where(sigma_1 > 0.01, sigma_limit / sigma_1, 3.0)
            fos_val = np.clip(fos_val, 0, 3)
            yield_mask = sigma_1 > (sigma_limit * 0.85)
            fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
            fos_sub = fos[mask]
            fos_sub = np.minimum(fos_sub, fos_val)
            fos[mask] = fos_sub
            if layer == layers_data_tuple[-1]:
                dome_width = (cavity_width / 2) * np.clip(1 - delta_z_local[mask] / (Hc + EPS), 0, 1)
                failure_zone = fos_val < 1.2
                dome_condition = (delta_z_local[mask] > 0) & (delta_z_local[mask] < Hc) & (np.abs(grid_x[mask] - px) < dome_width) & failure_zone
                if np.any(dome_condition):
                    decay = np.clip(1 - (delta_z_local[mask][dome_condition] / (Hc + EPS)), 0.3, 1.0)
                    fos_sub[dome_condition] = np.minimum(fos_sub[dome_condition], decay)
                    fos[mask] = fos_sub
    for px_idx in active_wells_tuple:
        px = well_x_tuple[px_idx]
        a = cavity_width / 2
        b = h_seam / 2
        cavity_ellipse = ((grid_x - px)**2 / (a**2 + EPS) + (grid_z - source_z_val)**2 / (b**2 + EPS)) < 1
        fos[cavity_ellipse] = 0.05
    bottom_layer = layers_data_tuple[-1]
    bottom_boundary = bottom_layer['z_start'] + bottom_layer['thickness']
    fos[grid_z > bottom_boundary] = 2.5
    all_wells = [0, 1, 2]
    for i in all_wells:
        if i not in active_wells_tuple:
            px = well_x_tuple[i]
            pillar_mask = (np.abs(grid_x - px) < h_seam * 1.5) & (np.abs(grid_z - source_z_val) < h_seam * 1.2)
            fos[pillar_mask] = 2.5
    if active_wells_tuple == (0, 2):
        selek_eni = np.abs(well_x_tuple[0] - well_x_tuple[2]) - cavity_width
        sigma_cm_pillar = ucs_coal_MPa * (s_dyn ** a_dyn)
        pillar_strength_pillar = sigma_cm_pillar * (WILSON_C1 + WILSON_C2 * selek_eni / h_seam)
        fos_pillar = pillar_strength_pillar / (sigma_v_coal_MPa + EPS)
        pillar_zone = (np.abs(grid_x - well_x_tuple[1]) < selek_eni/2) & (np.abs(grid_z - source_z_val) < h_seam)
        fos[pillar_zone] = np.maximum(fos[pillar_zone], fos_pillar)
    return np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)

@st.cache_data(hash_funcs={np.ndarray: lambda x: hashlib.md5(x.tobytes()).hexdigest()})
def compute_advanced_fos_wrapper(grid_x, grid_z, active_wells_tuple, well_x_tuple, source_z_val, h_seam, cavity_width,
                                 temp_field, sigma_v_field, layers_data_tuple, layer_bounds_full,
                                 E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn):
    return compute_advanced_fos(grid_x, grid_z, active_wells_tuple, well_x_tuple, source_z_val, h_seam, cavity_width,
                                temp_field, sigma_v_field, layers_data_tuple, layer_bounds_full,
                                E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn)

well_x_pos = [-well_distance, 0, well_distance]
states_132 = {1: (0,), 2: (0, 2), 3: (0, 1, 2)}
stage = st.select_slider(t('select_stage'), options=[1, 2, 3], value=1, key="ucg_stage")
active_wells = states_132[stage]

fos_all_stages = {}
for s_key in [1, 2, 3]:
    fos_all_stages[s_key] = compute_advanced_fos_wrapper(
        grid_x, grid_z, tuple(states_132[s_key]), tuple(well_x_pos),
        source_z, H_seam, cavity_width_global,
        temp_2d, grid_sigma_v,
        tuple(layers_data), tuple((z0,z1, dict(l)) for z0,z1,l in layer_bounds_full),
        E=PARAMS.E_mass, alpha=PARAMS.alpha_thermal, nu=nu_poisson, K0=nu_poisson/(1-nu_poisson),
        Hc=Hc, sigma_v_coal_MPa=sigma_v_coal, ucs_coal_MPa=ucs_seam,
        beta_th=beta_thermal, D_factor=D_factor, s_dyn=s_dyn, a_dyn=a_dyn
    )
fos_stage = fos_all_stages[stage]
fos_worst_case = fos_all_stages[3]

with c2:
    st.subheader(t('ucg_stages_title'))
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=(t('temp_subplot'), t('geomech_state')))
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42, thickness=15), name=t('temp_subplot')), row=1, col=1)
    step = 12
    qx, qz = grid_x[::step, ::step].flatten(), grid_z[::step, ::step].flatten()
    qu, qw = vx[::step, ::step].flatten(), vz[::step, ::step].flatten()
    qmag = gas_velocity[::step, ::step].flatten()
    qmag_max = qmag.max() + EPS
    mask_q = qmag > qmag_max * 0.05
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q] + EPS))
    fig_tm.add_trace(go.Scatter(x=qx[mask_q], y=qz[mask_q], mode='markers',
                                marker=dict(symbol='arrow', size=10, color=qmag[mask_q], colorscale='ice',
                                            cmin=0, cmax=qmag_max, angle=angles, opacity=0.85, showscale=False, line=dict(width=0)),
                                name=t('gas_flow')), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_stage, x=x_axis, y=z_axis,
                                colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],[0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
                                zmin=0, zmax=3, contours_showlines=False,
                                colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42, thickness=15), name="FOS"), row=2, col=1)
    fracture_mask = np.where(fos_stage < 1.2, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=fracture_mask, x=x_axis, y=z_axis,
                                colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(255,0,0,0.5)']],
                                showscale=False, opacity=0.6, hoverinfo='skip', name="Yielded Zones"), row=2, col=1)
    r_burn_vis = H_seam * 1.5
    for idx in active_wells:
        px = well_x_pos[idx]
        fig_tm.add_shape(type="circle", x0=px-r_burn_vis, x1=px+r_burn_vis,
                         y0=source_z-r_burn_vis, y1=source_z+r_burn_vis,
                         line=dict(color="orange", width=2), fillcolor='rgba(255,165,0,0.15)', row=2, col=1)
    for px in well_x_pos:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2,
                         y0=source_z-H_seam/2, y1=source_z+H_seam/2,
                         line=dict(color="lime", width=3), fillcolor="rgba(0,255,0,0.1)", row=2, col=1)
    if stage == 2:
        fig_tm.add_shape(type="rect", x0=well_x_pos[1]-80, x1=well_x_pos[1]+80,
                         y0=source_z-30, y1=source_z+30,
                         line=dict(color="cyan", width=4, dash="dash"), fillcolor='rgba(0,255,255,0.1)', row=2, col=1)
        fig_tm.add_annotation(x=well_x_pos[1], y=source_z+100, text=t('pillar_annotation'),
                              showarrow=True, arrowhead=2, font=dict(color="cyan", size=12), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=900, margin=dict(r=150,t=80,b=100),
                         showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    zoom_margin = H_seam * 12
    fig_tm.update_yaxes(range=[source_z + zoom_margin/2, source_z - zoom_margin], row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox(t('auto_animation')):
        anim_placeholder = st.empty()
        for s in [1, 2, 3]:
            fos_s = fos_all_stages[s]
            fig_s = go.Figure(go.Contour(z=fos_s, x=x_axis, y=z_axis,
                                         colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],[0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
                                         zmin=0, zmax=3, contours_showlines=False,
                                         colorbar=dict(title="FOS")))
            fig_s.update_yaxes(range=[source_z + zoom_margin/2, source_z - zoom_margin], autorange=False)
            fig_s.update_layout(template="plotly_dark", height=500, title=f"Bosqich {s} (1-3-2 sxemasi)")
            anim_placeholder.plotly_chart(fig_s, use_container_width=True)
            time.sleep(1.2)
        st.success(t('animation_done'))

    selek_eni = well_distance - cavity_width_global
    msgs = {
        1: f"**1-Bosqich:** Chap quduq yoqilgan. Qalinlik = {H_seam:.1f} m, Quduqlar masofasi = {well_distance:.0f} m, Selek eni = {selek_eni:.1f} m.",
        2: f"**2-Bosqich (Muhim):** O'ng quduq yoqilgan. O'rtadagi selek tomni ushlab turadi. Selek eni = {selek_eni:.1f} m.",
        3: f"**3-Bosqich:** Markaziy selek gazlashtirilmoqda. Barqaror cho'kish."
    }
    st.info(msgs[stage])
    if selek_eni < 18.5:
        st.error(f"⚠️ KRITIK: Selek o'lchami ({selek_eni:.1f} m) xavfsiz chegaradan past!")
    else:
        st.success(f"✅ BARQAROR: Selek o'lchami ({selek_eni:.1f} m) me'yorda.")

gas_risk_map = gas_migration_risk(temp_2d, perm, fos_stage)
water_risk_level, water_risk_val = water_inrush_risk(void_volume, 150.0, depth_seam, fos_final)

with st.expander(t('gas_risk_title')):
    fig_gas = go.Figure(go.Heatmap(z=gas_risk_map, x=x_axis, y=z_axis, colorscale='YlOrRd', zmin=0, zmax=1))
    fig_gas.update_layout(title=t('gas_risk_title'), template='plotly_dark')
    st.plotly_chart(fig_gas, use_container_width=True)

with st.expander(t('water_risk_title')):
    st.metric("Suv bosish xavfi", f"{water_risk_val:.2f}", delta=water_risk_level)
    st.progress(water_risk_val)

with st.expander(t('uncertainty_title')):
    st.write(f"**FOS (analitik):** {fos_analytic:.3f} ± {fos_std_analytic:.3f}")
    st.write(f"**95% CI:** {fos_analytic - 1.96*fos_std_analytic:.3f} – {fos_analytic + 1.96*fos_std_analytic:.3f}")

with st.expander(t('case_study_title')):
    st.markdown("""
    ### Chinchilla UCG Trial (Queensland, 2000-2002)
    - FOS: ~1.4 (minor pillar yielding)
    - Maks cho'kish: 2.5 cm
    - Bizning model: FOS={:.2f}, cho'kish={:.1f} cm
    ### Hanna UCG Trial (Wyoming, USA)
    - Termal maydon: 800-1000°C o'lchangan
    - Model: Maks T={:.0f}°C
    ### Angren UCG (O'zbekiston)
    - Monitoring parametrlari mos keladi (shartli)
    """.format(fos_final, np.max(sub_p)*100, np.max(temp_2d)))

st.header("🔄 Live 3D Monitoring (Real-time)")
tab_live, tab_ai_orig, tab_advanced = st.tabs([t('live_monitoring_tab'), t('ai_monitor_title'), t('advanced_analysis')])

with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies and alerts")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    if "stop_live" not in st.session_state:
        st.session_state.stop_live = False
    col_live1, col_live2 = st.columns(2)
    run_live = col_live1.button("▶️ Run Live Monitoring", key="run_live")
    stop_live_btn = col_live2.button("⏹ Stop Monitoring", key="stop_live_btn")
    if stop_live_btn:
        st.session_state.stop_live = True
    if run_live:
        st.session_state.stop_live = False
        subs_plot_live = st.empty()
        temp_plot_live = st.empty()
        pillar_plot_live = st.empty()
        trend_plot_live = st.empty()
        surface_3d_plot_live = st.empty()
        alert_box_live = st.empty()
        if 'live_data_list' not in st.session_state:
            st.session_state.live_data_list = []
        X_live = np.linspace(-20,20,50)
        Y_live = np.linspace(-20,20,50)
        X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_history_live = []
        fos_history_live = []
        width_history_live = []
        temp_history_live = []
        steps_done = 0
        while not st.session_state.stop_live and steps_done < TIME_STEPS:
            step_idx = steps_done
            Z_subs = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*(5+step_idx*0.1)**2))*5*step_idx/TIME_STEPS
            Z_temp = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*8**2))*T_source_max*step_idx/TIME_STEPS
            Z_filtered = gaussian_filter(Z_subs, sigma=1)
            anomalies = Z_subs - Z_filtered
            anomaly_points = np.where(np.abs(anomalies) > 0.2)
            pillar_width_pred = rec_width + np.random.normal(0,0.1)
            T_avg_live = np.mean(Z_temp)
            sigma_v_live = vertical_stress(depth_seam, avg_rho)
            sigma_thermal_live = (E_field.mean() * alpha_field.mean() * max(T_avg_live-T_REF_AMBIENT,0)) / (1 - 2*nu_poisson + EPS) / 1e6
            pore_pressure_live = pore_pressure_field(T_avg_live, depth_seam, np.mean(perm))
            pillar_live = apply_thermal_degradation(ucs_seam, T_avg_live, beta_thermal) * (WILSON_C1 + WILSON_C2 * rec_width/(H_seam+EPS))
            FOS_live = pillar_live / (sigma_v_live + sigma_thermal_live + pore_pressure_live + 1e-8)
            FOS_live = np.clip(FOS_live, 0, 5)
            mean_subs = np.mean(Z_subs)
            subs_history_live.append(mean_subs)
            fos_history_live.append(FOS_live)
            width_history_live.append(pillar_width_pred)
            temp_history_live.append(T_avg_live)
            st.session_state.live_data_list.append({
                'step': step_idx+1,
                'mean_subsidence_cm': mean_subs*100,
                'max_temp_c': np.max(Z_temp),
                'FOS': FOS_live,
                'pillar_width_m': pillar_width_pred
            })
            if len(st.session_state.live_data_list) > 1000:
                st.session_state.live_data_list = st.session_state.live_data_list[-1000:]
            st.session_state.live_history_df = pd.DataFrame(st.session_state.live_data_list)
            fig_subs = go.Figure(go.Heatmap(z=Z_subs*100, x=X_live, y=Y_live, colorscale='Viridis')).update_layout(title='Surface Subsidence (cm)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            subs_plot_live.plotly_chart(fig_subs, use_container_width=True)
            fig_temp = go.Figure(go.Heatmap(z=Z_temp, x=X_live, y=Y_live, colorscale='Hot')).update_layout(title='Temperature Field (°C)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            temp_plot_live.plotly_chart(fig_temp, use_container_width=True)
            pillar_plot_live.metric(label="Recommended Pillar Width (m)", value=f"{pillar_width_pred:.2f}", delta=f"FOS = {FOS_live:.2f}")
            trend_fig = go.Figure(go.Scatter(y=subs_history_live, mode='lines+markers', name='Subsidence (cm)')).update_layout(title='Subsidence Trend', xaxis_title='Time step', yaxis_title='Mean subsidence (cm)', height=350)
            trend_plot_live.plotly_chart(trend_fig, use_container_width=True)
            surface_fig = go.Figure(data=[go.Surface(z=Z_subs*100, x=X_live, y=Y_live, colorscale='Viridis', opacity=0.9)])
            if anomaly_points[0].size > 0:
                surface_fig.add_trace(go.Scatter3d(x=X_grid_live[anomaly_points], y=Y_grid_live[anomaly_points], z=Z_subs[anomaly_points]*100, mode='markers', marker=dict(color='red', size=5), name='Anomaly'))
            surface_fig.update_layout(title='3D Surface & Anomalies', scene=dict(zaxis_title='Subsidence (cm)'), height=500)
            surface_3d_plot_live.plotly_chart(surface_fig, use_container_width=True)
            alerts = []
            if FOS_live < 1.2:
                alerts.append("⚠️ FOS Critical!")
            if mean_subs*100 > 3:
                alerts.append("⚠️ High Subsidence!")
            if np.max(Z_temp) > 1100:
                alerts.append("🔥 Overheating Alert!")
            if alerts:
                alert_box_live.markdown("### 🔴 ALERTS\n" + "\n".join(alerts))
            else:
                alert_box_live.markdown("### 🟢 All systems normal")
            time.sleep(0.1)
            steps_done += 1
        if steps_done >= TIME_STEPS:
            st.success(f"✅ Live monitoring completed after {steps_done} steps.")
        elif st.session_state.stop_live:
            st.warning("Monitoring stopped by user.")
    if not st.session_state.live_history_df.empty:
        st.markdown("---")
        st.subheader("📥 Download Monitoring Results (CSV)")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(label=t('download_data'), data=csv_data, file_name="ucg_live_monitoring.csv", mime="text/csv")

with tab_ai_orig:
    st.markdown(f"*{t('ai_monitor_desc')}*")
    def get_sensor_data_sim(step, total_steps, base_temp):
        trend = step / total_steps
        temp = base_temp * (0.5 + 0.7*trend) + np.random.normal(0, 10)
        pressure = 2 + 5*trend + np.random.normal(0, 0.5)
        stress = 5 + 10*trend + np.random.normal(0, 0.5)
        return {"temperature": temp, "gas_pressure": pressure, "stress": stress}
    def compute_effective_stress(sensor):
        return sensor["stress"] - sensor["gas_pressure"] + 0.002 * sensor["temperature"]
    def detect_anomaly_z(history, value, threshold=2.0, window=20):
        if len(history) < window:
            return False
        recent = history[-window:]
        mean = np.mean(recent)
        std = np.std(recent) + EPS
        return abs(value - mean) > threshold * std
    def simulate_sensors_fos(n_steps):
        T = np.linspace(T_REF_AMBIENT, min(1100,T_source_max), n_steps) + np.random.normal(0,10,n_steps)
        sigma_v = np.linspace(5, min(15, sv_seam*10), n_steps) + np.random.normal(0,0.5,n_steps)
        return pd.DataFrame({'Temperature':T, 'VerticalStress':sigma_v})
    if PT_AVAILABLE:
        class SimpleNN(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(2,16)
                self.fc2 = nn.Linear(16,16)
                self.fc3 = nn.Linear(16,1)
            def forward(self, x):
                x = torch.relu(self.fc1(x))
                x = torch.relu(self.fc2(x))
                return 3.0 * torch.sigmoid(self.fc3(x))
        fos_nn_model = SimpleNN().to(device)
        fos_criterion = nn.MSELoss()
        fos_optimizer = torch.optim.Adam(fos_nn_model.parameters(), lr=0.01)
    else:
        fos_rf_model_tab2 = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED)
        fos_rf_model_tab2.fit([[T_REF_AMBIENT, 5.0]], [1.5])
    ai_tab1, ai_tab2 = st.tabs(["📡 Anomaliya Aniqlash (Digital Twin)", "📊 FOS Prediction (SimpleNN / RF)"])
    with ai_tab1:
        st.markdown("#### Sensor ma'lumotlari asosida real-vaqt anomaliya aniqlash")
        t1_col1, t1_col2, t1_col3 = st.columns([1,1,2])
        with t1_col1:
            ai_steps_1 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=60, step=10, key="ai_steps_1")
        with t1_col2:
            anomaly_threshold = st.slider("Anomaliya chegarasi (σ)", 1.0,4.0,2.0,0.5, key="thresh_1")
        with t1_col3:
            run_ai_1 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_1")
        if run_ai_1:
            placeholder_1 = st.empty()
            history_eff = []
            anomalies_eff = []
            temp_history = []
            gas_history = []
            stress_history = []
            for step in range(int(ai_steps_1)):
                sensor = get_sensor_data_sim(step, int(ai_steps_1), T_source_max*0.6)
                effective = compute_effective_stress(sensor)
                is_anomaly = detect_anomaly_z(history_eff, effective, threshold=anomaly_threshold)
                history_eff.append(effective)
                anomalies_eff.append(effective if is_anomaly else None)
                temp_history.append(sensor["temperature"])
                gas_history.append(sensor["gas_pressure"])
                stress_history.append(sensor["stress"])
                with placeholder_1.container():
                    acol1,acol2,acol3,acol4 = st.columns(4)
                    acol1.metric("🌡 Harorat", f"{sensor['temperature']:.1f} °C", delta=f"{sensor['temperature']-np.mean(temp_history):.1f}" if len(temp_history)>1 else None)
                    acol2.metric("💨 Gaz bosimi", f"{sensor['gas_pressure']:.2f} MPa")
                    acol3.metric("🧱 Effektiv σ", f"{effective:.2f} MPa", delta_color="inverse", delta="⚠️ Anomaliya!" if is_anomaly else "Normal")
                    acol4.metric("📈 Qadam", f"{step+1}/{int(ai_steps_1)}")
                    fig_a = make_subplots(rows=2,cols=2,subplot_titles=("Effektiv Kuchlanish & Anomaliyalar","Harorat Tarixi (°C)","Gaz Bosimi (MPa)","Stress Tarixi (MPa)"), vertical_spacing=0.15, horizontal_spacing=0.1)
                    fig_a.add_trace(go.Scatter(y=history_eff, mode='lines', name='Effektiv σ', line=dict(color='cyan',width=2)), row=1, col=1)
                    fig_a.add_trace(go.Scatter(y=anomalies_eff, mode='markers', name='Anomaliya', marker=dict(color='red',size=10,symbol='x')), row=1, col=1)
                    fig_a.add_trace(go.Scatter(y=temp_history, mode='lines', name='Harorat', line=dict(color='orange',width=2)), row=1, col=2)
                    fig_a.add_trace(go.Scatter(y=gas_history, mode='lines+markers', name='Gaz bosimi', line=dict(color='lime',width=1), marker=dict(size=4)), row=2, col=1)
                    fig_a.add_trace(go.Scatter(y=stress_history, mode='lines', name='Stress', line=dict(color='magenta',width=2)), row=2, col=2)
                    fig_a.update_layout(template="plotly_dark", height=500, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(t=60,b=60))
                    st.plotly_chart(fig_a, use_container_width=True, key=f"anom_{step}")
                    anomaly_count = sum(1 for a in anomalies_eff if a is not None)
                    if is_anomaly:
                        st.error(f"🚨 ANOMALIYA ANIQLANDI! (Jami: {anomaly_count}) — Collapse ehtimoli yuqori!")
                    elif effective > pillar_strength*0.8:
                        st.warning(f"⚠️ Kuchlanish Pillar Strength ({pillar_strength:.1f} MPa) ning 80% dan oshdi!")
                    else:
                        st.success(f"✅ Normal holat — Effektiv σ: {effective:.2f} MPa")
                    st.progress((step+1)/int(ai_steps_1))
                time.sleep(0.15)
            st.balloons()
            st.success(f"✅ Monitoring yakunlandi! Jami anomaliyalar: {sum(1 for a in anomalies_eff if a is not None)}")
    with ai_tab2:
        st.markdown("#### SimpleNN yoki RandomForest yordamida FOS (Factor of Safety) bashorati")
        t2_col1, t2_col2 = st.columns([1,3])
        with t2_col1:
            ai_steps_2 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=50, step=10, key="ai_steps_2")
            fos_target = st.number_input("Maqsad FOS qiymati", min_value=1.0, max_value=3.0, value=1.5, step=0.1, key="fos_target")
        with t2_col2:
            run_ai_2 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_2")
        if run_ai_2:
            placeholder_2 = st.empty()
            sensor_data_fos = simulate_sensors_fos(int(ai_steps_2))
            pillar_strength_pred = []
            for i in range(int(ai_steps_2)):
                row = sensor_data_fos.iloc[i]
                X = np.array([[row.Temperature, row.VerticalStress]])
                if PT_AVAILABLE:
                    X_t = torch.tensor(X, dtype=torch.float32).to(device)
                    y_pred = fos_nn_model(X_t).detach().cpu().numpy()[0][0]
                    target = torch.tensor([[fos_target]], dtype=torch.float32).to(device)
                    fos_optimizer.zero_grad()
                    loss = fos_criterion(fos_nn_model(X_t), target)
                    loss.backward()
                    fos_optimizer.step()
                else:
                    y_pred = fos_rf_model_tab2.predict(X)[0]
                pillar_strength_pred.append(float(y_pred))
                if y_pred < 1.0:
                    fos_color = t('fos_red')
                elif y_pred <= 1.5:
                    fos_color = t('fos_yellow')
                else:
                    fos_color = t('fos_green')
                with placeholder_2.container():
                    p2c1, p2c2, p2c3 = st.columns(3)
                    p2c1.metric("🌡 Harorat", f"{row.Temperature:.1f} °C")
                    p2c2.metric("🧱 Vertikal Stress", f"{row.VerticalStress:.2f} MPa")
                    p2c3.metric("📊 Bashorat FOS", f"{y_pred:.2f}", delta=fos_color)
                    fig_fos = make_subplots(rows=1, cols=2, subplot_titles=("FOS Bashorati (Tarixiy)", "Sensor: Harorat vs Stress"))
                    fig_fos.add_trace(go.Scatter(y=pillar_strength_pred[:i+1], mode='lines+markers', name=t('pillar_live'), line=dict(color='lime',width=2), marker=dict(size=5)), row=1, col=1)
                    fig_fos.add_hline(y=fos_target, line_dash="dash", line_color="yellow", annotation_text=f"Maqsad: {fos_target}", row=1, col=1)
                    fig_fos.add_trace(go.Scatter(x=sensor_data_fos['Temperature'].iloc[:i+1].tolist(), y=sensor_data_fos['VerticalStress'].iloc[:i+1].tolist(), mode='markers', name='Sensor yo\'li', marker=dict(color=list(range(i+1)), colorscale='Viridis', size=6, showscale=False)), row=1, col=2)
                    fig_fos.update_layout(template="plotly_dark", height=420, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), margin=dict(t=60,b=60))
                    fig_fos.update_xaxes(title_text="Qadam", row=1, col=1)
                    fig_fos.update_yaxes(title_text="FOS", row=1, col=1)
                    fig_fos.update_xaxes(title_text="Harorat (°C)", row=1, col=2)
                    fig_fos.update_yaxes(title_text="Vertikal Stress (MPa)", row=1, col=2)
                    st.plotly_chart(fig_fos, use_container_width=True, key=f"fospred_{i}")
                    st.info(f"Qadam {i+1}/{int(ai_steps_2)} | Model: {'PyTorch SimpleNN' if PT_AVAILABLE else 'RandomForest'} | {fos_color}")
                    st.progress((i+1)/int(ai_steps_2))
                time.sleep(0.05)
            st.balloons()
            final_fos = pillar_strength_pred[-1] if pillar_strength_pred else 0
            if final_fos < 1.0:
                st.error(f"🔴 Yakuniy FOS: {final_fos:.2f} — Xavfli zona!")
            elif final_fos <= 1.5:
                st.warning(f"🟡 Yakuniy FOS: {final_fos:.2f} — Noaniq holat")
            else:
                st.success(f"🟢 Yakuniy FOS: {final_fos:.2f} — Barqaror!")

with tab_advanced:
    st.header(t('advanced_analysis'))
    E_MODULUS_R, ALPHA_THERM, BETA_CONST = PARAMS.E_mass, PARAMS.alpha_thermal, beta_thermal
    target_l = layers_data[-1]
    ucs_0_r, gsi_val, mi_val = target_l['ucs'], target_l['gsi'], target_l['mi']
    H_depth_tot = sum(l['thickness'] for l in layers_data[:-1]) + target_l['thickness']/2
    sigma_v_tot = vertical_stress(H_depth_tot, target_l['rho'])
    mb_dyn, s_dyn, a_dyn = hoek_brown_params(gsi_val, mi_val, D_factor)
    ucs_t_dyn = apply_thermal_degradation(ucs_0_r, T_source_max, BETA_CONST)
    sigma_cm = ucs_t_dyn * (s_dyn ** a_dyn)
    p_str_final = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS))
    avg_pore_p = float(np.mean(pore_pressure[idx_closest, :]))
    def fos_with_pore_pressure(pillar_strength, sigma_v, pore_pressure, B_skempton=0.9):
        sigma_v_eff = max(sigma_v - B_skempton * pore_pressure, 0.01)
        return pillar_strength / sigma_v_eff
    fos_final = fos_with_pore_pressure(p_str_final, sigma_v_tot, avg_pore_p)
    t1,t2,t3 = st.tabs([t('tab_mass'), t('tab_thermal'), t('tab_stability')])
    with t1:
        st.subheader(t('hb_class'))
        c1r,c2r = st.columns(2)
        with c1r:
            st.latex(t('hb_mb', mb=mb_dyn))
            st.caption(t('hb_caption_mb', mi=mi_val))
            st.latex(t('hb_s', s=s_dyn))
            st.caption(t('hb_caption_s', gsi=gsi_val))
        with c2r:
            hb_ratio = (s_dyn ** a_dyn)
            strength_red_perc = (1.0 - hb_ratio) * 100.0
            st.markdown(t('hb_interpret', gsi=gsi_val, perc=strength_red_perc))
    with t2:
        st.subheader(t('thermal_params'))
        params_df = pd.DataFrame({t('param_table_param'): [t('modulus'), t('alpha'), t('temp0')],
                                  t('param_table_value'): [f"{E_MODULUS_R/1e6:.1f} MPa", f"{ALPHA_THERM} 1/°C", "20 °C"],
                                  t('param_table_reason'): [t('modulus_reason'), t('alpha_reason'), t('temp0_reason')]})
        st.table(params_df)
        st.markdown(t('ucs_decay'))
        st.latex(t('ucs_decay_eq', ucs=ucs_t_dyn))
        st.write(t('ucs_interpret', temp=T_source_max, perc=((1 - ucs_t_dyn/(ucs_0_r))*100)))
        st.markdown(t('thermal_stress'))
        st.latex(t('thermal_stress_eq', sigma=float(np.nanmax(sigma_thermal))))
    with t3:
        st.subheader(t('pillar_stability'))
        st.latex(t('fos_eq', fos=fos_final))
        st.write(t('pillar_wilson', w=rec_width, sv=sigma_v_tot, y=y_zone))
        st.markdown("---")
        st.write(t('references'))
        for ref in [t('ref1'), t('ref2'), t('ref3'), t('ref4')]:
            st.markdown(f"📖 {ref}")
        if fos_final < 1.3:
            st.error(t('conclusion_danger', fos=fos_final))
        else:
            st.success(t('conclusion_safe', fos=fos_final))
    st.markdown("---")
    with st.expander(t('methodology_expander')):
        st.markdown("#### Ushbu model quyidagi fundamental ilmiy ishlar asosida tuzilgan:")
        for r in [
            t('ref1'), t('ref2'), t('ref3'), t('ref4'),
            "**Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics for Underground Mining. Springer.",
            "**Peck, R. B. (1969).** Deep excavations and tunneling in soft ground. *7th ICSMFE*, Mexico City.",
            "**O'Reilly, M. P., & New, B. M. (1982).** Settlements above tunnels in the UK. *Tunnelling '82*, IMM London.",
            "**Darcy, H. (1856).** Les fontaines publiques de la ville de Dijon. Dalmont, Paris.",
            "**Terzaghi, K. (1943).** Theoretical Soil Mechanics. Wiley, New York."
        ]:
            st.write(r)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device} | FOS ± σ = {fos_analytic:.2f} ± {fos_std_analytic:.3f}")
