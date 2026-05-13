import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress, norm as gaussian_dist
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
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve, r2_score
from sklearn.model_selection import KFold
import joblib
from sklearn.preprocessing import StandardScaler
import requests
import logging
from scipy.signal import savgol_filter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
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

try:
    from filterpy.kalman import KalmanFilter
    FILTERPY_AVAILABLE = True
except ImportError:
    FILTERPY_AVAILABLE = False

try:
    import pymc as pm
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False

try:
    import torch_geometric.nn as geo_nn
    TORCH_GEO_AVAILABLE = True
except ImportError:
    TORCH_GEO_AVAILABLE = False

try:
    import cupy as cp
    GPU_AVAILABLE = True
    xp = cp
except ImportError:
    GPU_AVAILABLE = False
    xp = np

try:
    from mpi4py import MPI
    MPI_AVAILABLE = True
except ImportError:
    MPI_AVAILABLE = False

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
        'thermal_decay': "Termal Degradatsiya (β):",
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
        'ai_recommendation': "AI Tavsiya (Selek)",
        'monitoring_header': "📊 {obj_name}: Monitoring va Ekspert Xulosasi",
        'subsidence_title': "📉 Yer yuzasi cho'kishi (cm)",
        'thermal_deform_title': "🔥 Termal deformatsiya (cm)",
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
        'timeline_table': """
| Bosqich | Vaqti | Tavsif |
|---------|-------|--------|
| **Rejalashtirish** | 2026-04-01 | Validatsiya, xavfsiz bo'lish funksiyalarini ishlab chiqish |
| **Modellarni optimallashtirish** | 2026-05-15 | NN/RF testlash, FDM yaxshilash, keshlashtirish |
| **Integratsiya va testlash** | 2026-06-30 | Unit testlar, yakuniy vizualizatsiya, deploy |
        """,
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Monitoring ma'lumotlarini yuklab olish (CSV)"
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
        'thermal_decay': "Thermal Degradation (β):",
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
        'ai_recommendation': "AI Recommendation (Pillar)",
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
        'download_data': "📥 Download monitoring data (CSV)"
    },
    'ru': {
        'app_title': "Универсальный мониторинг деформации земной поверхности",
        'app_subtitle': "Термо-механический (ТМ) анализ и оптимизация размера целика",
        'sidebar_header_params': "⚙️ Общие параметры",
        'formula_show': "Показать формулы:",
        'project_name': "Название проекта:",
        'process_time': "Время процесса (часы):",
        'num_layers': "Количество слоёв:",
        'tensile_model': "Модель растяжения:",
        'rock_props': "💎 Свойства породы",
        'disturbance': "Фактор нарушения (D):",
        'poisson': "Коэффициент Пуассона (ν):",
        'stress_ratio': "Коэффициент напряжений (k = σh/σv):",
        'tensile_params': "📐 Растяжение и целик",
        'tensile_ratio': "Отношение растяжения (σt0/UCS):",
        'thermal_decay': "Термическое затухание (β):",
        'combustion': "🔥 Горение и термика",
        'burn_duration': "Длительность горения (часы):",
        'max_temp': "Максимальная температура (°C)",
        'timeline': "📅 Этапы проекта (Таймлайн)",
        'layer_params': "Параметры слоя {num}",
        'layer_name': "Название:",
        'thickness': "Мощность (м):",
        'ucs': "UCS (МПа):",
        'density': "Плотность (кг/м³):",
        'color': "Цвет:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (МПа):",
        'error_thick_positive': "Мощность должна быть >0",
        'error_ucs_positive': "UCS должен быть >0 МПа",
        'error_density_positive': "Плотность должна быть >0 кг/м³",
        'error_gsi_range': "GSI должен быть в диапазоне 10...100",
        'error_mi_positive': "mi >0",
        'error_min_layers': "❌ Необходим хотя бы 1 слой!",
        'warning_pytorch': "⚠️ PyTorch не установлен. Используется RandomForestClassifier.",
        'pillar_strength': "Прочность целика (σp)",
        'plastic_zone': "Пластическая зона (y)",
        'cavity_volume': "Объём полости",
        'max_permeability': "Макс. проницаемость",
        'ai_recommendation': "Рекомендация ИИ (Целик)",
        'monitoring_header': "📊 {obj_name}: Мониторинг и экспертное заключение",
        'subsidence_title': "📉 Оседание поверхности (см)",
        'thermal_deform_title': "🔥 Термическая деформация (см)",
        'hb_envelopes_title': "🛡️ Огибающие Хука-Брауна",
        'scientific_analysis': "📋 Научный анализ",
        'fos_red': "🔴 FOS < 1.0: Разрушение",
        'fos_yellow': "🟡 FOS 1.0–1.5: Неустойчиво",
        'fos_green': "🟢 FOS > 1.5: Устойчиво",
        'tm_field_title': "🔥 ТМ поле и интерференция целика",
        'temp_subplot': "Температурное поле (°C) + поток газа",
        'fos_subplot': "FOS + прогноз обрушения ИИ (НС) + зоны текучести",
        'gas_flow': "Поток газа",
        'shear': "Сдвиг",
        'tensile': "Растяжение",
        'ai_collapse': "Обрушение по ИИ (НС)",
        'monitoring_panel': "📊 {obj_name}: Комплексная панель мониторинга",
        'pillar_live': "Прочность целика",
        'rec_width_live': "Рекомендуемая ширина целика",
        'max_subsidence_live': "Макс. оседание",
        'process_stage': "Стадия процесса",
        'stage_active': "Активная",
        'stage_cooling': "Охлаждение",
        'ai_monitor_title': "🧠 UCG AI Predictive Monitoring",
        'ai_monitor_desc': "Данные датчиков в реальном времени и обнаружение аномалий",
        'ai_steps': "Шагов симуляции:",
        'ai_run_btn': "▶️ Запустить AI мониторинг",
        'ai_stop_btn': "⏹ Остановить",
        'advanced_analysis': "🔍 Углубленный динамический анализ и методологическое обоснование",
        'tab_mass': "🏗️ Параметры массива",
        'tab_thermal': "🔥 Термическая деградация",
        'tab_stability': "⚖️ Устойчивость и источники",
        'hb_class': "1. Классификация Хука-Брауна (2018)",
        'hb_mb': "m_b = {mb:.3f}",
        'hb_s': "s = {s:.4f}",
        'hb_caption_mb': "Функция угла трения массива (m_i={mi})",
        'hb_caption_s': "Степень трещиноватости (GSI={gsi})",
        'hb_interpret': "**Научный комментарий:** Согласно критерию Хука-Брауна (2018), GSI={gsi} означает, что прочность массива **на {perc:.1f}%** ниже лабораторных значений.",
        'thermal_params': "2. Анализ термо-механических коэффициентов",
        'param_table_param': "Параметр",
        'param_table_value': "Значение",
        'param_table_reason': "Обоснование выбора",
        'modulus': "Модуль упругости (E)",
        'alpha': "Термическое расширение (α)",
        'temp0': "Начальная T₀",
        'modulus_reason': "Характерный средний коэффициент деформации для угля.",
        'alpha_reason': "Коэффициент линейного теплового расширения угля (Yang, 2010).",
        'temp0_reason': "Начальная естественная температура угольного пласта.",
        'ucs_decay': "**A) Термическое снижение UCS:**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ МПа}}",
        'ucs_interpret': "**Интерпретация:** При температуре {temp}°C прочность породы снизилась на {perc:.1f}%.",
        'thermal_stress': "**B) Термическое напряжение ($\\sigma_{{th}}$):**",
        'thermal_stress_eq': r"\sigma_{{th}} \approx \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ МПа}}",
        'pillar_stability': "3. Устойчивость целика и библиография",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v}} = {fos:.2f}",
        'pillar_wilson': "**Согласно теории текучести целика Wilson (1972):** При ширине целика $w={w}$ м его центральное ядро выдерживает геостатическую нагрузку {sv:.2f} МПа. Пластическая зона: $y = {y:.1f}$ м.",
        'references': "#### 📚 Основные научные источники:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*.",
        'conclusion_danger': "🔴 **Научное заключение:** FOS={fos:.2f}. Высокая термическая деградация. Рекомендуется увеличить ширину целика или контролировать скорость газификации.",
        'conclusion_safe': "🟢 **Научное заключение:** FOS={fos:.2f}. Выбранные параметры обеспечивают устойчивость массива.",
        'methodology_expander': "📚 Научная методология и источники (PhD Research)",
        'tensile_empirical': "Эмпирическая (UCS)",
        'tensile_hb': "На основе HB (auto)",
        'tensile_manual': "Ручной ввод",
        'timeline_table': """
| Этап | Время | Описание |
|------|-------|----------|
| **Планирование** | 2026-04-01 | Валидация, разработка безопасных функций |
| **Оптимизация моделей** | 2026-05-15 | Тестирование NN/RF, улучшение FDM, кэширование |
| **Интеграция и тестирование** | 2026-06-30 | Модульные тесты, финальная визуализация, деплой |
        """,
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Скачать данные мониторинга (CSV)"
    }
}

FORMULA_OPTIONS = {
    'uz': ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"],
    'en': ["Close", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
           "3. Thermal Stress & Tension", "4. Pillar & Subsidence"],
    'ru': ["Закрыть", "1. Критерий Хука-Брауна (2018)", "2. Термическое повреждение и проницаемость",
           "3. Термическое напряжение и растяжение", "4. Целик и оседание"]
}

def t(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

EPS = 1e-9
st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

if 'language' not in st.session_state:
    st.session_state.language = 'uz'

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
tensile_ratio = st.sidebar.slider(t('tensile_ratio'), 0.03, 0.15, 0.08)
beta_thermal = st.sidebar.slider(
    "Termal degradatsiya koeffitsienti (β)",
    min_value=0.0005,
    max_value=0.02,
    value=0.005,
    step=0.0005
)

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40)
T_source_max = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

st.sidebar.markdown("---")
st.sidebar.subheader("Quduqlar konfiguratsiyasi")
well_distance = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

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

nx = 80
nz = 60
dx = 1.0
dz = 1.0
dt_sim = 0.01
total_time_sim = time_h * 3600.0
n_steps_sim = int(total_time_sim / dt_sim)
n_steps_sim = min(n_steps_sim, 2000)

well_x = np.array([-well_distance, 0, well_distance])
H_seam = layers_data[-1]['t']
source_z = total_depth - H_seam / 2

class UltimateGeoEngine:
    def __init__(self, nx, nz, dx, dz, dt, E0, nu, alpha, rho, cp, k0, ucs0, beta_damage):
        self.nx = nx
        self.nz = nz
        self.dx = dx
        self.dz = dz
        self.dt = dt
        self.E0 = E0
        self.nu = nu
        self.alpha = alpha
        self.rho = rho
        self.cp = cp
        self.k0 = k0
        self.ucs0 = ucs0
        self.beta_damage = beta_damage

        self.T = np.ones((nz, nx)) * 25.0
        self.damage = np.zeros((nz, nx))
        self.perm = np.ones((nz, nx)) * k0
        self.sxx = np.zeros((nz, nx))
        self.szz = np.zeros((nz, nx))
        self.sxz = np.zeros((nz, nx))
        self.alert_map = np.zeros((nz, nx))
        self.subsidence = np.zeros(nx)

    def conductivity(self):
        k = 0.42 - 1.2e-4 * self.T - 2e-8 * self.T**2
        return np.clip(k, 0.08, 0.42)

    def thermal_damage_func(self):
        dT = np.maximum(self.T - 20.0, 0.0)
        D = 1.0 - np.exp(-self.beta_damage * dT)
        return np.clip(D, 0.0, 0.999)

    def young_modulus(self):
        D = self.damage
        E = self.E0 * (1.0 - D)**2
        return np.clip(E, 0.05 * self.E0, self.E0)

    def solve_heat(self, Q):
        Told = self.T.copy()
        k = self.conductivity()
        alpha = k / (self.rho * self.cp)
        Txx = (Told[1:-1, 2:] - 2.0 * Told[1:-1, 1:-1] + Told[1:-1, :-2]) / self.dx**2
        Tzz = (Told[2:, 1:-1] - 2.0 * Told[1:-1, 1:-1] + Told[:-2, 1:-1]) / self.dz**2
        diffusion = alpha[1:-1, 1:-1] * (Txx + Tzz)
        source = Q[1:-1, 1:-1] / (self.rho * self.cp)
        self.T[1:-1, 1:-1] += self.dt * (diffusion + source)
        self.T[:, 0] = self.T[:, 1]
        self.T[:, -1] = self.T[:, -2]
        self.T[-1, :] = self.T[-2, :]
        self.T[0, :] = 0.9 * self.T[1, :] + 0.1 * 25.0

    def solve_stress(self):
        E = self.young_modulus()
        nu = self.nu
        exx = np.gradient(self.damage, axis=1)
        ezz = np.gradient(self.damage, axis=0)
        exz = 0.5 * (np.gradient(exx, axis=0) + np.gradient(ezz, axis=1))
        lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
        mu = E / (2.0 * (1.0 + nu))
        trace = exx + ezz
        dT = self.T - 20.0
        thermal_term = (3.0 * lam + 2.0 * mu) * self.alpha * dT
        self.sxx = 2.0 * mu * exx + lam * trace - thermal_term
        self.szz = 2.0 * mu * ezz + lam * trace - thermal_term
        self.sxz = 2.0 * mu * exz

    def von_mises(self):
        vm = np.sqrt(self.sxx**2 - self.sxx * self.szz + self.szz**2 + 3.0 * self.sxz**2)
        return np.maximum(vm, 0.0)

    def update_damage(self):
        thermal_D = self.thermal_damage_func()
        vm = self.von_mises()
        strength = self.ucs0 * (1.0 - thermal_D)
        mech_D = vm / (strength + EPS)
        mech_D = np.clip(mech_D, 0.0, 1.0)
        total_D = thermal_D + mech_D - thermal_D * mech_D
        self.damage = np.clip(total_D, 0.0, 0.999)

    def update_permeability(self):
        self.perm = self.k0 * (1.0 + 45.0 * self.damage**2)
        self.perm = np.clip(self.perm, 1e-16, 1e-11)

    def update_alerts(self):
        vm = self.von_mises()
        temp_norm = self.T / (np.max(self.T) + EPS)
        stress_norm = vm / (np.max(vm) + EPS)
        perm_norm = self.perm / (np.max(self.perm) + EPS)
        self.alert_map = 0.3 * temp_norm + 0.3 * stress_norm + 0.3 * self.damage + 0.1 * perm_norm

    def update_subsidence(self):
        cavity = np.sum(self.damage)
        x = np.arange(self.nx)
        center = self.nx // 2
        sigma = self.nx / 8.0
        gaussian = np.exp(-((x - center)**2) / (2.0 * sigma**2))
        self.subsidence = cavity * gaussian * 1e-5

    def step(self, Q):
        self.solve_heat(Q)
        self.solve_stress()
        self.update_damage()
        self.update_permeability()
        self.update_alerts()
        self.update_subsidence()

E0_val = 5e9
alpha_val = 1e-5
rho_rock = 1400.0
cp_rock = 1200.0
k0_perm = 1e-15
ucs_coal = layers_data[-1]['ucs'] * 1e6
engine = UltimateGeoEngine(nx, nz, dx, dz, dt_sim, E0_val, nu_poisson, alpha_val, rho_rock, cp_rock, k0_perm, ucs_coal, beta_thermal)

Q = np.zeros((nz, nx))
source_idx_z = int(source_z / (total_depth + 50) * nz)
for idx, px in enumerate(well_x):
    start_time = {0: 0, 1: 40, 2: 80}[idx]
    if time_h > start_time:
        elapsed = time_h - start_time
        T_curr = T_source_max if elapsed <= burn_duration else 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration))
        power = T_curr * 50
        x_idx = np.argmin(np.abs(np.linspace(-total_depth * 1.5, total_depth * 1.5, nx) - px))
        z_idx = source_idx_z
        Q[z_idx - 2:z_idx + 3, x_idx - 2:x_idx + 3] = power

for step in range(min(n_steps_sim, 500)):
    engine.step(Q)

T_field = engine.T
damage_field = engine.damage
perm_field = engine.perm
sxx_field = engine.sxx
szz_field = engine.szz
sxz_field = engine.sxz
alert_map = engine.alert_map
subsidence_array = engine.subsidence

x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, nx)
z_axis = np.linspace(0, total_depth + 50, nz)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)

fos_2d = np.clip((ucs_coal * (1 - damage_field)) / (np.maximum(np.sqrt(sxx_field**2 - sxx_field * szz_field + szz_field**2 + 3 * sxz_field**2), EPS) + 1e-9), 0.0, 3.0)

sub_p = subsidence_array * 100
horizontal_disp_cm = np.gradient(sub_p) * 0.1

cavity_volume = np.sum(damage_field) * dx * dz
avg_t_p = np.mean(T_field[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-beta_thermal * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = np.mean(engine.szz[np.abs(z_axis - source_z).argmin(), :]) / 1e6
w_sol = 20.0
E_MIN_CORE = 0.5 * H_seam
for _ in range(30):
    p_strength = (ucs_seam * strength_red) * (w_sol / (H_seam + EPS))**0.5
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

def optimize_pillar_ai(w_arr):
    w = w_arr[0]
    void_frac = float(np.mean(damage_field))
    p_str = (ucs_seam * strength_red) * (w / (H_seam + EPS))**0.5
    fos_w = p_str / (sv_seam + EPS)
    return -(fos_w - 10.0 * void_frac)

try:
    opt_result = minimize(optimize_pillar_ai, x0=[rec_width], bounds=[(5.0, 100.0)], method='SLSQP')
    optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except:
    optimal_width_ai = rec_width

st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{cavity_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm_field):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])
with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p, fill='tozeroy', line=dict(color='magenta', width=3))).update_layout(title=t('subsidence_title'), template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=horizontal_disp_cm, fill='tozeroy', line=dict(color='cyan', width=3))).update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    mb_s = layers_data[-1]['mi'] * np.exp((layers_data[-1]['gsi'] - 100) / (28 - 14 * D_factor))
    s_s = np.exp((layers_data[-1]['gsi'] - 100) / (9 - 3 * D_factor))
    a_s = 0.5 + (1 / 6) * (np.exp(-layers_data[-1]['gsi'] / 15) - np.exp(-20 / 3))
    s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + EPS) + s_s)**a_s
    ucs_burn = ucs_seam * np.exp(-beta_thermal * (T_source_max - 20))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + EPS) + s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam * strength_red) * (mb_s * sigma3_ax / (ucs_seam * strength_red + EPS) + s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name=t('tensile_hb'), line=dict(color='cyan', width=2, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name=t('combustion'), line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")), use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red'))
    st.warning(t('fos_yellow'))
    st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_layers.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}

with c2:
    st.subheader("UCG Yonish Bosqichlari (1 → 3 → 2 sxemasi) – Yangi Ilmiy Model")
    coal_layer = layers_data[-1]
    h_seam = coal_layer['t']
    ucs_coal_pa = coal_layer['ucs'] * 1e6
    rho_coal = coal_layer['rho']
    cavity_width = well_distance - rec_width
    cavity_width = max(cavity_width, 10)
    stage = st.select_slider("Bosqichni tanlang:", options=[1, 2, 3], value=1, key="ucg_stage_132")
    st.session_state['ucg_stage'] = stage
    active_wells = states_132[stage]

    def compute_advanced_fos(engine, well_x, active_wells, source_z, h_seam, cavity_width, layers_data, D_factor, nu_poisson):
        fos = np.full_like(engine.damage, 3.0)
        for px_idx in active_wells:
            px = well_x[px_idx]
            dist = np.sqrt((grid_x - px)**2 + (grid_z - source_z)**2)
            thermal_zone = dist < (h_seam * 3)
            for lyr in layers_data:
                mask = (grid_z >= lyr['z_start']) & (grid_z < lyr['z_start'] + lyr['t'])
                if not np.any(mask): continue
                ucs_pa = lyr['ucs'] * 1e6
                gsi = lyr['gsi']; mi = lyr['mi']
                mb = mi * np.exp((gsi - 100) / (28 - 14 * D_factor))
                s_hb = np.exp((gsi - 100) / (9 - 3 * D_factor))
                a_hb = 0.5 + (1 / 6) * (np.exp(-gsi / 15) - np.exp(-20 / 3))
                sigma_ci_T = ucs_pa * (1 - engine.damage[mask])
                sigma_v = engine.szz[mask] / 1e6
                sigma_3 = nu_poisson / (1 - nu_poisson) * sigma_v
                sigma_th = np.zeros_like(sigma_v)
                local_thermal = thermal_zone[mask]
                if np.any(local_thermal):
                    gradT = np.sqrt(np.gradient(engine.T, axis=1, edge_order=2)[mask]**2 + np.gradient(engine.T, axis=0, edge_order=2)[mask]**2)
                    sigma_th[local_thermal] = np.clip(0.65 * engine.young_modulus()[mask][local_thermal] * 1e-5 * (engine.T[mask][local_thermal] - 20) / (1 - nu_poisson) - 0.15 * gradT[local_thermal], 0, sigma_ci_T[local_thermal] * 0.35)
                sigma1_act = sigma_v + sigma_th
                sigma1_limit = sigma_3 + sigma_ci_T * (mb * sigma_3 / (sigma_ci_T + EPS) + s_hb)**a_hb
                fos_val = np.clip(sigma1_limit / (sigma1_act + EPS), 0, 3)
                fos[mask] = np.minimum(fos[mask], fos_val)
        for px_idx in active_wells:
            px = well_x[px_idx]
            a = cavity_width / 2
            b = h_seam / 2
            cavity_ellipse = ((grid_x - px)**2 / (a**2 + EPS) + (grid_z - source_z)**2 / (b**2 + EPS)) < 1
            fos[cavity_ellipse] = 0.05
        fos[grid_z > layers_data[-1]['z_start'] + layers_data[-1]['t']] = 2.5
        return fos

    fos_stage = compute_advanced_fos(engine, well_x, active_wells, source_z, h_seam, cavity_width, layers_data, D_factor, nu_poisson)

    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=(t('temp_subplot'), "Geomexanik Holat (Yangi Ilmiy Model)"))
    fig_tm.add_trace(go.Heatmap(z=T_field, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42, thickness=15), name=t('temp_subplot')), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_stage, x=x_axis, y=z_axis,
                                colorscale=[[0, 'black'], [0.1, 'red'], [0.4, 'orange'], [0.7, 'yellow'], [0.85, 'lime'], [1, 'darkgreen']],
                                zmin=0, zmax=3, contours_showlines=False,
                                colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42, thickness=15), name="FOS"), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=900, margin=dict(r=150, t=80, b=100),
                         showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    fig_tm.update_yaxes(range=[source_z + 100, source_z - 100], row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox("Avtomatik animatsiya (1→2→3 bosqichlar)"):
        anim_placeholder = st.empty()
        for s in [1, 2, 3]:
            wells_s = states_132[s]
            fos_s = compute_advanced_fos(engine, well_x, wells_s, source_z, h_seam, cavity_width, layers_data, D_factor, nu_poisson)
            fig_s = go.Figure(go.Contour(z=fos_s, x=x_axis, y=z_axis,
                                         colorscale=[[0, 'black'], [0.1, 'red'], [0.4, 'orange'], [0.7, 'yellow'], [0.85, 'lime'], [1, 'darkgreen']],
                                         zmin=0, zmax=3, contours_showlines=False,
                                         colorbar=dict(title="FOS")))
            fig_s.update_yaxes(range=[source_z + 100, source_z - 100], autorange=False)
            fig_s.update_layout(template="plotly_dark", height=500, title=f"Bosqich {s} (1-3-2 sxemasi)")
            anim_placeholder.plotly_chart(fig_s, use_container_width=True)
            time.sleep(1.2)
        st.success("Animatsiya yakunlandi.")

    selek_eni = well_distance - cavity_width
    msgs = {
        1: f"**1-Bosqich:** Chap quduq yoqilgan. Qalinlik = {h_seam:.1f} m, Quduqlar masofasi = {well_distance:.0f} m, Selek eni = {selek_eni:.1f} m.",
        2: f"**2-Bosqich (Muhim):** O‘ng quduq yoqilgan. O‘rtadagi selek tomni ushlab turadi. Selek eni = {selek_eni:.1f} m.",
        3: f"**3-Bosqich:** Markaziy selek gazlashtirilmoqda. Barqaror cho‘kish."
    }
    st.info(msgs[stage])
    if selek_eni < 18.5:
        st.error(f"⚠️ KRITIK: Selek o'lchami ({selek_eni:.1f} m) xavfsiz chegaradan past!")
    else:
        st.success(f"✅ BARQAROR: Selek o'lchami ({selek_eni:.1f} m) me'yorda.")

with st.expander("🌍 3D Litologik Kesim"):
    fig_3d = go.Figure()
    y_3d = np.linspace(-total_depth * 0.5, total_depth * 0.5, 30)
    for i, layer in enumerate(layers_data):
        z_top = layer['z_start']
        z_bot = layer['z_start'] + layer['t']
        x_3d = np.linspace(x_axis.min(), x_axis.max(), 30)
        X3, Y3 = np.meshgrid(x_3d, y_3d)
        Z_top = np.full_like(X3, z_top)
        Z_bot = np.full_like(X3, z_bot)
        hex_color = layer['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[j:j+2], 16) for j in (0, 2, 4))
        rgb_str = f"rgb({r},{g},{b})"
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_top, colorscale=[[0, rgb_str], [1, rgb_str]], showscale=False, opacity=0.7, name=layer['name']))
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_bot, colorscale=[[0, rgb_str], [1, rgb_str]], showscale=False, opacity=0.7, name=f"{layer['name']}_bottom"))
    stage_3d = st.session_state.get('ucg_stage', 3)
    active_wells_3d = states_132[stage_3d]
    for idx, px in enumerate(well_x):
        if idx in active_wells_3d:
            theta = np.linspace(0, 2 * np.pi, 30)
            phi = np.linspace(0, np.pi, 20)
            THETA, PHI = np.meshgrid(theta, phi)
            R_use = np.mean(engine.damage) * 10 + 5
            cx = px + R_use * np.sin(PHI) * np.cos(THETA)
            cy = R_use * np.sin(PHI) * np.sin(THETA)
            cz = source_z + R_use * np.cos(PHI)
            fig_3d.add_trace(go.Surface(x=cx, y=cy, z=cz, colorscale=[[0, 'orange'], [1, 'red']], showscale=False, opacity=0.85, name=f'Yonish kamerasi {idx+1}'))
    fig_3d.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Chuqurlik (m)', zaxis=dict(autorange='reversed'), camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))), template='plotly_dark', height=600, title="3D Litologik Model + Yonish Kameralari", showlegend=True)
    st.plotly_chart(fig_3d, use_container_width=True)
    st.caption("Sariq/qizil sferalar — yonish kameralari (faqat tanlangan bosqichdagi faol quduqlar uchun)")

st.header("🕹️ Ultimate Interactive Dashboard (Real-time Animation)")
st.caption(f"Joriy qatlam: {layers_data[-1]['name']}, qalinligi={H_seam:.1f} m, chuqurlik={total_depth:.1f} m, manba chuqurligi={source_z:.1f} m")

time_steps_dash = np.arange(0, time_h + 1, max(1, time_h // 20))
surface_x = x_axis
surface_h_disp = []
surface_v_disp = []
for time_step in time_steps_dash:
    v_disp = -np.interp(time_step, [0, time_h], [0, np.max(sub_p)]) * 0.01
    h_disp = -(surface_x / (0.45 * total_depth + EPS)) * v_disp
    surface_v_disp.append(v_disp)
    surface_h_disp.append(h_disp)
surface_h_disp = np.array(surface_h_disp)
surface_v_disp = np.array(surface_v_disp)

col1_dash, col2_dash = st.columns(2)
with col1_dash:
    fos_thresh_dash = st.slider("FOS Threshold (Yielded Zone)", 0.1, 2.0, 1.0, 0.05, key="fos_thresh_dash")
with col2_dash:
    disp_cscale = st.selectbox("Displacement Color Scale", ['Turbo', 'Viridis', 'Cividis'], index=0, key="disp_cscale")

def draw_interactive_ucg_dashboard(x_axis, z_axis, fos_2d, damage_2d, surface_x, surface_h_disp, surface_v_disp,
                                   time_steps=None, fos_threshold=1.0, disp_colorscale='Turbo',
                                   source_z=None, h_seam=None):
    if time_steps is None:
        time_steps = np.arange(surface_h_disp.shape[0])
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("A) FOS & Yielded Zones (2D)",
                                        "B) Total Displacement (2D, cm)",
                                        "C) Horizontal Surface Displacement (mm)",
                                        "D) Vertical Surface Displacement (mm)"),
                        horizontal_spacing=0.1, vertical_spacing=0.15)
    fig.add_trace(go.Heatmap(z=fos_2d, x=x_axis, y=z_axis, colorscale='RdYlGn', zmin=0, zmax=3,
                             colorbar=dict(title="FOS", x=0.45, y=0.78, thickness=12, len=0.42)), row=1, col=1)
    mask_fos = np.where(fos_2d < fos_threshold, 1, np.nan)
    fig.add_trace(go.Heatmap(z=mask_fos, x=x_axis, y=z_axis, colorscale=[[0, 'rgba(255,0,0,0.5)']], showscale=False), row=1, col=1)
    fig.add_trace(go.Heatmap(z=damage_2d, x=x_axis, y=z_axis, colorscale=disp_colorscale,
                             colorbar=dict(title="Damage", x=1.0, y=0.78, thickness=12, len=0.42)), row=1, col=2)
    for i, t in enumerate(time_steps):
        fig.add_trace(go.Heatmap(z=surface_h_disp[i:i+1, :], x=surface_x, y=[t], colorscale='Turbo',
                                 showscale=False, visible=(i == 0)), row=2, col=1)
        fig.add_trace(go.Heatmap(z=surface_v_disp[i:i+1, :], x=surface_x, y=[t], colorscale='Viridis',
                                 showscale=False, visible=(i == 0)), row=2, col=2)
    fig.update_layout(title="Ultimate UCG Dashboard", template='plotly_dark', height=900, showlegend=False,
                      updatemenus=[dict(type="buttons", showactive=False, y=1.05, x=1.15,
                                       buttons=[dict(label="Play", method="animate", args=[None, {"frame": {"duration": 500, "redraw": True}, "fromcurrent": True}]),
                                                dict(label="Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])])])
    fig.update_yaxes(autorange='reversed', row=1, col=1)
    fig.update_yaxes(autorange='reversed', row=1, col=2)
    return fig

dash_fig = draw_interactive_ucg_dashboard(x_axis, z_axis, fos_2d, damage_field, surface_x, surface_h_disp, surface_v_disp,
                                          time_steps=time_steps_dash, fos_threshold=fos_thresh_dash, disp_colorscale=disp_cscale,
                                          source_z=source_z, h_seam=H_seam)
st.plotly_chart(dash_fig, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")

if FASTAPI_AVAILABLE:
    app = FastAPI()
    @app.post("/predict")
    def predict_api(data: dict):
        temp = np.array(data["temp"])
        s1 = np.array(data["sigma1"])
        s3 = np.array(data["sigma3"])
        d = np.array(data["depth"])
        features = np.column_stack([temp, s1, s3, d])
        return {"collapse": np.zeros_like(temp).tolist()}
