import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress, norm
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

# =========================== FASTAPI IMPORT (xatolikka chidamli) ===========================
try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# =========================== PYTORCH IMPORT ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except:
    PT_AVAILABLE = False
    device = "cpu"

# =========================== SALib IMPORT ===========================
try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

# =========================== pyDOE IMPORT ===========================
try:
    from pyDOE import lhs
    PYDOE_AVAILABLE = True
except ImportError:
    PYDOE_AVAILABLE = False

# =========================== PyVista IMPORT ===========================
try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

# =========================== GLOBAL TRANSLATIONS ===========================
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
        'thermal_decay': "Thermal Decay (β):",
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
        'thermal_decay': "Thermal Decay (β):",
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

EPS = 1e-12

st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# Til tanlash
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

# Matematik metodologiya
st.sidebar.header(t('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(t('formula_show'), formula_opts)
if formula_option != formula_opts[0]:
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == formula_opts[1]:
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.latex(r"m_b = m_i \exp\left(\frac{GSI-100}{28-14D}\right); \quad s = \exp\left(\frac{GSI-100}{9-3D}\right)")
            st.latex(r"a = \frac{1}{2} + \frac{1}{6} \left( e^{-GSI/15} - e^{-20/3} \right)")
            st.info("**Hoek-Brown:** GSI va Disturbance (D) faktorlari asosida massiv mustahkamligini hisoblash.")
        elif formula_option == formula_opts[2]:
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
            st.latex(r"\sigma_{ci(T)} = \sigma_{ci} \cdot (1 - D(T))")
            st.latex(r"k = k_0 \left[ 1 + 20 \cdot D(T) + 50 \cdot V_{void} \right]")
            st.info("**Termal degradatsiya:** Harorat ta'sirida jins strukturasining emirilishi va o'tkazuvchanlik ortishi.")
        elif formula_option == formula_opts[3]:
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu} + \xi \cdot \nabla T")
            st.latex(r"\sigma_{t(T)} = \sigma_{t0} \cdot \exp\left(-\beta_{th} (T - 20)\right)")
            st.latex(r"FOS = \frac{\sigma_{limit}}{\sigma_{actual}}")
            st.info("**Termo-mexanika:** Termal kengayish kuchlanishi va cho'zilish mustahkamligining kamayishi.")
        elif formula_option == formula_opts[4]:
            st.latex(r"\sigma_{p} = (UCS \cdot \eta) \cdot \left( \frac{w}{H} \right)^{0.5}")
            st.latex(r"y = \frac{H}{2} \left( \sqrt{\frac{\sigma_v}{\sigma_p}} - 1 \right)")
            st.latex(r"S(x) = S_{max} \cdot \exp\left( -\frac{x^2}{2i^2} \right); \quad \epsilon = 1.52 \frac{S(x)}{R}")
            st.info("**Geomexanika:** Selek barqarorligi, plastik zona va yer yuzasining gorizontal deformatsiyasi.")

# Sidebar parametrlar
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

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

# Qatlam ma'lumotlari
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

# Harorat maydoni
@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20):
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
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam   = layers_data[-1]['t']
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20)

# Geomexanik hisob
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

def thermal_damage(T, beta=0.002):
    return 1 - np.exp(-beta * np.maximum(T - 100, 0))

stress_ratio = grid_sigma_v / (grid_ucs + EPS)
damage = thermal_damage(st.session_state.max_temp_map, beta=beta_thermal)
sigma_ci = grid_ucs * (1 - damage)

E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
dT_dx = np.gradient(temp_2d, axis=1, edge_order=2)
dT_dz = np.gradient(temp_2d, axis=0, edge_order=2)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)
sigma_thermal = CONSTRAINT_FACTOR * (
    E_MODULUS * ALPHA_T_COEFF * delta_T
) / (1 - nu_poisson + EPS)
sigma_thermal = np.clip(sigma_thermal, 0, sigma_ci * 0.3)
grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

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

def hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a):
    sigma3_safe = np.clip(sigma3, 1e-6, None)
    sigma_ci_safe = np.clip(sigma_ci, 1e-6, None)
    term = mb * sigma3_safe / (sigma_ci_safe + 1e-6) + s
    term = np.clip(term, 1e-6, 1e6)
    return sigma3_safe + sigma_ci_safe * (term ** a)

sigma1_limit = hoek_brown_sigma1(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)
shear_failure = sigma1_act >= sigma1_limit

strain_energy = sigma1_act * delta_T
spalling = tensile_failure & (temp_2d>400)
crushing = shear_failure & (temp_2d>600)
depth_factor = np.exp(-grid_z/(total_depth+EPS))
local_collapse_T = np.clip((st.session_state.max_temp_map-600)/300,0,1)
time_factor = np.clip((time_h-40)/60,0,1)
collapse_final = local_collapse_T * time_factor * (1-depth_factor)
void_mask_raw = spalling | crushing | (st.session_state.max_temp_map>900) | (strain_energy > 5000)
void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth>0.3) & (collapse_final>0.05)

phi = 0.05 + 0.4 * void_mask_permanent.astype(float)
perm = (phi**3) / ((1-phi+EPS)**2) * 1e-12
void_volume = np.sum(void_mask_permanent)*(x_axis[1]-x_axis[0])*(z_axis[1]-z_axis[0])
void_factor = np.where(void_mask_permanent, 0.1, 1.0)
sigma1_act *= void_factor
sigma3_act *= void_factor
sigma_ci *= void_factor

pressure = temp_2d*10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx, vz = -perm*dp_dx, -perm*dp_dz
gas_velocity = np.sqrt(vx**2+vz**2)

# =========================== AI MODEL ===========================
def physics_features(T, s1, s3, depth):
    dmg = thermal_damage(T)
    strength = 40 * (1 - dmg)
    fos = strength / (s1 + EPS)
    energy = T * s1 / (depth + 1)
    return np.column_stack([T, s1, s3, depth, dmg, fos, energy])

def generate_physics_dataset(temp_field, sigma1, sigma3, depth):
    feat = physics_features(temp_field.flatten(), sigma1.flatten(), sigma3.flatten(), depth.flatten())
    fos = feat[:,5]
    energy = feat[:,6]
    collapse = ((fos < 1.0) | (temp_field.flatten() > 800) | (energy > 4000)).astype(int)
    return feat, collapse

class CollapseNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(7,64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64,128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128,64), nn.ReLU(),
            nn.Linear(64,1), nn.Sigmoid()
        )
    def forward(self,x): return self.net(x)

class HybridCollapseNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(7, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, 1), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

def physics_loss(pred, sigma1, sigma_ci):
    fos = sigma_ci / (sigma1 + 1e-6)
    penalty = torch.mean((1 - fos) * pred)
    return penalty

def train_hybrid_model(X, y, sigma1, sigma_ci):
    model = HybridCollapseNet().to(device)
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    y_t = torch.tensor(y, dtype=torch.float32).view(-1,1).to(device)
    sigma1_t = torch.tensor(sigma1, dtype=torch.float32).to(device)
    sigma_ci_t = torch.tensor(sigma_ci, dtype=torch.float32).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=0.0003)
    for epoch in range(80):
        pred = model(X_t)
        bce = nn.BCELoss()(pred, y_t)
        phys = physics_loss(pred, sigma1_t, sigma_ci_t)
        loss = bce + 0.4 * phys
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model

def train_random_forest(X_scaled, y):
    rf = RandomForestClassifier(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_scaled, y)
    return rf

def save_all(model, rf, scaler):
    torch.save(model.state_dict(), "model.pt")
    joblib.dump(rf, "rf.pkl")
    joblib.dump(scaler, "scaler.pkl")

@st.cache_resource
def get_ensemble_model():
    if PT_AVAILABLE:
        try:
            X, y = generate_physics_dataset(temp_2d, sigma1_act, sigma3_act, grid_z)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            model = train_hybrid_model(X_scaled, y, sigma1_act.flatten(), sigma_ci.flatten())
            rf = train_random_forest(X_scaled, y)
            kf = KFold(n_splits=5)
            scores = []
            for train_idx, test_idx in kf.split(X_scaled):
                rf.fit(X_scaled[train_idx], y[train_idx])
                pred = rf.predict_proba(X_scaled[test_idx])[:,1]
                scores.append(roc_auc_score(y[test_idx], pred))
            st.write("Model AUC:", np.mean(scores))
            save_all(model, rf, scaler)
            return model, rf, scaler
        except Exception as e:
            st.error(f"Model training error: {str(e)}")
            return None, None, None
    else:
        return None, None, None

hybrid_model, rf_model, scaler = get_ensemble_model()

def predict_collapse(model, rf, scaler, X_raw):
    if model is None or rf is None:
        return np.zeros((X_raw.shape[0], 1))
    X_scaled = scaler.transform(X_raw)
    with torch.no_grad():
        nn_pred = model(torch.tensor(X_scaled, dtype=torch.float32).to(device)).cpu().numpy()
    rf_pred = rf.predict_proba(X_scaled)[:,1].reshape(-1,1)
    return 0.6*nn_pred + 0.4*rf_pred

collapse_pred = np.zeros_like(temp_2d)
if hybrid_model is not None:
    feat_pred = physics_features(temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten())
    try:
        collapse_pred = predict_collapse(hybrid_model, rf_model, scaler, feat_pred).reshape(temp_2d.shape)
    except Exception as e:
        st.error(f"Collapse prediction error: {str(e)}")
else:
    st.warning(t('warning_pytorch'))
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai)) > 1:
        rf_backup = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
        rf_backup.fit(X_ai, y_ai)
        collapse_pred = rf_backup.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
    else:
        collapse_pred = np.zeros_like(temp_2d)

# Selek optimizatsiyasi
avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
strength_red = np.exp(-0.0025*(avg_t_p-20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()
w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam*strength_red)*(w_sol/(H_seam+EPS))**0.5
    y_zone_calc = (H_seam/2)*(np.sqrt(sv_seam/(p_strength+EPS))-1)
    new_w = 2*max(y_zone_calc,1.5)+0.5*H_seam
    if abs(new_w-w_sol) < 0.1: break
    w_sol = new_w
rec_width = np.round(w_sol, 1)
pillar_strength = p_strength
y_zone = max(y_zone_calc, 1.5)

fos_2d = np.clip(sigma1_limit/(sigma1_act+EPS), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0.0, fos_2d)
void_frac_base = float(np.mean(void_mask_permanent))

def optimize_pillar_ai(w_arr):
    w = w_arr[0]
    strength = (ucs_seam*strength_red)*(w/(H_seam+EPS))**0.5
    risk = void_frac_base * np.exp(-0.01*(w-rec_width))
    return -(strength - 15.0*risk)
try:
    opt_result = minimize(optimize_pillar_ai, x0=[rec_width], bounds=[(5.0,100.0)], method='SLSQP')
    optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except:
    optimal_width_ai = rec_width

st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

# Cho‘kish va Hoek-Brown
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5,1.5,2])
s_max = (H_seam*0.04)*(min(time_h,120)/120)
sub_p = -s_max * np.exp(-(x_axis**2)/(2*(total_depth/2)**2))
uplift = (total_depth*1e-4)*np.exp(-(x_axis**2)/(total_depth*10))*(time_h/150)*100
with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta',width=3))).update_layout(title=t('subsidence_title'), template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy', line=dict(color='cyan',width=3))).update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam*(mb_s*sigma3_ax/(ucs_seam+EPS)+s_s)**a_s
    ucs_burn = ucs_seam*np.exp(-0.0025*(T_source_max-20))
    s1_burning = sigma3_ax + ucs_burn*(mb_s*sigma3_ax/(ucs_burn+EPS)+s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam*strength_red)*(mb_s*sigma3_ax/(ucs_seam*strength_red+EPS)+s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red',width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name=t('tensile_hb'), line=dict(color='cyan',width=2,dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name=t('combustion'), line=dict(color='orange',width=4)))
    st.plotly_chart(fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")), use_container_width=True)

# TM maydoni va quduqlar
st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_layers.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Quduqlar konfiguratsiyasi")
well_distance = st.sidebar.slider("Quduqlar orasidagi masofa (m):", 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")

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
    layer_bounds = [(l['z_start'], l['z_start'] + l['t'], l) for l in layers_data]
    sigma_v_coal = 0.0
    for l in layers_data[:-1]:
        sigma_v_coal += l['rho'] * 9.81 * l['t']
    sigma_v_coal += rho_coal * 9.81 * (h_seam / 2)
    sigma_v_coal = sigma_v_coal / 1e6
    Hc = h_seam * np.sqrt(sigma_v_coal / (coal_layer['ucs'] + 1e-5))
    Hc = np.clip(Hc, h_seam, h_seam * 4)
    states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
    stage = st.select_slider("Bosqichni tanlang:", options=[1, 2, 3], value=1, key="ucg_stage_132")
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
                    th_vals = (E * alpha * delta_T_m[local_thermal]) / (1 - nu)
                    sigma_th[local_thermal] = np.clip(th_vals, 0, sigma_ci_T[local_thermal] * 0.25)
                sigma_1 = sigma_v + sigma_th
                term = mb * sigma_3 / (sigma_ci_T + 1e5) + s_hb
                term = np.clip(term, 1e-6, 1e6)
                sigma_limit = sigma_3 + sigma_ci_T * (term)**a_hb
                fos_val = np.clip(sigma_limit / (sigma_1 + 1e6), 0, 3)
                yield_mask = sigma_1 > (sigma_limit * 0.85)
                fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
                fos_sub = fos[mask]
                fos_sub = np.minimum(fos_sub, fos_val)
                fos[mask] = fos_sub
                if layer == layers_data[-1]:
                    dome_width = (cavity_width / 2) * np.clip(1 - dz[mask] / (Hc + 1e-5), 0, 1)
                    failure_zone = fos_val < 1.2
                    dome_condition = (dz[mask] > 0) & (dz[mask] < Hc) & (np.abs(grid_x[mask] - px) < dome_width) & failure_zone
                    if np.any(dome_condition):
                        decay = np.clip(1 - (dz[mask][dome_condition] / (Hc + 1e-5)), 0.3, 1.0)
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
            fos_pillar = pillar_strength / (sigma_v_coal_pa + 1e5)
            pillar_zone = (np.abs(grid_x - well_x[1]) < selek_eni/2) & (np.abs(grid_z - source_z) < h_seam)
            fos[pillar_zone] = np.maximum(fos[pillar_zone], fos_pillar)
        fos = np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)
        return fos

    source_z_adv = total_depth - (h_seam / 2)
    fos_stage = compute_advanced_fos(
        grid_x, grid_z, active_wells, well_x, source_z_adv, h_seam, cavity_width,
        temp_2d, grid_sigma_v, layers_data, layer_bounds,
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
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name="AI Collapse"), row=2, col=1)
    shear_disp = np.copy(shear_failure); shear_disp[void_mask_permanent]=False
    tens_disp = np.copy(tensile_failure); tens_disp[void_mask_permanent]=False
    fig_tm.add_trace(go.Scatter(x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2], mode='markers', marker=dict(color='red',size=3,symbol='x'), name='Shear'), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2], mode='markers', marker=dict(color='blue',size=3,symbol='cross'), name='Tensile'), row=2, col=1)
    void_visual = np.where(void_mask_permanent>0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis, colorscale=[[0,'black'],[1,'black']], showscale=False, opacity=0.8, hoverinfo='skip'), row=2, col=1)
    fig_tm.add_shape(type="line", x0=x_axis.min(), x1=x_axis.max(), y0=source_z_adv-h_seam/2, y1=source_z_adv-h_seam/2,
                     line=dict(color="white", width=2, dash="dash"), row=2, col=1)
    fig_tm.add_shape(type="line", x0=x_axis.min(), x1=x_axis.max(), y0=source_z_adv+h_seam/2, y1=source_z_adv+h_seam/2,
                     line=dict(color="white", width=2, dash="dash"), row=2, col=1)
    zoom_margin = h_seam * 12
    fig_tm.update_layout(template="plotly_dark", height=900, margin=dict(r=150,t=80,b=100),
                         showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    fig_tm.update_yaxes(range=[source_z_adv + zoom_margin/2, source_z_adv - zoom_margin], row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox("Avtomatik animatsiya (1→2→3 bosqichlar)"):
        anim_placeholder = st.empty()
        for s in [1, 2, 3]:
            wells_s = states_132[s]
            fos_s = compute_advanced_fos(
                grid_x, grid_z, wells_s, well_x, source_z_adv, h_seam, cavity_width,
                temp_2d, grid_sigma_v, layers_data, layer_bounds,
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
        2: f"**2-Bosqich (Muhim):** O‘ng quduq yoqilgan. O‘rtadagi selek tomni ushlab turadi. Selek eni = {selek_eni:.1f} m.",
        3: f"**3-Bosqich:** Markaziy selek gazlashtirilmoqda. Barqaror cho‘kish."
    }
    st.info(msgs[stage])
    if selek_eni < 18.5:
        st.error(f"⚠️ KRITIK: Selek o'lchami ({selek_eni:.1f} m) xavfsiz chegaradan past!")
    else:
        st.success(f"✅ BARQAROR: Selek o'lchami ({selek_eni:.1f} m) me'yorda.")

# =========================== QO‘SHIMCHALAR ===========================
# Sobol sezgirlik (SALib)
if SALIB_AVAILABLE:
    with st.expander("📊 Global sezgirlik tahlili (Sobol')"):
        st.markdown("Kirish parametrlarining model chiqishiga umumiy ta’siri (birinchi va umumiy tartib indekslari).")
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

# LHS (pyDOE) va collapse ehtimolligi
if PYDOE_AVAILABLE:
    with st.expander("🎲 Latin Hypercube Sampling (Collapse ehtimolligi)"):
        N = 5000
        lhs_sample = lhs(3, samples=N)
        T_lhs = norm.ppf(lhs_sample[:,0], loc=800, scale=100)
        UCS_lhs = norm.ppf(lhs_sample[:,1], loc=40, scale=10)
        Depth_lhs = norm.ppf(lhs_sample[:,2], loc=200, scale=50)
        collapse_prob = 1 / (1 + np.exp(-(T_lhs/100 + Depth_lhs/200 - UCS_lhs/50)))
        fig_lhs = go.Figure(go.Histogram(x=collapse_prob, nbinsx=50, marker_color='orange'))
        fig_lhs.update_layout(title="Collapse ehtimolligi taqsimoti", template='plotly_dark')
        st.plotly_chart(fig_lhs, use_container_width=True)
        ci_low = np.percentile(collapse_prob, 5)
        ci_high = np.percentile(collapse_prob, 95)
        st.write(f"90% ishonch intervali: [{ci_low:.3f}, {ci_high:.3f}]")

# 3D hajm (PyVista yoki plotly)
if PYVISTA_AVAILABLE:
    with st.expander("🌋 3D litologik hajm (PyVista)"):
        try:
            grid_pv = pv.UniformGrid()
            grid_pv.dimensions = (50, 50, 30)
            values = np.random.rand(50*50*30)
            grid_pv["lithology"] = values
            plotter = pv.Plotter()
            plotter.add_volume(grid_pv, cmap="viridis")
            # Streamlitda stpyvista kerak, shuning uchun oddiy plot ko'rsatamiz
            st.image(plotter.screenshot(), use_container_width=True)
        except Exception as e:
            st.warning(f"PyVista vizualizatsiyasi amalga oshmadi: {e}")
else:
    with st.expander("🌋 3D hajm (plotly)"):
        st.info("PyVista mavjud emas, plotly orqali sodda hajm ko‘rinishi.")
        # Oddiy 3D hajm o‘rniga heatmap
        fig_vol = go.Figure(data=go.Volume(
            x=grid_x.flatten(), y=np.zeros_like(grid_x.flatten()), z=grid_z.flatten(),
            value=temp_2d.flatten(),
            isomin=100, isomax=800,
            opacity=0.1, surface_count=20, colorscale='Hot'))
        fig_vol.update_layout(title="Harorat hajmi (proxy)", height=500)
        st.plotly_chart(fig_vol, use_container_width=True)

# Dinamik risk indeksi va entropiya
weights = np.array([0.4, 0.3, 0.2, 0.1])  # expert-based
risk_index = (
    weights[0]*collapse_pred +
    weights[1]*(1-fos_2d) +
    weights[2]*perm/np.max(perm) +
    weights[3]*(temp_2d/np.max(temp_2d))
)
p = risk_index / np.sum(risk_index + 1e-12)
entropy = -np.sum(p * np.log(p + 1e-12))
st.metric("Tizim entropiyasi (noaniqlik)", f"{entropy:.3f}")

# Real-time harorat animatsiyasi
placeholder = st.empty()
if st.button("Harorat dinamik animatsiyasini ishga tushirish"):
    for t_anim in range(100):
        temp_dynamic = temp_2d + np.sin(t_anim/5)*50
        fig_anim = go.Figure(data=go.Heatmap(z=temp_dynamic, x=x_axis, y=z_axis, colorscale='Hot'))
        fig_anim.update_layout(title=f"Vaqt qadami {t_anim}", template='plotly_dark')
        placeholder.plotly_chart(fig_anim, use_container_width=True)
        time.sleep(0.1)

# Sensor API so‘rovi (simulyatsiya)
st.markdown("---")
st.subheader("📡 Tashqi sensor API ulanishi")
try:
    response = requests.get("http://sensor-api/data", timeout=5)
    if response.status_code == 200:
        data = response.json()
        st.success("Sensor ma'lumotlari olindi!")
        st.json(data)
        # sensor ma'lumotlarini integratsiya qilish
        # misol uchun:
        final_risk = (
            collapse_pred * 0.35 +
            (1/fos_2d) * 0.25 +
            (perm/np.max(perm)) * 0.2 +
            (temp_2d/np.max(temp_2d)) * 0.2
        )
        uncertainty = np.std(final_risk)
        sensitivity = Si['ST'] if SALIB_AVAILABLE else "SALib mavjud emas"
        st.write(f"Yakuniy risk noaniqligi: {uncertainty:.4f}")
        st.write("Sezgirlik:", sensitivity)
    else:
        st.warning("Sensor API javob bermadi.")
except:
    st.info("Sensor API hozirda ulanmagan (simulyatsiya).")

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")

# FASTAPI (agar kerak bo'lsa)
if FASTAPI_AVAILABLE:
    app = FastAPI()
    @app.post("/predict")
    def predict_api(data: dict):
        temp = np.array(data["temp"])
        s1   = np.array(data["sigma1"])
        s3   = np.array(data["sigma3"])
        d    = np.array(data["depth"])
        features = physics_features(temp, s1, s3, d)
        pred = hybrid_model(torch.tensor(features, dtype=torch.float32).to(device))
        return {"collapse": pred.detach().cpu().numpy().tolist()}
