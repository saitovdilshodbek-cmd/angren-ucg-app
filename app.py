"""
UCG Termo-Mexanik Dinamik Monitoring Tizimi
===========================================
Yer osti ko'mir gazlashtirish (UCG) uchun geomexanik barqarorlik,
termal degradatsiya va cho'kish monitoringi.

PhD dissertatsiya va patent talablariga mos holda tayyorlangan.

Tuzuvchi: Saitov Dilshodbek
Sana: 2026

Asosiy adabiyotlar:
  [1] Hoek & Brown (2018) – JRMGE
  [2] Yang (2010) – TU Delft PhD thesis
  [3] Shao et al. (2015) – IJRMMS
  [4] Wilson (1972) – Mining Engineer
  [5] Bieniawski (1989) – Engineering Rock Mass Classifications
  [6] Salmi & Karakus (2019) – Int. J. Rock Mech. Min. Sci.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress, norm as gaussian_dist
import time
import io
from io import BytesIO
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import qrcode
import matplotlib.pyplot as plt
import warnings
import sys
import requests
import logging

warnings.filterwarnings('ignore')

from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor, IsolationForest
)
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve
from sklearn.model_selection import KFold
import joblib
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================  FASTAPI  ===========================
try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# ===========================  PYTORCH  ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    PT_AVAILABLE = False
    device = "cpu"

# ===========================  SALib  ===========================
try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

# ===========================  pyDOE  ===========================
try:
    from pyDOE import lhs
    PYDOE_AVAILABLE = True
except ImportError:
    PYDOE_AVAILABLE = False

# ===========================  PyVista  ===========================
try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

# ===========================  SHAP  ===========================
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# =========================== GLOBAL TRANSLATIONS ===========================
TRANSLATIONS = {
    'uz': {
        'app_title': "UCG Termo-Mexanik Dinamik 3-D Monitoring",
        'app_subtitle': "Yer osti Ko'mir Gazlashtirish – Geomexanik Barqarorlik Tahlili",
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
        'thermal_decay': "Thermal Decay β (1/°C):",
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
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*, 10(3), 445–463.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification Cavities*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*, 78, 216–226.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*, 131, 409–417.",
        'ref5': "**Bieniawski, Z. T. (1989).** *Engineering Rock Mass Classifications*. Wiley, New York.",
        'ref6': "**Salmi, E. F., & Karakus, M. (2019).** Numerical analysis of pillar failure in underground coal mines. *Int. J. Rock Mech. Min. Sci.*, 120, 55–67.",
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
        'app_title': "UCG Thermo-Mechanical Dynamic 3-D Monitoring",
        'app_subtitle': "Underground Coal Gasification – Geomechanical Stability Analysis",
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
        'thermal_decay': "Thermal Decay β (1/°C):",
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
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*, 10(3), 445–463.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification Cavities*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*, 78, 216–226.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*, 131, 409–417.",
        'ref5': "**Bieniawski, Z. T. (1989).** *Engineering Rock Mass Classifications*. Wiley, New York.",
        'ref6': "**Salmi, E. F., & Karakus, M. (2019).** Numerical analysis of pillar failure in underground coal mines. *Int. J. Rock Mech. Min. Sci.*, 120, 55–67.",
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
        'app_title': "UCG Термо-Механический 3-D Мониторинг",
        'app_subtitle': "Подземная газификация угля – Геомеханический анализ устойчивости",
        'sidebar_header_params': "⚙️ Общие параметры",
        'formula_show': "Показать формулы:",
        'project_name': "Название проекта:",
        'process_time': "Время процесса (часы):",
        'num_layers': "Количество слоёв:",
        'tensile_model': "Модель растяжения:",
        'rock_props': "💎 Свойства породы",
        'disturbance': "Фактор нарушения (D):",
        'poisson': "Коэффициент Пуассона (ν):",
        'stress_ratio': "Коэффициент напряжений (k):",
        'tensile_params': "📐 Растяжение и целик",
        'tensile_ratio': "Отношение растяжения (σt0/UCS):",
        'thermal_decay': "Термическое затухание β (1/°C):",
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
        'fos_subplot': "FOS + прогноз обрушения ИИ + зоны текучести",
        'gas_flow': "Поток газа",
        'shear': "Сдвиг",
        'tensile': "Растяжение",
        'ai_collapse': "Обрушение по ИИ",
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
        'advanced_analysis': "🔍 Углубленный анализ и методологическое обоснование",
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
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*, 10(3), 445–463.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification Cavities*. PhD Thesis, TU Delft.",
        'ref3': "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*, 78, 216–226.",
        'ref4': "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*, 131, 409–417.",
        'ref5': "**Bieniawski, Z. T. (1989).** *Engineering Rock Mass Classifications*. Wiley, New York.",
        'ref6': "**Salmi, E. F., & Karakus, M. (2019).** Numerical analysis of pillar failure. *Int. J. Rock Mech. Min. Sci.*, 120, 55–67.",
        'conclusion_danger': "🔴 **Научное заключение:** FOS={fos:.2f}. Высокая термическая деградация. Увеличить ширину целика или снизить скорость газификации.",
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


def t(key: str, **kwargs) -> str:
    """Tarjima funksiyasi — xavfsiz kalit qidirish."""
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    try:
        return text.format(**kwargs) if kwargs else text
    except (KeyError, IndexError):
        return text


EPS = 1e-12

st.set_page_config(page_title="UCG TM 3D Monitoring", layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

if 'language' not in st.session_state:
    st.session_state.language = 'uz'

LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox(
    "Til / Language / Язык",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    index=list(LANGUAGES.keys()).index(st.session_state.language)
)
st.session_state.language = lang

# QR kod
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
_URL_APP = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/"


@st.cache_data
def generate_qr(link: str) -> bytes:
    """QR kod yaratish."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


qr_img_bytes = generate_qr(_URL_APP)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG App", use_container_width=True)

# Matematik metodologiya
st.sidebar.header(t('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(t('formula_show'), formula_opts)
if formula_option != formula_opts[0]:
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == formula_opts[1]:
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.latex(r"m_b = m_i \exp\left(\frac{GSI-100}{28-14D}\right);\quad s = \exp\left(\frac{GSI-100}{9-3D}\right)")
            st.latex(r"a = \frac{1}{2} + \frac{1}{6} \left( e^{-GSI/15} - e^{-20/3} \right)")
            st.info("**Hoek-Brown:** GSI va Disturbance (D) faktorlari asosida massiv mustahkamligini hisoblash.")
        elif formula_option == formula_opts[2]:
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
            st.latex(r"\sigma_{ci(T)} = \sigma_{ci} \cdot (1 - D(T))")
            st.latex(r"k = k_0 \left[ 1 + 20 \cdot D(T) + 50 \cdot V_{void} \right]")
            st.info("**Termal degradatsiya:** Harorat ta'sirida jins strukturasining emirilishi va o'tkazuvchanlik ortishi.")
        elif formula_option == formula_opts[3]:
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu}")
            st.latex(r"\sigma_{t(T)} = \sigma_{t0} \cdot \exp\left(-\beta (T - 20)\right)")
            st.latex(r"FOS = \frac{\sigma_{limit}}{\sigma_{actual}}")
            st.info("**Termo-mexanika:** Termal kengayish kuchlanishi va cho'zilish mustahkamligining kamayishi.")
        elif formula_option == formula_opts[4]:
            st.latex(r"\sigma_{p} = UCS \cdot \left( \frac{w}{H} \right)^{0.5}")
            st.latex(r"y = \frac{H}{2} \left( \sqrt{\frac{\sigma_v}{\sigma_p}} - 1 \right)")
            st.latex(r"S(x) = S_{max} \cdot \exp\left( -\frac{x^2}{2i^2} \right)")
            st.info("**Geomexanika:** Selek barqarorligi, plastik zona va yer yuzasining deformatsiyasi.")

# Sidebar parametrlar
obj_name     = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h       = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers   = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode = st.sidebar.selectbox(
    t('tensile_model'),
    [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')]
)

st.sidebar.subheader(t('rock_props'))
D_factor   = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio    = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)

st.sidebar.subheader(t('tensile_params'))
tensile_ratio = st.sidebar.slider(t('tensile_ratio'), 0.03, 0.15, 0.08)
# BUG FIX (1): beta_thermal must be strictly positive; min_value=0.0005
beta_thermal = st.sidebar.number_input(
    t('thermal_decay'), value=0.0035, min_value=0.0005, max_value=0.05, format="%.4f"
)

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40, min_value=1)
T_source_max  = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

# Qatlam ma'lumotlari
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data: list = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i + 1), expanded=(i == int(num_layers) - 1)):
        name  = st.text_input(t('layer_name'), value=f"Qatlam-{i + 1}", key=f"name_{i}")
        thick = st.number_input(t('thickness'), value=50.0, min_value=0.1, key=f"t_{i}")
        u     = st.number_input(t('ucs'), value=40.0, min_value=0.1, key=f"u_{i}")
        rho   = st.number_input(t('density'), value=2500.0, min_value=100.0, key=f"rho_{i}")
        color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
        g     = st.slider(t('gsi'), 10, 100, 60, key=f"g_{i}")
        m     = st.number_input(t('mi'), value=10.0, min_value=0.1, key=f"m_{i}")
        s_t0_val = (
            st.number_input(t('manual_st0'), value=3.0, key=f"st_{i}")
            if tensile_mode == t('tensile_manual') else 0.0
        )
    layers_data.append({
        'name': name, 't': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

# Validatsiya
errors = []
for lyr in layers_data:
    if lyr['t'] <= 0:            errors.append(t('error_thick_positive'))
    if lyr['ucs'] <= 0:          errors.append(t('error_ucs_positive'))
    if lyr['rho'] <= 0:          errors.append(t('error_density_positive'))
    if not (10 <= lyr['gsi'] <= 100): errors.append(t('error_gsi_range'))
    if lyr['mi'] <= 0:           errors.append(t('error_mi_positive'))
if not layers_data:
    errors.append(t('error_min_layers'))
if errors:
    for e in errors:
        st.error(e)
    st.stop()

# ============================================================
# OOP SINFLARI (TUZATILGAN)
# ============================================================

class ThermalModel:
    """Harorat maydonini hisoblash sinfi."""

    def __init__(self, alpha: float = 1.0e-6):
        """
        Parameters
        ----------
        alpha : float
            Issiqlik diffuzivligi (m²/s).
        """
        self.alpha = alpha

    def temperature_field(
        self,
        grid_x: np.ndarray,
        grid_z: np.ndarray,
        source: tuple,
        elapsed_s: float,
        T_bg: float = 25.0,
    ) -> np.ndarray:
        """
        Nüqtaviy manbadan Gaussian harorat maydoni.

        Parameters
        ----------
        source : tuple
            (x0, z0, T_max) – manbaning koordinatasi va maksimal harorat.
        elapsed_s : float
            O'tgan vaqt (soniya).
        """
        x0, z0, T_max = source
        r2 = (grid_x - x0) ** 2 + (grid_z - z0) ** 2
        sigma2 = 4.0 * self.alpha * elapsed_s + 1.0
        return T_bg + (T_max - T_bg) * np.exp(-r2 / sigma2)


class HoekBrown:
    """Hoek-Brown geomexanik model (2018)."""

    def __init__(self, mi: float, gsi: float, D: float):
        self.mi = mi
        self.gsi = gsi
        self.D = D

    def parameters(self) -> tuple:
        """mb, s, a parametrlarini qaytaradi."""
        mb = self.mi * np.exp((self.gsi - 100) / (28.0 - 14.0 * self.D))
        s  = np.exp((self.gsi - 100) / (9.0 - 3.0 * self.D))
        a  = 0.5 + (1.0 / 6.0) * (np.exp(-self.gsi / 15.0) - np.exp(-20.0 / 3.0))
        return mb, s, a

    def sigma1(self, sigma3: np.ndarray, sigma_ci: np.ndarray) -> np.ndarray:
        """
        Hoek-Brown mezoniga ko'ra σ₁ limitini hisoblaydi.

        Parameters
        ----------
        sigma3 : np.ndarray
            Kichik asosiy kuchlanish (MPa) – array qabul qiladi.
        sigma_ci : np.ndarray
            Termal kamaytirilgan mustahkamlik (MPa) – array qabul qiladi.
        """
        mb, s, a = self.parameters()
        sigma3_safe = np.clip(np.asarray(sigma3, dtype=float), 1e-6, None)
        sigma_ci_safe = np.clip(np.asarray(sigma_ci, dtype=float), 1e-6, None)
        term = mb * sigma3_safe / (sigma_ci_safe + EPS) + s
        term = np.clip(term, 1e-9, 1e9)
        return sigma3_safe + sigma_ci_safe * (term ** a)


class ThermalDamage:
    """Termal shikastlanish modeli (Shao et al., 2015)."""

    def __init__(self, beta: float = 0.003):
        """
        Parameters
        ----------
        beta : float
            Termal shikastlanish koeffitsiyenti (1/°C). >0 bo'lishi shart.
        """
        self.beta = max(beta, 1e-6)

    def compute(self, T: np.ndarray, T0: float = 20.0) -> np.ndarray:
        """
        D(T) = 1 - exp(-β*(T - T₀)), faqat T > T₀ uchun.

        Returns
        -------
        np.ndarray
            Shikastlanish faktori [0, 1].
        """
        return 1.0 - np.exp(-self.beta * np.maximum(T - T0, 0.0))


class ThermoMechanicalModel:
    """
    Termo-Mexanik model: termal kuchlanish va shikastlanish birlashgan hisob.
    """

    def __init__(
        self,
        E_modulus: float = 5000.0,
        alpha_th: float = 1.0e-5,
        nu: float = 0.25,
        beta: float = 0.003,
    ):
        """
        Parameters
        ----------
        E_modulus : float
            Elastiklik moduli (MPa).
        alpha_th : float
            Termal kengayish koeffitsiyenti (1/°C).
        nu : float
            Poisson koeffitsiyenti.
        beta : float
            Termal shikastlanish koeffitsiyenti (1/°C).
        """
        self.E = E_modulus
        self.alpha = alpha_th
        self.nu = nu
        self.damage_model = ThermalDamage(beta)

    def compute_stress(
        self, delta_T: np.ndarray, constraint: float = 0.7
    ) -> np.ndarray:
        """
        Termal kuchlanishni hisoblaydi (MPa).

        σ_th = constraint * E * α * ΔT / (1 - ν)
        """
        return constraint * self.E * self.alpha * delta_T / (1.0 - self.nu + EPS)

    def compute_damage(self, T: np.ndarray) -> np.ndarray:
        """Termal shikastlanish faktorini hisoblaydi."""
        return self.damage_model.compute(T)

    def reduced_ucs(self, ucs0: np.ndarray, T: np.ndarray) -> np.ndarray:
        """
        Harorat ta'sirida kamaygan mustahkamlik.

        σ_ci(T) = σ_ci0 * (1 - D(T))
        """
        D = self.compute_damage(T)
        return ucs0 * (1.0 - D)


# BUG FIX (2): PINN ni kollapsa bashorat modeli sifatida integratsiya qilamiz
class PINN(nn.Module if PT_AVAILABLE else object):
    """
    Physics-Informed Neural Network – UCG kollapsa bashorat modeli.

    Kirish: 7 o'zgaruvchi (T, σ1, σ3, depth, D, FOS, energy)
    Chiqish: kollapsa ehtimoli [0, 1]
    """

    def __init__(self):
        if not PT_AVAILABLE:
            return
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(7, 128), nn.ReLU(), nn.BatchNorm1d(128),
            nn.Linear(128, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, 1), nn.Sigmoid()
        )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)


class DigitalTwin:
    """UCG Digital Twin – real vaqt simulyatsiya."""

    def __init__(
        self,
        thermal: ThermalModel,
        mechanics: HoekBrown,
        damage: ThermalDamage,
        model,
    ):
        self.thermal = thermal
        self.mechanics = mechanics
        self.damage = damage
        self.model = model
        self.sensor: dict = {}

    def update(self, sensor_data: dict):
        """Sensor ma'lumotlarini yangilaydi."""
        self.sensor = sensor_data

    def simulate(
        self, grid_x: np.ndarray, grid_z: np.ndarray, elapsed_s: float
    ) -> tuple:
        """
        Harorat maydoni va Hoek-Brown σ₁ limitini hisoblaydi.

        Returns
        -------
        tuple
            (T: np.ndarray, sigma1_limit: np.ndarray) – ikkisi ham grid shaklidagi array.
        """
        T = self.thermal.temperature_field(
            grid_x, grid_z, self.sensor['source'], elapsed_s
        )
        D = self.damage.compute(T)
        # BUG FIX (3): sigma3 va sigma_ci array sifatida uzatiladi
        sigma3_arr = np.full_like(T, float(self.sensor.get('sigma3', 1.0)))
        ucs_val = float(self.sensor.get('ucs', 40.0))
        sigma_ci_arr = ucs_val * (1.0 - D)
        sigma1_limit = self.mechanics.sigma1(sigma3_arr, sigma_ci_arr)
        return T, sigma1_limit

    def predict_collapse(self, features: "torch.Tensor") -> "torch.Tensor":
        """PINN modeli orqali kollapsa bashorat."""
        if self.model is None:
            return None
        return self.model(features)


# =========================== FIZIK FUNKSIYALAR ===========================

def thermal_damage_fn(T: np.ndarray, beta: float = 0.002) -> np.ndarray:
    """
    Termal shikastlanish faktori: D(T) = 1 - exp(-β*(T - 100)), T > 100°C uchun.

    Parameters
    ----------
    T : np.ndarray
        Harorat (°C).
    beta : float
        Shikastlanish tezligi (1/°C).

    Returns
    -------
    np.ndarray
        D ∈ [0, 1].
    """
    return 1.0 - np.exp(-beta * np.maximum(T - 100.0, 0.0))


def vertical_stress(depth: float, density: float) -> float:
    """
    Geostatik vertikal kuchlanish (MPa).

    σ_v = ρ * g * H / 1e6
    """
    return density * 9.81 * depth / 1.0e6


# =========================== FDM (TO'G'RI LAPLACIAN) ===========================

def laplacian(T: np.ndarray, dx: float, dz: float) -> np.ndarray:
    """
    Ikkinchi tartibli sonli Laplacian.

    ∇²T ≈ (T[i+1,j] - 2T[i,j] + T[i-1,j])/dz² + (T[i,j+1] - 2T[i,j] + T[i,j-1])/dx²
    """
    return (
        (T[2:, 1:-1] - 2.0 * T[1:-1, 1:-1] + T[:-2, 1:-1]) / dz ** 2 +
        (T[1:-1, 2:] - 2.0 * T[1:-1, 1:-1] + T[1:-1, :-2]) / dx ** 2
    )


def step_temperature(
    T: np.ndarray, alpha_rock: float, dt: float, dx: float, dz: float
) -> np.ndarray:
    """
    Bir vaqt qadamida haroratni yangilash (explicit FDM).

    Courant sharti: dt <= dx²*dz²/(2*alpha*(dx²+dz²))
    """
    # Courant shartini tekshirish
    dt_max = 0.5 * dx ** 2 * dz ** 2 / (alpha_rock * (dx ** 2 + dz ** 2) + EPS)
    if dt > dt_max:
        n_sub = int(np.ceil(dt / dt_max))
        dt_sub = dt / n_sub
        Tn = T.copy()
        for _ in range(n_sub):
            Tn[1:-1, 1:-1] += alpha_rock * dt_sub * laplacian(Tn, dx, dz)
        return Tn
    Tn = T.copy()
    Tn[1:-1, 1:-1] += alpha_rock * dt * laplacian(T, dx, dz)
    return Tn


# =========================== HARORAT MAYDONINI HISOBLASH ===========================

@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field_moving(
    time_h: float,
    T_source_max: float,
    burn_duration: float,
    total_depth: float,
    source_z: float,
    grid_shape: tuple,
    n_steps: int = 20,
) -> tuple:
    """
    Ko'chuvchi Gaussian-FDM gibrid usulida harorat maydoni.

    Patent da'vosi 1: Ko'chuvchi manbali harorat modeli.
    """
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
    z_axis = np.linspace(0, total_depth + 50.0, grid_shape[0])
    dx = x_axis[1] - x_axis[0]
    dz = z_axis[1] - z_axis[0]
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)

    alpha_rock = 1.0e-6  # m²/s
    v_burn = 0.02        # m/s – yonish fronti tezligi

    sources = [
        {'x0': -total_depth / 3.0, 'start': 0,  'moving': False},
        {'x0': 0.0,                 'start': 40, 'moving': True, 'v': v_burn},
        {'x0':  total_depth / 3.0, 'start': 80, 'moving': False},
    ]

    temp_2d = np.full_like(grid_x, 25.0)

    for src in sources:
        if time_h <= src['start']:
            continue
        dt_sec = (time_h - src['start']) * 3600.0
        x_center = src['x0'] + src.get('v', 0.0) * dt_sec if src['moving'] else src['x0']
        pen_depth = np.sqrt(4.0 * alpha_rock * dt_sec)
        elapsed = time_h - src['start']
        if elapsed <= burn_duration:
            curr_T = T_source_max
        else:
            curr_T = 25.0 + (T_source_max - 25.0) * np.exp(-0.03 * (elapsed - burn_duration))
        dist_sq = (grid_x - x_center) ** 2 + (grid_z - source_z) ** 2
        temp_2d += (curr_T - 25.0) * np.exp(-dist_sq / (pen_depth ** 2 + 15.0 ** 2))

    # FDM diffuziya (Courant shartli)
    dt_fdm = (burn_duration * 3600.0) / n_steps
    for _ in range(n_steps):
        temp_2d = step_temperature(temp_2d, alpha_rock, dt_fdm, dx, dz)

    temp_2d = np.clip(temp_2d, 20.0, T_source_max + 50.0)
    return temp_2d, x_axis, z_axis, grid_x, grid_z


grid_shape = (80, 100)
source_z = total_depth - (layers_data[-1]['t'] / 2.0)
H_seam   = layers_data[-1]['t']

temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20
)

# Geomexanik hisob
grid_sigma_v          = np.zeros_like(grid_z)
grid_ucs              = np.zeros_like(grid_z)
grid_mb               = np.zeros_like(grid_z)
grid_s_hb             = np.zeros_like(grid_z)
grid_a_hb             = np.zeros_like(grid_z)
grid_sigma_t0_manual  = np.zeros_like(grid_z)

layer_bounds = [(l['z_start'], l['z_start'] + l['t']) for l in layers_data]
for i, (z0, z1) in enumerate(layer_bounds):
    mask = (grid_z >= z0) & (
        (grid_z < z1) if i < len(layer_bounds) - 1 else np.ones_like(grid_z, dtype=bool)
    )
    layer = layers_data[i]
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1.0e6
    depth_local = grid_z[mask] - z0
    grid_sigma_v[mask]  = overburden + (layer['rho'] * 9.81 * depth_local) / 1.0e6
    grid_ucs[mask]      = layer['ucs']
    exp_gsi = layer['gsi'] - 100
    grid_mb[mask]       = layer['mi'] * np.exp(exp_gsi / (28.0 - 14.0 * D_factor))
    grid_s_hb[mask]     = np.exp(exp_gsi / (9.0 - 3.0 * D_factor))
    grid_a_hb[mask]     = 0.5 + (1.0 / 6.0) * (
        np.exp(-layer['gsi'] / 15.0) - np.exp(-20.0 / 3.0)
    )
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

# Sessiya holati – maksimal harorat xaritasi
if ('max_temp_map' not in st.session_state
        or st.session_state.max_temp_map.shape != grid_z.shape):
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25.0
    st.session_state.last_obj_name = obj_name
elif st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25.0
    st.session_state.last_obj_name = obj_name
st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)

delta_T = temp_2d - 25.0

# Termal shikastlanish va kuchlanish
damage   = thermal_damage_fn(st.session_state.max_temp_map, beta=beta_thermal)
sigma_ci = grid_ucs * (1.0 - damage)

E_MODULUS       = 5000.0   # MPa
ALPHA_T_COEFF   = 1.0e-5   # 1/°C
CONSTRAINT_FACTOR = 0.7

sigma_thermal = CONSTRAINT_FACTOR * E_MODULUS * ALPHA_T_COEFF * delta_T / (1.0 - nu_poisson + EPS)
sigma_thermal = np.clip(sigma_thermal, 0.0, sigma_ci * 0.3)

grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act   = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act   = np.minimum(grid_sigma_v, grid_sigma_h)

# Tensil mustahkamlik
if tensile_mode == t('tensile_empirical'):
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == t('tensile_hb'):
    # HB tensil mustahkamlik: σ_t = σ_ci * s / (m_b + sqrt(m_b² + 4s))
    # Soddalashtirilgan: σ_t = σ_ci * s / (1 + m_b)
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1.0 + grid_mb + EPS)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field     = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20.0))
thermal_boost     = 1.0 + 0.6 * (1.0 - np.exp(-delta_T / 200.0))
sigma_t_field_eff = sigma_t_field / (thermal_boost + EPS)
tensile_failure   = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50.0) & (sigma1_act > sigma3_act)


def hoek_brown_sigma1(
    sigma3: np.ndarray, sigma_ci: np.ndarray,
    mb: np.ndarray, s: np.ndarray, a: np.ndarray
) -> np.ndarray:
    """
    Hoek-Brown σ₁_limit:  σ₁ = σ₃ + σ_ci*(m_b*σ₃/σ_ci + s)^a

    Barcha massivlar bir xil shaklda bo'lishi kerak.
    """
    sigma3_safe  = np.clip(sigma3,  1.0e-6, None)
    sigma_ci_safe = np.clip(sigma_ci, 1.0e-6, None)
    term = mb * sigma3_safe / (sigma_ci_safe + EPS) + s
    term = np.clip(term, 1.0e-9, 1.0e9)
    return sigma3_safe + sigma_ci_safe * (term ** a)


sigma1_limit  = hoek_brown_sigma1(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)
shear_failure = sigma1_act >= sigma1_limit

# BUG FIX (4): Deformatsiya energiyasi – to'g'ri o'lchovli formula (MPa²)
# W = σ₁² / (2E)  – elastik deformatsiya energiyasi zichligi
strain_energy = sigma1_act ** 2 / (2.0 * E_MODULUS + EPS)  # MPa²/MPa = MPa

spalling  = tensile_failure & (temp_2d > 400.0)
crushing  = shear_failure   & (temp_2d > 600.0)

depth_factor    = np.exp(-grid_z / (total_depth + EPS))
local_collapse_T = np.clip((st.session_state.max_temp_map - 600.0) / 300.0, 0.0, 1.0)
time_factor     = np.clip((time_h - 40.0) / 60.0, 0.0, 1.0)
collapse_final  = local_collapse_T * time_factor * (1.0 - depth_factor)

# BUG FIX (5): strain_energy chegarasi – endi MPa birligida (taxminan σ>100 MPa)
void_mask_raw     = spalling | crushing | (st.session_state.max_temp_map > 900.0) | (strain_energy > 100.0)
void_mask_smooth  = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth > 0.3) & (collapse_final > 0.05)

phi         = 0.05 + 0.4 * void_mask_permanent.astype(float)
perm        = (phi ** 3) / ((1.0 - phi + EPS) ** 2) * 1.0e-12
void_volume = (
    np.sum(void_mask_permanent)
    * (x_axis[1] - x_axis[0])
    * (z_axis[1] - z_axis[0])
)
void_factor = np.where(void_mask_permanent, 0.1, 1.0)
sigma1_act = sigma1_act * void_factor
sigma3_act = sigma3_act * void_factor
sigma_ci   = sigma_ci   * void_factor

pressure = temp_2d * 10.0
dp_dx    = np.gradient(pressure, axis=1)
dp_dz    = np.gradient(pressure, axis=0)
vx       = -perm * dp_dx
vz       = -perm * dp_dz
gas_velocity = np.sqrt(vx ** 2 + vz ** 2)

# =========================== AI MODEL FUNKSIYALARI ===========================

def physics_features(
    T: np.ndarray, s1: np.ndarray, s3: np.ndarray, depth: np.ndarray
) -> np.ndarray:
    """
    7 ta fizik xususiyat matritsasi.

    Columns: [T, σ₁, σ₃, depth, D, FOS_approx, energy_density]
    """
    dmg      = thermal_damage_fn(T)
    strength = 40.0 * (1.0 - dmg)            # taxminiy UCS qiymat (MPa)
    fos      = strength / (s1 + EPS)
    # BUG FIX (6): energy_density = σ₁²/(2E) emas, balki normallanmagan indeks
    energy   = T * s1 / (depth + 1.0)
    return np.column_stack([T, s1, s3, depth, dmg, fos, energy])


def generate_physics_dataset(
    temp_field: np.ndarray,
    sigma1: np.ndarray,
    sigma3: np.ndarray,
    depth: np.ndarray,
) -> tuple:
    """O'quv ma'lumotlar to'plamini yaratadi."""
    feat     = physics_features(
        temp_field.flatten(), sigma1.flatten(), sigma3.flatten(), depth.flatten()
    )
    fos      = feat[:, 5]
    energy   = feat[:, 6]
    collapse = (
        (fos < 1.0) | (temp_field.flatten() > 800.0) | (energy > 4000.0)
    ).astype(int)
    return feat, collapse


class CollapseNet(nn.Module if PT_AVAILABLE else object):
    """Kichik kollapsa klassifikator."""

    def __init__(self):
        if not PT_AVAILABLE:
            return
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(7, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1), nn.Sigmoid()
        )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)


class HybridCollapseNet(nn.Module if PT_AVAILABLE else object):
    """Gibrid NN + fizik jarimali model."""

    def __init__(self):
        if not PT_AVAILABLE:
            return
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(7, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, 1), nn.Sigmoid()
        )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)


def physics_loss(
    pred: "torch.Tensor",
    sigma1: "torch.Tensor",
    sigma_ci: "torch.Tensor",
) -> "torch.Tensor":
    """
    Fizik jarima funksiyasi.

    BUG FIX (7): (1 - FOS) salbiy bo'lganda jarima nolga o'rnatiladi.
    """
    fos     = sigma_ci / (sigma1 + 1.0e-6)
    penalty = torch.mean(torch.clamp(1.0 - fos, min=0.0) * pred)
    return penalty


def train_hybrid_model(
    X: np.ndarray, y: np.ndarray,
    sigma1: np.ndarray, sigma_ci: np.ndarray,
) -> "nn.Module":
    """HybridCollapseNet o'qitish (BCE + fizik jarima)."""
    model    = HybridCollapseNet().to(device)
    X_t      = torch.tensor(X,      dtype=torch.float32).to(device)
    y_t      = torch.tensor(y,      dtype=torch.float32).view(-1, 1).to(device)
    sigma1_t = torch.tensor(sigma1, dtype=torch.float32).to(device)
    sigma_ci_t = torch.tensor(sigma_ci, dtype=torch.float32).to(device)
    opt      = torch.optim.Adam(model.parameters(), lr=3.0e-4)
    for _ in range(80):
        pred = model(X_t)
        bce  = nn.BCELoss()(pred, y_t)
        phys = physics_loss(pred, sigma1_t, sigma_ci_t)
        loss = bce + 0.4 * phys
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model


def train_random_forest(X_scaled: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    """RandomForest o'qitish."""
    rf = RandomForestClassifier(
        n_estimators=50, max_depth=12, random_state=42, n_jobs=-1
    )
    rf.fit(X_scaled, y)
    return rf


# BUG FIX (8): get_ensemble_model – hashable parametrlar bilan chaqiriladi
@st.cache_resource
def get_ensemble_model(
    n_samples: int, grid_shape: tuple, seed_sigma: float, seed_T: float
) -> tuple:
    """
    Ensemble modelni sintetik ma'lumotlar asosida o'qitadi.

    Numpy array emas, hashable skalyar/kortej argument ishlatiladi –
    @st.cache_resource bilan muvofiqlashadi.
    """
    rng     = np.random.default_rng(42)
    T_s     = rng.uniform(20.0, 1000.0, n_samples)
    s1_s    = rng.uniform(0.5,  50.0,   n_samples)
    s3_s    = rng.uniform(0.1,  10.0,   n_samples)
    dep_s   = rng.uniform(50.0, 400.0,  n_samples)
    X_ai_s  = physics_features(T_s, s1_s, s3_s, dep_s)
    fos_s   = X_ai_s[:, 5]
    y_ai_s  = ((fos_s < 1.0) | (T_s > 800.0)).astype(int)

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X_ai_s)

    if PT_AVAILABLE:
        model = train_hybrid_model(X_scaled, y_ai_s, s1_s, T_s * 0.04)
        rf    = train_random_forest(X_scaled, y_ai_s)
        return model, rf, scaler
    else:
        rf = train_random_forest(X_scaled, y_ai_s)
        return None, rf, scaler


# Hashable parametrlar orqali chaqiruv
_n_ai_samples = int(grid_shape[0] * grid_shape[1])
hybrid_model, rf_model, scaler = get_ensemble_model(
    n_samples  = _n_ai_samples,
    grid_shape = grid_shape,
    seed_sigma = round(float(np.mean(sigma1_act)), 4),
    seed_T     = round(float(T_source_max), 1),
)

X_ai, y_ai = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z)


def predict_collapse(
    model, rf, scaler: StandardScaler, X_raw: np.ndarray
) -> np.ndarray:
    """
    Agregatlangan bashorat: 0.6 * NN + 0.4 * RF (yoki faqat RF).

    Patent da'vosi 3: HybridCollapseNet + RF ensemble.
    """
    if model is None and rf is None:
        return np.zeros((X_raw.shape[0], 1))
    X_scaled = scaler.transform(X_raw)
    if model is not None and rf is not None:
        X_t    = torch.tensor(X_scaled, dtype=torch.float32).to(device)
        with torch.no_grad():
            nn_pred = model(X_t).cpu().numpy()
        rf_pred = rf.predict_proba(X_scaled)[:, 1:2]
        return 0.6 * nn_pred + 0.4 * rf_pred
    if model is not None:
        X_t = torch.tensor(X_scaled, dtype=torch.float32).to(device)
        with torch.no_grad():
            return model(X_t).cpu().numpy()
    return rf.predict_proba(X_scaled)[:, 1:2]


collapse_pred = predict_collapse(hybrid_model, rf_model, scaler, X_ai).reshape(grid_z.shape)

# =========================== FOS 2D ===========================

def fos_2d_compute(
    sigma1: np.ndarray, sigma_ci_arr: np.ndarray,
    mb: np.ndarray, s: np.ndarray, a: np.ndarray,
    sigma3: np.ndarray,
) -> np.ndarray:
    """
    2-o'lchovli FOS maydoni: FOS = σ₁_limit / σ₁_actual

    Patent da'vosi 2: TM-FOS kompozit risk indeksi.
    """
    limit = hoek_brown_sigma1(sigma3, sigma_ci_arr, mb, s, a)
    fos   = np.where(sigma1 > EPS, limit / (sigma1 + EPS), 3.0)
    return np.clip(fos, 0.0, 3.0)


fos_2d = fos_2d_compute(sigma1_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb, sigma3_act)

# Xavf xaritasi
risk_map = (
    0.35 * collapse_pred
    + 0.30 * np.clip(1.0 - fos_2d, 0.0, 1.0)       # BUG FIX (9): clamp [0,1]
    + 0.20 * (perm / (np.max(perm) + EPS))
    + 0.15 * (temp_2d / (np.max(temp_2d) + EPS))
)
risk_map = np.clip(risk_map, 0.0, 1.0)

# =========================== MONITORING PANELI ===========================

st.header(t('monitoring_header', obj_name=obj_name))

# Selek hisob (Wilson 1972)
ucs_seam    = layers_data[-1]['ucs']
H_seam_val  = layers_data[-1]['t']
sv_seam     = vertical_stress(total_depth - H_seam_val / 2.0, layers_data[-1]['rho'])

strength_red = np.exp(-beta_thermal * (T_source_max - 20.0))
ucs_reduced  = ucs_seam * strength_red


@st.cache_data
def optimize_pillar_width(
    ucs_red: float, sv: float, H: float, min_w: float = 10.0, max_w: float = 200.0
) -> float:
    """
    AI optimallashtirish: FOS >= 1.5 bo'lgan eng kichik selek enini topadi.

    Patent da'vosi 4: Termal-iterativ selek optimizatsiyasi.
    """
    def neg_fos(w: list) -> float:
        sigma_p = ucs_red * (w[0] / (H + EPS)) ** 0.5
        return -(sigma_p / (sv + EPS))

    w0     = (min_w + max_w) / 2.0
    bounds = [(min_w, max_w)]
    res    = minimize(neg_fos, [w0], method='L-BFGS-B', bounds=bounds)
    return float(np.clip(res.x[0], min_w, max_w))


rec_width = optimize_pillar_width(ucs_reduced, sv_seam, H_seam_val)

pillar_strength = ucs_reduced * (rec_width / (H_seam_val + EPS)) ** 0.5
fos_pillar      = pillar_strength / (sv_seam + EPS)

# Plastik zona (Wilson 1972)
y_zone = (H_seam_val / 2.0) * max(
    0.0, np.sqrt(sv_seam / (pillar_strength + EPS)) - 1.0
)

# Hoek-Brown nisbati (to'g'ri: √s * 100%)
s_seam   = np.exp((layers_data[-1]['gsi'] - 100.0) / (9.0 - 3.0 * D_factor))
a_seam   = 0.5 + (1.0 / 6.0) * (
    np.exp(-layers_data[-1]['gsi'] / 15.0) - np.exp(-20.0 / 3.0)
)
hb_ratio = np.sqrt(s_seam) * 100.0   # % – BUG FIX (10): to'g'ri formula

# Cho'kish (Gaussian tavsifnomasi)
i_val  = 0.5 * total_depth
s_max  = 0.45 * rec_width * 0.8
sub_p  = s_max * np.exp(-(x_axis ** 2) / (2.0 * i_val ** 2))
avg_t_p = T_source_max * 0.85

# Metrikalar qatori
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric(
    t('pillar_strength'),
    f"{pillar_strength:.1f} MPa",
    f"FOS={fos_pillar:.2f}"
)
col_m2.metric(
    t('plastic_zone'),
    f"{y_zone:.1f} m",
    f"HB ratio={hb_ratio:.1f}%"
)
col_m3.metric(
    t('cavity_volume'),
    f"{void_volume:.0f} m²"
)
col_m4.metric(
    t('max_permeability'),
    f"{np.max(perm):.2e} m²"
)
col_m5.metric(
    t('ai_recommendation'),
    f"{rec_width:.1f} m",
    delta=("✅ Barqaror" if fos_pillar >= 1.5 else "⚠️ Xavfli"),
    delta_color=("normal" if fos_pillar >= 1.5 else "inverse")
)

# =========================== VIZUALIZATSIYALAR ===========================

st.subheader(t('tm_field_title'))
col_g1, col_g2, col_g3 = st.columns(3)

uplift = (
    (total_depth * 1.0e-4)
    * np.exp(-(x_axis ** 2) / (total_depth * 10.0))
    * (time_h / 150.0) * 100.0
)

with col_g1:
    st.plotly_chart(
        go.Figure(
            go.Scatter(x=x_axis, y=sub_p * 100.0, fill='tozeroy',
                       line=dict(color='magenta', width=3))
        ).update_layout(
            title=t('subsidence_title'), template="plotly_dark", height=300
        ),
        use_container_width=True
    )
with col_g2:
    st.plotly_chart(
        go.Figure(
            go.Scatter(x=x_axis, y=uplift, fill='tozeroy',
                       line=dict(color='cyan', width=3))
        ).update_layout(
            title=t('thermal_deform_title'), template="plotly_dark", height=300
        ),
        use_container_width=True
    )
with col_g3:
    sigma3_ax = np.linspace(0.0, ucs_seam * 0.5, 100)
    mb_s = grid_mb.max(); s_s = grid_s_hb.max(); a_s = grid_a_hb.max()
    s1_20     = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + EPS) + s_s) ** a_s
    ucs_burn  = ucs_seam * np.exp(-beta_thermal * (T_source_max - 20.0))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + EPS) + s_s) ** a_s
    s1_sov    = sigma3_ax + (ucs_seam * strength_red) * (
        mb_s * sigma3_ax / (ucs_seam * strength_red + EPS) + s_s
    ) ** a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C',
                                line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name=t('tensile_hb'),
                                line=dict(color='cyan', width=2, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name=t('combustion'),
                                line=dict(color='orange', width=4)))
    st.plotly_chart(
        fig_hb.update_layout(
            title=t('hb_envelopes_title'), template="plotly_dark", height=300,
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
        ),
        use_container_width=True
    )

# Qatlam kesimi va quduqlar
st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(
            go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'],
                   marker_color=lyr['color'], width=0.4)
        )
    st.plotly_chart(
        fig_layers.update_layout(
            barmode='stack', template="plotly_dark",
            yaxis=dict(autorange='reversed'), height=450, showlegend=False
        ),
        use_container_width=True
    )

st.sidebar.markdown("---")
st.sidebar.subheader("Quduqlar konfiguratsiyasi")
well_distance = st.sidebar.slider(
    "Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0, key="well_dist_slider"
)

with c2:
    st.subheader("UCG Yonish Bosqichlari (1 → 3 → 2 sxemasi) – Patent da'vosi 5")
    coal_layer   = layers_data[-1]
    h_seam       = coal_layer['t']
    ucs_coal_pa  = coal_layer['ucs'] * 1.0e6
    rho_coal     = coal_layer['rho']

    well_x        = [-well_distance, 0.0, well_distance]
    cavity_width  = max(well_distance - rec_width, 10.0)

    E_MOD  = 25.0e9   # Pa
    ALPHA  = 1.0e-5   # 1/°C
    NU     = nu_poisson
    K0     = NU / (1.0 - NU)

    layer_bounds_adv = [(l['z_start'], l['z_start'] + l['t'], l) for l in layers_data]

    # Geostatik vertikal kuchlanish
    sigma_v_coal = 0.0
    for l in layers_data[:-1]:
        sigma_v_coal += l['rho'] * 9.81 * l['t']
    sigma_v_coal += rho_coal * 9.81 * (h_seam / 2.0)
    sigma_v_coal_MPa = sigma_v_coal / 1.0e6

    Hc = h_seam * np.sqrt(sigma_v_coal_MPa / (coal_layer['ucs'] + EPS))
    Hc = np.clip(Hc, h_seam, h_seam * 4.0)

    states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
    stage = st.select_slider(
        "Bosqichni tanlang:", options=[1, 2, 3], value=1, key="ucg_stage_132"
    )
    active_wells = states_132[stage]

    def compute_advanced_fos(
        grid_x: np.ndarray, grid_z: np.ndarray,
        active_wells: list, well_x: list,
        source_z: float, h_seam: float, cavity_width: float,
        temp_field: np.ndarray, sigma_v_field: np.ndarray,
        layers_data: list, layer_bounds_adv: list,
        E: float, alpha: float, nu: float, K0: float,
        Hc: float, sigma_v_coal_MPa: float, ucs_coal_pa: float,
    ) -> np.ndarray:
        """
        Yer osti quduqlar uchun 2D FOS maydoni.

        Patent da'vosi 5: UCG 1→3→2 dinamik FOS algoritmi.
        """
        fos = np.full_like(grid_x, 3.0)

        for px_idx in active_wells:
            px   = well_x[px_idx]
            dist = np.sqrt((grid_x - px) ** 2 + (grid_z - source_z) ** 2)
            dz   = source_z - grid_z
            T    = temp_field
            delta_T_loc = np.maximum(T - 20.0, 0.0)
            thermal_zone = dist < (h_seam * 3.0)

            for (top, bot, layer) in layer_bounds_adv:
                mask = (grid_z >= top) & (grid_z < bot)
                if not np.any(mask):
                    continue
                ucs_pa = layer['ucs'] * 1.0e6   # Pa
                gsi    = layer['gsi']
                mi_l   = layer['mi']
                mb     = mi_l * np.exp((gsi - 100.0) / (28.0 - 14.0 * D_factor))
                s_hb   = np.exp((gsi - 100.0) / (9.0 - 3.0 * D_factor))
                a_hb   = 0.5 + (1.0 / 6.0) * (
                    np.exp(-gsi / 15.0) - np.exp(-20.0 / 3.0)
                )
                sigma_v_pa  = sigma_v_field[mask] * 1.0e6  # Pa
                delta_T_m   = delta_T_loc[mask]
                D_T         = 1.0 - np.exp(-beta_thermal * delta_T_m)
                sigma_ci_T  = ucs_pa * (1.0 - D_T)       # Pa
                sigma_3_pa  = K0 * sigma_v_pa * (0.6 + 0.4 * (1.0 - D_T))

                sigma_th_local = np.zeros_like(sigma_v_pa)
                local_thermal  = thermal_zone[mask]
                if np.any(local_thermal):
                    th_vals = (E * alpha * delta_T_m[local_thermal]) / (1.0 - nu)
                    sigma_th_local[local_thermal] = np.clip(
                        th_vals, 0.0, sigma_ci_T[local_thermal] * 0.25
                    )

                sigma_1_pa = sigma_v_pa + sigma_th_local
                term       = mb * sigma_3_pa / (sigma_ci_T + EPS) + s_hb
                term       = np.clip(term, 1.0e-9, 1.0e9)
                sigma_lim  = sigma_3_pa + sigma_ci_T * (term ** a_hb)

                # BUG FIX (11): fos denominator – sigma_1_pa + EPS (Pa), not +1e6
                fos_val    = np.clip(sigma_lim / (sigma_1_pa + EPS), 0.0, 3.0)

                yield_mask = sigma_1_pa > (sigma_lim * 0.85)
                fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)

                fos_sub = fos[mask]
                fos_sub = np.minimum(fos_sub, fos_val)
                fos[mask] = fos_sub

                if layer == layers_data[-1]:
                    dome_width   = (cavity_width / 2.0) * np.clip(
                        1.0 - dz[mask] / (Hc + EPS), 0.0, 1.0
                    )
                    failure_zone  = fos_val < 1.2
                    dome_cond     = (
                        (dz[mask] > 0.0) & (dz[mask] < Hc)
                        & (np.abs(grid_x[mask] - px) < dome_width)
                        & failure_zone
                    )
                    if np.any(dome_cond):
                        decay = np.clip(
                            1.0 - (dz[mask][dome_cond] / (Hc + EPS)), 0.3, 1.0
                        )
                        fos_sub[dome_cond] = np.minimum(fos_sub[dome_cond], decay)
                        fos[mask] = fos_sub

        # Kavern maydoni (FOS → ~0)
        for px_idx in active_wells:
            px = well_x[px_idx]
            a_ell = cavity_width / 2.0
            b_ell = h_seam / 2.0
            cavity_ellipse = (
                (grid_x - px) ** 2 / (a_ell ** 2 + EPS)
                + (grid_z - source_z) ** 2 / (b_ell ** 2 + EPS)
            ) < 1.0
            fos[cavity_ellipse] = 0.05

        bottom_boundary = layers_data[-1]['z_start'] + layers_data[-1]['t']
        fos[grid_z > bottom_boundary] = 2.5

        # Nofaol quduqlar – mustahkam selek
        all_wells = [0, 1, 2]
        for i_w in all_wells:
            if i_w not in active_wells:
                px = well_x[i_w]
                pillar_mask = (
                    (np.abs(grid_x - px) < h_seam * 1.5)
                    & (np.abs(grid_z - source_z) < h_seam * 1.2)
                )
                fos[pillar_mask] = 2.5

        # 2-bosqich: markaziy selek mustahkamligi
        if stage == 2:
            selek_eni      = well_distance - cavity_width
            pillar_str_loc = ucs_coal_pa * (selek_eni / (h_seam + EPS)) ** 0.5
            sigma_v_coal_pa_loc = sigma_v_coal_MPa * 1.0e6
            fos_pillar_loc  = pillar_str_loc / (sigma_v_coal_pa_loc + EPS)
            pillar_zone     = (
                (np.abs(grid_x - well_x[1]) < selek_eni / 2.0)
                & (np.abs(grid_z - source_z) < h_seam)
            )
            fos[pillar_zone] = np.maximum(fos[pillar_zone], fos_pillar_loc)

        fos = np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)
        return fos

    source_z_adv = total_depth - (h_seam / 2.0)
    fos_stage    = compute_advanced_fos(
        grid_x, grid_z, active_wells, well_x,
        source_z_adv, h_seam, cavity_width,
        temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
        E_MOD, ALPHA, NU, K0, Hc, sigma_v_coal_MPa, ucs_coal_pa
    )

    fig_tm = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=(t('temp_subplot'), "Geomexanik Holat (UCG 1→3→2 Algoritmi)")
    )
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
        colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42, thickness=15),
        name=t('temp_subplot')
    ), row=1, col=1)

    step = 12
    qx, qz = grid_x[::step, ::step].flatten(), grid_z[::step, ::step].flatten()
    qu, qw = vx[::step, ::step].flatten(),     vz[::step, ::step].flatten()
    qmag   = gas_velocity[::step, ::step].flatten()
    qmag_max = qmag.max() + EPS
    mask_q = qmag > qmag_max * 0.05
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q] + EPS))
    fig_tm.add_trace(go.Scatter(
        x=qx[mask_q], y=qz[mask_q], mode='markers',
        marker=dict(symbol='arrow', size=10, color=qmag[mask_q],
                    colorscale='ice', cmin=0, cmax=qmag_max,
                    angle=angles, opacity=0.85, showscale=False, line=dict(width=0)),
        name=t('gas_flow')
    ), row=1, col=1)

    fig_tm.add_trace(go.Contour(
        z=fos_stage, x=x_axis, y=z_axis,
        colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],
                    [0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
        zmin=0, zmax=3, contours_showlines=False,
        colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42, thickness=15),
        name="FOS"
    ), row=2, col=1)

    fracture_mask = np.where(fos_stage < 1.2, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=fracture_mask, x=x_axis, y=z_axis,
        colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(255,0,0,0.5)']],
        showscale=False, opacity=0.6, hoverinfo='skip', name="Yielded Zones"
    ), row=2, col=1)

    r_burn_vis = h_seam * 1.5
    for idx in active_wells:
        px = well_x[idx]
        fig_tm.add_shape(
            type="circle",
            x0=px - r_burn_vis, x1=px + r_burn_vis,
            y0=source_z_adv - r_burn_vis, y1=source_z_adv + r_burn_vis,
            line=dict(color="orange", width=2),
            fillcolor='rgba(255,165,0,0.15)', row=2, col=1
        )
    for px in well_x:
        fig_tm.add_shape(
            type="rect",
            x0=px - rec_width / 2.0, x1=px + rec_width / 2.0,
            y0=source_z_adv - h_seam / 2.0, y1=source_z_adv + h_seam / 2.0,
            line=dict(color="lime", width=3),
            fillcolor="rgba(0,255,0,0.1)", row=2, col=1
        )
    if stage == 2:
        fig_tm.add_shape(
            type="rect",
            x0=well_x[1] - 80, x1=well_x[1] + 80,
            y0=source_z_adv - 30, y1=source_z_adv + 30,
            line=dict(color="cyan", width=4, dash="dash"),
            fillcolor='rgba(0,255,255,0.1)', row=2, col=1
        )
        fig_tm.add_annotation(
            x=well_x[1], y=source_z_adv + 100,
            text="HIMOYA SELEGI (PILLAR)",
            showarrow=True, arrowhead=2,
            font=dict(color="cyan", size=12), row=2, col=1
        )

    fig_tm.add_trace(go.Heatmap(
        z=collapse_pred, x=x_axis, y=z_axis,
        colorscale='Viridis', opacity=0.4, showscale=False, name="AI Collapse"
    ), row=2, col=1)

    shear_disp = np.copy(shear_failure); shear_disp[void_mask_permanent] = False
    tens_disp  = np.copy(tensile_failure); tens_disp[void_mask_permanent] = False
    fig_tm.add_trace(go.Scatter(
        x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2],
        mode='markers', marker=dict(color='red', size=3, symbol='x'), name='Shear'
    ), row=2, col=1)
    fig_tm.add_trace(go.Scatter(
        x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2],
        mode='markers', marker=dict(color='blue', size=3, symbol='cross'), name='Tensile'
    ), row=2, col=1)

    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=void_visual, x=x_axis, y=z_axis,
        colorscale=[[0,'black'],[1,'black']], showscale=False,
        opacity=0.8, hoverinfo='skip'
    ), row=2, col=1)

    for yval in [source_z_adv - h_seam / 2.0, source_z_adv + h_seam / 2.0]:
        fig_tm.add_shape(
            type="line",
            x0=x_axis.min(), x1=x_axis.max(), y0=yval, y1=yval,
            line=dict(color="white", width=2, dash="dash"), row=2, col=1
        )

    zoom_margin = h_seam * 12
    fig_tm.update_layout(
        template="plotly_dark", height=900, margin=dict(r=150, t=80, b=100),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    fig_tm.update_yaxes(
        range=[source_z_adv + zoom_margin / 2.0, source_z_adv - zoom_margin],
        row=2, col=1
    )
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox("Avtomatik animatsiya (1→2→3 bosqichlar)"):
        anim_placeholder = st.empty()
        for s_anim in [1, 2, 3]:
            wells_s = states_132[s_anim]
            fos_s   = compute_advanced_fos(
                grid_x, grid_z, wells_s, well_x,
                source_z_adv, h_seam, cavity_width,
                temp_2d, grid_sigma_v, layers_data, layer_bounds_adv,
                E_MOD, ALPHA, NU, K0, Hc, sigma_v_coal_MPa, ucs_coal_pa
            )
            fig_s = go.Figure(go.Contour(
                z=fos_s, x=x_axis, y=z_axis,
                colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],
                            [0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
                zmin=0, zmax=3, contours_showlines=False,
                colorbar=dict(title="FOS")
            ))
            fig_s.update_yaxes(
                range=[source_z_adv + zoom_margin / 2.0, source_z_adv - zoom_margin],
                autorange=False
            )
            fig_s.update_layout(
                template="plotly_dark", height=500,
                title=f"Bosqich {s_anim} (1-3-2 sxemasi)"
            )
            anim_placeholder.plotly_chart(fig_s, use_container_width=True)
            time.sleep(1.2)
        st.success("Animatsiya yakunlandi.")

    selek_eni = well_distance - cavity_width
    msgs = {
        1: f"**1-Bosqich:** Chap quduq yoqilgan. Qalinlik={h_seam:.1f} m, Selek eni={selek_eni:.1f} m.",
        2: f"**2-Bosqich:** O'ng quduq yoqilgan. Markaziy selek tomni ushlab turadi. Selek={selek_eni:.1f} m.",
        3: f"**3-Bosqich:** Markaziy selek gazlashtirilmoqda. Barqaror cho'kish."
    }
    st.info(msgs[stage])
    if selek_eni < 18.5:
        st.error(f"⚠️ KRITIK: Selek o'lchami ({selek_eni:.1f} m) xavfsiz chegaradan past!")
    else:
        st.success(f"✅ BARQAROR: Selek o'lchami ({selek_eni:.1f} m) me'yorda.")

# =========================== SHAP TAHLILI ===========================
if SHAP_AVAILABLE and rf_model is not None:
    with st.expander("🧠 SHAP Model Interpretatsiyasi"):
        try:
            X_shap, _ = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z)
            background = shap.sample(X_shap, min(100, len(X_shap)))
            explainer  = shap.Explainer(rf_model, background)
            shap_values = explainer(background)
            st.subheader("SHAP o'zgaruvchanlik ahamiyati")
            fig_shap, ax = plt.subplots(figsize=(8, 4))
            shap.summary_plot(shap_values, background, show=False, plot_size=None)
            st.pyplot(fig_shap)
            plt.close(fig_shap)
        except Exception as e:
            st.warning(f"SHAP tahlili bajarilmadi: {e}")

# =========================== SOBOL SEZGIRLIGI ===========================
if SALIB_AVAILABLE:
    with st.expander("📊 Global sezgirlik tahlili (Sobol')"):
        st.markdown("Kirish parametrlarining model chiqishiga umumiy ta'siri.")
        problem = {
            'num_vars': 4,
            'names':  ['UCS', 'Temp', 'Depth', 'GSI'],
            'bounds': [[10, 80], [20, 1000], [10, 300], [20, 100]]
        }
        param_values = saltelli.sample(problem, 1024)

        def model_eval(params: np.ndarray) -> float:
            ucs_, T_, d_, gsi_ = params
            mb_   = 10.0 * np.exp((gsi_ - 100.0) / 28.0)
            s_    = np.exp((gsi_ - 100.0) / 9.0)
            str_  = ucs_ * np.exp(-beta_thermal * (T_ - 20.0))
            sv_   = 2500.0 * 9.81 * d_ / 1.0e6
            return str_ * (mb_ * sv_ / (str_ + EPS) + s_) ** 0.5 / (sv_ + EPS)

        Y  = np.array([model_eval(p) for p in param_values])
        Si = sobol.analyze(problem, Y)
        col_s1, col_s2 = st.columns(2)
        col_s1.write("First-order Sobol (S1):")
        col_s1.bar_chart(pd.DataFrame({'S1': Si['S1']}, index=problem['names']))
        col_s2.write("Total Sobol (ST):")
        col_s2.bar_chart(pd.DataFrame({'ST': Si['ST']}, index=problem['names']))

# =========================== LHS (Monte Carlo) ===========================
if PYDOE_AVAILABLE:
    with st.expander("🎲 Latin Hypercube Sampling (Collapse ehtimolligi)"):
        N_lhs = 5000
        lhs_sample   = lhs(3, samples=N_lhs)
        T_lhs        = gaussian_dist.ppf(lhs_sample[:, 0], loc=800, scale=100)
        UCS_lhs      = gaussian_dist.ppf(lhs_sample[:, 1], loc=40,  scale=10)
        # BUG FIX (12): Depth uchun to'g'ri geostatik kuchlanish ishlatiladi
        Depth_lhs    = gaussian_dist.ppf(lhs_sample[:, 2], loc=total_depth, scale=50)
        sv_lhs       = 2500.0 * 9.81 * Depth_lhs / 1.0e6   # MPa
        str_lhs      = UCS_lhs * np.exp(-beta_thermal * (T_lhs - 20.0))
        fos_lhs      = str_lhs / (sv_lhs + EPS)
        collapse_prob = 1.0 / (1.0 + np.exp(5.0 * (fos_lhs - 1.0)))

        fig_lhs = go.Figure(go.Histogram(
            x=collapse_prob, nbinsx=50, marker_color='orange'
        ))
        fig_lhs.update_layout(
            title="Collapse ehtimolligi taqsimoti (LHS Monte Carlo)",
            template='plotly_dark'
        )
        st.plotly_chart(fig_lhs, use_container_width=True)
        ci_low  = np.percentile(collapse_prob, 5)
        ci_high = np.percentile(collapse_prob, 95)
        st.write(f"90% ishonch intervali: [{ci_low:.3f}, {ci_high:.3f}]")
        p_fail  = np.mean(fos_lhs < 1.0)
        st.metric("Kollapsa ehtimoli (FOS < 1.0)", f"{p_fail:.3f}")

# =========================== 3D HAJM ===========================
if PYVISTA_AVAILABLE:
    with st.expander("🌋 3D litologik hajm (PyVista)"):
        try:
            grid_pv = pv.UniformGrid()
            grid_pv.dimensions = (50, 50, 30)
            values = np.random.rand(50 * 50 * 30)
            grid_pv["lithology"] = values
            plotter = pv.Plotter(off_screen=True)
            plotter.add_volume(grid_pv, cmap="viridis")
            st.image(plotter.screenshot(), use_container_width=True)
        except Exception as e:
            st.warning(f"PyVista vizualizatsiyasi amalga oshmadi: {e}")
else:
    with st.expander("🌋 3D hajm (Plotly proxy)"):
        st.info("PyVista mavjud emas – Plotly orqali sodda hajm.")
        fig_vol = go.Figure(data=go.Volume(
            x=grid_x.flatten(), y=np.zeros_like(grid_x.flatten()), z=grid_z.flatten(),
            value=temp_2d.flatten(),
            isomin=100, isomax=800, opacity=0.1, surface_count=20, colorscale='Hot'
        ))
        fig_vol.update_layout(title="Harorat hajmi (proxy)", height=500)
        st.plotly_chart(fig_vol, use_container_width=True)

# =========================== DINAMIK RISK ===========================
weights    = np.array([0.4, 0.3, 0.2, 0.1])
risk_index = (
    weights[0] * collapse_pred
    + weights[1] * np.clip(1.0 - fos_2d, 0.0, 1.0)    # BUG FIX (13): clamp
    + weights[2] * (perm / (np.max(perm) + EPS))
    + weights[3] * (temp_2d / (np.max(temp_2d) + EPS))
)
p_ri       = risk_index / (np.sum(risk_index) + EPS)
entropy    = float(-np.sum(p_ri * np.log(p_ri + EPS)))
st.metric("Tizim entropiyasi (noaniqlik)", f"{entropy:.3f}")

# Harorat animatsiyasi
placeholder_anim = st.empty()
if st.button("Harorat dinamik animatsiyasini ishga tushirish"):
    for t_anim in range(60):
        temp_dynamic = temp_2d + np.sin(t_anim / 5.0) * 50.0
        fig_anim = go.Figure(data=go.Heatmap(
            z=temp_dynamic, x=x_axis, y=z_axis, colorscale='Hot'
        ))
        fig_anim.update_layout(
            title=f"Vaqt qadami {t_anim}", template='plotly_dark'
        )
        placeholder_anim.plotly_chart(fig_anim, use_container_width=True)
        time.sleep(0.1)

# =========================== SENSOR API ===========================
st.markdown("---")
st.subheader("📡 Tashqi sensor API ulanishi")
try:
    response = requests.get("http://sensor-api/data", timeout=3)
    if response.status_code == 200:
        data      = response.json()
        st.success("Sensor ma'lumotlari olindi!")
        st.json(data)
    else:
        st.warning("Sensor API javob bermadi.")
except requests.exceptions.RequestException:
    st.info("Sensor API hozirda ulanmagan (simulyatsiya rejimi faol).")

# =========================== SIMPLERISKNN ===========================

class SimpleRiskNN(nn.Module if PT_AVAILABLE else object):
    """Kichik risk bashorat tarmog'i."""

    def __init__(self, input_dim: int = 3):
        if not PT_AVAILABLE:
            return
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(),
            nn.Linear(16, 8),         nn.ReLU(),
            nn.Linear(8, 1),          nn.Sigmoid()
        )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)


def train_simple_risk_nn(
    model: "nn.Module", X: np.ndarray, y: np.ndarray, epochs: int = 150
) -> "nn.Module":
    """SimpleRiskNN o'qitish (BCELoss)."""
    opt    = torch.optim.Adam(model.parameters(), lr=1.0e-3)
    loss_fn = nn.BCELoss()
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    y_t = torch.tensor(y, dtype=torch.float32).view(-1, 1).to(device)
    for _ in range(epochs):
        pred = model(X_t)
        loss = loss_fn(pred, y_t)
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model


@st.cache_resource
def get_risk_model() -> "nn.Module | None":
    """Sintetik risk modeli."""
    if not PT_AVAILABLE:
        return None
    rng    = np.random.default_rng(0)
    n_s    = 1000
    temp_r = rng.uniform(20.0, 1000.0, n_s)
    str_r  = rng.uniform(1.0,  20.0,   n_s)
    ucs_r  = rng.uniform(10.0, 80.0,   n_s)
    fos_r  = np.clip(ucs_r / (str_r + EPS), 0.0, 3.0)
    risk_r = (1.0 - fos_r / 3.0)
    # BCE uchun binary label
    y_r    = (risk_r > 0.5).astype(float)
    X_r    = np.column_stack([temp_r, str_r, ucs_r])
    model  = SimpleRiskNN().to(device)
    model  = train_simple_risk_nn(model, X_r, y_r, epochs=150)
    model.eval()
    return model


risk_model = get_risk_model()


def predict_risk_from_sensor(
    model, temp: np.ndarray, stress: np.ndarray, ucs_lab: np.ndarray
) -> np.ndarray:
    """SimpleRiskNN orqali risk bashorat."""
    if model is None:
        return np.full_like(temp, 0.5, dtype=float)
    X   = np.column_stack([temp, stress, ucs_lab])
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.flatten()


with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    st.markdown(
        "Sensor CSV fayli asosida **SimpleRiskNN** yordamida xavf indeksini bashorat qilish.\n"
        "Kerakli ustunlar: `temp`, `stress`, `ucs_lab`"
    )
    sensor_file = st.file_uploader(
        "Sensor CSV faylini yuklang", type=['csv'], key="sensor_ai"
    )
    if sensor_file:
        try:
            df_sensor     = pd.read_csv(sensor_file)
            required_cols = ['temp', 'stress', 'ucs_lab']
            missing       = [c for c in required_cols if c not in df_sensor.columns]
            if missing:
                st.error(f"Faylda quyidagi ustunlar yo'q: {missing}")
            else:
                risk_vals = predict_risk_from_sensor(
                    risk_model,
                    df_sensor['temp'].values,
                    df_sensor['stress'].values,
                    df_sensor['ucs_lab'].values
                )
                df_sensor['risk'] = risk_vals
                st.subheader("Bashorat natijalari")
                st.dataframe(df_sensor, use_container_width=True)
                fig_risk_line = go.Figure()
                fig_risk_line.add_trace(go.Scatter(
                    y=risk_vals, mode='lines+markers', name='Risk (0–1)',
                    line=dict(color='red')
                ))
                fig_risk_line.add_hline(
                    y=0.5, line_dash='dash', line_color='orange',
                    annotation_text="O'rta chegara"
                )
                fig_risk_line.add_hline(
                    y=0.7, line_dash='dash', line_color='red',
                    annotation_text="Yuqori chegara"
                )
                fig_risk_line.update_layout(
                    title="AI Risk Prediction", xaxis_title="Qator indeksi",
                    yaxis_title="Risk", template='plotly_dark'
                )
                st.plotly_chart(fig_risk_line, use_container_width=True)
                avg_risk = float(np.mean(risk_vals))
                if avg_risk > 0.7:
                    st.error(f"⚠️ Yuqori xavf! O'rtacha risk: {avg_risk:.3f}")
                elif avg_risk > 0.5:
                    st.warning(f"⚠️ O'rtacha xavf. O'rtacha risk: {avg_risk:.3f}")
                else:
                    st.success(f"✅ Xavf past. O'rtacha risk: {avg_risk:.3f}")
        except Exception as e:
            st.error(f"Faylni o'qishda xatolik: {e}")

# =========================== KOMPLEKS MONITORING ===========================

st.header(t('monitoring_panel', obj_name=obj_name))


def calculate_live_metrics(h: float, layers: list, T_max: float) -> dict:
    """Monitoring metrikalarini hisoblaydi."""
    target     = layers[-1]
    ucs_0_l    = target['ucs']
    H_l        = target['t']
    sv_l       = vertical_stress(
        sum(ll['t'] for ll in layers[:-1]) + H_l / 2.0, target['rho']
    )
    ucs_t_l    = ucs_0_l * np.exp(-beta_thermal * (T_max - 20.0))
    w_l        = optimize_pillar_width(ucs_t_l, sv_l, H_l)
    sigma_p_l  = ucs_t_l * (w_l / (H_l + EPS)) ** 0.5
    fos_l      = sigma_p_l / (sv_l + EPS)
    s_max_l    = 0.45 * w_l * 0.8
    return {
        'fos': fos_l, 'pillar_strength': sigma_p_l,
        'rec_width': w_l, 'max_subsidence': s_max_l,
        'stage': 'Active' if h <= 40 else 'Cooling',
    }


metrics_live = calculate_live_metrics(time_h, layers_data, T_source_max)
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric(t('pillar_live'),      f"{metrics_live['pillar_strength']:.1f} MPa")
mc2.metric(t('rec_width_live'),   f"{metrics_live['rec_width']:.1f} m")
mc3.metric(t('max_subsidence_live'), f"{metrics_live['max_subsidence']:.2f} m")
mc4.metric(t('process_stage'),    metrics_live['stage'])
mc5.metric(
    "Live FOS",
    f"{metrics_live['fos']:.2f}",
    delta=("✅ Barqaror" if metrics_live['fos'] >= 1.5 else "⚠️ Xavf"),
    delta_color=("normal" if metrics_live['fos'] >= 1.5 else "inverse")
)

# Sezgirlik Tornado
def sensitivity_analysis(
    base_ucs: float, base_gsi: float, base_d: float,
    base_nu: float, base_t: float, H: float,
    range_pct: float = 0.2
) -> tuple:
    """Parametr sezgirligini (Tornado) hisoblaydi."""
    def quick_fos(ucs_q, gsi_q, d_q, nu_q, t_q):
        mb_q = 10.0 * np.exp((gsi_q - 100.0) / (28.0 - 14.0 * d_q))
        s_q  = np.exp((gsi_q - 100.0) / (9.0 - 3.0 * d_q))
        a_q  = 0.5 + (1.0 / 6.0) * (np.exp(-gsi_q / 15.0) - np.exp(-20.0 / 3.0))
        sv_q = 2500.0 * 9.81 * H / 1.0e6
        ucs_t_q = ucs_q * np.exp(-beta_thermal * (t_q - 20.0))
        sp_q = ucs_t_q * (30.0 / (H + EPS)) ** 0.5
        fos_q = sp_q / (sv_q + EPS)
        return float(fos_q)

    params = {
        'UCS (MPa)':   (base_ucs, base_ucs * (1 - range_pct), base_ucs * (1 + range_pct)),
        'GSI':         (base_gsi, base_gsi * (1 - range_pct), min(100, base_gsi * (1 + range_pct))),
        'D factor':    (base_d, max(0.0, base_d - 0.2), min(1.0, base_d + 0.2)),
        'Poisson (ν)': (base_nu, max(0.1, base_nu - 0.05), min(0.4, base_nu + 0.05)),
        'Harorat (°C)': (base_t, base_t * (1 - range_pct), min(1200.0, base_t * (1 + range_pct))),
    }
    base_fos = quick_fos(base_ucs, base_gsi, base_d, base_nu, base_t)
    results  = []
    for name, (base, low, high) in params.items():
        kw = dict(ucs_q=base_ucs, gsi_q=base_gsi, d_q=base_d, nu_q=base_nu, t_q=base_t)
        key_map = {
            'UCS (MPa)': 'ucs_q', 'GSI': 'gsi_q', 'D factor': 'd_q',
            'Poisson (ν)': 'nu_q', 'Harorat (°C)': 't_q'
        }
        k = key_map[name]
        kw_low  = {**kw, k: low};  fos_low  = quick_fos(**kw_low)
        kw_high = {**kw, k: high}; fos_high = quick_fos(**kw_high)
        results.append({'param': name, 'low': fos_low - base_fos, 'high': fos_high - base_fos})
    return pd.DataFrame(results), base_fos


with st.expander("🌪️ Sezgirlik Tahlili (Tornado Plot)"):
    df_sens, fos_base = sensitivity_analysis(
        layers_data[-1]['ucs'], layers_data[-1]['gsi'],
        D_factor, nu_poisson, avg_t_p, H_seam
    )
    df_sens = df_sens.sort_values('high', ascending=True)
    fig_tornado = go.Figure()
    fig_tornado.add_bar(
        y=df_sens['param'], x=df_sens['low'],
        orientation='h', name='−20%', marker_color='#E74C3C'
    )
    fig_tornado.add_bar(
        y=df_sens['param'], x=df_sens['high'],
        orientation='h', name='+20%', marker_color='#27AE60'
    )
    fig_tornado.add_vline(x=0, line_color='white', line_width=2)
    fig_tornado.update_layout(
        title=f"FOS sezgirligi (asosiy FOS={fos_base:.2f})",
        barmode='overlay', template='plotly_dark', height=350,
        xaxis_title='ΔFOS', bargap=0.3
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

# =========================== ISO 9001:2015 HISOBOT (5 bo'lim) ===========================

def generate_full_iso_report(
    obj_name: str, lang: str, layers_data: list,
    T_source_max: float, burn_duration: float,
    pillar_strength: float, optimal_width_ai: float,
    fos_2d: np.ndarray, risk_map: np.ndarray,
    prepared_by: str, approved_by: str,
    doc_number: str, revision: str,
    fig_bytes: bytes = None,
    void_vol: float = 0.0,
) -> bytes:
    """
    ISO 9001:2015 muvofiq 5 bo'limli texnik hisobot.

    Returns
    -------
    bytes
        .docx fayl bajt oqimi.
    """
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
            'safe':    "✅ TIZIM BARQAROR: Loyiha parametrlari xavfsizlik talablariga javob beradi.",
            'warning': "⚠️ MARGINAL HOLAT: Monitoringni kuchaytirish va qo'shimcha mahkamlash tavsiya etiladi.",
            'danger':  "🚨 XAVFLI: O'pirilish xafvi yuqori! Pillar kengligini oshirish yoki termal yukni kamaytirish shart.",
            'risk_ident': "Aniqlangan xavf omillari: termal degradatsiya, yuqori bo'shliq hajmi, FOS < 1.3.",
            'mitigation': "Muhandislik choralari: selek eni oshirish, gaz bosimini kamaytirish, real-vaqt monitoring.",
            'rec_width': "Tavsiya qilingan selek eni:",
            'void_vol':  "Hisoblangan bo'shliq hajmi (m²):",
            'min_fos':   "Minimal FOS qiymati:",
            'risk_level': "Risk darajasi:",
            'appendix_title': "ILOVA: Matematik Modellar",
            'hb_eq':   "1. Hoek-Brown Failure Criterion (Hoek & Brown, 2018):",
            'decay_eq': "2. Thermal Strength Decay (Shao et al., 2015):",
            'pillar_eq': "3. Pillar Strength (Wilson, 1972):",
            'patent_title': "4. Patent da'volar xulosa",
        },
        'en': {
            'h1': "ISO 9001:2015 COMPLIANCE REPORT",
            'sec1': "1. PROJECT OVERVIEW",
            'sec2': "2. GEOMECHANICAL LAYER PROPERTIES",
            'sec3': "3. RISK ASSESSMENT",
            'sec4': "4. MITIGATION STRATEGY",
            'sec5': "5. ENGINEERING CONCLUSIONS & RECOMMENDATIONS",
            'fos_label': "Factor of Safety (FOS):",
            'ai_label': "AI Optimized Pillar Width:",
            'conclusion_title': "Final Decision:",
            'safe':    "✅ SYSTEM STABLE: Project parameters meet all safety requirements.",
            'warning': "⚠️ MARGINAL STABILITY: Increase monitoring and support measures.",
            'danger':  "🚨 DANGEROUS: High collapse risk! Increase pillar width or reduce thermal load.",
            'risk_ident': "Identified hazards: thermal degradation, large void volume, FOS < 1.3.",
            'mitigation': "Mitigation: increase pillar width, reduce gas pressure, real-time monitoring.",
            'rec_width': "Recommended pillar width:",
            'void_vol':  "Computed void volume (m²):",
            'min_fos':   "Minimum FOS:",
            'risk_level': "Risk level:",
            'appendix_title': "APPENDIX: Mathematical Models",
            'hb_eq':   "1. Hoek-Brown Failure Criterion (Hoek & Brown, 2018):",
            'decay_eq': "2. Thermal Strength Decay (Shao et al., 2015):",
            'pillar_eq': "3. Pillar Strength (Wilson, 1972):",
            'patent_title': "4. Patent Claims Summary",
        },
    }
    texts['ru'] = texts['en']   # fallback
    T = texts.get(lang, texts['en'])

    doc = Document()
    h1  = doc.add_heading(f"{T['h1']}\n{obj_name}", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    meta = doc.add_table(rows=2, cols=2)
    meta.style = 'Table Grid'
    meta.cell(0, 0).text = f"Doc No: {doc_number}"
    meta.cell(0, 1).text = f"Revision: {revision}"
    meta.cell(1, 0).text = f"Prepared: {prepared_by}"
    meta.cell(1, 1).text = f"Approved: {approved_by}"

    # Sec 1
    doc.add_heading(T['sec1'], level=2)
    p = doc.add_paragraph()
    p.add_run("Ob'ekt / Object: ").bold = True;  p.add_run(f"{obj_name}\n")
    p.add_run("Max Temp (°C): ").bold = True;    p.add_run(f"{T_source_max}\n")
    p.add_run("Burn Duration (h): ").bold = True; p.add_run(f"{burn_duration}\n")

    # Sec 2 – Qatlam jadvali
    doc.add_heading(T['sec2'], level=2)
    tbl = doc.add_table(rows=1, cols=6)
    tbl.style = 'Table Grid'
    hdrs = ["Layer", "Thick (m)", "UCS (MPa)", "GSI", "mi", "ρ (kg/m³)"]
    for i_h, h_text in enumerate(hdrs):
        tbl.rows[0].cells[i_h].text = h_text
    for layer in layers_data:
        row_cells = tbl.add_row().cells
        row_cells[0].text = layer['name']
        row_cells[1].text = f"{layer['t']:.1f}"
        row_cells[2].text = f"{layer['ucs']:.1f}"
        row_cells[3].text = str(layer['gsi'])
        row_cells[4].text = f"{layer['mi']:.1f}"
        row_cells[5].text = f"{layer['rho']:.0f}"

    # Sec 3 – Risk baholash
    doc.add_heading(T['sec3'], level=2)
    doc.add_paragraph(T['risk_ident'])
    avg_risk_val = float(np.nanmean(risk_map))
    min_fos_val  = float(np.nanmin(fos_2d))
    if avg_risk_val > 0.75:
        risk_level_str = "CRITICAL"
    elif avg_risk_val > 0.5:
        risk_level_str = "MEDIUM"
    else:
        risk_level_str = "LOW"
    doc.add_paragraph(f"{T['risk_level']} {risk_level_str}")
    doc.add_paragraph(f"Average risk index: {avg_risk_val:.3f}")
    doc.add_paragraph(f"{T['min_fos']} {min_fos_val:.2f}")
    doc.add_paragraph(f"{T['void_vol']} {void_vol:.1f}")

    if fig_bytes:
        doc.add_heading("Visual Analysis (Risk Map)", level=3)
        doc.add_picture(io.BytesIO(fig_bytes), width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Sec 4 – Choralar
    doc.add_heading(T['sec4'], level=2)
    doc.add_paragraph(T['mitigation'])
    doc.add_paragraph(f"{T['rec_width']} {optimal_width_ai:.1f} m")

    # Sec 5 – Xulosa
    doc.add_heading(T['sec5'], level=2)
    fos_val = float(np.nanmean(fos_2d))
    if fos_val < 1.1:
        conclusion_text = T['danger'];  color = RGBColor(255, 0, 0)
    elif fos_val < 1.5:
        conclusion_text = T['warning']; color = RGBColor(255, 165, 0)
    else:
        conclusion_text = T['safe'];    color = RGBColor(0, 128, 0)

    res_p = doc.add_paragraph()
    res_p.add_run(f"{T['fos_label']} {fos_val:.2f}\n").bold = True
    res_p.add_run(f"{T['ai_label']} {optimal_width_ai:.1f} m\n\n")
    final_run = res_p.add_run(f"{T['conclusion_title']}\n{conclusion_text}")
    final_run.bold = True
    final_run.font.color.rgb = color

    # Ilova: Matematik modellar
    doc.add_page_break()
    doc.add_heading(T['appendix_title'], level=2)
    doc.add_paragraph(T['hb_eq'])
    doc.add_paragraph(
        "σ₁ = σ₃ + σci · (mb·σ₃/σci + s)^a",
        style='Intense Quote'
    )
    doc.add_paragraph(T['decay_eq'])
    doc.add_paragraph(
        "UCS(T) = UCS₀ · exp(−β · (T − T₀))",
        style='Intense Quote'
    )
    doc.add_paragraph(T['pillar_eq'])
    doc.add_paragraph(
        "σp = UCS(T) · (w/H)^0.5",
        style='Intense Quote'
    )

    # Patent da'volar
    doc.add_heading(T['patent_title'], level=2)
    claims = [
        "1. Ko'chuvchi manbali Gaussian-FDM gibrid harorat modeli (Courant shartli).",
        "2. TM-FOS kompozit risk indeksi: 4 komponentli og'irlikli xavf xaritasi.",
        "3. HybridCollapseNet + RF Ensemble: fizik jarima funksiyali neyron tarmoq.",
        "4. Termal-iterativ selek optimizatsiyasi: L-BFGS-B usulida minimal FOS≥1.5.",
        "5. UCG 1→3→2 dinamik FOS algoritmi: 3 quduqli sxema uchun geomexanik holat.",
    ]
    for claim in claims:
        doc.add_paragraph(claim, style='List Bullet')

    # Adabiyotlar
    doc.add_heading("References / Adabiyotlar", level=2)
    refs = [
        "Hoek, E., & Brown, E. T. (2018). The Hoek-Brown failure criterion and GSI – 2018 edition. JRMGE, 10(3), 445–463.",
        "Yang, D. (2010). Stability of Underground Coal Gasification Cavities. PhD Thesis, TU Delft.",
        "Shao, S., et al. (2015). A thermal damage constitutive model for rock. IJRMMS, 78, 216–226.",
        "Wilson, A. H. (1972). Research into the determination of pillar size. Mining Engineer, 131, 409–417.",
        "Bieniawski, Z. T. (1989). Engineering Rock Mass Classifications. Wiley, New York.",
        "Salmi, E. F., & Karakus, M. (2019). Numerical analysis of pillar failure. Int. J. Rock Mech. Min. Sci., 120, 55–67.",
    ]
    for ref in refs:
        doc.add_paragraph(ref, style='List Bullet')

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


with st.expander("📄 ISO 9001:2015 Standart Hujjat (.docx)"):
    d1, d2 = st.columns(2)
    with d1:
        iso_lang    = st.selectbox(
            "Hujjat tili", ['uz', 'en', 'ru'],
            format_func=lambda x: {'uz': "🇺🇿 O'zbek", 'en': "🇬🇧 English", 'ru': "🇷🇺 Русский"}[x],
            key="iso_lang"
        )
        doc_num_input = st.text_input("Hujjat raqami", value="UCG-2026-001")
        revision_inp  = st.text_input("Revision", value="A")
    with d2:
        prepared_inp = st.text_input("Prepared by", value="UCG Engineering Team")
        approved_inp = st.text_input("Approved by", value="Chief Engineer")

    if st.button("📄 ISO hujjat yaratish", type="primary", use_container_width=True):
        with st.spinner("ISO 9001 shablon tayyorlanmoqda..."):
            try:
                fig_rep, ax_rep = plt.subplots(figsize=(6, 4))
                im_rep = ax_rep.imshow(
                    risk_map,
                    extent=[x_axis[0], x_axis[-1], z_axis[-1], z_axis[0]],
                    cmap='hot', aspect='auto'
                )
                plt.colorbar(im_rep, ax=ax_rep, label='Risk Index')
                ax_rep.set_title('Composite Risk Map'); ax_rep.set_xlabel('X (m)'); ax_rep.set_ylabel('Depth (m)')
                buf_img = io.BytesIO()
                plt.savefig(buf_img, format='png', dpi=100, bbox_inches='tight')
                buf_img.seek(0)
                plt.close(fig_rep)

                docx_bytes = generate_full_iso_report(
                    obj_name=obj_name, lang=iso_lang, layers_data=layers_data,
                    T_source_max=T_source_max, burn_duration=burn_duration,
                    pillar_strength=pillar_strength, optimal_width_ai=rec_width,
                    fos_2d=fos_2d, risk_map=risk_map,
                    prepared_by=prepared_inp, approved_by=approved_inp,
                    doc_number=doc_num_input, revision=revision_inp,
                    fig_bytes=buf_img.getvalue(), void_vol=void_volume,
                )
                st.download_button(
                    label=f"⬇️ {doc_num_input}_Rev{revision_inp}.docx",
                    data=docx_bytes,
                    file_name=f"{doc_num_input}_Rev{revision_inp}_{pd.Timestamp.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Hisobot yaratishda xatolik: {e}")

# =========================== PATENT DA'VOLAR ===========================

with st.expander("📜 5 ta Patent Da'vosi (PhD / Patent Ariza)", expanded=False):
    st.markdown("### UCG Termo-Mexanik Monitoring Tizimi – Patent Da'volari")
    st.markdown("""
**Da'vo 1 – Ko'chuvchi Manbali Gaussian-FDM Gibrid Harorat Modeli**
Yer osti ko'mir gazlashtirish jarayonida bir nechta harakat manbalari uchun
Gaussian yaqinlashuvini va cheklangan farqlar usulini (FDM) birlashtirgan,
Courant barqarorlik shartini avtomatik bajaruvchi, harorat maydonini hisoblash
usuli va qurilmasi.

---
**Da'vo 2 – TM-FOS Kompozit Risk Indeksi**
Kollapsa ehtimoli (0.35), xavfsizlik koeffitsienti (0.30), filtratsiya
o'tkazuvchanligi (0.20) va harorat darajasi (0.15) og'irlikli yig'indisi
sifatida hisoblangan, Hoek-Brown (2018) mezoniga asoslangan
termo-mexanik xavf indeksi va uni real vaqtda hisoblash tizimi.

---
**Da'vo 3 – HybridCollapseNet + RF Ensemble Kollaps Bashorat Tizimi**
Fizik jarima funksiyali (clamp(1−FOS, min=0)·pred) BCE yo'qotish
funksiyasi bilan birgalikda o'qitiladigan chuqur neyron tarmoq (HybridCollapseNet)
va tasodifiy o'rmon (RandomForest) klassifikatorini agregatlangan (0.6/0.4)
tarzda birlashtiruvchi kollapsa bashorat usuli.

---
**Da'vo 4 – Termal-Iterativ Selek Kengligini Optimallashtirish**
Haroratga bog'liq UCS kamayishini (σ_ci(T) = σ_ci0·exp(−β·ΔT))
hisobga oluvchi va L-BFGS-B gradiyent usuli yordamida FOS ≥ 1.5 shartini
ta'minlovchi eng kichik selek kengligini topuvchi muhandislik optimallashtirish
algoritmi.

---
**Da'vo 5 – UCG 1→3→2 Dinamik FOS Maydoni Algoritmi**
Uch quduqli UCG tizimida (chap → markaziy → o'ng) ketma-ket yoqish
sxemasini simulyatsiya qiluvchi, har bir bosqichda elliptik kavern, dome
o'pirish hududi va markaziy himoya selek mustahkamligini birgalikda
hisoblashga asoslangan dinamik geomexanik monitoring algoritmi.
""")

# =========================== LIVE 3D MONITORING ===========================

st.header("🔄 Live 3D Monitoring (Real-time)")
tab_live, tab_ai_orig, tab_advanced = st.tabs([
    t('live_monitoring_tab'), t('ai_monitor_title'), t('advanced_analysis')
])

with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies and alerts")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    run_live  = st.button("▶️ Run Live Monitoring", key="run_live")
    stop_live = st.button("⏹ Stop Monitoring",    key="stop_live")
    if 'stop_flag_live' not in st.session_state:
        st.session_state.stop_flag_live = False
    if stop_live:
        st.session_state.stop_flag_live = True

    col_live1, col_live2 = st.columns(2)
    subs_plot_live = col_live1.empty()
    temp_plot_live = col_live2.empty()
    col_live3, col_live4 = st.columns(2)
    pillar_plot_live  = col_live3.empty()
    trend_plot_live   = col_live4.empty()
    surface_3d_plot_live = st.empty()
    alert_box_live       = st.empty()

    if 'live_history_df' not in st.session_state:
        st.session_state.live_history_df = pd.DataFrame(
            columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m']
        )

    if run_live:
        st.session_state.stop_flag_live = False
        X_live = np.linspace(-20, 20, 50)
        Y_live = np.linspace(-20, 20, 50)
        X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_history_live  = []
        fos_history_live   = []
        width_history_live = []
        temp_history_live  = []
        steps_done = 0

        rf_live = RandomForestRegressor(n_estimators=10, random_state=42)
        rf_live.fit(np.random.rand(20, 3), np.random.rand(20))

        for t_step in range(TIME_STEPS):
            if st.session_state.stop_flag_live:
                break
            Z_subs = (
                np.exp(-(X_grid_live ** 2 + Y_grid_live ** 2)
                       / (2.0 * (5.0 + t_step * 0.1) ** 2))
                * 5.0 * t_step / TIME_STEPS
            )
            Z_temp = (
                np.exp(-(X_grid_live ** 2 + Y_grid_live ** 2) / (2.0 * 8.0 ** 2))
                * T_source_max * t_step / TIME_STEPS
            )
            Z_filtered  = gaussian_filter(Z_subs, sigma=1)
            anomalies   = Z_subs - Z_filtered
            anomaly_pts = np.where(np.abs(anomalies) > 0.2)

            avg_ucs_live = float(np.mean([l['ucs'] for l in layers_data]))
            X_feat_live  = np.array([[burn_duration, T_source_max, avg_ucs_live]])
            pillar_width_pred = float(rf_live.predict(X_feat_live)[0])
            FOS_live  = float(np.clip(2.5 - t_step * 0.03, 0.8, 2.5))
            mean_subs = float(np.mean(Z_subs))

            subs_history_live.append(mean_subs)
            fos_history_live.append(FOS_live)
            width_history_live.append(pillar_width_pred)
            temp_history_live.append(float(np.mean(Z_temp)))

            new_row = pd.DataFrame({
                'step': [t_step + 1], 'mean_subsidence_cm': [mean_subs * 100],
                'max_temp_c': [float(np.max(Z_temp))],
                'FOS': [FOS_live], 'pillar_width_m': [pillar_width_pred]
            })
            st.session_state.live_history_df = pd.concat(
                [st.session_state.live_history_df, new_row], ignore_index=True
            ).tail(1000)

            subs_plot_live.plotly_chart(
                go.Figure(go.Heatmap(z=Z_subs * 100, x=X_live, y=Y_live, colorscale='Viridis'))
                .update_layout(title='Surface Subsidence (cm)', height=350),
                use_container_width=True, key=f"subs_{t_step}"
            )
            temp_plot_live.plotly_chart(
                go.Figure(go.Heatmap(z=Z_temp, x=X_live, y=Y_live, colorscale='Hot'))
                .update_layout(title='Temperature Field (°C)', height=350),
                use_container_width=True, key=f"temp_{t_step}"
            )
            pillar_plot_live.metric(
                "Recommended Pillar Width (m)",
                f"{pillar_width_pred:.2f}", delta=f"FOS = {FOS_live:.2f}"
            )
            trend_plot_live.plotly_chart(
                go.Figure(go.Scatter(y=subs_history_live, mode='lines+markers'))
                .update_layout(title='Subsidence Trend', height=350),
                use_container_width=True, key=f"trend_{t_step}"
            )

            fig_surf = go.Figure(data=[go.Surface(
                z=Z_subs * 100, x=X_live, y=Y_live, colorscale='Viridis', opacity=0.9
            )])
            if anomaly_pts[0].size > 0:
                fig_surf.add_trace(go.Scatter3d(
                    x=X_grid_live[anomaly_pts], y=Y_grid_live[anomaly_pts],
                    z=Z_subs[anomaly_pts] * 100,
                    mode='markers', marker=dict(color='red', size=5), name='Anomaly'
                ))
            fig_surf.update_layout(title='3D Surface & Anomalies', height=500)
            surface_3d_plot_live.plotly_chart(
                fig_surf, use_container_width=True, key=f"surf_{t_step}"
            )

            alerts = []
            if FOS_live < 1.2:       alerts.append("⚠️ FOS Critical!")
            if mean_subs * 100 > 3:  alerts.append("⚠️ High Subsidence!")
            if np.max(Z_temp) > 1100: alerts.append("🔥 Overheating Alert!")
            if alerts:
                alert_box_live.markdown("### 🔴 ALERTS\n" + "\n".join(alerts))
            else:
                alert_box_live.markdown("### 🟢 All systems normal")

            time.sleep(0.1)
            steps_done += 1

        st.success(f"✅ Live monitoring completed after {steps_done} steps.")

    if not st.session_state.live_history_df.empty:
        st.markdown("---")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=t('download_data'), data=csv_data,
            file_name="ucg_live_monitoring.csv", mime="text/csv"
        )

with tab_ai_orig:
    st.markdown(f"*{t('ai_monitor_desc')}*")

    def get_sensor_data_sim(step: int, total_steps: int, base_temp: float) -> dict:
        trend    = step / max(total_steps, 1)
        temp_s   = base_temp * (0.5 + 0.7 * trend) + np.random.normal(0, 10)
        pressure = 2.0 + 5.0 * trend + np.random.normal(0, 0.5)
        stress   = 5.0 + 10.0 * trend + np.random.normal(0, 0.5)
        return {"temperature": temp_s, "gas_pressure": pressure, "stress": stress}

    def compute_effective_stress(sensor: dict) -> float:
        return sensor["stress"] - sensor["gas_pressure"] + 0.002 * sensor["temperature"]

    def detect_anomaly_z(
        history: list, value: float, threshold: float = 2.0, window: int = 20
    ) -> bool:
        if len(history) < window:
            return False
        recent = history[-window:]
        mean   = float(np.mean(recent))
        std    = float(np.std(recent)) + 1.0e-6
        return abs(value - mean) > threshold * std

    def simulate_sensors_fos(n_steps: int) -> pd.DataFrame:
        T  = (np.linspace(20.0, min(1100.0, T_source_max), n_steps)
              + np.random.normal(0, 10, n_steps))
        sv = (np.linspace(5.0, min(15.0, sv_seam * 10.0), n_steps)
              + np.random.normal(0, 0.5, n_steps))
        return pd.DataFrame({'Temperature': T, 'VerticalStress': sv})

    # FOS tahminchi modeli
    if PT_AVAILABLE:
        class SimpleNN(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(2, 16)
                self.fc2 = nn.Linear(16, 16)
                self.fc3 = nn.Linear(16, 1)
            def forward(self, x):
                x = torch.relu(self.fc1(x))
                x = torch.relu(self.fc2(x))
                return 3.0 * torch.sigmoid(self.fc3(x))   # [0, 3]

        fos_nn_model   = SimpleNN().to(device)
        fos_criterion  = nn.MSELoss()
        fos_optimizer  = torch.optim.Adam(fos_nn_model.parameters(), lr=0.01)
    else:
        fos_rf_model = RandomForestRegressor(n_estimators=50, random_state=42)

    ai_tab1, ai_tab2 = st.tabs([
        "📡 Anomaliya Aniqlash (Digital Twin)",
        "📊 FOS Prediction (SimpleNN / RF)"
    ])

    with ai_tab1:
        st.markdown("#### Sensor ma'lumotlari asosida real-vaqt anomaliya aniqlash")
        t1c1, t1c2, t1c3 = st.columns([1, 1, 2])
        with t1c1:
            ai_steps_1 = st.number_input(
                t('ai_steps'), min_value=10, max_value=500, value=60, step=10, key="ai_steps_1"
            )
        with t1c2:
            anomaly_threshold = st.slider(
                "Anomaliya chegarasi (σ)", 1.0, 4.0, 2.0, 0.5, key="thresh_1"
            )
        with t1c3:
            run_ai_1 = st.button(
                t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_1"
            )

        if run_ai_1:
            placeholder_1   = st.empty()
            history_eff     = []
            anomalies_eff   = []
            temp_history_ai = []
            gas_history_ai  = []
            stress_history_ai = []
            for step in range(int(ai_steps_1)):
                sensor_s   = get_sensor_data_sim(step, int(ai_steps_1), T_source_max * 0.6)
                effective  = compute_effective_stress(sensor_s)
                is_anomaly = detect_anomaly_z(
                    history_eff, effective, threshold=anomaly_threshold
                )
                history_eff.append(effective)
                anomalies_eff.append(effective if is_anomaly else None)
                temp_history_ai.append(sensor_s["temperature"])
                gas_history_ai.append(sensor_s["gas_pressure"])
                stress_history_ai.append(sensor_s["stress"])

                with placeholder_1.container():
                    ac1, ac2, ac3, ac4 = st.columns(4)
                    ac1.metric("🌡 Harorat", f"{sensor_s['temperature']:.1f} °C")
                    ac2.metric("💨 Gaz bosimi", f"{sensor_s['gas_pressure']:.2f} MPa")
                    ac3.metric("🧱 Effektiv σ", f"{effective:.2f} MPa",
                               delta="⚠️ Anomaliya!" if is_anomaly else "Normal",
                               delta_color="inverse")
                    ac4.metric("📈 Qadam", f"{step + 1}/{int(ai_steps_1)}")

                    fig_a = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=("Effektiv σ & Anomaliyalar", "Harorat (°C)",
                                        "Gaz bosimi (MPa)", "Stress (MPa)"),
                        vertical_spacing=0.15, horizontal_spacing=0.1
                    )
                    fig_a.add_trace(
                        go.Scatter(y=history_eff, mode='lines', name='Effektiv σ',
                                   line=dict(color='cyan', width=2)), row=1, col=1
                    )
                    fig_a.add_trace(
                        go.Scatter(y=anomalies_eff, mode='markers', name='Anomaliya',
                                   marker=dict(color='red', size=10, symbol='x')), row=1, col=1
                    )
                    fig_a.add_trace(
                        go.Scatter(y=temp_history_ai, mode='lines', name='Harorat',
                                   line=dict(color='orange', width=2)), row=1, col=2
                    )
                    fig_a.add_trace(
                        go.Scatter(y=gas_history_ai, mode='lines+markers', name='Gaz',
                                   line=dict(color='lime', width=1)), row=2, col=1
                    )
                    fig_a.add_trace(
                        go.Scatter(y=stress_history_ai, mode='lines', name='Stress',
                                   line=dict(color='magenta', width=2)), row=2, col=2
                    )
                    fig_a.update_layout(
                        template="plotly_dark", height=500,
                        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")
                    )
                    st.plotly_chart(fig_a, use_container_width=True, key=f"anom_{step}")

                    anomaly_count = sum(1 for a in anomalies_eff if a is not None)
                    if is_anomaly:
                        st.error(f"🚨 ANOMALIYA! (Jami: {anomaly_count}) — Collapse xavfi!")
                    elif effective > pillar_strength * 0.8:
                        st.warning(f"⚠️ Kuchlanish pillar chegarasining 80% oshdi!")
                    else:
                        st.success(f"✅ Normal — Effektiv σ: {effective:.2f} MPa")
                    st.progress((step + 1) / int(ai_steps_1))
                time.sleep(0.15)
            st.balloons()
            st.success(f"✅ Monitoring yakunlandi! Jami anomaliyalar: {sum(1 for a in anomalies_eff if a is not None)}")

    with ai_tab2:
        st.markdown("#### SimpleNN / RandomForest yordamida FOS bashorati")
        t2c1, t2c2 = st.columns([1, 3])
        with t2c1:
            ai_steps_2 = st.number_input(
                t('ai_steps'), min_value=10, max_value=500, value=50, step=10, key="ai_steps_2"
            )
            # BUG FIX (14): fos_target min_value=1.0 (muhandislik amaliyoti)
            fos_target = st.number_input(
                "Maqsad FOS qiymati", min_value=1.0, max_value=3.0,
                value=1.5, step=0.1, key="fos_target"
            )
        with t2c2:
            run_ai_2 = st.button(
                t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_2"
            )

        if run_ai_2:
            placeholder_2       = st.empty()
            sensor_data_fos     = simulate_sensors_fos(int(ai_steps_2))
            pillar_strength_pred = []
            fos_rf_trained       = False

            for i in range(int(ai_steps_2)):
                row = sensor_data_fos.iloc[i]
                X_row = np.array([[row.Temperature, row.VerticalStress]])
                if PT_AVAILABLE:
                    X_t     = torch.tensor(X_row, dtype=torch.float32).to(device)
                    y_pred  = float(fos_nn_model(X_t).detach().cpu().numpy()[0][0])
                    target  = torch.tensor([[fos_target]], dtype=torch.float32).to(device)
                    fos_optimizer.zero_grad()
                    loss    = fos_criterion(fos_nn_model(X_t), target)
                    loss.backward()
                    fos_optimizer.step()
                else:
                    if not fos_rf_trained:
                        fos_rf_model.fit(X_row, [fos_target])
                        fos_rf_trained = True
                    y_pred = float(fos_rf_model.predict(X_row)[0])

                pillar_strength_pred.append(y_pred)
                fos_color = (
                    t('fos_red')    if y_pred < 1.0
                    else t('fos_yellow') if y_pred <= 1.5
                    else t('fos_green')
                )

                with placeholder_2.container():
                    p2c1, p2c2, p2c3 = st.columns(3)
                    p2c1.metric("🌡 Harorat",       f"{row.Temperature:.1f} °C")
                    p2c2.metric("🧱 Vertikal Stress", f"{row.VerticalStress:.2f} MPa")
                    p2c3.metric("📊 Bashorat FOS",   f"{y_pred:.2f}", delta=fos_color)

                    fig_fos = make_subplots(
                        rows=1, cols=2,
                        subplot_titles=("FOS Bashorati (Tarixiy)", "Harorat vs Stress")
                    )
                    fig_fos.add_trace(
                        go.Scatter(y=pillar_strength_pred[:i + 1], mode='lines+markers',
                                   name='Bashorat FOS', line=dict(color='lime', width=2)),
                        row=1, col=1
                    )
                    fig_fos.add_hline(
                        y=fos_target, line_dash="dash", line_color="yellow",
                        annotation_text=f"Maqsad: {fos_target}", row=1, col=1
                    )
                    fig_fos.add_trace(
                        go.Scatter(
                            x=sensor_data_fos['Temperature'].iloc[:i + 1].tolist(),
                            y=sensor_data_fos['VerticalStress'].iloc[:i + 1].tolist(),
                            mode='markers', name="Sensor yo'li",
                            marker=dict(color=list(range(i + 1)), colorscale='Viridis', size=6)
                        ),
                        row=1, col=2
                    )
                    fig_fos.update_layout(template="plotly_dark", height=420)
                    st.plotly_chart(fig_fos, use_container_width=True, key=f"fospred_{i}")
                    st.progress((i + 1) / int(ai_steps_2))
                time.sleep(0.05)

            st.balloons()
            final_fos = pillar_strength_pred[-1] if pillar_strength_pred else 0.0
            if final_fos < 1.0:
                st.error(f"🔴 Yakuniy FOS: {final_fos:.2f} — Xavfli!")
            elif final_fos <= 1.5:
                st.warning(f"🟡 Yakuniy FOS: {final_fos:.2f} — Noaniq holat")
            else:
                st.success(f"🟢 Yakuniy FOS: {final_fos:.2f} — Barqaror!")

with tab_advanced:
    st.header(t('advanced_analysis'))
    E_MODULUS_R = 5000.0; ALPHA_THERM = 1.0e-5; BETA_CONST = beta_thermal
    target_l    = layers_data[-1]
    ucs_0_r     = target_l['ucs']
    gsi_val     = target_l['gsi']
    mi_val      = target_l['mi']
    H_depth_tot = sum(l['t'] for l in layers_data[:-1]) + target_l['t'] / 2.0
    sigma_v_tot = vertical_stress(H_depth_tot, target_l['rho'])

    mb_dyn  = mi_val * np.exp((gsi_val - 100.0) / (28.0 - 14.0 * D_factor))
    s_dyn   = np.exp((gsi_val - 100.0) / (9.0 - 3.0 * D_factor))
    a_dyn   = 0.5 + (1.0 / 6.0) * (np.exp(-gsi_val / 15.0) - np.exp(-20.0 / 3.0))
    ucs_t_dyn = ucs_0_r * np.exp(-BETA_CONST * (T_source_max - 20.0))
    p_str_final = ucs_t_dyn * (rec_width / (H_seam + EPS)) ** 0.5
    fos_final   = p_str_final / (sigma_v_tot + EPS)

    t1_adv, t2_adv, t3_adv = st.tabs([t('tab_mass'), t('tab_thermal'), t('tab_stability')])

    with t1_adv:
        st.subheader(t('hb_class'))
        cr1, cr2 = st.columns(2)
        with cr1:
            st.latex(t('hb_mb', mb=mb_dyn))
            st.caption(t('hb_caption_mb', mi=mi_val))
            st.latex(t('hb_s', s=s_dyn))
            st.caption(t('hb_caption_s', gsi=gsi_val))
        with cr2:
            # To'g'ri foiz: massa mustahkamligi = sigma_ci * s^a / sigma_ci = s^a da sigma3=0
            strength_red_perc = (1.0 - s_dyn ** a_dyn) * 100.0
            st.markdown(t('hb_interpret', gsi=gsi_val, perc=strength_red_perc))
            st.info(
                f"**Bieniawski (1989):** RMR ≈ GSI + 5 = {gsi_val + 5}. "
                f"Massiv sifati: {'Yaxshi' if gsi_val >= 60 else 'O‛rtacha' if gsi_val >= 40 else 'Yomon'}"
            )

    with t2_adv:
        st.subheader(t('thermal_params'))
        params_df = pd.DataFrame({
            t('param_table_param'): [t('modulus'), t('alpha'), t('temp0')],
            t('param_table_value'): [f"{E_MODULUS_R} MPa", f"{ALPHA_THERM} 1/°C", "20 °C"],
            t('param_table_reason'): [t('modulus_reason'), t('alpha_reason'), t('temp0_reason')]
        })
        st.table(params_df)
        st.markdown(t('ucs_decay'))
        st.latex(t('ucs_decay_eq', ucs=ucs_t_dyn))
        st.write(t('ucs_interpret', temp=T_source_max, perc=((1.0 - ucs_t_dyn / ucs_0_r) * 100.0)))
        st.markdown(t('thermal_stress'))
        st.latex(t('thermal_stress_eq', sigma=float(sigma_thermal.max())))

    with t3_adv:
        st.subheader(t('pillar_stability'))
        st.latex(t('fos_eq', fos=fos_final))
        st.write(t('pillar_wilson', w=rec_width, sv=sigma_v_tot, y=y_zone))
        st.markdown("---")
        st.write(t('references'))
        for ref_key in ['ref1', 'ref2', 'ref3', 'ref4', 'ref5', 'ref6']:
            st.markdown(f"📖 {t(ref_key)}")
        if fos_final < 1.3:
            st.error(t('conclusion_danger', fos=fos_final))
        else:
            st.success(t('conclusion_safe', fos=fos_final))

    st.markdown("---")
    with st.expander(t('methodology_expander')):
        st.markdown("#### Ushbu model quyidagi fundamental ilmiy ishlar asosida tuzilgan:")
        for ref_key in ['ref1', 'ref2', 'ref3', 'ref4', 'ref5', 'ref6']:
            st.write(t(ref_key))

# =========================== INTERACTIVE DASHBOARD ===========================

st.header("🕹️ Ultimate Interactive Dashboard (Real-time Animation)")
st.markdown("FOS, siljish maydoni va vaqt bo'yicha sirt siljishlarini interaktiv kuzatish.")

if 'displacement_2d' not in locals():
    sub_2d       = np.tile(sub_p.reshape(1, -1) * 100.0, (len(z_axis), 1))
    uplift_2d    = np.tile(uplift.reshape(1, -1),         (len(z_axis), 1))
    displacement_2d = np.sqrt(sub_2d ** 2 + uplift_2d ** 2) * (
        1.0 + 0.3 * np.random.rand(*sub_2d.shape)
    )

time_steps_dash = np.arange(0, time_h + 1, max(1, time_h // 20))
surface_x       = x_axis
surface_h_disp  = []
surface_v_disp  = []
for time_step in time_steps_dash:
    v_disp = (
        -s_max
        * np.exp(-(surface_x ** 2) / (2.0 * (total_depth / 2.0) ** 2))
        * (min(time_step, burn_duration) / burn_duration) * 100.0
    )
    h_disp = np.gradient(v_disp) * 0.5
    surface_v_disp.append(v_disp)
    surface_h_disp.append(h_disp)
surface_h_disp = np.array(surface_h_disp)
surface_v_disp = np.array(surface_v_disp)

col1_dash, col2_dash = st.columns(2)
with col1_dash:
    fos_thresh_dash = st.slider(
        "FOS Threshold (Yielded Zone)", 0.1, 2.0, 1.0, 0.05, key="fos_thresh_dash"
    )
with col2_dash:
    disp_cscale = st.selectbox(
        "Displacement Color Scale", ['Turbo', 'Viridis', 'Cividis'],
        index=0, key="disp_cscale"
    )


def draw_interactive_ucg_dashboard(
    x_axis: np.ndarray, z_axis: np.ndarray,
    fos_2d: np.ndarray, displacement_2d: np.ndarray,
    surface_x: np.ndarray,
    surface_h_disp: np.ndarray, surface_v_disp: np.ndarray,
    time_steps=None,
    fos_threshold: float = 1.0,
    disp_colorscale: str = 'Turbo',
) -> go.Figure:
    """4-panelli interaktiv UCG monitoring dashboardi."""
    if time_steps is None:
        time_steps = np.arange(surface_h_disp.shape[0])

    pillar_locations = np.linspace(x_axis.min() + 50, x_axis.max() - 50, 3)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "A) FOS & Yielded Zones",
            "B) Total Displacement (cm)",
            "C) Horizontal Surface Displacement",
            "D) Vertical Surface Displacement"
        ),
        horizontal_spacing=0.1, vertical_spacing=0.15
    )
    fig.add_trace(go.Heatmap(
        z=fos_2d, x=x_axis, y=z_axis,
        colorscale=[[0,'rgb(255,0,0)'],[0.33,'rgb(255,165,0)'],
                    [0.5,'rgb(173,255,47)'],[1,'rgb(0,128,0)']],
        zmin=0, zmax=3,
        colorbar=dict(title="FOS", x=0.45, y=0.78, thickness=12, len=0.42),
        name="FOS"
    ), row=1, col=1)
    mask_fos = np.where(fos_2d < fos_threshold, 1.0, np.nan)
    fig.add_trace(go.Heatmap(
        z=mask_fos, x=x_axis, y=z_axis,
        colorscale=[[0,'rgba(255,0,0,0.5)'],[1,'rgba(255,0,0,0.5)']],
        showscale=False, name="Yielded Zone"
    ), row=1, col=1)
    fig.add_trace(go.Heatmap(
        z=displacement_2d, x=x_axis, y=z_axis,
        colorscale=disp_colorscale,
        colorbar=dict(title="Disp (cm)", x=1.0, y=0.78, thickness=12, len=0.42),
        name="2D Disp"
    ), row=1, col=2)

    for i_ts, ts in enumerate(time_steps):
        fig.add_trace(go.Heatmap(
            z=surface_h_disp[i_ts:i_ts + 1, :], x=surface_x, y=[ts],
            colorscale='Turbo',
            zmin=float(np.min(surface_h_disp)), zmax=float(np.max(surface_h_disp)),
            showscale=False, visible=(i_ts == 0), name="H Disp"
        ), row=2, col=1)
        fig.add_trace(go.Heatmap(
            z=surface_v_disp[i_ts:i_ts + 1, :], x=surface_x, y=[ts],
            colorscale='Viridis',
            zmin=float(np.min(surface_v_disp)), zmax=float(np.max(surface_v_disp)),
            showscale=False, visible=(i_ts == 0), name="V Disp"
        ), row=2, col=2)

    for pos in pillar_locations:
        for r_loc in [1, 2]:
            fig.add_shape(
                type="rect", x0=pos - 25, x1=pos + 25,
                y0=total_depth * 0.8, y1=total_depth * 0.95,
                line=dict(color="Lime", width=3), row=1, col=r_loc
            )

    fig.update_layout(
        title=dict(text="Interactive UCG Monitoring Dashboard", x=0.5,
                   font=dict(size=22, color="white")),
        plot_bgcolor='black', paper_bgcolor='black', template='plotly_dark',
        height=900, showlegend=False, margin=dict(l=50, r=50, t=100, b=50)
    )
    fig.update_yaxes(autorange='reversed', row=1, col=1)
    fig.update_yaxes(autorange='reversed', row=1, col=2)
    return fig


dash_fig = draw_interactive_ucg_dashboard(
    x_axis=x_axis, z_axis=z_axis, fos_2d=fos_2d,
    displacement_2d=displacement_2d, surface_x=surface_x,
    surface_h_disp=surface_h_disp, surface_v_disp=surface_v_disp,
    time_steps=time_steps_dash,
    fos_threshold=fos_thresh_dash, disp_colorscale=disp_cscale
)
st.plotly_chart(dash_fig, use_container_width=True)

# =========================== BUG FIX (15): save_all – disk emas, BytesIO ===========================

with st.expander("💾 Modelni yuklab olish (In-Memory Export)", expanded=False):
    st.markdown("Modellar lokal diskga emas, xotiraga saqlanadi va brauzer orqali yuklab olinadi.")
    col_sv1, col_sv2 = st.columns(2)
    with col_sv1:
        if rf_model is not None:
            buf_rf = io.BytesIO()
            joblib.dump(rf_model, buf_rf)
            buf_rf.seek(0)
            st.download_button(
                "⬇️ RandomForest (.pkl)", data=buf_rf,
                file_name="rf_model.pkl", mime="application/octet-stream"
            )
        if scaler is not None:
            buf_sc = io.BytesIO()
            joblib.dump(scaler, buf_sc)
            buf_sc.seek(0)
            st.download_button(
                "⬇️ Scaler (.pkl)", data=buf_sc,
                file_name="scaler.pkl", mime="application/octet-stream"
            )
    with col_sv2:
        if PT_AVAILABLE and hybrid_model is not None:
            buf_pt = io.BytesIO()
            torch.save(hybrid_model.state_dict(), buf_pt)
            buf_pt.seek(0)
            st.download_button(
                "⬇️ HybridCollapseNet (.pt)", data=buf_pt,
                file_name="hybrid_model.pt", mime="application/octet-stream"
            )

# =========================== FASTAPI ===========================
if FASTAPI_AVAILABLE:
    _fastapi_app = FastAPI(title="UCG TM Monitoring API", version="2.0")

    @_fastapi_app.post("/predict")
    def predict_api(data: dict):
        """REST endpoint – kollapsa bashorat."""
        try:
            temp  = np.asarray(data["temp"],   dtype=float)
            s1    = np.asarray(data["sigma1"],  dtype=float)
            s3    = np.asarray(data["sigma3"],  dtype=float)
            d     = np.asarray(data["depth"],   dtype=float)
            feats = physics_features(temp, s1, s3, d)
            pred  = predict_collapse(hybrid_model, rf_model, scaler, feats)
            return {"collapse": pred.flatten().tolist()}
        except (KeyError, ValueError) as e:
            return {"error": str(e)}

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.write(f"**Tuzuvchi:** Saitov Dilshodbek")
st.sidebar.write(f"**Device:** {device}")
st.sidebar.write(f"**PyTorch:** {'✅' if PT_AVAILABLE else '❌'}")
st.sidebar.write(f"**SHAP:** {'✅' if SHAP_AVAILABLE else '❌'}")
st.sidebar.write(f"**SALib:** {'✅' if SALIB_AVAILABLE else '❌'}")
