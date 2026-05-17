import streamlit as st
st.set_page_config(page_title="UCG Research Platform", layout="wide", initial_sidebar_state="expanded")
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.stats import linregress, norm as gaussian_dist
from scipy.integrate import trapezoid
import time
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import io
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('default')
import sys
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import logging
from scipy.signal import savgol_filter

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
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

if "language" not in st.session_state:
    st.session_state.language = "uz"
if "live_history_df" not in st.session_state:
    st.session_state.live_history_df = pd.DataFrame(columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m'])

EPS = 1e-6
PARAMS = {
    "phi_deg": 35.0,
    "cohesion": 5e6,
    "alpha_thermal": 3e-5,
    "gas_temp": 1100,
    "subsidence_rate": 0.012,
    "thermal_damage_beta": 0.002,
    "extraction_ratio": 0.6,
    "E_mass": 25e9
}

TRANSLATIONS = {
    'uz': {
        'app_title': "Ilmiy tadqiqot platformasi - Yer yuzasi deformatsiyasi monitoringi",
        'app_subtitle': "Termo-Mexanik (TM) tahlil va selek o'lchami optimizatsiyasi",
        'sidebar_header_params': "⚙️ Umumiy parametrlar",
        'formula_show': "Formulalarni ko'rish:",
        'project_name': "Loyiha nomi:",
        'process_time': "Jarayon vaqti (soat):",
        'num_layers': "Qatlamlar soni:",
        'tensile_model': "Tensile modeli:",
        'rock_props': "💎 Jins xususiyatlari",
        'disturbance': "Disturbance Factor (D):",
        'poisson': "Poisson koeffitsiyenti (ν):",
        'stress_ratio': "Stress Ratio (k = σh/σv):",
        'tensile_params': "📐 Cho'zilish va selek",
        'thermal_decay_label': "Termal degradatsiya (β):",
        'combustion': "🔥 Yonish va termal",
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
        'pillar_strength': "Selek mustahkamligi (σp)",
        'plastic_zone': "Plastik zona (y)",
        'cavity_volume': "Kamera hajmi",
        'max_permeability': "Maks. o'tkazuvchanlik",
        'ai_recommendation': "Analitik tavsiya (selek)",
        'monitoring_header': "📊 {obj_name}: Monitoring va ekspert xulosasi",
        'subsidence_title': "📉 Yer yuzasi cho'kishi (cm)",
        'thermal_deform_title': "🔥 Gorizontal siljish (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown konvertlari",
        'scientific_analysis': "📋 Ilmiy tahlil",
        'fos_red': "🔴 FOS < 1.0: Buzilish",
        'fos_yellow': "🟡 FOS 1.0–1.5: Beqaror",
        'fos_green': "🟢 FOS > 1.5: Barqaror",
        'tm_field_title': "🔥 TM Maydoni va selek interferensiyasi",
        'temp_subplot': "Harorat maydoni (°C) + Gaz oqimi",
        'fos_subplot': "FOS + AI Collapse Prediction (NN) + Yielded Zones",
        'gas_flow': "Gaz oqimi",
        'shear': "Shear",
        'tensile': "Tensile",
        'ai_collapse': "AI Collapse (NN)",
        'monitoring_panel': "📊 {obj_name}: Kompleks monitoring paneli",
        'pillar_live': "Selek mustahkamligi",
        'rec_width_live': "Tavsiya: Selek eni",
        'max_subsidence_live': "Maks. cho'kish",
        'process_stage': "Jarayon bosqichi",
        'stage_active': "Faol",
        'stage_cooling': "Sovish",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'ai_monitor_desc': "Real-vaqt sensor ma'lumotlari va anomaliya aniqlash",
        'ai_steps': "Simulyatsiya qadamlari soni:",
        'ai_run_btn': "▶️ AI Monitoringni Ishga Tushirish",
        'ai_stop_btn': "⏹ To'xtatish",
        'advanced_analysis': "🔍 Chuqurlashtirilgan dinamik tahlil va metodik asoslash",
        'tab_mass': "🏗️ Massiv parametrlari",
        'tab_thermal': "🔥 Termal degradatsiya",
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
        'well_config': "Quduqlar konfiguratsiyasi",
        'well_distance': "Quduqlar orasidagi masofa (m):",
        'warning_cavity_width': "Ogohlantirish: Selek kengligi quduqlar masofasidan katta. cavity_width=1m deb olindi.",
        'ucg_stages_title': "UCG Yonish Bosqichlari (1-2-3 sxemasi) – Ilmiy Model",
        'select_stage': "Bosqichni tanlang:",
        'geomech_state': "Geomexanik Holat (Yangi Ilmiy Model)",
        'auto_animation': "Avtomatik animatsiya (1→2→3 bosqichlar)",
        'animation_done': "Animatsiya yakunlandi.",
        'pillar_annotation': "HIMOYA SELEGI (PILLAR)",
        'system_entropy': "Tizim entropiyasi (noaniqlik)",
    },
    'en': {
        'app_title': "Scientific Research Platform - Surface Deformation Monitoring",
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
        'ucg_stages_title': "UCG Burning Stages (1-2-3 scheme) – Scientific Model",
        'select_stage': "Select stage:",
        'geomech_state': "Geomechanical State (New Scientific Model)",
        'auto_animation': "Auto animation (1→2→3 stages)",
        'animation_done': "Animation finished.",
        'pillar_annotation': "PROTECTIVE PILLAR",
        'system_entropy': "System entropy (uncertainty)",
    },
    'ru': {
        'app_title': "Научно-исследовательская платформа – Мониторинг деформаций поверхности",
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
        'ucg_stages_title': "Стадии горения UCG (схема 1-2-3) – Научная модель",
        'select_stage': "Выберите стадию:",
        'geomech_state': "Геомеханическое состояние (Новая научная модель)",
        'auto_animation': "Авто анимация (1→2→3 стадии)",
        'animation_done': "Анимация завершена.",
        'pillar_annotation': "ЗАЩИТНЫЙ ЦЕЛИК",
        'system_entropy': "Системная энтропия (неопределённость)",
    }
}

FORMULA_OPTIONS = {
    'uz': ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Termal shikastlanish va o'tkazuvchanlik",
           "3. Termal kuchlanish va cho'zilish", "4. Selek va cho'kish"],
    'en': ["Close", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"],
    'ru': ["Закрыть", "1. Разрушение Хука-Брауна (2018)", "2. Термическое повреждение и проницаемость",
           "3. Термическое напряжение и растяжение", "4. Целик и оседание"]
}

def t(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

# -------------------------- Fizik funksiyalar --------------------------
def hoek_brown_sig1(s3, sigci, mb, s, a):
    """Hoek-Brown 2018 sigma1 hisobi (MPa)."""
    s3e = np.maximum(s3, 0)
    term = mb * (s3e/(sigci+EPS)) + s
    return s3e + sigci * np.maximum(term, 0)**a

def hoek_brown_params(GSI, mi, D):
    """Hoek-Brown 2018 parametrlarini hisoblash."""
    mb = mi * np.exp((GSI - 100)/(28 - 14*D))
    s = np.exp((GSI - 100)/(9 - 3*D))
    a = 0.5 + (np.exp(-GSI/15) - np.exp(-20/3))/6
    return mb, s, a

def tensile_strength_hb2018(sigci, mb, s):
    """Hoek-Brown 2018 bo'yicha cho'zilish mustahkamligi (MPa)."""
    return s * sigci / (mb + EPS)

def thermal_damage(T, beta=PARAMS["thermal_damage_beta"]):
    return 1 - np.exp(-beta * np.maximum(T-20, 0))

def apply_thermal_degradation(ucs0, T, beta):
    return np.clip(ucs0 * (1 - thermal_damage(T, beta)), 0.5, None)

def thermal_conductivity(T, k0=2.5):
    """Ko'mir issiqlik o'tkazuvchanligi (W/m·K) – kvadratik pasayish."""
    return np.clip(k0 * (1 - 0.0003*(T-20) + 1e-7*(T-20)**2), 0.5, None)

def specific_heat(T):
    """Ko'mirning solishtirma issiqlik sig'imi (J/kg·K) – piroliz piki bilan."""
    cp = 960 + 0.14*T
    cp += 400 * np.exp(-((T-450)**2)/(2*30**2))
    return np.clip(cp, 900, 3000)

def young_modulus_temperature(T):
    """Ko'mir elastiklik moduli (Pa) – eksponensial yumshatish."""
    return np.clip(5e9 * np.exp(-0.0018*(T-20)), 0.15*5e9, 5e9)

def vertical_stress(depth, density):
    return density * 9.81 * depth / 1e6

def pore_pressure_field(T, depth, perm, water_table=20):
    hydro = np.maximum(0, depth - water_table) * 1000 * 9.81
    gas_p = 1e5 + 50*(T-25)
    perm_eff = 1e5 * np.log10(perm/1e-15 + 1)
    return (hydro + gas_p + perm_eff)/1e6

def kirsch_stress(x, z, sh, sv, a, pp=0):
    r = np.sqrt(x**2 + z**2)
    r = np.maximum(r, a + 1e-3)
    th = np.arctan2(z, x)
    a2 = (a/r)**2
    a4 = (a/r)**4
    c2 = np.cos(2*th)
    s2 = np.sin(2*th)
    sr = (sh+sv)/2*(1-a2) + (sh-sv)/2*(1-4*a2+3*a4)*c2 - pp
    st = (sh+sv)/2*(1+a2) - (sh-sv)/2*(1+3*a4)*c2 - pp
    tr = -(sh-sv)/2*(1+2*a2-3*a4)*s2
    return sr, st, tr

def principal_stresses(sx, sy, txy):
    avg = (sx+sy)/2
    R = np.sqrt(((sx-sy)/2)**2 + txy**2)
    return avg+R, avg-R

def solve_heat_equation(T, Q, rho, cp, k, dx, dz, dt, h_conv, T_air, n):
    alpha = k/(rho*cp)
    dt_max = 1./(2*np.max(alpha)*(1/dx**2+1/dz**2))
    dt = min(dt, 0.8*dt_max)
    for _ in range(n):
        T_old = T.copy()
        Txx = (T_old[1:-1,2:] - 2*T_old[1:-1,1:-1] + T_old[1:-1,:-2])/dx**2
        Tzz = (T_old[2:,1:-1] - 2*T_old[1:-1,1:-1] + T_old[:-2,1:-1])/dz**2
        T_new = T_old.copy()
        T_new[1:-1,1:-1] = T_old[1:-1,1:-1] + dt*(alpha[1:-1,1:-1]*(Txx+Tzz) + Q[1:-1,1:-1]/(rho[1:-1,1:-1]*cp[1:-1,1:-1]))
        T_new[:,0] = T_new[:,1]; T_new[:,-1] = T_new[:,-2]
        T_new[-1,:] = T_new[-2,:]
        T_new[0,:] = T_new[1,:] + dz*h_conv/k[0,:]*(T_air - T_new[0,:])
        T = T_new.copy()
    return T

def evolving_cavity_radius(time_h, T_field, beta):
    dmg = thermal_damage(T_field, beta)
    return np.clip(5 + 0.015*np.mean(dmg)*time_h, 5, 40)

@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field(time_h, T_max, burn_dur, total_depth, source_z, grid_shape):
    D = 8.5e-7
    x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, grid_shape[1])
    z_axis = np.linspace(0, total_depth+50, grid_shape[0])
    dx = x_axis[1]-x_axis[0]
    dz = z_axis[1]-z_axis[0]
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
    T = np.full_like(grid_x, 25.0)
    rho = np.full_like(T, 1400.0)
    cp = specific_heat(T)
    k = thermal_conductivity(T)
    total_time = max(burn_dur, time_h)*3600
    dt_max = 1./(2*np.max(k/(rho*cp))*(1/dx**2+1/dz**2))
    dt = 0.8*dt_max
    n_steps = min(max(int(total_time/dt), 20), 5000)
    dt = total_time/n_steps
    v_burn = 0.02
    sources = [
        {'x0':-total_depth/3,'start':0,'moving':False},
        {'x0':0,'start':40,'moving':True,'v':v_burn},
        {'x0':total_depth/3,'start':80,'moving':False}
    ]
    for step in range(n_steps):
        t_h = (step+1)*dt/3600
        Q = np.zeros_like(T)
        for src in sources:
            if t_h <= src['start']: continue
            dt_s = (t_h - src['start'])*3600
            x_c = src['x0'] + src['v']*dt_s if src['moving'] else src['x0']
            elapsed = t_h - src['start']
            cur_T = T_max if elapsed<=burn_dur else 25 + (T_max-25)*np.exp(-0.03*(elapsed-burn_dur))
            pen = np.sqrt(4*D*dt_s) + 15
            dist2 = (grid_x-x_c)**2 + (grid_z-source_z)**2
            Q += (cur_T-25)*np.exp(-dist2/(pen**2))
        T = solve_heat_equation(T, Q, rho, cp, k, dx, dz, dt, h_conv=10, T_air=25, n=1)
    return T, x_axis, z_axis, grid_x, grid_z

# --------------------------- UI va asosiy hisoblar ---------------------------
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
url = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/#ucg-termo-mexanik-dinamik-3-d-model"

@st.cache_data
def generate_qr(link: str) -> bytes:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

qr_img_bytes = generate_qr(url)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

st.sidebar.header(t('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(t('formula_show'), formula_opts)
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
            st.latex(r"\sigma_{p} = (UCS \cdot \eta) \cdot \left( \frac{w}{H} \right)^{0.5}")
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
beta_thermal = st.sidebar.slider(t('thermal_decay_label'), min_value=0.0005, max_value=0.02, value=PARAMS["thermal_damage_beta"], step=0.0005)

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40, min_value=1)
T_source_max = st.sidebar.slider(t('max_temp'), 600, 1200, PARAMS["gas_temp"])

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

grid_shape = (80, 100)
source_z = total_depth - (layers_data[-1]['thickness'] / 2)
H_seam = layers_data[-1]['thickness']

temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape)

dx_val = x_axis[1] - x_axis[0]
dz_val = z_axis[1] - z_axis[0]

E_field = young_modulus_temperature(temp_2d)
alpha_field = thermal_expansion_temperature(temp_2d)
grid_rho = np.zeros_like(temp_2d)
layer_bounds = [(l['z_start'], l['z_start'] + l['thickness']) for l in layers_data]
for i, (z0, z1) in enumerate(layer_bounds):
    mask = (grid_z >= z0) & (grid_z < z1 if i < len(layer_bounds)-1 else True)
    layer = layers_data[i]
    grid_rho[mask] = density_temperature(layer['rho'], temp_2d[mask])

grid_sigma_v = np.zeros((len(z_axis), len(x_axis)))
for i in range(len(z_axis)):
    if i == 0:
        grid_sigma_v[0,:] = 0
    else:
        dz_i = z_axis[i] - z_axis[i-1]
        grid_sigma_v[i,:] = grid_sigma_v[i-1,:] + grid_rho[i,:] * 9.81 * dz_i / 1e6
grid_sigma_h = k_ratio * grid_sigma_v

cavity_radius = evolving_cavity_radius(time_h, temp_2d, beta_thermal)
perm_tmp = 1e-15 * np.exp(8 * thermal_damage(temp_2d, beta_thermal))
pore_pressure = pore_pressure_field(temp_2d, grid_z, perm_tmp)

sigma_rr, sigma_tt, tau_rt = kirsch_stress(grid_x, grid_z - source_z,
                                           grid_sigma_h, grid_sigma_v,
                                           cavity_radius, pore_pressure)

delta_T = np.maximum(temp_2d - 20, 0)
sigma_thermal = (E_field * alpha_field * delta_T) / (1 - nu_poisson + EPS) / 1e6
relax_factor = np.exp(-2.5 * thermal_damage(temp_2d, beta_thermal))
sigma_thermal *= relax_factor
sigma_x_total = sigma_rr - sigma_thermal
sigma_z_total = sigma_tt - sigma_thermal

dT_dx, dT_dz = np.gradient(temp_2d, dx_val, dz_val)
G = E_field / (2 * (1 + nu_poisson))
tau_thermal = G * alpha_field * dT_dx * dT_dz / 1e6
tau_rt += tau_thermal

sigma1_act, sigma3_act = principal_stresses(sigma_x_total, sigma_z_total, tau_rt)

grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
for i, (z0, z1) in enumerate(layer_bounds):
    mask = (grid_z >= z0) & (grid_z < z1 if i < len(layer_bounds)-1 else True)
    layer = layers_data[i]
    grid_ucs[mask] = layer['ucs']
    mb_i, s_i, a_i = hoek_brown_params(layer['gsi'], layer['mi'], D_factor)
    grid_mb[mask] = mb_i
    grid_s_hb[mask] = s_i
    grid_a_hb[mask] = a_i

sigma_ci = apply_thermal_degradation(grid_ucs, temp_2d, beta_thermal)
damage = np.clip(sigma1_act / (sigma_ci * (grid_mb*sigma3_act/(sigma_ci+EPS) + grid_s_hb)**grid_a_hb + EPS), 0, 1)

void_fraction = gaussian_filter(damage * (temp_2d > 600), sigma=2)
void_mask_permanent = void_fraction > 0.5
void_volume = np.sum(void_mask_permanent) * dx_val * dz_val  # m² (2D kesim yuzasi)

volumetric_strain = (sigma_thermal * 1e6) / (E_field + EPS)
perm = 1e-15 * np.exp(8*damage + 12 * volumetric_strain)
perm_x = perm * 5
perm_z = perm
perm = np.clip(perm, 1e-16, 1e-10)

T_kelvin = temp_2d + 273.15
M_gas = 0.028
R_universal = 8.314
pressure_field = 1e5 + 50 * (T_kelvin - 293.15)
gas_density = (pressure_field * M_gas) / (R_universal * T_kelvin)

dp_dx, dp_dz = np.gradient(pressure_field, dx_val, dz_val)
mu_gas = 3e-5
vx = -perm_x * dp_dx / mu_gas
vz = -perm_z * dp_dz / mu_gas
gas_velocity = np.sqrt(vx**2 + vz**2)

phi_rad = np.radians(PARAMS["phi_deg"])
influence_radius = 0.45 * total_depth   # Peck (1969) bo'yicha
c_subs = PARAMS["subsidence_rate"]
Smax = H_seam * 0.04
subsidence_t = Smax * (1 - np.exp(-c_subs * time_h))
subsidence_raw = -subsidence_t * np.exp(-(x_axis**2) / (2 * influence_radius**2))
subsidence_raw = savgol_filter(subsidence_raw, window_length=min(11, len(x_axis)-1 if len(x_axis)%2!=0 else len(x_axis)-2), polyorder=3)
subs_grad = np.gradient(subsidence_raw, dx_val)
void_factor = 1 + 0.35 * float(np.mean(void_mask_permanent))
sub_p = subsidence_raw * void_factor + 0.08 * subs_grad
horizontal_disp_cm = -np.gradient(sub_p, dx_val) * 100

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
for _ in range(30):
    p_strength = sigma_cm * (w_sol / (H_seam + EPS))**0.5
    ratio = sv_seam / (p_strength + EPS)
    if ratio >= 1.0:
        y_zone_calc = (H_seam / 2.0) * (np.sqrt(ratio) - 1.0)
    else:
        y_zone_calc = 0.0
    new_w = 2.0 * max(y_zone_calc, 1.5) + E_MIN_CORE
    if abs(new_w - w_sol) < 0.05:
        break
    w_sol = 0.6 * new_w + 0.4 * w_sol
rec_width = np.round(w_sol, 1)
pillar_strength = p_strength
y_zone = max(y_zone_calc, 1.5)

rock_factor = (target_layer['gsi']/100) * (target_layer['mi']/20) * (1 - D_factor)
thermal_factor = np.exp(-0.002 * avg_t_p)
analytical_width = 4 + 0.12 * ucs_seam * rock_factor * thermal_factor * (1 + nu_poisson) * np.sqrt(k_ratio)
analytical_width = np.clip(analytical_width, 5, 100)

st.info("""
**Ilmiy ogohlantirish:** Kirsch stress yechimi kvazistatik bo'shliq faraziga asoslanadi.
Katta deformatsiyalar va geometriya o'zgarishi uchun FEM remeshing talab etiladi.
Shuningdek, to'liq THM bog'lanish (T↔σ↔k↔p) hozircha qayta aloqa siklida to'liq amalga oshirilmagan.
""")

st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
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

cavity_width_global = well_distance - rec_width
if cavity_width_global < 1.0:
    st.warning(t('warning_cavity_width'))
    cavity_width_global = 1.0

CONFINEMENT = 0.65
RELAX = 0.15

layer_bounds_adv = [(l['z_start'], l['z_start'] + l['thickness'], l) for l in layers_data]
sigma_v_coal = 0.0
for l in layers_data[:-1]:
    sigma_v_coal += l['rho'] * 9.81 * l['thickness']
sigma_v_coal += layers_data[-1]['rho'] * 9.81 * (H_seam / 2)
sigma_v_coal = sigma_v_coal / 1e6
Hc = H_seam * np.sqrt(sigma_v_coal / (layers_data[-1]['ucs'] + EPS))
Hc = np.clip(Hc, H_seam, H_seam * 4)

def compute_advanced_fos(grid_x, grid_z, active_wells, well_x, source_z, h_seam, cavity_width,
                         temp_field, sigma_v_field, layers_data, layer_bounds,
                         E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa):
    fos = np.full_like(grid_x, 3.0)
    for px_idx in active_wells:
        px = well_x[px_idx]
        dist = np.sqrt((grid_x - px)**2 + (grid_z - source_z)**2)
        delta_z_local = source_z - grid_z
        T = temp_field
        delta_T = np.maximum(T - 20, 0)
        thermal_zone = dist < (h_seam * 3)
        for (top, bot, layer) in layer_bounds:
            mask = (grid_z >= top) & (grid_z < bot)
            if not np.any(mask): continue
            ucs_l = layer['ucs']
            gsi = layer['gsi']; mi = layer['mi']
            mb, s, a = hoek_brown_params(gsi, mi, D_factor)
            sigma_v = sigma_v_field[mask]
            delta_T_m = delta_T[mask]
            sigma_ci_T = apply_thermal_degradation(ucs_l, delta_T_m, beta_thermal)
            sigma_3 = K0 * sigma_v * (0.6 + 0.4 * (1 - thermal_damage(delta_T_m, beta_thermal)))
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
            sigma_limit = hoek_brown_sig1(sigma_3, sigma_ci_T, mb, s, a)
            fos_val = np.clip(sigma_limit / (sigma_1 + EPS), 0, 3)
            yield_mask = sigma_1 > (sigma_limit * 0.85)
            fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
            fos_sub = fos[mask]
            fos_sub = np.minimum(fos_sub, fos_val)
            fos[mask] = fos_sub
            if layer == layers_data[-1]:
                dome_width = (cavity_width / 2) * np.clip(1 - delta_z_local[mask] / (Hc + EPS), 0, 1)
                failure_zone = fos_val < 1.2
                dome_condition = (delta_z_local[mask] > 0) & (delta_z_local[mask] < Hc) & (np.abs(grid_x[mask] - px) < dome_width) & failure_zone
                if np.any(dome_condition):
                    decay = np.clip(1 - (delta_z_local[mask][dome_condition] / (Hc + EPS)), 0.3, 1.0)
                    fos_sub[dome_condition] = np.minimum(fos_sub[dome_condition], decay)
                    fos[mask] = fos_sub
    for px_idx in active_wells:
        px = well_x[px_idx]
        a = cavity_width / 2
        b = h_seam / 2
        cavity_ellipse = ((grid_x - px)**2 / (a**2 + EPS) + (grid_z - source_z)**2 / (b**2 + EPS)) < 1
        fos[cavity_ellipse] = np.nan  # cavity ichi FOS aniqlanmagan
    bottom_layer = layers_data[-1]
    bottom_boundary = bottom_layer['z_start'] + bottom_layer['thickness']
    fos[grid_z > bottom_boundary] = 2.5
    all_wells = [0, 1, 2]
    for i in all_wells:
        if i not in active_wells:
            px = well_x[i]
            pillar_mask = (np.abs(grid_x - px) < h_seam * 1.5) & (np.abs(grid_z - source_z) < h_seam * 1.2)
            fos[pillar_mask] = 2.5
    if active_wells == [0, 2]:
        selek_eni = np.abs(well_x[0] - well_x[2]) - cavity_width
        mb_p, s_p, a_p = hoek_brown_params(layers_data[-1]['gsi'], layers_data[-1]['mi'], D_factor)
        sigma_cm_pillar = ucs_coal_MPa * (s_p ** a_p)
        pillar_strength_pillar = sigma_cm_pillar * (selek_eni / (h_seam + EPS)) ** 0.5
        fos_pillar = pillar_strength_pillar / (sigma_v_coal_MPa + EPS)
        pillar_zone = (np.abs(grid_x - well_x[1]) < selek_eni/2) & (np.abs(grid_z - source_z) < h_seam)
        fos[pillar_zone] = np.maximum(fos[pillar_zone], fos_pillar)
    return np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)

fos_2d = compute_advanced_fos(
    grid_x, grid_z, [0,1,2], [-well_distance, 0, well_distance], source_z, H_seam, cavity_width_global,
    temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
    E=PARAMS["E_mass"], alpha=PARAMS["alpha_thermal"], nu=nu_poisson, K0=nu_poisson/(1-nu_poisson),
    Hc=Hc, sigma_v_coal_MPa=sigma_v_coal, ucs_coal_MPa=layers_data[-1]['ucs']
)

with c2:
    st.subheader(t('ucg_stages_title'))
    well_x_pos = [-well_distance, 0, well_distance]
    states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
    stage = st.select_slider(t('select_stage'), options=[1, 2, 3], value=1, key="ucg_stage")
    active_wells = states_132[stage]
    cavity_width_stage = cavity_width_global

    fos_stage = compute_advanced_fos(
        grid_x, grid_z, active_wells, well_x_pos, source_z, H_seam, cavity_width_stage,
        temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
        E=PARAMS["E_mass"], alpha=PARAMS["alpha_thermal"], nu=nu_poisson, K0=nu_poisson/(1-nu_poisson),
        Hc=Hc, sigma_v_coal_MPa=sigma_v_coal, ucs_coal_MPa=layers_data[-1]['ucs']
    )

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
            wells_s = states_132[s]
            fos_s = compute_advanced_fos(
                grid_x, grid_z, wells_s, well_x_pos, source_z, H_seam, cavity_width_global,
                temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
                E=PARAMS["E_mass"], alpha=PARAMS["alpha_thermal"], nu=nu_poisson, K0=nu_poisson/(1-nu_poisson),
                Hc=Hc, sigma_v_coal_MPa=sigma_v_coal, ucs_coal_MPa=layers_data[-1]['ucs']
            )
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

# -------------------- AI modellar va xavf tahlili --------------------
def physics_features(T, s1, s3, depth, ucs_seam_val):
    dmg = thermal_damage(T, beta_thermal)
    strength = ucs_seam_val * (1 - dmg)
    fos = strength / (s1 + EPS)
    energy = T * s1 / (depth + 1)
    return np.column_stack([T, s1, s3, depth, dmg, fos, energy])

@st.cache_data
def generate_physics_dataset(temp_field, sigma1, sigma3, depth, ucs_seam_val):
    feat = physics_features(temp_field.flatten(), sigma1.flatten(), sigma3.flatten(), depth.flatten(), ucs_seam_val)
    fos = feat[:,5]
    energy = feat[:,6]
    collapse = ((fos < 1.0) | (temp_field.flatten() > 800) | (energy > 4000)).astype(int)
    return feat, collapse

X_ai, y_ai = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z, ucs_seam)

if PT_AVAILABLE:
    class HybridPINN(nn.Module):
        def __init__(self, input_dim):
            super().__init__()
            self.input_dim = input_dim
            self.net = nn.Sequential(
                nn.Linear(input_dim, 128), nn.Tanh(),
                nn.Linear(128, 128), nn.Tanh(),
                nn.Linear(128, 64), nn.Tanh(),
                nn.Linear(64, 1), nn.Sigmoid()
            )
        def forward(self, x):
            if x.shape[1] != self.input_dim:
                raise ValueError(f"Expected {self.input_dim} features but got {x.shape[1]}")
            return self.net(x)

    def train_hybrid_model(X, y, sigma1, sigma_ci, temp, damage):
        y = np.clip(y, 0, 1)
        model = HybridPINN(input_dim=X.shape[1]).to(device)
        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        y_t = torch.tensor(y, dtype=torch.float32).view(-1,1).to(device)
        sigma1_t = torch.tensor(sigma1, dtype=torch.float32).to(device)
        sigma_ci_t = torch.tensor(sigma_ci, dtype=torch.float32).to(device)
        temp_t = torch.tensor(temp, dtype=torch.float32).to(device)
        damage_t = torch.tensor(damage, dtype=torch.float32).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=0.0003)
        for epoch in range(80):
            opt.zero_grad()
            pred = model(X_t)
            bce = nn.BCELoss()(pred, y_t)
            loss = bce
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        return model

def train_random_forest(X_scaled, y):
    rf = RandomForestClassifier(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_scaled, y)
    return rf

@st.cache_resource
def get_ensemble_model(X, y, sigma1, sigma_ci, temp, damage):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    if PT_AVAILABLE:
        model = train_hybrid_model(X_train, y_train, sigma1[:len(X_train)], sigma_ci[:len(X_train)],
                                   temp[:len(X_train)], damage[:len(X_train)])
        rf = train_random_forest(X_train, y_train)
    else:
        model = None
        rf = train_random_forest(X_train, y_train)
    return model, rf, scaler, X_test, y_test

hybrid_model, rf_model, scaler, X_test, y_test = get_ensemble_model(
    X_ai, y_ai, sigma1_act.flatten(), sigma_ci.flatten(),
    temp_2d.flatten(), damage.flatten()
)

if rf_model is not None:
    pred_test = rf_model.predict(X_test)
    acc = accuracy_score(y_test, pred_test)
    st.write(f"AI Model Validatsiyasi: Accuracy = {acc:.3f}")
    unique_y = np.unique(y_test)
    if len(unique_y) > 1:
        auc = roc_auc_score(y_test, pred_test)
        st.write(f"AUC = {auc:.3f}")
    else:
        st.write("AUC hisoblanmadi (faqat bir sinf mavjud).")

def predict_collapse(model, rf, scaler, X_raw):
    if model is None and rf is None:
        return np.zeros((X_raw.shape[0], 1))
    X_scaled = scaler.transform(X_raw)
    if model is not None:
        with torch.no_grad():
            nn_pred = model(torch.tensor(X_scaled, dtype=torch.float32).to(device)).cpu().numpy()
    else:
        nn_pred = np.zeros((X_raw.shape[0], 1))
    try:
        rf_pred = rf.predict_proba(X_scaled)[:,1].reshape(-1,1)
    except IndexError:
        rf_pred = rf.predict_proba(X_scaled)[:,-1].reshape(-1,1)
    return 0.6*nn_pred + 0.4*rf_pred

collapse_pred = np.zeros_like(temp_2d)
try:
    feat_pred = physics_features(temp_2d.flatten(), sigma1_act.flatten(),
                                 sigma3_act.flatten(), grid_z.flatten(), ucs_seam)
    collapse_pred = predict_collapse(hybrid_model, rf_model, scaler, feat_pred).reshape(temp_2d.shape)
except Exception as e:
    logger.error(f"Collapse prediction error: {str(e)}")
    collapse_pred = np.zeros_like(temp_2d)

weights = np.array([0.4, 0.3, 0.2, 0.1])
max_perm = np.max(perm)
if max_perm == 0:
    max_perm = 1e-20
risk_index_var = (
    weights[0]*collapse_pred +
    weights[1]*(1 - fos_2d/3.0) +
    weights[2]*(perm / max_perm) +
    weights[3]*(temp_2d / np.max(temp_2d))
)
risk_index_var = np.maximum(0, risk_index_var)
risk_flat = risk_index_var.flatten()
risk_prob = risk_flat / (np.sum(risk_flat) + 1e-12)
entropy = -np.sum(risk_prob * np.log(risk_prob + 1e-12))
st.metric(t('system_entropy'), f"{entropy:.3f}")

# -------------------- Qo'shimcha analizlar --------------------
# Sobol sezgirlik tahlili
if SALIB_AVAILABLE:
    with st.expander("📊 Global sezgirlik tahlili (Sobol')"):
        st.markdown("Hoek-Brown parametrlarining sezgirligi.")
        problem = {
            'num_vars': 4,
            'names': ['UCS', 'GSI', 'D', 'Temperature'],
            'bounds': [[10, 80], [20, 80], [0, 1], [20, 1200]]
        }
        param_values = saltelli.sample(problem, 1024)
        def sobol_model(params):
            ucs, gsi, d, temp = params[:,0], params[:,1], params[:,2], params[:,3]
            mb, s, a = hoek_brown_params(gsi, 10, d)
            ucs_T = apply_thermal_degradation(ucs, temp, beta_thermal)
            sigma_cm = ucs_T * (s**a)
            return sigma_cm
        Y = sobol_model(param_values)
        Si = sobol.analyze(problem, Y)
        st.write("Birinchi tartibli indekslar:", Si['S1'])
        st.write("Umumiy tartibli indekslar:", Si['ST'])

# Monte Carlo FOS
with st.expander("🎲 Monte Carlo Noaniqlik Tahlili"):
    mc_col1, mc_col2 = st.columns([1,2])
    with mc_col1:
        ucs_std_val = st.number_input("UCS standart og'ish (MPa)", value=5.0, min_value=0.1)
        gsi_std_val = st.number_input("GSI standart og'ish", value=5.0, min_value=0.1)
        n_mc = st.selectbox("Simulyatsiya soni", [500,1000,2000,5000], index=1)
    with mc_col2:
        fos_mc, pf = monte_carlo_fos(layers_data[-1]['ucs'], ucs_std_val,
                                     layers_data[-1]['gsi'], gsi_std_val,
                                     layers_data[-1]['mi'],
                                     D_factor, avg_t_p, H_seam,
                                     depth_seam, avg_rho, rec_width, beta_thermal, n_sim=n_mc)
        fig_mc = go.Figure()
        fig_mc.add_histogram(x=fos_mc, nbinsx=40,
                             marker_color=np.where(fos_mc<1.0,'#E74C3C','#27AE60'),
                             name='FOS taqsimoti')
        fig_mc.add_vline(x=1.0, line_color='red', line_dash='dash', annotation_text='FOS=1.0')
        fig_mc.add_vline(x=1.5, line_color='yellow', line_dash='dash', annotation_text='FOS=1.5')
        fig_mc.add_vline(x=np.mean(fos_mc), line_color='cyan', line_dash='dot', annotation_text=f"O'rtacha={np.mean(fos_mc):.2f}")
        fig_mc.update_layout(template='plotly_dark', height=350, title=f"FOS taqsimoti | Failure ehtimoli: {pf*100:.1f}%",
                             xaxis_title='FOS', yaxis_title='Chastota')
        st.plotly_chart(fig_mc, use_container_width=True)
    mc_stats = pd.DataFrame({'Ko\'rsatkich': ['O\'rtacha FOS', 'Mediana', 'Std og\'ish', '5-percentil', '95-percentil', 'Failure ehtimoli'],
                             'Qiymat': [f"{np.mean(fos_mc):.3f}", f"{np.median(fos_mc):.3f}", f"{np.std(fos_mc):.3f}", f"{np.percentile(fos_mc,5):.3f}", f"{np.percentile(fos_mc,95):.3f}", f"{pf*100:.2f}%"]})
    st.dataframe(mc_stats, hide_index=True, use_container_width=True)

# SHAP interpretatsiya
if SHAP_AVAILABLE and rf_model is not None:
    with st.expander("🧠 SHAP Model Interpretatsiyasi"):
        try:
            X_shap, _ = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z, ucs_seam)
            background = shap.sample(X_shap, 100)
            explainer = shap.Explainer(rf_model, background)
            shap_values = explainer(background)
            feature_names = ["Temperature", "Sigma1", "Sigma3", "Depth", "Damage", "FOS", "Energy"]
            st.subheader("SHAP o'zgaruvchanlik ahamiyati")
            fig_shap, ax = plt.subplots()
            shap.summary_plot(shap_values, background, feature_names=feature_names, show=False)
            st.pyplot(fig_shap)
        except Exception as e:
            st.warning(f"SHAP tahlili bajarilmadi: {e}")

# 3D vizualizatsiya
if PYVISTA_AVAILABLE:
    with st.expander("🌋 3D litologik hajm (PyVista)"):
        try:
            nx, ny, nz = 50, 50, 30
            x_pv = np.linspace(x_axis.min(), x_axis.max(), nx)
            z_pv = np.linspace(z_axis.min(), z_axis.max(), nz)
            y_pv = np.linspace(0, 100, ny)
            X, Y, Z = np.meshgrid(x_pv, y_pv, z_pv, indexing='ij')
            from scipy.interpolate import RegularGridInterpolator
            interp_temp = RegularGridInterpolator((z_axis, x_axis), temp_2d)
            pts = np.column_stack([Z.flatten(), X.flatten()])
            T_vol = interp_temp(pts).reshape(nx, ny, nz)
            grid_pv = pv.StructuredGrid(X, Y, Z)
            grid_pv.point_data["temperature"] = T_vol.flatten()
            plotter = pv.Plotter()
            plotter.add_volume(grid_pv, scalars="temperature", cmap="hot")
            st.image(plotter.screenshot(), use_container_width=True)
        except Exception as e:
            st.warning(f"PyVista vizualizatsiyasi amalga oshmadi: {e}")

# ISO hisobot
def generate_full_iso_report(obj_name, lang, layers_data, T_source_max, burn_duration,
                             pillar_strength, analytical_width, fos_2d, risk_map, void_volume,
                             prepared_by, approved_by, doc_number, revision, fig_bytes=None):
    texts = {
        'uz': {
            'h1': "ISO 9001:2015 MUVOFIQDAT HISOBOTI",
            'sec1': "1. LOYIHA UMUMIY TAVSIFI",
            'sec2': "2. GEOMEXANIK QATLAMLAR VA XOSSALARI",
            'sec3': "3. RISKNI BAHOLASH (RISK ASSESSMENT)",
            'sec4': "4. XAVFNI KAMAYTIRISH CHORALARI (MITIGATION)",
            'sec5': "5. MUHANDISLIK XULOSASI VA TAVSIYALAR",
            'fos_label': "Xavfsizlik koeffitsienti (FOS):",
            'ai_label': "Analitik optimallashtirilgan kenglik:",
            'conclusion_title': "Yakuniy qaror:",
            'safe': "✅ TIZIM BARQAROR: Loyiha parametrlari xavfsizlik talablariga javob beradi.",
            'warning': "⚠️ MARGINAL HOLAT: Monitoringni kuchaytirish va qo'shimcha mahkamlash tavsiya etiladi.",
            'danger': "🚨 XAVFLI: O'pirilish xafvi yuqori! Pillar kengligini oshirish yoki termal yukni kamaytirish shart.",
            'risk_ident': "Aniqlangan xavf omillari: termal degradatsiya, yuqori bo'shliq hajmi, FOS < 1.3.",
            'mitigation': "Muhandislik choralari: selek eni oshirish, gaz bosimini kamaytirish, real-vaqt monitoring."
        },
        'en': {
            'h1': "ISO 9001:2015 COMPLIANCE REPORT",
            'sec1': "1. PROJECT OVERVIEW",
            'sec2': "2. GEOMECHANICAL PROPERTIES",
            'sec3': "3. RISK ASSESSMENT",
            'sec4': "4. MITIGATION STRATEGY",
            'sec5': "5. ENGINEERING CONCLUSIONS",
            'fos_label': "Factor of Safety (FOS):",
            'ai_label': "Analytical Optimized Width:",
            'conclusion_title': "Final Decision:",
            'safe': "✅ SYSTEM STABLE: Project parameters meet safety requirements.",
            'warning': "⚠️ MARGINAL STABILITY: Increased monitoring and support recommended.",
            'danger': "🚨 DANGEROUS: High risk of collapse! Increase pillar width or reduce thermal load.",
            'risk_ident': "Identified hazards: thermal degradation, large void volume, FOS < 1.3.",
            'mitigation': "Mitigation: increase pillar width, reduce gas pressure, real-time monitoring."
        },
        'ru': {
            'h1': "ОТЧЕТ О СООТВЕТСТВИИ ISO 9001:2015",
            'sec1': "1. ОБЗОР ПРОЕКТА",
            'sec2': "2. ГЕОМЕХАНИЧЕСКИЕ СВОЙСТВА",
            'sec3': "3. ОЦЕНКА РИСКОВ",
            'sec4': "4. СТРАТЕГИЯ СНИЖЕНИЯ РИСКОВ",
            'sec5': "5. ИНЖЕНЕРНЫЕ ВЫВОДЫ",
            'fos_label': "Коэффициент безопасности (FOS):",
            'ai_label': "Аналитическая оптимизированная ширина:",
            'conclusion_title': "Окончательное решение:",
            'safe': "✅ СИСТЕМА СТАБИЛЬНА: Параметры проекта соответствуют требованиям безопасности.",
            'warning': "⚠️ ПРЕДЕЛЬНАЯ УСТОЙЧИВОСТЬ: Рекомендуется усилить мониторинг и поддержку.",
            'danger': "🚨 ОПАСНО: Высокий риск обрушения! Увеличьте ширину целика или уменьшите термическую нагрузку.",
            'risk_ident': "Выявленные опасности: термическая деградация, большой объем пустот, FOS < 1.3.",
            'mitigation': "Меры: увеличить ширину целика, снизить давление газа, мониторинг в реальном времени."
        }
    }
    t_texts = texts.get(lang, texts['en'])
    doc = Document()
    header = doc.add_heading(f"{t_texts['h1']}\n{obj_name}", level=1)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.style = 'Table Grid'
    meta_table.cell(0,0).text = f"Doc No: {doc_number}"
    meta_table.cell(0,1).text = f"Revision: {revision}"
    meta_table.cell(1,0).text = f"Prepared: {prepared_by}"
    meta_table.cell(1,1).text = f"Approved: {approved_by}"
    doc.add_heading(t_texts['sec1'], level=2)
    p = doc.add_paragraph()
    p.add_run(f"Ob'ekt nomi: ").bold = True
    p.add_run(f"{obj_name}\n")
    p.add_run(f"Maksimal harorat: ").bold = True
    p.add_run(f"{T_source_max} °C\n")
    p.add_run(f"Yonish davomiyligi: ").bold = True
    p.add_run(f"{burn_duration} soat")
    doc.add_heading(t_texts['sec2'], level=2)
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    hdrs = ["Layer Name", "Thick (m)", "UCS (MPa)", "GSI", "mi"]
    for i, h in enumerate(hdrs):
        table.rows[0].cells[i].text = h
    for layer in layers_data:
        row = table.add_row().cells
        row[0].text = layer['name']
        row[1].text = f"{layer['thickness']:.1f}"
        row[2].text = f"{layer['ucs']:.1f}"
        row[3].text = str(layer['gsi'])
        row[4].text = f"{layer['mi']:.1f}"
    doc.add_heading(t_texts['sec3'], level=2)
    doc.add_paragraph(t_texts['risk_ident'])
    avg_risk = np.mean(risk_map)
    doc.add_paragraph(f"O'rtacha xavf indeksi: {avg_risk:.3f}")
    doc.add_paragraph(f"FOS minimal: {np.min(fos_2d):.2f}, maksimal bo'shliq: {void_volume:.1f} m²")
    doc.add_heading(t_texts['sec4'], level=2)
    doc.add_paragraph(t_texts['mitigation'])
    doc.add_paragraph(f"Tavsiya qilingan selek eni: {analytical_width:.1f} m")
    if fig_bytes:
        doc.add_heading("Visual Analysis (Risk Map)", level=2)
        image_stream = io.BytesIO(fig_bytes)
        doc.add_picture(image_stream, width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading(t_texts['sec5'], level=2)
    fos_val = np.nanmean(fos_2d)
    risk_level = "LOW"
    if np.max(risk_map) > 0.75:
        risk_level = "CRITICAL"
    elif np.max(risk_map) > 0.5:
        risk_level = "MEDIUM"
    doc.add_paragraph(f"Risk Level: {risk_level}")
    conclusion_text = ""
    color = RGBColor(0, 128, 0)
    if fos_val < 1.1:
        conclusion_text = t_texts['danger']
        color = RGBColor(255, 0, 0)
    elif fos_val < 1.5:
        conclusion_text = t_texts['warning']
        color = RGBColor(255, 165, 0)
    else:
        conclusion_text = t_texts['safe']
    res_p = doc.add_paragraph()
    res_p.add_run(f"{t_texts['fos_label']} {fos_val:.2f}\n").bold = True
    res_p.add_run(f"{t_texts['ai_label']} {analytical_width:.1f} m\n\n")
    final_run = res_p.add_run(f"{t_texts['conclusion_title']}\n{conclusion_text}")
    final_run.bold = True
    final_run.font.color.rgb = color
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

with st.expander("📄 ISO 9001:2015 Standart Hujjat (.docx)"):
    d1, d2 = st.columns(2)
    with d1:
        iso_lang = st.selectbox("Hujjat tili", ['uz','en','ru'], format_func=lambda x: {'uz':"🇺🇿 O'zbek",'en':"🇬🇧 English",'ru':"🇷🇺 Русский"}[x], key="iso_lang")
        doc_num_input = st.text_input("Hujjat raqami", value="UCG-2026-001")
        revision_inp = st.text_input("Revision", value="A")
    with d2:
        prepared_inp = st.text_input("Prepared by", value="UCG Engineering Team")
        approved_inp = st.text_input("Approved by", value="Chief Engineer")
    if st.button("📄 ISO hujjat yaratish (kengaytirilgan)", type="primary", use_container_width=True):
        with st.spinner("ISO 9001 shablon tayyorlanmoqda..."):
            try:
                fig, ax = plt.subplots(figsize=(6,4))
                im = ax.imshow(risk_index_var, extent=[x_axis[0], x_axis[-1], z_axis[-1], z_axis[0]], cmap='hot', aspect='auto')
                plt.colorbar(im, ax=ax, label='Risk Index')
                ax.set_title('Composite Risk Map')
                ax.set_xlabel('X (m)')
                ax.set_ylabel('Depth (m)')
                buf_img = io.BytesIO()
                plt.savefig(buf_img, format='png', dpi=100)
                buf_img.seek(0)
                plt.close()
                docx_bytes = generate_full_iso_report(
                    obj_name=obj_name, lang=iso_lang, layers_data=layers_data,
                    T_source_max=T_source_max, burn_duration=burn_duration,
                    pillar_strength=pillar_strength, analytical_width=analytical_width,
                    fos_2d=fos_2d, risk_map=risk_index_var,
                    void_volume=void_volume,
                    prepared_by=prepared_inp, approved_by=approved_inp,
                    doc_number=doc_num_input, revision=revision_inp,
                    fig_bytes=buf_img.getvalue()
                )
                st.download_button(label=f"⬇️ {doc_num_input}_Rev{revision_inp}.docx", data=docx_bytes,
                                   file_name=f"{doc_num_input}_Rev{revision_inp}_{pd.Timestamp.now().strftime('%Y%m%d')}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"Hisobot yaratishda xatolik: {e}")

# Live monitoring
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
            sigma_thermal_live = (E_field.mean() * alpha_field.mean() * max(T_avg_live-20,0)) / (1 - 2*nu_poisson + EPS) / 1e6
            pore_pressure_live = pore_pressure_field(T_avg_live, depth_seam, np.mean(perm))
            pillar_live = apply_thermal_degradation(ucs_seam, T_avg_live, beta_thermal) * (rec_width/(H_seam+EPS))**0.5
            FOS_live = pillar_live / (sigma_v_live + sigma_thermal_live + pore_pressure_live + 1e-8)
            FOS_live = np.clip(FOS_live, 0, 5)
            mean_subs = np.mean(Z_subs)
            subs_history_live.append(mean_subs)
            fos_history_live.append(FOS_live)
            width_history_live.append(pillar_width_pred)
            temp_history_live.append(T_avg_live)
            new_row = pd.DataFrame({'step':[step_idx+1],'mean_subsidence_cm':[mean_subs*100],'max_temp_c':[np.max(Z_temp)],'FOS':[FOS_live],'pillar_width_m':[pillar_width_pred]})
            st.session_state.live_history_df = pd.concat([st.session_state.live_history_df, new_row], ignore_index=True).tail(1000).copy()
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
    if 'live_history_df' in st.session_state and not st.session_state.live_history_df.empty:
        st.markdown("---")
        st.subheader("📥 Download Monitoring Results (CSV)")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(label=t('download_data'), data=csv_data, file_name="ucg_live_monitoring.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")
