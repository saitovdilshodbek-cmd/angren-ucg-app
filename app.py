"""
UCG ULTIMATE DIGITAL TWIN
Barcha modullar bitta faylda (modullashtirilgan versiya alohida fayllarda ham mavjud)
Streamlit ilovasi – Yer yuzasi deformatsiyasi monitoringi, AI, Digital Twin, Real-time 3D, ISO hisobot
"""

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
import warnings
import json
import threading
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import joblib
import requests
from datetime import datetime

# Machine Learning
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import IsolationForest

# Deep Learning (optional)
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    PT_AVAILABLE = False
    device = "cpu"

# Database (optional)
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    import psycopg2
    PG_AVAILABLE = True
except ImportError:
    PG_AVAILABLE = False

# MQTT (optional)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# 3D (optional)
try:
    import pyvista as pv
    PV_AVAILABLE = True
except ImportError:
    PV_AVAILABLE = False

# Word report
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

warnings.filterwarnings('ignore')

# ========================== GLOBAL CONSTANTS ==========================
EPS = 1e-12
APP_URL = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app"

# ========================== TRANSLATIONS ==========================
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

# ========================== UTILS ==========================
def generate_qr(link):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ========================== PHYSICS (improved from PRO CORE) ==========================
def thermal_damage(T):
    """Termal damage indeksi (0..0.95)"""
    if T < 100:
        return 0.0
    elif T < 400:
        return 0.1 * (T - 100) / 300
    elif T < 800:
        return 0.1 + 0.4 * (T - 400) / 400
    else:
        return min(0.95, 0.5 + 0.45 * (T - 800) / 400)

def calc_vertical_stress(depth, density=2500):
    gamma = density * 9.81 / 1e6  # MPa/m
    return gamma * depth

def hoek_brown_strength(ucs, gsi, mi, D, sigma3=0):
    mb = mi * np.exp((gsi - 100) / (28 - 14 * D))
    s = np.exp((gsi - 100) / (9 - 3 * D))
    a = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
    return sigma3 + ucs * (mb * sigma3 / ucs + s)**a

def improved_fos(ucs, gsi, mi, D, nu, T, depth, H_seam):
    """Termal degradatsiya va Hoek-Brown asosida FOS"""
    damage = thermal_damage(T)
    ucs_eff = ucs * (1 - damage)
    sigma_strength = hoek_brown_strength(ucs_eff, gsi, mi, D, sigma3=0)
    sigma_v = calc_vertical_stress(depth)
    pillar_effect = (20 / (H_seam + EPS))**0.5
    fos = (sigma_strength * pillar_effect) / (sigma_v + EPS)
    return np.clip(fos, 0, 5)

# ========================== SIMULATION (Temperature field) ==========================
@st.cache_data(show_spinner=False, max_entries=50)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20):
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
    z_axis = np.linspace(0, total_depth + 50, grid_shape[0])
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
    alpha_rock = 1.0e-6
    v_burn = 0.02  # m/s yonish tezligi
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
    # Diffuziya
    DX, DT = 1.0, 0.1
    Q_heat = np.zeros_like(temp_2d)
    for _ in range(n_steps):
        Tn = temp_2d.copy()
        Tn[1:-1,1:-1] = (temp_2d[1:-1,1:-1] + alpha_rock*DT*((temp_2d[2:,1:-1]-2*temp_2d[1:-1,1:-1]+temp_2d[:-2,1:-1])/(DX**2+EPS) +
                         (temp_2d[1:-1,2:]-2*temp_2d[1:-1,1:-1]+temp_2d[1:-1,:-2])/(DX**2+EPS)) + Q_heat[1:-1,1:-1]*DT)
        temp_2d = Tn
    return temp_2d, x_axis, z_axis, grid_x, grid_z

# ========================== GEOMECHANICS (full from first code) ==========================
def compute_geomechanics(layers_data, grid_z, grid_x, temp_2d, D_factor, nu_poisson, k_ratio,
                         tensile_mode, tensile_ratio, beta_thermal, total_depth, EPS):
    # Qatlamlar bo'yicha sigma_v, ucs, mb, s, a, sigma_t0_manual
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

    # Maksimal harorat xaritasi (kumulyativ)
    if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
        st.session_state.max_temp_map = np.ones_like(grid_z)*25
    st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
    delta_T = temp_2d - 25.0

    temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
    damage = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
    sigma_ci = grid_ucs * (1 - damage)

    E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
    dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
    thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)
    sigma_thermal = CONSTRAINT_FACTOR*(E_MODULUS*ALPHA_T_COEFF*delta_T)/(1-nu_poisson+EPS) + 0.3*thermal_gradient
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
    sigma3_safe = np.maximum(sigma3_act, 0.01)
    sigma1_limit = sigma3_safe + sigma_ci*(grid_mb*sigma3_safe/(sigma_ci+EPS)+grid_s_hb)**grid_a_hb
    shear_failure = sigma1_act >= sigma1_limit

    spalling = tensile_failure & (temp_2d>400)
    crushing = shear_failure & (temp_2d>600)
    depth_factor = np.exp(-grid_z/(total_depth+EPS))
    local_collapse_T = np.clip((st.session_state.max_temp_map-600)/300,0,1)
    time_factor = np.clip((st.session_state.get('time_h', 24)-40)/60,0,1)
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

    fos_2d = np.clip(sigma1_limit/(sigma1_act+EPS),0,3.0)
    fos_2d = np.where(void_mask_permanent,0.0,fos_2d)

    return {
        'sigma1': sigma1_act, 'sigma3': sigma3_act, 'fos': fos_2d,
        'void': void_mask_permanent, 'perm': perm, 'gas_velocity': gas_velocity,
        'damage': damage, 'sigma_ci': sigma_ci, 'sigma1_limit': sigma1_limit,
        'void_volume': void_volume
    }

# ========================== AI MODELS ==========================
@st.cache_resource(show_spinner=False)
def load_ai_fos_model():
    """RandomForestRegressor for FOS prediction (temp, stress, ucs)"""
    def generate_training_data(n=500):
        X, y = [], []
        for _ in range(n):
            temp = np.random.uniform(100, 1200)
            stress = np.random.uniform(2, 20)
            ucs = np.random.uniform(10, 80)
            fos = ucs / (stress + 0.01) * np.exp(-0.001*(temp-20))
            X.append([temp, stress, ucs])
            y.append(fos)
        return np.array(X), np.array(y)
    X, y = generate_training_data()
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

@st.cache_resource(show_spinner=False)
def get_nn_collapse_model():
    if not PT_AVAILABLE:
        return None
    class CollapseNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(4,32), nn.ReLU(), nn.Linear(32,64), nn.ReLU(), nn.Linear(64,1), nn.Sigmoid())
        def forward(self,x): return self.net(x)
    # Generate synthetic dataset
    def generate_ucg_dataset(n=10000):
        data = []
        for _ in range(n):
            T = np.random.uniform(20,1000)
            s1 = np.random.uniform(0,50)
            s3 = np.random.uniform(0,30)
            d = np.random.uniform(0,300)
            damage = 1 - np.exp(-0.002*max(T-100,0))
            strength = 40*(1-damage)
            collapse = 1 if (s1>strength or T>700) else 0
            data.append([T,s1,s3,d,collapse])
        return np.array(data)
    data = generate_ucg_dataset()
    X = torch.tensor(data[:,:-1], dtype=torch.float32)
    y = torch.tensor(data[:,-1], dtype=torch.float32).view(-1,1)
    model = CollapseNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.BCELoss()
    for epoch in range(50):
        pred = model(X)
        loss = loss_fn(pred, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    model.eval()
    return model

def predict_nn_collapse(model, temp, s1, s3, depth):
    if model is None:
        return np.zeros_like(temp)
    X = np.column_stack([temp.flatten(), s1.flatten(), s3.flatten(), depth.flatten()])
    X_t = torch.tensor(X, dtype=torch.float32)
    with torch.no_grad():
        pred = model(X_t).numpy()
    return pred.reshape(temp.shape)

# ========================== PILLAR OPTIMIZATION ==========================
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

# ========================== DATABASE (SQLite) ==========================
def init_db():
    if not SQLITE_AVAILABLE:
        return
    conn = sqlite3.connect("ucg_monitor.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            temperature REAL,
            stress REAL,
            pressure REAL,
            fos REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_data(temp, stress, pressure, fos):
    if not SQLITE_AVAILABLE:
        return
    conn = sqlite3.connect("ucg_monitor.db")
    c = conn.cursor()
    c.execute("INSERT INTO monitoring (time, temperature, stress, pressure, fos) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().isoformat(), temp, stress, pressure, fos))
    conn.commit()
    conn.close()

init_db()

# ========================== DIGITAL TWIN CLASS ==========================
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

# ========================== ISO REPORT GENERATOR ==========================
def generate_full_iso_report(obj_name, lang, layers_data, T_source_max, burn_duration,
                             pillar_strength, optimal_width_ai, fos_2d, risk_map,
                             prepared_by, approved_by, doc_number, revision, fig_bytes=None):
    texts = {
        'uz': {
            'h1': "ISO 9001:2015 MUVOFIQDAT HISOBOTI",
            'sec1': "1. LOYIHA UMUMIY TAVSIFI",
            'sec2': "2. GEOMEXANIK QATLAMLAR VA XOSSALARI",
            'sec3': "3. BARQARORLIK VA PILLAR DIZAYNI",
            'sec4': "4. XAVFNI BAHOLASH (RISK ASSESSMENT)",
            'sec5': "5. MUHANDISLIK XULOSASI VA TAVSIYALAR",
            'fos_label': "Xavfsizlik koeffitsienti (FOS):",
            'ai_label': "AI tomonidan optimallashtirilgan kenglik:",
            'conclusion_title': "Yakuniy qaror:",
            'safe': "✅ TIZIM BARQAROR: Loyiha parametrlari xavfsizlik talablariga javob beradi.",
            'warning': "⚠️ MARGINAL HOLAT: Monitoringni kuchaytirish va qo'shimcha mahkamlash tavsiya etiladi.",
            'danger': "🚨 XAVFLI: O'pirilish xafvi yuqori! Pillar kengligini oshirish yoki termal yukni kamaytirish shart."
        },
        'en': {
            'h1': "ISO 9001:2015 COMPLIANCE REPORT",
            'sec1': "1. PROJECT OVERVIEW",
            'sec2': "2. GEOMECHANICAL PROPERTIES",
            'sec3': "3. STABILITY AND PILLAR DESIGN",
            'sec4': "4. RISK ASSESSMENT",
            'sec5': "5. ENGINEERING CONCLUSIONS",
            'fos_label': "Factor of Safety (FOS):",
            'ai_label': "AI Optimized Width:",
            'conclusion_title': "Final Decision:",
            'safe': "✅ SYSTEM STABLE: Project parameters meet safety requirements.",
            'warning': "⚠️ MARGINAL STABILITY: Increased monitoring and support recommended.",
            'danger': "🚨 DANGEROUS: High risk of collapse! Increase pillar width or reduce thermal load."
        }
    }
    t_text = texts.get(lang, texts['en'])
    doc = Document()
    doc.add_heading(f"{t_text['h1']}\n{obj_name}", level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.style = 'Table Grid'
    meta_table.cell(0,0).text = f"Doc No: {doc_number}"
    meta_table.cell(0,1).text = f"Revision: {revision}"
    meta_table.cell(1,0).text = f"Prepared: {prepared_by}"
    meta_table.cell(1,1).text = f"Approved: {approved_by}"
    doc.add_heading(t_text['sec1'], level=2)
    doc.add_paragraph(f"Ob'ekt nomi: {obj_name}\nMaksimal harorat: {T_source_max} °C\nYonish davomiyligi: {burn_duration} soat")
    doc.add_heading(t_text['sec2'], level=2)
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    for i, h in enumerate(["Layer Name", "Thick (m)", "UCS (MPa)", "GSI", "mi"]):
        table.rows[0].cells[i].text = h
    for layer in layers_data:
        row = table.add_row().cells
        row[0].text = layer['name']
        row[1].text = f"{layer['t']:.1f}"
        row[2].text = f"{layer['ucs']:.1f}"
        row[3].text = str(layer['gsi'])
        row[4].text = f"{layer['mi']:.1f}"
    if fig_bytes:
        doc.add_heading("Visual Analysis", level=2)
        image_stream = io.BytesIO(fig_bytes)
        doc.add_picture(image_stream, width=Inches(5.5))
    doc.add_heading(t_text['sec5'], level=2)
    fos_val = np.nanmean(fos_2d)
    if fos_val < 1.1:
        conclusion_text = t_text['danger']
        color = RGBColor(255,0,0)
    elif fos_val < 1.5:
        conclusion_text = t_text['warning']
        color = RGBColor(255,165,0)
    else:
        conclusion_text = t_text['safe']
        color = RGBColor(0,128,0)
    p = doc.add_paragraph()
    p.add_run(f"{t_text['fos_label']} {fos_val:.2f}\n").bold = True
    p.add_run(f"{t_text['ai_label']} {optimal_width_ai:.1f} m\n\n")
    final_run = p.add_run(f"{t_text['conclusion_title']}\n{conclusion_text}")
    final_run.bold = True
    final_run.font.color.rgb = color
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# ========================== MAIN STREAMLIT APP ==========================
st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# Language
if 'language' not in st.session_state:
    st.session_state.language = 'uz'
LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# QR Code
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Mobil ilovaga o'tish")
qr_img_bytes = generate_qr(APP_URL)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

# Sidebar Parameters
st.sidebar.header(t('sidebar_header_params'))
formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(t('formula_show'), formula_opts)
if formula_option != formula_opts[0]:
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == formula_opts[1]:
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.latex(r"m_b = m_i \exp\left(\frac{GSI-100}{28-14D}\right); \quad s = \exp\left(\frac{GSI-100}{9-3D}\right)")
        elif formula_option == formula_opts[2]:
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
        elif formula_option == formula_opts[3]:
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu} + \xi \cdot \nabla T")
        elif formula_option == formula_opts[4]:
            st.latex(r"\sigma_{p} = (UCS \cdot \eta) \cdot \left( \frac{w}{H} \right)^{0.5}")

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

# Layers input
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(t('layer_params', num=i+1), expanded=(i == int(num_layers)-1)):
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

# Validation
for lyr in layers_data:
    if lyr['t'] <= 0: st.error(t('error_thick_positive')); st.stop()
    if lyr['ucs'] <= 0: st.error(t('error_ucs_positive')); st.stop()
    if lyr['rho'] <= 0: st.error(t('error_density_positive')); st.stop()
    if not (10 <= lyr['gsi'] <= 100): st.error(t('error_gsi_range')); st.stop()
    if lyr['mi'] <= 0: st.error(t('error_mi_positive')); st.stop()
if not layers_data: st.error(t('error_min_layers')); st.stop()

# Compute temperature field
grid_shape = (80, 100)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20)
st.session_state.time_h = time_h  # for geomechanics

# Geomechanics
geo = compute_geomechanics(layers_data, grid_z, grid_x, temp_2d, D_factor, nu_poisson, k_ratio,
                           tensile_mode, tensile_ratio, beta_thermal, total_depth, EPS)

sigma1_act = geo['sigma1']
sigma3_act = geo['sigma3']
fos_2d = geo['fos']
void_mask_permanent = geo['void']
perm = geo['perm']
gas_velocity = geo['gas_velocity']
damage = geo['damage']
void_volume = geo['void_volume']

# AI Collapse prediction
nn_model = get_nn_collapse_model()
if nn_model is not None and PT_AVAILABLE:
    collapse_pred = predict_nn_collapse(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)
else:
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai)) > 1:
        rf_clf = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42)
        rf_clf.fit(X_ai, y_ai)
        collapse_pred = rf_clf.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
    else:
        collapse_pred = np.zeros_like(temp_2d)

# Pillar optimization
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

# Metrics row
st.subheader(t('monitoring_header', obj_name=obj_name))
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

# Subsidence and Hoek-Brown plots
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
    mb_s, s_s, a_s = geo['sigma1_limit'].max()/ucs_seam, 0.1, 0.5  # approximate
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

# TM Field (temperature + FOS + collapse)
st.markdown("---")
c1, c2 = st.columns([1,2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_s = go.Figure()
    for lyr in layers_data:
        fig_s.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False)
    st.plotly_chart(fig_s, use_container_width=True)
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
    fig_tm.add_trace(go.Contour(z=void_mask_permanent.astype(int), x=x_axis, y=z_axis, showscale=False,
                                contours=dict(coloring='lines'), line=dict(color='white',width=2)), row=2, col=1)
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name=t('ai_collapse')), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(r=150,t=80,b=100), showlegend=True,
                         legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# Live Monitoring Tab
st.header("🔄 Live 3D Monitoring (Real-time)")
tab_live, tab_ai_orig, tab_advanced = st.tabs([t('live_monitoring_tab'), t('ai_monitor_title'), t('advanced_analysis')])

with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies and alerts")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    run_live = st.button("▶️ Run Live Monitoring", key="run_live")
    stop_live = st.button("⏹ Stop Monitoring", key="stop_live")
    if 'stop_flag_live' not in st.session_state: st.session_state.stop_flag_live = False
    if stop_live: st.session_state.stop_flag_live = True
    col_live1, col_live2 = st.columns(2)
    subs_plot_live = col_live1.empty(); temp_plot_live = col_live2.empty()
    col_live3, col_live4 = st.columns(2)
    pillar_plot_live = col_live3.empty(); trend_plot_live = col_live4.empty()
    surface_3d_plot_live = st.empty(); alert_box_live = st.empty()
    if 'live_history_df' not in st.session_state:
        st.session_state.live_history_df = pd.DataFrame(columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m'])
    if run_live:
        st.session_state.stop_flag_live = False
        X_live = np.linspace(-20,20,50); Y_live = np.linspace(-20,20,50); X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_history_live = []; fos_history_live = []; width_history_live = []; temp_history_live = []; steps_done = 0
        rf_live = RandomForestRegressor(n_estimators=10, random_state=42)
        dummy_X = np.random.rand(10,3); dummy_y = np.random.rand(10); rf_live.fit(dummy_X, dummy_y)
        for t_step in range(TIME_STEPS):
            if st.session_state.stop_flag_live: break
            Z_subs = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*(5+t_step*0.1)**2))*5*t_step/TIME_STEPS
            Z_temp = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*8**2))*T_source_max*t_step/TIME_STEPS
            Z_filtered = gaussian_filter(Z_subs, sigma=1); anomalies = Z_subs-Z_filtered; anomaly_points = np.where(np.abs(anomalies)>0.2)
            avg_ucs = np.mean([l['ucs'] for l in layers_data])
            X_feat = np.array([[burn_duration, T_source_max, avg_ucs]]).reshape(1,-1)
            pillar_width_pred = rf_live.predict(X_feat)[0]
            FOS_live = np.clip(2.5 - t_step*0.03, 0.8, 2.5)
            mean_subs = np.mean(Z_subs)
            subs_history_live.append(mean_subs); fos_history_live.append(FOS_live); width_history_live.append(pillar_width_pred); temp_history_live.append(np.mean(Z_temp))
            new_row = pd.DataFrame({'step':[t_step+1],'mean_subsidence_cm':[mean_subs*100],'max_temp_c':[np.max(Z_temp)],'FOS':[FOS_live],'pillar_width_m':[pillar_width_pred]})
            st.session_state.live_history_df = pd.concat([st.session_state.live_history_df, new_row], ignore_index=True).tail(1000)
            fig_subs = go.Figure(go.Heatmap(z=Z_subs*100, x=X_live, y=Y_live, colorscale='Viridis')).update_layout(title='Surface Subsidence (cm)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            subs_plot_live.plotly_chart(fig_subs, use_container_width=True, key=f"subs_{t_step}")
            fig_temp = go.Figure(go.Heatmap(z=Z_temp, x=X_live, y=Y_live, colorscale='Hot')).update_layout(title='Temperature Field (°C)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            temp_plot_live.plotly_chart(fig_temp, use_container_width=True, key=f"temp_{t_step}")
            pillar_plot_live.metric(label="Recommended Pillar Width (m)", value=f"{pillar_width_pred:.2f}", delta=f"FOS = {FOS_live:.2f}")
            trend_fig = go.Figure(go.Scatter(y=subs_history_live, mode='lines+markers', name='Subsidence (cm)')).update_layout(title='Subsidence Trend', xaxis_title='Time step', yaxis_title='Mean subsidence (cm)', height=350)
            trend_plot_live.plotly_chart(trend_fig, use_container_width=True, key=f"trend_{t_step}")
            surface_fig = go.Figure(data=[go.Surface(z=Z_subs*100, x=X_live, y=Y_live, colorscale='Viridis', opacity=0.9)])
            if anomaly_points[0].size>0:
                surface_fig.add_trace(go.Scatter3d(x=X_grid_live[anomaly_points], y=Y_grid_live[anomaly_points], z=Z_subs[anomaly_points]*100, mode='markers', marker=dict(color='red', size=5), name='Anomaly'))
            surface_fig.update_layout(title='3D Surface & Anomalies', scene=dict(zaxis_title='Subsidence (cm)'), height=500)
            surface_3d_plot_live.plotly_chart(surface_fig, use_container_width=True, key=f"surf_{t_step}")
            alerts = []
            if FOS_live<1.2: alerts.append("⚠️ FOS Critical!")
            if mean_subs*100>3: alerts.append("⚠️ High Subsidence!")
            if np.max(Z_temp)>1100: alerts.append("🔥 Overheating Alert!")
            if alerts: alert_box_live.markdown("### 🔴 ALERTS\n"+"\n".join(alerts))
            else: alert_box_live.markdown("### 🟢 All systems normal")
            time.sleep(0.1); steps_done+=1
        st.success(f"✅ Live monitoring completed after {steps_done} steps.")
    if not st.session_state.live_history_df.empty:
        st.markdown("---")
        st.subheader("📥 Download Monitoring Results (CSV)")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(label=t('download_data'), data=csv_data, file_name="ucg_live_monitoring.csv", mime="text/csv")

# AI Monitoring Tab (Digital Twin + Anomaly + FOS prediction)
with tab_ai_orig:
    st.markdown(f"*{t('ai_monitor_desc')}*")
    # Digital Twin
    if 'twin' not in st.session_state:
        st.session_state.twin = DigitalTwin()
    twin = st.session_state.twin
    st.subheader("🧠 Digital Twin Real-time Simulator")
    run_dt = st.button("▶️ Start Digital Twin Simulation")
    if run_dt:
        placeholder_dt = st.empty()
        for step in range(50):
            state = twin.update()
            fos_val = improved_fos(ucs_seam, layers_data[-1]['gsi'], layers_data[-1]['mi'],
                                   D_factor, nu_poisson, state["T"], H_seam, H_seam)
            # GPU prediction if available
            if PT_AVAILABLE:
                fos_ai = predict_fos_gpu(state["T"], state["stress"], ucs_seam)
            else:
                fos_ai = fos_val
            insert_data(state["T"], state["stress"], state["pressure"], fos_val)
            with placeholder_dt.container():
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("🌡 Temp", f"{state['T']:.1f} °C")
                c2.metric("🧱 Stress", f"{state['stress']:.2f} MPa")
                c3.metric("💨 Pressure", f"{state['pressure']:.2f} MPa")
                c4.metric("🛡 FOS (Physics)", f"{fos_val:.2f}")
                st.metric("🤖 AI FOS (RF)", f"{fos_ai:.2f}")
                if fos_val < 1.2:
                    st.error("🚨 COLLAPSE RISK!")
                elif fos_val < 1.5:
                    st.warning("⚠️ WARNING ZONE")
                else:
                    st.success("✅ STABLE")
            time.sleep(0.2)
        st.balloons()
    # Anomaly detection (IsolationForest)
    st.subheader("📡 Anomaly Detection (ML)")
    anomaly_model = IsolationForest(contamination=0.05, random_state=42)
    if st.button("Run Anomaly Detection on Twin History"):
        if len(twin.history) > 10:
            temps = [h["T"] for h in twin.history]
            data = np.array(temps).reshape(-1,1)
            preds = anomaly_model.fit_predict(data)
            anomalies = [i for i, p in enumerate(preds) if p == -1]
            fig_anom = go.Figure()
            fig_anom.add_trace(go.Scatter(y=temps, mode='lines', name='Temperature'))
            fig_anom.add_trace(go.Scatter(x=anomalies, y=[temps[i] for i in anomalies], mode='markers', marker=dict(color='red', size=10), name='Anomaly'))
            st.plotly_chart(fig_anom, use_container_width=True)
            st.write(f"Detected {len(anomalies)} anomalies")
        else:
            st.warning("Run Digital Twin first to generate history")

# Advanced Analysis Tab
with tab_advanced:
    st.header(t('advanced_analysis'))
    base_params = {
        'ucs': layers_data[-1]['ucs'],
        'gsi': layers_data[-1]['gsi'],
        'mi': layers_data[-1]['mi'],
        'D': D_factor,
        'nu': nu_poisson,
        'T': T_source_max,
        'depth': H_seam,
        'H': H_seam
    }
    # Monte Carlo
    with st.expander("🎲 Monte Carlo Risk Analysis"):
        mc_fos = monte_carlo_fos(500, base_params)
        fig_mc = go.Figure()
        fig_mc.add_histogram(x=mc_fos, nbinsx=30)
        fig_mc.add_vline(x=1.3, line_dash="dash", line_color="red")
        st.plotly_chart(fig_mc, use_container_width=True)
        st.metric("Failure Probability (FOS<1.3)", f"{np.mean(mc_fos < 1.3)*100:.2f}%")
    # Tornado sensitivity
    with st.expander("🌪️ Sensitivity Analysis PRO"):
        df_sens, base_fos = sensitivity_analysis_pro(base_params)
        fig_tornado = go.Figure()
        fig_tornado.add_bar(y=df_sens['param'], x=df_sens['low'], orientation='h', name='-20%', marker_color='#E74C3C')
        fig_tornado.add_bar(y=df_sens['param'], x=df_sens['high'], orientation='h', name='+20%', marker_color='#27AE60')
        fig_tornado.add_vline(x=0, line_color='white')
        fig_tornado.update_layout(title=f"FOS Sensitivity (base FOS={base_fos:.2f})", barmode='overlay', height=400)
        st.plotly_chart(fig_tornado, use_container_width=True)
    # AI FOS prediction
    st.subheader("🤖 AI FOS Prediction (RandomForest)")
    ai_model = load_ai_fos_model()
    sigma_v_pred = calc_vertical_stress(H_seam)
    pred_fos = ai_model.predict([[T_source_max, sigma_v_pred, layers_data[-1]['ucs']]])[0]
    st.metric("AI Predicted FOS", f"{pred_fos:.2f}")
    # Composite risk map
    risk_map = np.clip(0.4*(1-fos_2d/2) + 0.3*damage + 0.2*void_mask_permanent.astype(float) + 0.1*(temp_2d/T_source_max), 0, 1)
    st.subheader("⚠️ Composite Risk Index")
    fig_risk = go.Figure(go.Heatmap(z=risk_map, x=x_axis, y=z_axis, colorscale='RdYlGn_r', zmin=0, zmax=1))
    fig_risk.update_layout(title="Risk Map", yaxis=dict(autorange='reversed'), height=400)
    st.plotly_chart(fig_risk, use_container_width=True)
    risk_avg = np.mean(risk_map)
    st.metric("Average Risk Index", f"{risk_avg:.2f}")
    if risk_avg > 0.7:
        st.error("🚨 HIGH RISK")
    elif risk_avg > 0.4:
        st.warning("⚠️ MEDIUM RISK")
    else:
        st.success("✅ LOW RISK")

# ISO Report Section
with st.expander("📄 ISO 9001:2015 Standart Hujjat (.docx)"):
    d1, d2 = st.columns(2)
    with d1:
        iso_lang = st.selectbox("Hujjat tili", ['uz','en','ru'], format_func=lambda x: {'uz':"🇺🇿 O'zbek",'en':"🇬🇧 English",'ru':"🇷🇺 Русский"}[x], key="iso_lang")
        doc_num_input = st.text_input("Hujjat raqami", value="UCG-2026-001")
        revision_inp = st.text_input("Revision", value="A")
    with d2:
        prepared_inp = st.text_input("Prepared by", value="UCG Engineering Team")
        approved_inp = st.text_input("Approved by", value="Chief Engineer")
    if st.button("📄 ISO hujjat yaratish", type="primary", use_container_width=True):
        with st.spinner("ISO 9001 shablon tayyorlanmoqda..."):
            try:
                fig, ax = plt.subplots(figsize=(6,4))
                im = ax.imshow(risk_map, extent=[x_axis[0], x_axis[-1], z_axis[-1], z_axis[0]], cmap='hot', aspect='auto')
                plt.colorbar(im, ax=ax, label='Risk Index')
                ax.set_title('Composite Risk Map')
                buf_img = io.BytesIO()
                plt.savefig(buf_img, format='png', dpi=100)
                buf_img.seek(0)
                plt.close()
                docx_bytes = generate_full_iso_report(
                    obj_name=obj_name, lang=iso_lang, layers_data=layers_data,
                    T_source_max=T_source_max, burn_duration=burn_duration,
                    pillar_strength=pillar_strength, optimal_width_ai=optimal_width_ai,
                    fos_2d=fos_2d, risk_map=risk_map,
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

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device} | PT: {PT_AVAILABLE}")
