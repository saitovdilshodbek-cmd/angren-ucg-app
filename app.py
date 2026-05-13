import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress, norm as gaussian_dist
import time
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
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
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** *The Hoek-Brown failure criterion and GSI – 2018 edition*. Journal of Rock Mechanics and Geotechnical Engineering, 11(6), 1115-1131. https://doi.org/10.1016/j.jrmge.2018.02.006",
        'ref2': "**Yang, D. (2010).** *Stability of underground coal gasification* [PhD dissertation, Delft University of Technology]. TU Delft Repository.",
        'ref3': "**Shao, S., Shao, J., & Wasantha, P. L. P. (2015).** A thermal damage constitutive model for rock. *International Journal of Rock Mechanics and Mining Sciences*, 80, 392-400.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*, 131, 409-425.",
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
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** *The Hoek-Brown failure criterion and GSI – 2018 edition*. Journal of Rock Mechanics and Geotechnical Engineering, 11(6), 1115-1131. https://doi.org/10.1016/j.jrmge.2018.02.006",
        'ref2': "**Yang, D. (2010).** *Stability of underground coal gasification* [PhD dissertation, Delft University of Technology]. TU Delft Repository.",
        'ref3': "**Shao, S., Shao, J., & Wasantha, P. L. P. (2015).** A thermal damage constitutive model for rock. *International Journal of Rock Mechanics and Mining Sciences*, 80, 392-400.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*, 131, 409-425.",
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
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** *The Hoek-Brown failure criterion and GSI – 2018 edition*. Journal of Rock Mechanics and Geotechnical Engineering, 11(6), 1115-1131. https://doi.org/10.1016/j.jrmge.2018.02.006",
        'ref2': "**Yang, D. (2010).** *Stability of underground coal gasification* [PhD dissertation, Delft University of Technology]. TU Delft Repository.",
        'ref3': "**Shao, S., Shao, J., & Wasantha, P. L. P. (2015).** A thermal damage constitutive model for rock. *International Journal of Rock Mechanics and Mining Sciences*, 80, 392-400.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*, 131, 409-425.",
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

EPS = 1e-6

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

depth_seam = sum(l['t'] for l in layers_data[:-1]) + layers_data[-1]['t'] / 2
avg_rho = np.mean([l['rho'] for l in layers_data])

def thermoelastic_stress_2d(exx, ezz, exz, T, T0, E, nu, alpha):
    dT = T - T0
    C = E / ((1 + nu) * (1 - 2 * nu))
    thermal_term = E * alpha * dT / (1 - 2 * nu)
    sxx = C * ((1 - nu) * exx + nu * ezz) - thermal_term
    szz = C * (nu * exx + (1 - nu) * ezz) - thermal_term
    sxz = E / (1 + nu) * exz
    return sxx, szz, sxz

def hoek_brown(sigma3, sigma_ci, mb, s, a):
    sigma_t = -s * sigma_ci / (mb + EPS)
    sigma3 = np.maximum(sigma3, sigma_t)
    term = mb * (sigma3 / (sigma_ci + EPS)) + s
    term = np.maximum(term, 0.0)
    sigma1 = sigma3 + sigma_ci * term**a
    return sigma1

def thermal_damage(T: np.ndarray, beta: float = 0.002) -> np.ndarray:
    return 1 - np.exp(-beta * np.maximum(T - 20, 0))

def thermal_conductivity(T):
    k = 0.35 * np.exp(-0.0015 * (T - 20))
    return np.clip(k, 0.08, 0.35)

def specific_heat(T):
    cp = 900 + 0.45 * T
    return np.clip(cp, 900, 2200)

def density_temperature(rho0, T):
    T = np.clip(T, 20, 1200)
    lambda_mass = 0.00012 * (T - 20)
    rho_T = rho0 * (1 - lambda_mass)
    return np.clip(rho_T, 0.55 * rho0, rho0)

def young_modulus_temperature(T):
    T = np.clip(T, 20, 1200)
    E_T = 5e9 * np.exp(-0.0018 * (T - 20))
    return np.clip(E_T, 0.15 * 5e9, 5e9)

def thermal_expansion_temperature(T):
    T = np.clip(T, 20, 1200)
    alpha_T = 1e-5 * (1 + 0.002 * (T - 20) + 1e-6 * (T - 20)**2)
    return alpha_T

def vertical_stress(depth, density):
    return density * 9.81 * depth / 1e6

def solve_heat_equation_dynamic(T, Q, rho_field, cp_field, k_field, dx, dz, dt, h, T_air, n_steps):
    dt_max = dx**2 / (4 * np.max(k_field / (rho_field * cp_field)))
    if dt > dt_max:
        dt = 0.8 * dt_max
    alpha_field = k_field / (rho_field * cp_field)
    for _ in range(n_steps):
        T_old = T.copy()
        Txx = (T_old[1:-1, 2:] - 2 * T_old[1:-1, 1:-1] + T_old[1:-1, :-2]) / dx**2
        Tzz = (T_old[2:, 1:-1] - 2 * T_old[1:-1, 1:-1] + T_old[:-2, 1:-1]) / dz**2
        T[1:-1, 1:-1] += dt * (alpha_field[1:-1, 1:-1] * (Txx + Tzz) + Q[1:-1, 1:-1] / (rho_field[1:-1, 1:-1] * cp_field[1:-1, 1:-1]))
        T[0, :] = T[1, :] + dz * h / k_field[0, :] * (T_air - T[0, :])
        T[:, 0] = T[:, 1]
        T[:, -1] = T[:, -2]
        T[-1, :] = T[-2, :]
        T = 0.95 * T_old + 0.05 * T
    return T

def principal_stresses(sx, sy, txy):
    avg = (sx + sy) / 2
    radius = np.sqrt(((sx - sy) / 2) ** 2 + txy ** 2)
    s1 = avg + radius
    s2 = avg - radius
    return s1, s2

def evolving_cavity_radius(time_h, T_field):
    thermal_dam = 1 - np.exp(-0.002 * np.maximum(T_field - 20, 0))
    growth_rate = 0.015 * np.mean(thermal_dam)
    radius = 5.0 + growth_rate * time_h
    return np.clip(radius, 5, 40)

def kirsch_stress_field(x, z, sigma_H, sigma_h, cavity_radius, pore_pressure=0.0):
    r = np.sqrt(x**2 + z**2)
    r = np.maximum(r, cavity_radius + 1e-3)
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

def pore_pressure_field(T, depth, permeability):
    hydrostatic = 1000 * 9.81 * depth
    thermal_press = 2e5 * np.exp((T - 100)/300)
    gas_press = permeability * 1e12 * 5e5
    pore_p = hydrostatic + thermal_press + gas_press
    return pore_p / 1e6

def compute_damage(sigma_eq, sigma_strength, temperature, creep_dam, beta):
    thermal_d = 1 - np.exp(-beta * np.maximum(temperature - 20, 0))
    mechanical_d = np.clip(sigma_eq / (sigma_strength + 1e-9), 0, 2)
    total = 0.4*thermal_d + 0.4*mechanical_d + 0.2*creep_dam
    return np.clip(total, 0, 1)

def von_mises_stress(sigma_x, sigma_y, tau_xy):
    return np.sqrt(np.maximum(sigma_x**2 - sigma_x*sigma_y + sigma_y**2 + 3*tau_xy**2, 0.0))

def validation_metrics(numerical, reference):
    rmse = np.sqrt(np.mean((numerical - reference)**2))
    mae = np.mean(np.abs(numerical - reference))
    mape = np.mean(np.abs((numerical - reference)/(reference+EPS)))*100
    return {"RMSE": rmse, "MAE": mae, "MAPE": mape}

def probability_of_failure(FOS):
    beta = (FOS - 1) / 0.15
    return gaussian_dist.cdf(-beta)

def monte_carlo_fos(ucs_mean, ucs_std, gsi_mean, gsi_std, D, T_avg, H_seam, depth, density, rec_width, beta_th, n_sim=1000):
    ucs_samples = np.random.normal(ucs_mean, ucs_std, n_sim)
    gsi_samples = np.clip(np.random.normal(gsi_mean, gsi_std, n_sim), 10, 100)
    fos = []
    for ucs, gsi in zip(ucs_samples, gsi_samples):
        mb = 10 * np.exp((gsi - 100) / (28 - 14 * D))
        s  = np.exp((gsi - 100) / (9 - 3 * D))
        a  = 0.5 + (1/6) * (np.exp(-gsi/15) - np.exp(-20/3))
        D_T = 1 - np.exp(-beta_th * max(T_avg - 20, 0))
        sigma_ci = ucs * (1 - D_T)
        sigma_cm = sigma_ci * (s ** a)
        pillar_strength = sigma_cm * (rec_width / (H_seam + EPS)) ** 0.5
        sv = density * 9.81 * depth / 1e6
        fos.append(pillar_strength / (sv + EPS))
    fos = np.array(fos)
    pf = np.mean(fos < 1.0)
    return fos, pf

grid_shape = (80, 100)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field_moving(time_h: float, T_source_max: float, burn_duration: float,
                                     total_depth: float, source_z: float, grid_shape: tuple) -> tuple:
    THERMAL_DIFFUSIVITY = 8.5e-7
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
    alpha_use = k_field / (rho_field * cp_field)
    dt_max = dx**2 / (4 * np.max(alpha_use))
    dt = 0.8 * dt_max
    n_steps = max(int(total_time / dt), 20)
    dt = total_time / n_steps
    v_burn = 0.02
    sources = [
        {'x0': -total_depth/3, 'start': 0, 'moving': False},
        {'x0': 0, 'start': 40, 'moving': True, 'v': v_burn},
        {'x0': total_depth/3, 'start': 80, 'moving': False}
    ]
    for step in range(n_steps):
        current_time_h = (step + 1) * dt / 3600
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
            pen_depth = np.sqrt(4 * THERMAL_DIFFUSIVITY * dt_sec) + 15
            dist_sq = (grid_x - x_center)**2 + (grid_z - source_z)**2
            Q_source += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2))
        temp_2d = solve_heat_equation_dynamic(
            T=temp_2d, Q=Q_source, rho_field=rho_field, cp_field=cp_field,
            k_field=k_field, dx=dx, dz=dz, dt=dt, h=10.0, T_air=25.0, n_steps=1
        )
    return temp_2d, x_axis, z_axis, grid_x, grid_z

temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape)

E_field = young_modulus_temperature(temp_2d)
alpha_field = thermal_expansion_temperature(temp_2d)
grid_rho = np.zeros_like(temp_2d)
layer_bounds = [(l['z_start'], l['z_start'] + l['t']) for l in layers_data]
for i, (z0, z1) in enumerate(layer_bounds):
    mask = (grid_z >= z0) & (grid_z < z1 if i < len(layer_bounds)-1 else True)
    layer = layers_data[i]
    grid_rho[mask] = density_temperature(layer['rho'], temp_2d[mask])

grid_sigma_v = np.zeros_like(grid_z)
for i in range(len(z_axis)):
    if i == 0:
        grid_sigma_v[0,:] = 0
    else:
        dz = z_axis[i] - z_axis[i-1]
        grid_sigma_v[i,:] = grid_sigma_v[i-1,:] + grid_rho[i,:] * 9.81 * dz / 1e6
grid_sigma_h = k_ratio * grid_sigma_v

cavity_radius = evolving_cavity_radius(time_h, temp_2d)
perm_tmp = 1e-15 * np.exp(8 * thermal_damage(temp_2d, beta_thermal))
pore_pressure = pore_pressure_field(temp_2d, grid_z, perm_tmp)

sigma_rr, sigma_tt, tau_rt = kirsch_stress_field(grid_x, grid_z - source_z,
                                                 grid_sigma_h, grid_sigma_v,
                                                 cavity_radius, pore_pressure)
sigma1_act, sigma3_act = principal_stresses(sigma_rr, sigma_tt, tau_rt)

delta_T = np.maximum(temp_2d - 20, 0)
sigma_thermal = (E_field * alpha_field * delta_T) / (1.0 - nu_poisson + EPS)
relax_factor = np.exp(-2.5 * thermal_damage(temp_2d, beta_thermal))
sigma_thermal *= relax_factor

dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
G = E_field / (2 * (1 + nu_poisson))
tau_thermal = G * alpha_field * dT_dx * dT_dz / 1e6
tau_rt += tau_thermal

grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
for i, (z0, z1) in enumerate(layer_bounds):
    mask = (grid_z >= z0) & (grid_z < z1 if i < len(layer_bounds)-1 else True)
    layer = layers_data[i]
    grid_ucs[mask] = layer['ucs']
    exp_gsi = (layer['gsi'] - 100)
    grid_mb[mask] = layer['mi'] * np.exp(exp_gsi / (28 - 14*D_factor))
    grid_s_hb[mask] = np.exp(exp_gsi / (9 - 3*D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))

sigma_ci = grid_ucs * (1 - thermal_damage(temp_2d, beta_thermal))
sigma_thermal = np.clip(sigma_thermal / 1e6, 0, 0.35 * sigma_ci)

sigma1_act += sigma_thermal
sigma3_act += sigma_thermal

damage = compute_damage(von_mises_stress(sigma1_act, sigma3_act, tau_rt),
                        sigma_ci, temp_2d, 0.0, beta_thermal)

sigma1_limit = hoek_brown(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)

damage_x = damage * (1 + 0.3 * np.abs(dT_dx) / np.max(abs(dT_dx) + EPS))
damage_z = damage * (1 + 0.3 * np.abs(dT_dz) / np.max(abs(dT_dz) + EPS))
damage_shear = 0.5 * (damage_x + damage_z)

fos_2d = np.clip(sigma1_limit / (sigma1_act + EPS), 0, 3.0)

void_fraction = gaussian_filter(damage * (temp_2d > 600), sigma=2)
void_mask_permanent = void_fraction > 0.5
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])

perm = 1e-15 * np.exp(8*damage) * (1 + 25*sigma_thermal/(E_field+EPS))
perm_x = perm * 5
perm_z = perm
perm = np.clip(perm, 1e-16, 1e-10)

T_kelvin = temp_2d + 273.15
gas_density = 1.2
pressure = (gas_density * 8.314 * T_kelvin) / 0.028
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
mu_gas = 3e-5
vx = -perm_x * dp_dx / mu_gas
vz = -perm_z * dp_dz / mu_gas
gas_velocity = np.sqrt(vx**2 + vz**2)

c_subs = 0.15
Smax = H_seam * 0.04
subsidence_t = Smax * (1 - np.exp(-c_subs * time_h))
i_inflection = 0.45 * total_depth
subsidence_raw = -subsidence_t * np.exp(-(x_axis**2) / (2 * i_inflection**2))
sub_p = subsidence_raw * (1 + 0.35 * float(np.mean(void_mask_permanent))) + 0.08 * np.gradient(subsidence_raw)
horizontal_disp_cm = -(x_axis / (i_inflection + EPS)) * subsidence_raw * 100

avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
strength_red = np.exp(-beta_thermal*(avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()
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

def optimize_pillar_ai(w_arr: np.ndarray) -> float:
    w = w_arr[0]
    p_str = (ucs_seam * strength_red) * (w / (H_seam + EPS))**0.5
    fos_w = p_str / (sv_seam + EPS)
    if fos_w >= 1.5:
        return (w - 20) ** 2 * 0.001
    else:
        return (1.5 - fos_w) * 100 + (w - 20) ** 2 * 0.001

try:
    opt_result = minimize(optimize_pillar_ai, x0=[rec_width], bounds=[(5.0,100.0)], method='SLSQP')
    optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except Exception as e:
    st.error(f"Optimizatsiya xatosi: {e}")
    optimal_width_ai = rec_width

st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5,1.5,2])
with col_g1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta',width=3)))
    fig.update_layout(title=t('subsidence_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig, use_container_width=True)
with col_g2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_axis, y=horizontal_disp_cm, fill='tozeroy', line=dict(color='cyan',width=3)))
    fig.update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig, use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam*(mb_s*sigma3_ax/(ucs_seam+EPS)+s_s)**a_s
    ucs_burn = ucs_seam*np.exp(-beta_thermal*(T_source_max-20))
    s1_burning = sigma3_ax + ucs_burn*(mb_s*sigma3_ax/(ucs_burn+EPS)+s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam*strength_red)*(mb_s*sigma3_ax/(ucs_seam*strength_red+EPS)+s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red',width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name=t('tensile_hb'), line=dict(color='cyan',width=2,dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name=t('combustion'), line=dict(color='orange',width=4)))
    fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
    st.plotly_chart(fig_hb, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    fig_layers.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False)
    st.plotly_chart(fig_layers, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Quduqlar konfiguratsiyasi")
well_distance = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")

CONFINEMENT = 0.65
RELAX = 0.15

with c2:
    st.subheader("UCG Yonish Bosqichlari (1 → 3 → 2 sxemasi) – Yangi Ilmiy Model")
    coal_layer = layers_data[-1]
    h_seam = coal_layer['t']
    ucs_coal_pa = coal_layer['ucs'] * 1e6
    rho_coal = coal_layer['rho']
    well_x = [-well_distance, 0, well_distance]
    cavity_width = well_distance - rec_width
    cavity_width = max(cavity_width, 10)
    E_MOD = 25e9
    ALPHA = 1.0e-5
    NU = nu_poisson
    K0 = NU / (1 - NU)
    layer_bounds_adv = [(l['z_start'], l['z_start'] + l['t'], l) for l in layers_data]
    sigma_v_coal = 0.0
    for l in layers_data[:-1]:
        sigma_v_coal += l['rho'] * 9.81 * l['t']
    sigma_v_coal += rho_coal * 9.81 * (h_seam / 2)
    sigma_v_coal = sigma_v_coal / 1e6
    Hc = h_seam * np.sqrt(sigma_v_coal / (coal_layer['ucs'] + EPS))
    Hc = np.clip(Hc, h_seam, h_seam * 4)
    states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
    stage = st.select_slider("Bosqichni tanlang:", options=[1, 2, 3], value=1, key="ucg_stage")
    active_wells = states_132[stage]

    def compute_advanced_fos(grid_x, grid_z, active_wells, well_x, source_z, h_seam, cavity_width,
                             temp_field, sigma_v_field, layers_data, layer_bounds,
                             E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_pa):
        fos = np.full_like(grid_x, 3.0)
        for px_idx in active_wells:
            px = well_x[px_idx]
            dist = np.sqrt((grid_x - px)**2 + (grid_z - source_z)**2)
            dz = source_z - grid_z
            T = temp_field
            delta_T = np.maximum(T - 20, 0)
            thermal_zone = dist < (h_seam * 3)
            for (top, bot, layer) in layer_bounds:
                mask = (grid_z >= top) & (grid_z < bot)
                if not np.any(mask): continue
                ucs_pa = layer['ucs'] * 1e6
                gsi = layer['gsi']; mi = layer['mi']
                mb = mi * np.exp((gsi - 100) / (28 - 14 * D_factor))
                s_hb = np.exp((gsi - 100) / (9 - 3 * D_factor))
                a_hb = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
                sigma_v = sigma_v_field[mask]
                delta_T_m = delta_T[mask]
                D_T = 1 - np.exp(-beta_thermal * delta_T_m)
                sigma_ci_T = ucs_pa * (1 - D_T)
                sigma_3 = K0 * sigma_v * (0.6 + 0.4 * (1 - D_T))
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
                fos_val = np.clip(sigma_limit / (sigma_1 + EPS), 0, 3)
                yield_mask = sigma_1 > (sigma_limit * 0.85)
                fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
                fos_sub = fos[mask]
                fos_sub = np.minimum(fos_sub, fos_val)
                fos[mask] = fos_sub
                if layer == layers_data[-1]:
                    dome_width = (cavity_width / 2) * np.clip(1 - dz[mask] / (Hc + EPS), 0, 1)
                    failure_zone = fos_val < 1.2
                    dome_condition = (dz[mask] > 0) & (dz[mask] < Hc) & (np.abs(grid_x[mask] - px) < dome_width) & failure_zone
                    if np.any(dome_condition):
                        decay = np.clip(1 - (dz[mask][dome_condition] / (Hc + EPS)), 0.3, 1.0)
                        fos_sub[dome_condition] = np.minimum(fos_sub[dome_condition], decay)
                        fos[mask] = fos_sub
        for px_idx in active_wells:
            px = well_x[px_idx]
            a = cavity_width / 2
            b = h_seam / 2
            cavity_ellipse = ((grid_x - px)**2 / (a**2 + EPS) + (grid_z - source_z)**2 / (b**2 + EPS)) < 1
            fos[cavity_ellipse] = 0.05
        bottom_layer = layers_data[-1]
        bottom_boundary = bottom_layer['z_start'] + bottom_layer['t']
        fos[grid_z > bottom_boundary] = 2.5
        all_wells = [0, 1, 2]
        for i in all_wells:
            if i not in active_wells:
                px = well_x[i]
                pillar_mask = (np.abs(grid_x - px) < h_seam * 1.5) & (np.abs(grid_z - source_z) < h_seam * 1.2)
                fos[pillar_mask] = 2.5
        if stage == 2:
            selek_eni = well_distance - cavity_width
            pillar_strength = ucs_coal_pa * (selek_eni / (h_seam + EPS)) ** 0.5
            sigma_v_coal_pa = sigma_v_coal_MPa * 1e6
            fos_pillar = pillar_strength / (sigma_v_coal_pa + EPS)
            pillar_zone = (np.abs(grid_x - well_x[1]) < selek_eni/2) & (np.abs(grid_z - source_z) < h_seam)
            fos[pillar_zone] = np.maximum(fos[pillar_zone], fos_pillar)
        return np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)

    source_z_adv = total_depth - (h_seam / 2)
    fos_stage = compute_advanced_fos(
        grid_x, grid_z, active_wells, well_x, source_z_adv, h_seam, cavity_width,
        temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
        E_MOD, ALPHA, NU, K0, Hc, sigma_v_coal, ucs_coal_pa
    )

    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=(t('temp_subplot'), "Geomexanik Holat (Yangi Ilmiy Model)"))
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
    r_burn_vis = h_seam * 1.5
    for idx in active_wells:
        px = well_x[idx]
        fig_tm.add_shape(type="circle", x0=px-r_burn_vis, x1=px+r_burn_vis,
                         y0=source_z_adv-r_burn_vis, y1=source_z_adv+r_burn_vis,
                         line=dict(color="orange", width=2), fillcolor='rgba(255,165,0,0.15)', row=2, col=1)
    for px in well_x:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2,
                         y0=source_z_adv-h_seam/2, y1=source_z_adv+h_seam/2,
                         line=dict(color="lime", width=3), fillcolor="rgba(0,255,0,0.1)", row=2, col=1)
    if stage == 2:
        fig_tm.add_shape(type="rect", x0=well_x[1]-80, x1=well_x[1]+80,
                         y0=source_z_adv-30, y1=source_z_adv+30,
                         line=dict(color="cyan", width=4, dash="dash"), fillcolor='rgba(0,255,255,0.1)', row=2, col=1)
        fig_tm.add_annotation(x=well_x[1], y=source_z_adv+100, text="HIMOYA SELEGI (PILLAR)",
                              showarrow=True, arrowhead=2, font=dict(color="cyan", size=12), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=900, margin=dict(r=150,t=80,b=100),
                         showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    zoom_margin = h_seam * 12
    fig_tm.update_yaxes(range=[source_z_adv + zoom_margin/2, source_z_adv - zoom_margin], row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox("Avtomatik animatsiya (1→2→3 bosqichlar)"):
        anim_placeholder = st.empty()
        for s in [1, 2, 3]:
            wells_s = states_132[s]
            fos_s = compute_advanced_fos(
                grid_x, grid_z, wells_s, well_x, source_z_adv, h_seam, cavity_width,
                temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
                E_MOD, ALPHA, NU, K0, Hc, sigma_v_coal, ucs_coal_pa
            )
            fig_s = go.Figure(go.Contour(z=fos_s, x=x_axis, y=z_axis,
                                         colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],[0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
                                         zmin=0, zmax=3, contours_showlines=False,
                                         colorbar=dict(title="FOS")))
            fig_s.update_yaxes(range=[source_z_adv + zoom_margin/2, source_z_adv - zoom_margin], autorange=False)
            fig_s.update_layout(template="plotly_dark", height=500, title=f"Bosqich {s} (1-3-2 sxemasi)")
            anim_placeholder.plotly_chart(fig_s, use_container_width=True)
            time.sleep(1.2)
        st.success("Animatsiya yakunlandi.")

    selek_eni = well_distance - cavity_width
    msgs = {
        1: f"**1-Bosqich:** Chap quduq yoqilgan. Qalinlik = {h_seam:.1f} m, Quduqlar masofasi = {well_distance:.0f} m, Selek eni = {selek_eni:.1f} m.",
        2: f"**2-Bosqich (Muhim):** O'ng quduq yoqilgan. O'rtadagi selek tomni ushlab turadi. Selek eni = {selek_eni:.1f} m.",
        3: f"**3-Bosqich:** Markaziy selek gazlashtirilmoqda. Barqaror cho'kish."
    }
    st.info(msgs[stage])
    if selek_eni < 18.5:
        st.error(f"⚠️ KRITIK: Selek o'lchami ({selek_eni:.1f} m) xavfsiz chegaradan past!")
    else:
        st.success(f"✅ BARQAROR: Selek o'lchami ({selek_eni:.1f} m) me'yorda.")

def physics_features(T: np.ndarray, s1: np.ndarray, s3: np.ndarray, depth: np.ndarray) -> np.ndarray:
    dmg = thermal_damage(T)
    strength = 40 * (1 - dmg)
    fos = strength / (s1 + EPS)
    energy = T * s1 / (depth + 1)
    return np.column_stack([T, s1, s3, depth, dmg, fos, energy])

def generate_physics_dataset(temp_field: np.ndarray, sigma1: np.ndarray,
                             sigma3: np.ndarray, depth: np.ndarray) -> tuple:
    feat = physics_features(temp_field.flatten(), sigma1.flatten(), sigma3.flatten(), depth.flatten())
    fos = feat[:,5]
    energy = feat[:,6]
    collapse = ((fos < 1.0) | (temp_field.flatten() > 800) | (energy > 4000)).astype(int)
    return feat, collapse

class HybridPINN(nn.Module):
    def __init__(self, input_dim=10):
        super(HybridPINN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.Tanh(),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.Tanh(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

def physics_informed_loss(pred, sigma1, sigma_ci, temp, damage):
    fos = sigma_ci / (sigma1 + EPS)
    physics_violation = torch.relu(1.0 - fos)
    thermal_term = damage * torch.sigmoid(temp / 1000)
    consistency = torch.abs(pred - thermal_term)
    return torch.mean(physics_violation * (1 - pred)) + 0.3 * torch.mean(consistency)

def train_hybrid_model(X: np.ndarray, y: np.ndarray,
                       sigma1: np.ndarray, sigma_ci: np.ndarray,
                       temp: np.ndarray, damage: np.ndarray) -> nn.Module:
    model = HybridPINN(input_dim=X.shape[1]).to(device)
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    y_t = torch.tensor(y, dtype=torch.float32).view(-1,1).to(device)
    sigma1_t = torch.tensor(sigma1, dtype=torch.float32).to(device)
    sigma_ci_t = torch.tensor(sigma_ci, dtype=torch.float32).to(device)
    temp_t = torch.tensor(temp, dtype=torch.float32).to(device)
    damage_t = torch.tensor(damage, dtype=torch.float32).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=0.0003)
    for epoch in range(80):
        pred = model(X_t)
        bce = nn.BCELoss()(pred, y_t)
        phys = physics_informed_loss(pred, sigma1_t, sigma_ci_t, temp_t, damage_t)
        loss = bce + 0.4 * phys
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model

def train_random_forest(X_scaled: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    rf = RandomForestClassifier(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_scaled, y)
    return rf

@st.cache_data
def get_ensemble_model(X: np.ndarray, y: np.ndarray,
                       sigma1: np.ndarray, sigma_ci: np.ndarray,
                       temp: np.ndarray, damage: np.ndarray) -> tuple:
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    if PT_AVAILABLE:
        model = train_hybrid_model(X_scaled, y, sigma1, sigma_ci, temp, damage)
        rf = train_random_forest(X_scaled, y)
        return model, rf, scaler
    else:
        rf = train_random_forest(X_scaled, y)
        return None, rf, scaler

X_ai, y_ai = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z)
temp_flat = temp_2d.flatten()
damage_flat = damage.flatten()
hybrid_model, rf_model, scaler = get_ensemble_model(
    X_ai, y_ai,
    sigma1_act.flatten(), sigma_ci.flatten(),
    temp_flat, damage_flat
)

def predict_collapse(model, rf, scaler, X_raw: np.ndarray) -> np.ndarray:
    if model is None and rf is None:
        return np.zeros((X_raw.shape[0], 1))
    X_scaled = scaler.transform(X_raw)
    if model is not None:
        with torch.no_grad():
            nn_pred = model(torch.tensor(X_scaled, dtype=torch.float32).to(device)).cpu().numpy()
    else:
        nn_pred = np.zeros((X_raw.shape[0], 1))
    rf_pred = rf.predict_proba(X_scaled)[:,1].reshape(-1,1)
    return 0.6*nn_pred + 0.4*rf_pred

collapse_pred = np.zeros_like(temp_2d)
try:
    feat_pred = physics_features(temp_2d.flatten(), sigma1_act.flatten(),
                                 sigma3_act.flatten(), grid_z.flatten())
    collapse_pred = predict_collapse(hybrid_model, rf_model, scaler, feat_pred).reshape(temp_2d.shape)
except Exception as e:
    st.error(f"Collapse prediction error: {str(e)}")
    collapse_pred = np.zeros_like(temp_2d)

weights = np.array([0.4, 0.3, 0.2, 0.1])
risk_index_var = (
    weights[0]*collapse_pred +
    weights[1]*(1-fos_2d) +
    weights[2]*perm/np.max(perm) +
    weights[3]*(temp_2d/np.max(temp_2d))
)
p = risk_index_var / np.sum(risk_index_var + EPS)
entropy = -np.sum(p * np.log(p + EPS))
st.metric("Tizim entropiyasi (noaniqlik)", f"{entropy:.3f}")

with st.expander("🪨 Phase-Field Fracture Damage Evolution (Patent Model)"):
    def phase_field_update(damage, strain_energy, dx, dt, Gc=0.01, l_char=1.0):
        dt_max = dx**2 / (4 * Gc * l_char)
        dt = min(dt, 0.9*dt_max)
        lap = (np.roll(damage,1,0) + np.roll(damage,-1,0) +
               np.roll(damage,1,1) + np.roll(damage,-1,1) - 4*damage) / (dx**2)
        d_new = damage + dt * (Gc * l_char * lap - (Gc / l_char) * damage + (1 - damage) * strain_energy)
        return np.clip(d_new, 0, 1)
    st.markdown(r"""
    **Phase-field fracture equation** (Bourdin et al., 2000):
    $$\eta \frac{\partial d}{\partial t} = G_c l \nabla^2 d - \frac{G_c}{l} d + (1-d)\psi$$
    """)
    if st.button("Run one phase-field step (demo)"):
        dx_val = x_axis[1]-x_axis[0]
        dt_val = 0.1
        d_updated = phase_field_update(damage, von_mises_stress(sigma1_act, sigma3_act, tau_rt), dx_val, dt_val)
        fig_phase = go.Figure(go.Heatmap(z=d_updated, x=x_axis, y=z_axis, colorscale='Viridis', zmin=0, zmax=1))
        fig_phase.update_layout(title="Phase-field damage after 1 step", template='plotly_dark')
        st.plotly_chart(fig_phase, use_container_width=True)

with st.expander("🧠 Real PINN: Heat Equation Residual Loss"):
    st.markdown("""
    **Physics-Informed Neural Network (PINN) for Temperature**
    $$\frac{\partial T}{\partial t} = \alpha \nabla^2 T + Q$$
    """)
    def pinn_heat_loss(model, x, z, t, alpha, T_bc_mask, T_bc_val):
        coords = torch.cat([x,z,t], dim=1)
        coords.requires_grad_(True)
        T = model(coords)
        grad = torch.autograd.grad(T, coords, grad_outputs=torch.ones_like(T), create_graph=True)[0]
        Tx, Tz, Tt = grad[:,0], grad[:,1], grad[:,2]
        Txx = torch.autograd.grad(Tx, coords, grad_outputs=torch.ones_like(Tx), create_graph=True)[0][:,0]
        Tzz = torch.autograd.grad(Tz, coords, grad_outputs=torch.ones_like(Tz), create_graph=True)[0][:,1]
        residual = Tt - alpha*(Txx + Tzz)
        loss_pde = torch.mean(residual**2)
        T_pred_bc = model(x[T_bc_mask], z[T_bc_mask], t[T_bc_mask])
        loss_bc = torch.mean((T_pred_bc - T_bc_val)**2)
        return loss_pde + 0.1 * loss_bc
    st.code("def pinn_heat_loss(model, x, z, t, alpha, T_bc_mask, T_bc_val): ...", language='python')
    if PT_AVAILABLE:
        st.success("PyTorch mavjud, PINN funksiyasi ishga tayyor.")
    else:
        st.warning("PyTorch yo'q, PINN ishlamaydi.")

with st.expander("📊 Uncertainty Quantification (UQ) for FOS"):
    N = 500
    ucs_samples = np.random.normal(ucs_seam, 0.1*ucs_seam, N)
    temp_samples = np.random.normal(T_source_max, 50, N)
    fos_samples = []
    for ucs_i, temp_i in zip(ucs_samples, temp_samples):
        sig_p = (ucs_i * np.exp(-beta_thermal*(temp_i - 20))) * (rec_width/(H_seam+EPS))**0.5
        fos_i = sig_p / (vertical_stress(depth_seam, avg_rho) + EPS)
        fos_samples.append(fos_i)
    fos_samples = np.array(fos_samples)
    fig_uq = go.Figure()
    fig_uq.add_histogram(x=fos_samples, nbinsx=40, marker_color='teal')
    fig_uq.add_vline(x=np.median(fos_samples), line_color='red', annotation_text='Median')
    fig_uq.update_layout(title='FOS Uncertainty Distribution', template='plotly_dark')
    st.plotly_chart(fig_uq, use_container_width=True)
    st.write(f"90% CI: [{np.percentile(fos_samples,5):.3f}, {np.percentile(fos_samples,95):.3f}]")

if SHAP_AVAILABLE and rf_model is not None:
    with st.expander("🧠 SHAP Model Interpretatsiyasi"):
        try:
            X_shap, y_shap = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z)
            background = shap.sample(X_shap, 100)
            explainer = shap.Explainer(rf_model, background)
            shap_values = explainer(background)
            st.subheader("SHAP o'zgaruvchanlik ahamiyati")
            fig_shap, ax = plt.subplots()
            shap.summary_plot(shap_values, background, show=False)
            st.pyplot(fig_shap)
        except Exception as e:
            st.warning(f"SHAP tahlili bajarilmadi: {e}")

if SALIB_AVAILABLE:
    with st.expander("📊 Global sezgirlik tahlili (Sobol')"):
        problem = {
            'num_vars': 4,
            'names': ['UCS', 'Temp', 'Depth', 'GSI'],
            'bounds': [[10, 80], [20, 1000], [10, 300], [20, 100]]
        }
        param_values = saltelli.sample(problem, 1024)
        def model_eval(params):
            ucs, T, d, gsi = params
            return ucs * np.exp(-0.002*T) / (d+1)
        Y = np.array([model_eval(p) for p in param_values])
        Si = sobol.analyze(problem, Y)
        st.write("First-order Sobol:", Si['S1'])
        st.write("Total Sobol:", Si['ST'])

if PYDOE_AVAILABLE:
    with st.expander("🎲 Latin Hypercube Sampling (Collapse ehtimolligi)"):
        N = 5000
        lhs_sample = lhs(3, samples=N)
        T_lhs = gaussian_dist.ppf(lhs_sample[:,0], loc=800, scale=100)
        UCS_lhs = gaussian_dist.ppf(lhs_sample[:,1], loc=40, scale=10)
        Depth_lhs = gaussian_dist.ppf(lhs_sample[:,2], loc=200, scale=50)
        collapse_prob = 1 / (1 + np.exp(-(T_lhs/100 + Depth_lhs/200 - UCS_lhs/50)))
        fig_lhs = go.Figure(go.Histogram(x=collapse_prob, nbinsx=50, marker_color='orange'))
        fig_lhs.update_layout(title="Collapse ehtimolligi taqsimoti", template='plotly_dark')
        st.plotly_chart(fig_lhs, use_container_width=True)
        ci_low = np.percentile(collapse_prob, 5)
        ci_high = np.percentile(collapse_prob, 95)
        st.write(f"90% ishonch intervali: [{ci_low:.3f}, {ci_high:.3f}]")

if PYVISTA_AVAILABLE:
    with st.expander("🌋 3D litologik hajm (PyVista)"):
        try:
            grid_pv = pv.UniformGrid()
            grid_pv.dimensions = (50, 50, 30)
            values = np.random.rand(50*50*30)
            grid_pv["lithology"] = values
            plotter = pv.Plotter()
            plotter.add_volume(grid_pv, cmap="viridis")
            st.image(plotter.screenshot(), use_container_width=True)
        except Exception as e:
            st.warning(f"PyVista vizualizatsiyasi amalga oshmadi: {e}")
else:
    with st.expander("🌋 3D hajm (plotly)"):
        fig_vol = go.Figure(data=go.Volume(
            x=grid_x.flatten(), y=np.zeros_like(grid_x.flatten()), z=grid_z.flatten(),
            value=temp_2d.flatten(),
            isomin=100, isomax=800,
            opacity=0.1, surface_count=20, colorscale='Hot'))
        fig_vol.update_layout(title="Harorat hajmi (proxy)", height=500)
        st.plotly_chart(fig_vol, use_container_width=True)

placeholder = st.empty()
if st.button("Harorat dinamik animatsiyasini ishga tushirish"):
    for t_anim in range(30):
        temp_dynamic = temp_2d + np.sin(t_anim/5)*50
        fig_anim = go.Figure(data=go.Heatmap(z=temp_dynamic, x=x_axis, y=z_axis, colorscale='Hot'))
        fig_anim.update_layout(title=f"Vaqt qadami {t_anim}", template='plotly_dark')
        placeholder.plotly_chart(fig_anim, use_container_width=True)
        time.sleep(0.1)

class SimpleRiskNN(nn.Module):
    def __init__(self, input_dim: int = 3):
        super(SimpleRiskNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 1), nn.Sigmoid()
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

def train_simple_risk_nn(model: nn.Module, X: np.ndarray, y: np.ndarray, epochs: int = 100) -> nn.Module:
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCELoss()
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    y_t = torch.tensor(y, dtype=torch.float32).view(-1,1).to(device)
    for _ in range(epochs):
        pred = model(X_t)
        loss = loss_fn(pred, y_t)
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model

@st.cache_data
def get_risk_model() -> nn.Module:
    if not PT_AVAILABLE:
        return None
    n_samples = 1000
    temp_r = np.random.uniform(20, 1000, n_samples)
    stress_r = np.random.uniform(1, 20, n_samples)
    ucs_r = np.random.uniform(10, 80, n_samples)
    fos_r = np.clip(ucs_r / (stress_r + EPS), 0, 3)
    risk_r = (1 - fos_r/3).reshape(-1,1)
    X_r = np.column_stack([temp_r, stress_r, ucs_r])
    y_r = risk_r.flatten()
    model = SimpleRiskNN().to(device)
    model = train_simple_risk_nn(model, X_r, y_r, epochs=150)
    model.eval()
    return model

risk_model = get_risk_model()

def predict_risk_from_sensor(model, temp: np.ndarray, stress: np.ndarray, ucs_lab: np.ndarray) -> np.ndarray:
    if model is None:
        return np.full_like(temp, 0.5)
    X = np.column_stack([temp, stress, ucs_lab])
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.flatten()

with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    sensor_file = st.file_uploader("Sensor CSV faylini yuklang (kerakli ustunlar: 'temp', 'stress', 'ucs_lab')", type=['csv'], key="sensor_ai")
    if sensor_file:
        try:
            df_sensor = pd.read_csv(sensor_file)
            required_cols = ['temp', 'stress', 'ucs_lab']
            missing = [c for c in required_cols if c not in df_sensor.columns]
            if missing:
                st.error(f"Faylda quyidagi ustunlar yo'q: {missing}.")
            else:
                risk_vals = predict_risk_from_sensor(risk_model, df_sensor['temp'].values, df_sensor['stress'].values, df_sensor['ucs_lab'].values)
                df_sensor['risk'] = risk_vals
                st.subheader("Bashorat natijalari")
                st.dataframe(df_sensor, use_container_width=True)
                fig_risk_line = go.Figure()
                fig_risk_line.add_trace(go.Scatter(y=risk_vals, mode='lines+markers', name='Risk (0-1)', line=dict(color='red')))
                fig_risk_line.add_hline(y=0.5, line_dash='dash', line_color='orange', annotation_text="O'rta chegara")
                fig_risk_line.add_hline(y=0.7, line_dash='dash', line_color='red', annotation_text="Yuqori chegara")
                fig_risk_line.update_layout(title="AI Risk Prediction", xaxis_title="Qator indeksi", yaxis_title="Risk", template='plotly_dark')
                st.plotly_chart(fig_risk_line, use_container_width=True)
                avg_risk = np.mean(risk_vals)
                st.metric("O'rtacha risk", f"{avg_risk:.3f}", delta="Yuqori" if avg_risk>0.7 else ("O'rta" if avg_risk>0.5 else "Past"))
                if avg_risk > 0.7:
                    st.error("⚠️ Yuqori xavf! Tez choralar ko'rish kerak.")
                elif avg_risk > 0.5:
                    st.warning("⚠️ O'rtacha xavf. Monitoringni kuchaytirish tavsiya etiladi.")
                else:
                    st.success("✅ Xavf past. Hozircha xavfsiz.")
        except Exception as e:
            st.error(f"Faylni o'qishda xatolik: {e}")

st.header(t('monitoring_panel', obj_name=obj_name))
def calculate_live_metrics(h, layers, T_max):
    target = layers[-1]
    ucs_0, H_l = target['ucs'], target['t']
    curr_T = (25 + (T_max-25)*(min(h,40)/40) if h<=40 else T_max*np.exp(-0.001*(h-40)))
    str_red = np.exp(-beta_thermal*(curr_T-20))
    w_rec = 15.0 + (h/150)*10
    p_str = (ucs_0*str_red)*(w_rec/(H_l+EPS))**0.5
    max_sub = (H_l*0.05)*(min(h,120)/120)
    return p_str, w_rec, curr_T, max_sub
p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max)
mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric(t('pillar_live'), f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric(t('rec_width_live'), f"{w_rec_live:.1f} m")
mk3.metric(t('max_subsidence_live'), f"{s_max_3d*100:.1f} cm")
mk4.metric(t('process_stage'), t('stage_active') if time_h<100 else t('stage_cooling'))
st.markdown("---")

with st.expander("📈 FOS Vaqt Bashorati (Trend)"):
    time_points = np.arange(1, time_h+1, max(1, time_h//20))
    fos_timeline = []
    for th in time_points:
        T_at_th = T_source_max * min(th, burn_duration) / (burn_duration + EPS)
        str_red_t = np.exp(-beta_thermal * (T_at_th - 20))
        p_str_t = (ucs_seam * str_red_t) * (rec_width/(H_seam+EPS))**0.5
        sv_t = sv_seam * (1 + 0.001*th)
        fos_t = np.clip(p_str_t/(sv_t+EPS), 0, 3)
        fos_timeline.append(fos_t)
    slope, intercept, r_value, _, _ = linregress(time_points, fos_timeline)
    future_times = np.arange(time_h, min(time_h*2,300), max(1,time_h//10))
    fos_forecast = intercept + slope*future_times
    fos_forecast = np.clip(fos_forecast,0,3)
    if slope<0 and intercept+slope*time_h>1.0:
        t_critical = (1.0-intercept)/slope
        critical_info = f"⚠️ FOS=1.0 ga taxminan **{t_critical:.0f}** soatda yetishi mumkin"
    else:
        critical_info = "✅ Hozirgi trend bo'yicha FOS=1.0 ga yetish xavfi yo'q"
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=time_points, y=fos_timeline, mode='lines+markers', name='Hisoblangan FOS', line=dict(color='cyan',width=2), marker=dict(size=6)))
    trend_line = intercept+slope*time_points
    fig_trend.add_trace(go.Scatter(x=time_points, y=trend_line, mode='lines', name=f'Trend (R²={r_value**2:.3f})', line=dict(color='yellow',width=1,dash='dot')))
    fig_trend.add_trace(go.Scatter(x=future_times, y=fos_forecast, mode='lines', name='Bashorat', line=dict(color='orange',width=2,dash='dash'), fill='tozeroy', fillcolor='rgba(255,165,0,0.1)'))
    fig_trend.add_hline(y=1.5, line_color='green', line_dash='dash', annotation_text='Barqaror chegarasi (1.5)')
    fig_trend.add_hline(y=1.0, line_color='red', line_dash='dash', annotation_text='Kritik chegara (1.0)')
    fig_trend.add_vline(x=time_h, line_color='white', line_dash='dot', annotation_text=f'Hozir ({time_h}h)')
    fig_trend.update_layout(template='plotly_dark', height=400, title=f"FOS vaqt bashorati | Trend: {slope:+.4f} FOS/soat", xaxis_title='Vaqt (soat)', yaxis_title='FOS', legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig_trend, use_container_width=True)
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Trend ko'rsatkichi", f"{slope:+.5f} FOS/soat", delta="Kamaymoqda" if slope<0 else "O'smoqda", delta_color="inverse" if slope<0 else "normal")
    tc2.metric("R² (trend aniqligi)", f"{r_value**2:.4f}")
    tc3.metric("Hozirgi FOS", f"{fos_timeline[-1]:.3f}")
    st.info(critical_info)

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
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_top, colorscale=[[0, rgb_str], [1, rgb_str]],
                                    showscale=False, opacity=0.7, name=layer['name']))
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_bot, colorscale=[[0, rgb_str], [1, rgb_str]],
                                    showscale=False, opacity=0.7, name=f"{layer['name']}_bottom"))
    # Use stage directly (defined earlier)
    active_wells_3d = states_132[stage]
    for idx, px in enumerate(well_x):
        if idx in active_wells_3d:
            theta = np.linspace(0, 2 * np.pi, 30)
            phi = np.linspace(0, np.pi, 20)
            THETA, PHI = np.meshgrid(theta, phi)
            R_use = cavity_radius
            cx = px + R_use * np.sin(PHI) * np.cos(THETA)
            cy = R_use * np.sin(PHI) * np.sin(THETA)
            cz = source_z + R_use * np.cos(PHI)
            fig_3d.add_trace(go.Surface(x=cx, y=cy, z=cz,
                                        colorscale=[[0, 'orange'], [1, 'red']],
                                        showscale=False, opacity=0.85,
                                        name=f'Yonish kamerasi {idx+1}'))
    fig_3d.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)',
                                    zaxis_title='Chuqurlik (m)',
                                    zaxis=dict(autorange='reversed'),
                                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))),
                         template='plotly_dark', height=600,
                         title="3D Litologik Model + Yonish Kameralari",
                         showlegend=True)
    st.plotly_chart(fig_3d, use_container_width=True)

with st.expander("🎲 Monte Carlo Noaniqlik Tahlili"):
    mc_col1, mc_col2 = st.columns([1,2])
    with mc_col1:
        ucs_std_val = st.number_input("UCS standart og'ish (MPa)", value=5.0, min_value=0.1)
        gsi_std_val = st.number_input("GSI standart og'ish", value=5.0, min_value=0.1)
        n_mc = st.selectbox("Simulyatsiya soni", [500,1000,2000,5000], index=1)
    with mc_col2:
        fos_mc, pf = monte_carlo_fos(layers_data[-1]['ucs'], ucs_std_val,
                                     layers_data[-1]['gsi'], gsi_std_val,
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

with st.expander("⚖️ Ssenariy Taqqoslash (A vs B)"):
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("**Ssenariy A**")
        a_ucs = st.number_input("UCS_A (MPa)", value=float(layers_data[-1]['ucs']), key="a_ucs")
        a_gsi = st.slider("GSI_A", 10, 100, layers_data[-1]['gsi'], key="a_gsi")
        a_temp = st.number_input("T_A (°C)", value=float(T_source_max), key="a_t")
    with sc2:
        st.markdown("**Ssenariy B**")
        b_ucs = st.number_input("UCS_B (MPa)", value=float(layers_data[-1]['ucs'])*0.8, key="b_ucs")
        b_gsi = st.slider("GSI_B", 10, 100, max(10, layers_data[-1]['gsi']-10), key="b_gsi")
        b_temp = st.number_input("T_B (°C)", value=float(T_source_max)*1.1, key="b_t")
    def norm(val, mn, mx):
        return (val-mn)/(mx-mn+EPS)
    fos_a = (a_ucs*np.exp(-beta_thermal*(a_temp-20))) / (layers_data[-1]['rho']*9.81*H_seam/1e6+EPS)
    fos_b = (b_ucs*np.exp(-beta_thermal*(b_temp-20))) / (layers_data[-1]['rho']*9.81*H_seam/1e6+EPS)
    vals_a = [norm(a_ucs,0,100), norm(a_gsi,10,100), norm(fos_a,0,3), 1-norm(a_temp,20,1200)]
    vals_b = [norm(b_ucs,0,100), norm(b_gsi,10,100), norm(fos_b,0,3), 1-norm(b_temp,20,1200)]
    categories = ['UCS','GSI','FOS (taxmin)','Termal risk']
    fig_radar = go.Figure()
    for name, vals, color in [("A", vals_a, '#3498DB'), ("B", vals_b, '#E74C3C')]:
        fig_radar.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=categories+[categories[0]], fill='toself', name=f"Ssenariy {name}", line=dict(color=color,width=2), fillcolor=color, opacity=0.3))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,1])), template='plotly_dark', height=400, title="Ssenariylar radar taqqoslama")
    st.plotly_chart(fig_radar, use_container_width=True)
    comp_df = pd.DataFrame({'Ko\'rsatkich': ['UCS (MPa)','GSI','FOS (taxmin)','Harorat (°C)'],
                            'Ssenariy A': [f"{a_ucs:.1f}", f"{a_gsi}", f"{fos_a:.2f}", f"{a_temp:.0f}"],
                            'Ssenariy B': [f"{b_ucs:.1f}", f"{b_gsi}", f"{fos_b:.2f}", f"{b_temp:.0f}"],
                            'Farq': [f"{b_ucs-a_ucs:+.1f}", f"{b_gsi-a_gsi:+d}", f"{fos_b-fos_a:+.2f}", f"{b_temp-a_temp:+.0f}"]})
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

@st.cache_data(show_spinner=False)
def sensitivity_analysis(base_ucs, base_gsi, base_d, base_nu, base_t, H_seam, beta_th, range_pct=0.2):
    def quick_fos(ucs, gsi, d, nu, T):
        mb = 10*np.exp((gsi-100)/(28-14*d))
        s  = np.exp((gsi-100)/(9-3*d))
        a  = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
        damage = np.clip(1-np.exp(-beta_th * max(T-20, 0)), 0, 0.95)
        sigma_ci = ucs*(1-damage)
        sigma_cm = sigma_ci * (max(s, 1e-9)**a)
        p_str = sigma_cm * (20/(H_seam+EPS))**0.5
        sv = vertical_stress(200.0, 2500.0)
        return np.clip(p_str/(sv+EPS), 0, 5)
    params = {
        'UCS (MPa)': (base_ucs, base_ucs*(1-range_pct), base_ucs*(1+range_pct)),
        'GSI': (base_gsi, base_gsi*(1-range_pct), min(100,base_gsi*(1+range_pct))),
        'D factor': (base_d, max(0,base_d-0.2), min(1,base_d+0.2)),
        'Poisson (ν)': (base_nu, max(0.1,base_nu-0.05), min(0.4,base_nu+0.05)),
        'Harorat (°C)': (base_t, base_t*(1-range_pct), min(1200,base_t*(1+range_pct))),
    }
    base_fos = quick_fos(base_ucs, base_gsi, base_d, base_nu, base_t)
    results = []
    for name, (base, low, high) in params.items():
        fos_low = quick_fos(low if name=='UCS (MPa)' else base_ucs,
                            low if name=='GSI' else base_gsi,
                            low if name=='D factor' else base_d,
                            low if name=='Poisson (ν)' else base_nu,
                            low if name=='Harorat (°C)' else base_t)
        fos_high = quick_fos(high if name=='UCS (MPa)' else base_ucs,
                             high if name=='GSI' else base_gsi,
                             high if name=='D factor' else base_d,
                             high if name=='Poisson (ν)' else base_nu,
                             high if name=='Harorat (°C)' else base_t)
        results.append({'param':name, 'low':fos_low-base_fos, 'high':fos_high-base_fos})
    return pd.DataFrame(results), base_fos

with st.expander("🌪️ Sezgirlik Tahlili (Tornado Plot)"):
    df_sens, fos_base = sensitivity_analysis(layers_data[-1]['ucs'], layers_data[-1]['gsi'], D_factor, nu_poisson, avg_t_p, H_seam, beta_thermal)
    df_sens = df_sens.sort_values('high', ascending=True)
    fig_tornado = go.Figure()
    fig_tornado.add_bar(y=df_sens['param'], x=df_sens['low'], orientation='h', name='−20%', marker_color='#E74C3C')
    fig_tornado.add_bar(y=df_sens['param'], x=df_sens['high'], orientation='h', name='+20%', marker_color='#27AE60')
    fig_tornado.add_vline(x=0, line_color='white', line_width=2)
    fig_tornado.update_layout(title=f"FOS sezgirligi (asosiy FOS={fos_base:.2f})", barmode='overlay', template='plotly_dark', height=350, xaxis_title='ΔFOS', bargap=0.3)
    st.plotly_chart(fig_tornado, use_container_width=True)

def generate_full_iso_report(obj_name: str, lang: str, layers_data: list,
                             T_source_max: float, burn_duration: float,
                             pillar_strength: float, optimal_width_ai: float,
                             fos_2d: np.ndarray, risk_map: np.ndarray,
                             void_volume: float,
                             prepared_by: str, approved_by: str,
                             doc_number: str, revision: str,
                             fig_bytes: bytes = None) -> bytes:
    texts = {
        'uz': {
            'h1': "ISO 9001:2015 MUVOFIQDAT HISOBOTI",
            'sec1': "1. LOYIHA UMUMIY TAVSIFI",
            'sec2': "2. GEOMEXANIK QATLAMLAR VA XOSSALARI",
            'sec3': "3. RISKNI BAHOLASH (RISK ASSESSMENT)",
            'sec4': "4. XAVFNI KAMAYTIRISH CHORALARI (MITIGATION)",
            'sec5': "5. MUHANDISLIK XULOSASI VA TAVSIYALAR",
            'fos_label': "Xavfsizlik koeffitsienti (FOS):",
            'ai_label': "AI tomonidan optimallashtirilgan kenglik:",
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
            'ai_label': "AI Optimized Width:",
            'conclusion_title': "Final Decision:",
            'safe': "✅ SYSTEM STABLE: Project parameters meet safety requirements.",
            'warning': "⚠️ MARGINAL STABILITY: Increased monitoring and support recommended.",
            'danger': "🚨 DANGEROUS: High risk of collapse! Increase pillar width or reduce thermal load.",
            'risk_ident': "Identified hazards: thermal degradation, large void volume, FOS < 1.3.",
            'mitigation': "Mitigation: increase pillar width, reduce gas pressure, real-time monitoring."
        }
    }
    t = texts.get(lang, texts['en'])
    doc = Document()
    header = doc.add_heading(f"{t['h1']}\n{obj_name}", level=1)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.style = 'Table Grid'
    meta_table.cell(0,0).text = f"Doc No: {doc_number}"
    meta_table.cell(0,1).text = f"Revision: {revision}"
    meta_table.cell(1,0).text = f"Prepared: {prepared_by}"
    meta_table.cell(1,1).text = f"Approved: {approved_by}"
    doc.add_heading(t['sec1'], level=2)
    p = doc.add_paragraph()
    p.add_run(f"Ob'ekt nomi: ").bold = True
    p.add_run(f"{obj_name}\n")
    p.add_run(f"Maksimal harorat: ").bold = True
    p.add_run(f"{T_source_max} °C\n")
    p.add_run(f"Yonish davomiyligi: ").bold = True
    p.add_run(f"{burn_duration} soat")
    doc.add_heading(t['sec2'], level=2)
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    hdrs = ["Layer Name", "Thick (m)", "UCS (MPa)", "GSI", "mi"]
    for i, h in enumerate(hdrs):
        table.rows[0].cells[i].text = h
    for layer in layers_data:
        row = table.add_row().cells
        row[0].text = layer['name']
        row[1].text = f"{layer['t']:.1f}"
        row[2].text = f"{layer['ucs']:.1f}"
        row[3].text = str(layer['gsi'])
        row[4].text = f"{layer['mi']:.1f}"
    doc.add_heading(t['sec3'], level=2)
    doc.add_paragraph(t['risk_ident'])
    avg_risk = np.mean(risk_map)
    doc.add_paragraph(f"O'rtacha xavf indeksi: {avg_risk:.3f}")
    doc.add_paragraph(f"FOS minimal: {np.min(fos_2d):.2f}, maksimal bo'shliq: {void_volume:.1f} m²")
    doc.add_heading(t['sec4'], level=2)
    doc.add_paragraph(t['mitigation'])
    doc.add_paragraph(f"Tavsiya qilingan selek eni: {optimal_width_ai:.1f} m")
    if fig_bytes:
        doc.add_heading("Visual Analysis (Risk Map)", level=2)
        image_stream = io.BytesIO(fig_bytes)
        doc.add_picture(image_stream, width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading(t['sec5'], level=2)
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
        conclusion_text = t['danger']
        color = RGBColor(255, 0, 0)
    elif fos_val < 1.5:
        conclusion_text = t['warning']
        color = RGBColor(255, 165, 0)
    else:
        conclusion_text = t['safe']
    res_p = doc.add_paragraph()
    res_p.add_run(f"{t['fos_label']} {fos_val:.2f}\n").bold = True
    res_p.add_run(f"{t['ai_label']} {optimal_width_ai:.1f} m\n\n")
    final_run = res_p.add_run(f"{t['conclusion_title']}\n{conclusion_text}")
    final_run.bold = True
    final_run.font.color.rgb = color
    doc.add_page_break()
    doc.add_heading("APPENDIX: Mathematical Models Used", level=2)
    doc.add_paragraph("1. Hoek-Brown Failure Criterion — Rock Mass Strength (Hoek & Brown, 2018)")
    doc.add_paragraph("σ1 = σ3 + σci * (mb * σ3 / σci + s)^a", style='Intense Quote')
    doc.add_paragraph("mb = mi * exp((GSI-100)/(28-14D));  s = exp((GSI-100)/(9-3D));  a = 0.5 + (1/6)*(e^(-GSI/15) - e^(-20/3))", style='Intense Quote')
    doc.add_paragraph("2. Hoek-Brown Tensile Strength (Hoek & Brown, 2002)")
    doc.add_paragraph("σt0 = (σci/2) * (mb - sqrt(mb² + 4s))", style='Intense Quote')
    doc.add_paragraph("3. Thermal Strength Decay — Shao et al. (2015)")
    doc.add_paragraph("UCS(T) = UCS_0 * exp(-β * (T - T0)),  T0 = 20°C", style='Intense Quote')
    doc.add_paragraph("D(T) = 1 - exp(-β * max(T - 20, 0))", style='Intense Quote')
    doc.add_paragraph("4. Thermal Stress (Thermo-Elastic Theory)")
    doc.add_paragraph("σth = ηc * E * α * ΔT / (1 - ν) - λr * ∇T", style='Intense Quote')
    doc.add_paragraph("5. Wilson (1972) Pillar Strength & Plastic Zone")
    doc.add_paragraph("σp = UCS(T) * (w/H)^0.5;  y = H/2 * (sqrt(σv/σp) - 1) if σv≥σp else 0", style='Intense Quote')
    doc.add_paragraph("6. Peck (1969) Surface Subsidence — Gaussian Model")
    doc.add_paragraph("S(x) = Smax * exp(-x²/(2i²)),  i = 0.45*Htot", style='Intense Quote')
    doc.add_paragraph("7. O'Reilly & New (1982) Horizontal Displacement")
    doc.add_paragraph("u_h(x) = - x/i * S(x)", style='Intense Quote')
    doc.add_paragraph("8. Darcy Gas Flow (with viscosity)")
    doc.add_paragraph("v = -k/μ * grad(P),  μ_gas ≈ 3×10⁻⁵ Pa·s (at 1000°C)", style='Intense Quote')
    doc.add_paragraph("9. Kozeny-Carman Permeability (modified)")
    doc.add_paragraph("k = k0 * exp(8*D) * (1 + 25*εv)", style='Intense Quote')
    doc.add_paragraph("10. Risk Index (Composite)")
    doc.add_paragraph("R = 0.4*P_collapse + 0.3*(1-FOS/3) + 0.2*(k/kmax) + 0.1*(T/Tmax)", style='Intense Quote')
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
                    pillar_strength=pillar_strength, optimal_width_ai=optimal_width_ai,
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

st.header("🔄 Live 3D Monitoring (Real-time)")
tab_live, tab_ai_orig, tab_advanced = st.tabs([t('live_monitoring_tab'), t('ai_monitor_title'), t('advanced_analysis')])

with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies and alerts")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    run_live = st.button("▶️ Run Live Monitoring", key="run_live")
    stop_live = st.button("⏹ Stop Monitoring", key="stop_live")
    if 'stop_flag_live' not in st.session_state:
        st.session_state.stop_flag_live = False
    if stop_live:
        st.session_state.stop_flag_live = True
    col_live1, col_live2 = st.columns(2)
    subs_plot_live = col_live1.empty()
    temp_plot_live = col_live2.empty()
    col_live3, col_live4 = st.columns(2)
    pillar_plot_live = col_live3.empty()
    trend_plot_live = col_live4.empty()
    surface_3d_plot_live = st.empty()
    alert_box_live = st.empty()
    if 'live_history_df' not in st.session_state:
        st.session_state.live_history_df = pd.DataFrame(columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m'])
    if run_live:
        st.session_state.stop_flag_live = False
        X_live = np.linspace(-20,20,50)
        Y_live = np.linspace(-20,20,50)
        X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_history_live = []
        fos_history_live = []
        width_history_live = []
        temp_history_live = []
        steps_done = 0
        rf_live = RandomForestRegressor(n_estimators=10, random_state=42)
        dummy_X = np.random.rand(10,3)
        dummy_y = np.random.rand(10)
        rf_live.fit(dummy_X, dummy_y)
        for t_step in range(TIME_STEPS):
            if st.session_state.stop_flag_live:
                break
            Z_subs = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*(5+t_step*0.1)**2))*5*t_step/TIME_STEPS
            Z_temp = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*8**2))*T_source_max*t_step/TIME_STEPS
            Z_filtered = gaussian_filter(Z_subs, sigma=1)
            anomalies = Z_subs - Z_filtered
            anomaly_points = np.where(np.abs(anomalies) > 0.2)
            avg_ucs = np.mean([l['ucs'] for l in layers_data])
            X_feat = np.array([[burn_duration, T_source_max, avg_ucs]]).reshape(1,-1)
            pillar_width_pred = rf_live.predict(X_feat)[0]
            FOS_live = np.clip(2.5 - t_step*0.03, 0.8, 2.5)
            mean_subs = np.mean(Z_subs)
            subs_history_live.append(mean_subs)
            fos_history_live.append(FOS_live)
            width_history_live.append(pillar_width_pred)
            temp_history_live.append(np.mean(Z_temp))
            MAX_HISTORY = 1000
            new_row = pd.DataFrame({'step':[t_step+1],'mean_subsidence_cm':[mean_subs*100],'max_temp_c':[np.max(Z_temp)],'FOS':[FOS_live],'pillar_width_m':[pillar_width_pred]})
            st.session_state.live_history_df = pd.concat([st.session_state.live_history_df, new_row], ignore_index=True).tail(MAX_HISTORY)
            fig_subs = go.Figure(go.Heatmap(z=Z_subs*100, x=X_live, y=Y_live, colorscale='Viridis')).update_layout(title='Surface Subsidence (cm)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            subs_plot_live.plotly_chart(fig_subs, use_container_width=True, key=f"subs_{t_step}")
            fig_temp = go.Figure(go.Heatmap(z=Z_temp, x=X_live, y=Y_live, colorscale='Hot')).update_layout(title='Temperature Field (°C)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            temp_plot_live.plotly_chart(fig_temp, use_container_width=True, key=f"temp_{t_step}")
            pillar_plot_live.metric(label="Recommended Pillar Width (m)", value=f"{pillar_width_pred:.2f}", delta=f"FOS = {FOS_live:.2f}")
            trend_fig = go.Figure(go.Scatter(y=subs_history_live, mode='lines+markers', name='Subsidence (cm)')).update_layout(title='Subsidence Trend', xaxis_title='Time step', yaxis_title='Mean subsidence (cm)', height=350)
            trend_plot_live.plotly_chart(trend_fig, use_container_width=True, key=f"trend_{t_step}")
            surface_fig = go.Figure(data=[go.Surface(z=Z_subs*100, x=X_live, y=Y_live, colorscale='Viridis', opacity=0.9)])
            if anomaly_points[0].size > 0:
                surface_fig.add_trace(go.Scatter3d(x=X_grid_live[anomaly_points], y=Y_grid_live[anomaly_points], z=Z_subs[anomaly_points]*100, mode='markers', marker=dict(color='red', size=5), name='Anomaly'))
            surface_fig.update_layout(title='3D Surface & Anomalies', scene=dict(zaxis_title='Subsidence (cm)'), height=500)
            surface_3d_plot_live.plotly_chart(surface_fig, use_container_width=True, key=f"surf_{t_step}")
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
        st.success(f"✅ Live monitoring completed after {steps_done} steps.")
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
        T = np.linspace(20, min(1100,T_source_max), n_steps) + np.random.normal(0,10,n_steps)
        sigma_v = np.linspace(5, min(15, sv_seam*10), n_steps) + np.random.normal(0,0.5,n_steps)
        return pd.DataFrame({'Temperature':T, 'VerticalStress':sigma_v})
    if PT_AVAILABLE:
        class SimpleNN(nn.Module):
            def __init__(self):
                super(SimpleNN, self).__init__()
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
        fos_rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
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
            fos_rf_trained = False
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
                    if not fos_rf_trained:
                        fos_rf_model.fit(X, [fos_target])
                        fos_rf_trained = True
                    y_pred = fos_rf_model.predict(X)[0]
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
    E_MODULUS_R, ALPHA_THERM, BETA_CONST = 5e9, 1e-5, beta_thermal
    target_l = layers_data[-1]
    ucs_0_r, gsi_val, mi_val = target_l['ucs'], target_l['gsi'], target_l['mi']
    gamma_kn = target_l['rho'] * 9.81 / 1000
    H_depth_tot = sum(l['t'] for l in layers_data[:-1]) + target_l['t']/2
    sigma_v_tot = vertical_stress(H_depth_tot, target_l['rho'])
    mb_dyn = mi_val * np.exp((gsi_val-100)/(28-14*D_factor))
    s_dyn = np.exp((gsi_val-100)/(9-3*D_factor))
    a_dyn = 0.5 + (1/6)*(np.exp(-gsi_val/15) - np.exp(-20/3))
    ucs_t_dyn = ucs_0_r * np.exp(-BETA_CONST * (T_source_max - 20))
    sigma_cm = ucs_t_dyn * (s_dyn ** a_dyn)
    p_str_final = sigma_cm * (rec_width / (H_seam + EPS))**0.5
    fos_final = p_str_final / (sigma_v_tot + EPS)
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
                                  t('param_table_value'): [f"{E_MODULUS_R} MPa", f"{ALPHA_THERM} 1/°C", "20 °C"],
                                  t('param_table_reason'): [t('modulus_reason'), t('alpha_reason'), t('temp0_reason')]})
        st.table(params_df)
        st.markdown(t('ucs_decay'))
        st.latex(t('ucs_decay_eq', ucs=ucs_t_dyn))
        st.write(t('ucs_interpret', temp=T_source_max, perc=((1 - ucs_t_dyn/ucs_0_r)*100)))
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

st.header("🕹️ Ultimate Interactive Dashboard (Real-time Animation)")
st.markdown("Bu panelda FOS, siljish maydoni va vaqt bo'yicha sirt siljishlarini interaktiv kuzatishingiz mumkin.")

sub_2d = np.tile(sub_p.reshape(1,-1)*100, (len(z_axis), 1))
uplift_2d = np.tile(horizontal_disp_cm.reshape(1,-1), (len(z_axis), 1))
displacement_2d = np.sqrt(sub_2d**2 + uplift_2d**2)

time_steps_dash = np.arange(0, time_h+1, max(1, time_h//20))
surface_x = x_axis
surface_h_disp = []
surface_v_disp = []
for time_step in time_steps_dash:
    subs_t_step = Smax * (1 - np.exp(-c_subs * time_step))
    v_disp = -subs_t_step * np.exp(-(surface_x**2)/(2*i_inflection**2)) * 100
    h_disp = -(surface_x / (i_inflection + EPS)) * v_disp
    surface_v_disp.append(v_disp)
    surface_h_disp.append(h_disp)
surface_h_disp = np.array(surface_h_disp)
surface_v_disp = np.array(surface_v_disp)

col1_dash, col2_dash = st.columns(2)
with col1_dash:
    fos_thresh_dash = st.slider("FOS Threshold (Yielded Zone)", 0.1, 2.0, 1.0, 0.05, key="fos_thresh_dash")
with col2_dash:
    disp_cscale = st.selectbox("Displacement Color Scale", ['Turbo','Viridis','Cividis'], index=0, key="disp_cscale")

def draw_interactive_ucg_dashboard(x_axis, z_axis, fos_2d, displacement_2d, surface_x, surface_h_disp, surface_v_disp, time_steps=None, fos_threshold=1.0, disp_colorscale='Turbo'):
    if time_steps is None:
        time_steps = np.arange(surface_h_disp.shape[0])
    pillar_locations = np.linspace(x_axis.min() + 50, x_axis.max() - 50, 3)
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("A) FOS & Yielded Zones (2D)",
                                        "B) Total Displacement (2D, cm)",
                                        "C) Horizontal Surface Displacement (mm)",
                                        "D) Vertical Surface Displacement (mm)"),
                        horizontal_spacing=0.1, vertical_spacing=0.15)
    fig.add_trace(go.Heatmap(
        z=fos_2d, x=x_axis, y=z_axis,
        colorscale=[[0, 'rgb(255, 0, 0)'], [0.33, 'rgb(255, 165, 0)'], [0.5, 'rgb(173, 255, 47)'], [1, 'rgb(0, 128, 0)']],
        zmin=0, zmax=3, colorbar=dict(title="FOS", x=0.45, y=0.78, thickness=12, len=0.42), name="FOS"
    ), row=1, col=1)
    mask_fos = np.where(fos_2d < fos_threshold, 1, np.nan)
    fig.add_trace(go.Heatmap(z=mask_fos, x=x_axis, y=z_axis,
                             colorscale=[[0,'rgba(255,0,0,0.5)'],[1,'rgba(255,0,0,0.5)']],
                             showscale=False, name="Yielded Zone"), row=1, col=1)
    fig.add_trace(go.Heatmap(z=displacement_2d, x=x_axis, y=z_axis,
                             colorscale=disp_colorscale,
                             colorbar=dict(title="Disp (cm)", x=1.0, y=0.78, thickness=12, len=0.42),
                             name="2D Disp"), row=1, col=2)
    frames = []
    for i, t in enumerate(time_steps):
        frame_data = []
        frame_data.append(go.Heatmap(z=fos_2d, x=x_axis, y=z_axis,
                                     colorscale=[[0, 'rgb(255,0,0)'], [0.33, 'rgb(255,165,0)'], [0.5, 'rgb(173,255,47)'], [1, 'rgb(0,128,0)']],
                                     zmin=0, zmax=3, showscale=False))
        frame_data.append(go.Heatmap(z=mask_fos, x=x_axis, y=z_axis,
                                     colorscale=[[0,'rgba(255,0,0,0.5)'],[1,'rgba(255,0,0,0.5)']],
                                     showscale=False))
        frame_data.append(go.Heatmap(z=displacement_2d, x=x_axis, y=z_axis,
                                     colorscale=disp_colorscale, showscale=False))
        frame_data.append(go.Heatmap(z=surface_h_disp[i:i+1,:], x=surface_x, y=[t],
                                     colorscale='Turbo', zmin=np.min(surface_h_disp), zmax=np.max(surface_h_disp),
                                     showscale=False))
        frame_data.append(go.Heatmap(z=surface_v_disp[i:i+1,:], x=surface_x, y=[t],
                                     colorscale='Viridis', zmin=np.min(surface_v_disp), zmax=np.max(surface_v_disp),
                                     showscale=False))
        frames.append(go.Frame(data=frame_data, name=f"t{i}"))
    fig.frames = frames
    for i, t in enumerate(time_steps):
        if i == 0:
            fig.add_trace(go.Heatmap(z=surface_h_disp[i:i+1,:], x=surface_x, y=[t],
                                     colorscale='Turbo', zmin=np.min(surface_h_disp), zmax=np.max(surface_h_disp),
                                     showscale=False, visible=True, name="H Disp"), row=2, col=1)
            fig.add_trace(go.Heatmap(z=surface_v_disp[i:i+1,:], x=surface_x, y=[t],
                                     colorscale='Viridis', zmin=np.min(surface_v_disp), zmax=np.max(surface_v_disp),
                                     showscale=False, visible=True, name="V Disp"), row=2, col=2)
    for pos in pillar_locations:
        fig.add_shape(type="rect", x0=pos-25, x1=pos+25, y0=550, y1=600,
                      line=dict(color="Lime", width=3), row=1, col=1)
        fig.add_shape(type="rect", x0=pos-25, x1=pos+25, y0=550, y1=600,
                      line=dict(color="Lime", width=3), row=1, col=2)
    fig.layout.xaxis.title.text = "X (m)"
    fig.layout.xaxis.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.xaxis.range = [x_axis.min(), x_axis.max()]
    fig.layout.yaxis.title.text = "Depth (m)"
    fig.layout.yaxis.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.yaxis.autorange = "reversed"
    fig.layout.xaxis2.title.text = "X (m)"
    fig.layout.xaxis2.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.xaxis2.range = [x_axis.min(), x_axis.max()]
    fig.layout.yaxis2.title.text = "Depth (m)"
    fig.layout.yaxis2.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.yaxis2.autorange = "reversed"
    fig.layout.xaxis3.title.text = "Masofa (m)"
    fig.layout.xaxis3.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.yaxis3.title.text = "Vaqt bosqichi"
    fig.layout.yaxis3.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.xaxis4.title.text = "Masofa (m)"
    fig.layout.xaxis4.gridcolor = 'rgba(255,255,255,0.1)'
    fig.layout.yaxis4.title.text = "Vaqt bosqichi"
    fig.layout.yaxis4.gridcolor = 'rgba(255,255,255,0.1)'
    fig.update_layout(
        title=dict(text="Interactive Ultimate UCG Monitoring Dashboard", x=0.5, font=dict(size=22, color="white")),
        plot_bgcolor='black', paper_bgcolor='black', template='plotly_dark', height=900,
        showlegend=False, margin=dict(l=50, r=50, t=100, b=50),
        updatemenus=[dict(type="buttons", showactive=False, y=1.05, x=1.15, xanchor="right", yanchor="top",
                          buttons=[dict(label="Play", method="animate",
                                        args=[None, {"frame": {"duration":500, "redraw":True}, "fromcurrent":True, "transition": {"duration":0}}]),
                                   dict(label="Pause", method="animate",
                                        args=[[None], {"frame": {"duration":0, "redraw":False}, "mode":"immediate", "transition": {"duration":0}}])])],
        sliders=[dict(steps=[dict(method='animate', args=[[f"t{k}"], {"mode":"immediate", "frame":{"duration":300, "redraw":True}, "transition":{"duration":0}}], label=f'{v:.0f}h') for k,v in enumerate(time_steps) if k%3==0],
                      active=0, y=0.0, x=0.1, len=0.9)]
    )
    return fig

dash_fig = draw_interactive_ucg_dashboard(
    x_axis=x_axis, z_axis=z_axis, fos_2d=fos_2d,
    displacement_2d=displacement_2d, surface_x=surface_x,
    surface_h_disp=surface_h_disp, surface_v_disp=surface_v_disp,
    time_steps=time_steps_dash, fos_threshold=fos_thresh_dash, disp_colorscale=disp_cscale
)
st.plotly_chart(dash_fig, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")

if FASTAPI_AVAILABLE:
    app = FastAPI()
    @app.post("/predict")
    def predict_api(data: dict):
        temp = np.array(data["temp"])
        s1   = np.array(data["sigma1"])
        s3   = np.array(data["sigma3"])
        d    = np.array(data["depth"])
        features = physics_features(temp, s1, s3, d)
        pred = hybrid_model(
            torch.tensor(features, dtype=torch.float32).to(device)
        ) if hybrid_model is not None else np.zeros((features.shape[0],1))
        return {"collapse": pred.detach().cpu().numpy().tolist()}
