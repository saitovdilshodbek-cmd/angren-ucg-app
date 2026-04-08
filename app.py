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
from sklearn.linear_model import LinearRegression
import io
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import torch
import torch.nn as nn
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import joblib
import requests
import warnings
from dataclasses import dataclass
warnings.filterwarnings('ignore')

# =========================== TRY/EXCEPT PYTORCH ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except:
    PT_AVAILABLE = False
    device = "cpu"

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

# =========================== DATACLASS LAYER ===========================
@dataclass
class Layer:
    name: str
    thickness: float
    ucs: float
    density: float
    gsi: float
    mi: float
    color: str

# =========================== CONSTANTS (MODEL_PARAMS, PHYSICS) ===========================
MODEL_PARAMS = {
    "alpha_rock": 1e-6,
    "v_burn": 0.02,
    "DX": 1.0,
    "DT": 0.1
}

PHYSICS = {
    "damage_beta": 0.002,
    "strength_decay": 0.0025,
    "spalling_temp": 400,
    "crushing_temp": 600,
    "void_temp": 900
}

EPS = 1e-12

# =========================== STREAMLIT PAGE CONFIG ===========================
st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# =========================== TILNI SOZLASH ===========================
if 'language' not in st.session_state:
    st.session_state.language = 'uz'

LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))

# Agar til o'zgargan bo'lsa, sahifani qayta yuklash
if lang != st.session_state.language:
    st.session_state.language = lang
    st.rerun()

# =========================== SECRETS (APP_URL) ===========================
try:
    url = st.secrets.get("APP_URL", "https://default-link.com")
except:
    url = "https://default-link.com"

# =========================== QR KOD GENERATORI ===========================
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
qr_img_bytes = generate_qr(url)
st.sidebar.image(qr_img_bytes, caption="Scan QR: Angren UCG API", use_container_width=True)

# =========================== MATEMATIK METODOLOGIYA ===========================
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

# =========================== SIDEBAR PARAMETRLAR ===========================
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

# =========================== QATLAM MA'LUMOTLARI ===========================
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
if errors:
    for e in errors:
        st.error(e)
    st.stop()
if not layers_data:
    st.error(t('error_min_layers'))
    st.stop()

# =========================== KESHLANGAN HARORAT MAYDONI (HARAKATLANUVCHI MANBA BILAN) ===========================
@st.cache_data(show_spinner=False, max_entries=50, ttl=300)
def compute_temperature_field_moving(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20):
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
    z_axis = np.linspace(0, total_depth + 50, grid_shape[0])
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
    alpha_rock = MODEL_PARAMS["alpha_rock"]
    v_burn = MODEL_PARAMS["v_burn"]
    # Uchta manba: statsionar + harakatlanuvchi
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
    Q_heat = np.zeros_like(temp_2d)
    for src in sources:
        if time_h > src['start']:
            elapsed = time_h - src['start']
            if elapsed <= burn_duration:
                curr_T = T_source_max
            else:
                curr_T = 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration))
            if src['moving']:
                x_center = src['x0'] + src['v'] * (time_h - src['start'])*3600
            else:
                x_center = src['x0']
            Q_heat += (curr_T/10.0) * np.exp(-((grid_x - x_center)**2 + (grid_z - source_z)**2)/(2*30**2))
    # Diffuziya
    DX, DT = MODEL_PARAMS["DX"], MODEL_PARAMS["DT"]
    for _ in range(n_steps):
        Tn = temp_2d.copy()
        Tn[1:-1,1:-1] = (temp_2d[1:-1,1:-1] + alpha_rock*DT*((temp_2d[2:,1:-1]-2*temp_2d[1:-1,1:-1]+temp_2d[:-2,1:-1])/(DX**2+EPS) +
                         (temp_2d[1:-1,2:]-2*temp_2d[1:-1,1:-1]+temp_2d[1:-1,:-2])/(DX**2+EPS)) + Q_heat[1:-1,1:-1]*DT)
        temp_2d = Tn
    return temp_2d, x_axis, z_axis, grid_x, grid_z

grid_shape = (80, 100)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam   = layers_data[-1]['t']
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape, n_steps=20)

# Gaussian filter qo'llash
temp_2d = gaussian_filter(temp_2d, sigma=2)

# =========================== QATLAM INDEKSLASH (digitize) ===========================
layer_bounds = np.array([l['z_start'] for l in layers_data] + [total_depth])
layer_ids = np.digitize(grid_z.flatten(), layer_bounds) - 1
layer_ids = np.clip(layer_ids, 0, len(layers_data)-1).reshape(grid_z.shape)

grid_ucs = np.array([layers_data[i]['ucs'] for i in layer_ids.flatten()]).reshape(grid_z.shape)
grid_mi = np.array([layers_data[i]['mi'] for i in layer_ids.flatten()]).reshape(grid_z.shape)
grid_gsi = np.array([layers_data[i]['gsi'] for i in layer_ids.flatten()]).reshape(grid_z.shape)
grid_rho = np.array([layers_data[i]['rho'] for i in layer_ids.flatten()]).reshape(grid_z.shape)
grid_sigma_t0_manual = np.array([layers_data[i]['sigma_t0_manual'] for i in layer_ids.flatten()]).reshape(grid_z.shape)

# =========================== GEOMEXANIK HISOBI (tezlashtirilgan) ===========================
grid_sigma_v = np.zeros_like(grid_z)
# overburden stress
cum_stress = np.cumsum([l['rho']*9.81*l['t'] for l in layers_data]) / 1e6
for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data)-1: mask = grid_z >= layer['z_start']
    over = cum_stress[i-1] if i>0 else 0
    grid_sigma_v[mask] = over + (layer['rho']*9.81*(grid_z[mask]-layer['z_start']))/1e6

grid_mb = grid_mi * np.exp((grid_gsi-100)/(28-14*D_factor))
grid_s_hb = np.exp((grid_gsi-100)/(9-3*D_factor))
grid_a_hb = 0.5 + (1/6)*(np.exp(-grid_gsi/15)-np.exp(-20/3))

# Maksimal harorat xaritasi (decay bilan)
if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
    st.session_state.max_temp_map = temp_2d.copy()
    st.session_state.last_obj_name = obj_name
elif st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map = temp_2d.copy()
    st.session_state.last_obj_name = obj_name
else:
    st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map * 0.98, temp_2d)

delta_T = temp_2d - 25.0
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage = np.clip(1 - np.exp(-PHYSICS["damage_beta"] * temp_eff), 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

# Termal stress
E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)
sigma_thermal = CONSTRAINT_FACTOR*(E_MODULUS*ALPHA_T_COEFF*delta_T)/(1-nu_poisson+EPS) + 0.3*thermal_gradient
grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == t('tensile_empirical'): grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == t('tensile_hb'): grid_sigma_t0_base = (sigma_ci * grid_s_hb)/(1+grid_mb+EPS)
else: grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal*(temp_2d-20))
thermal_boost = 1 + 0.6*(1-np.exp(-delta_T/200))
sigma_t_field_eff = sigma_t_field/(thermal_boost+EPS)

tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T>50) & (sigma1_act>sigma3_act)
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci*(grid_mb*sigma3_safe/(sigma_ci+EPS)+grid_s_hb)**grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > PHYSICS["spalling_temp"])
crushing = shear_failure & (temp_2d > PHYSICS["crushing_temp"])
depth_factor = np.exp(-grid_z/(total_depth+EPS))
local_collapse_T = np.clip((st.session_state.max_temp_map-600)/300,0,1)
time_factor = np.clip((time_h-40)/60,0,1)
collapse_final = local_collapse_T * time_factor * (1-depth_factor)
void_mask_raw = spalling | crushing | (st.session_state.max_temp_map > PHYSICS["void_temp"])
void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth>0.3) & (collapse_final>0.05)

# O'tkazuvchanlik (viskozite bilan)
phi = 0.05 + 0.4 * void_mask_permanent.astype(float)
perm = (phi**3) / ((1-phi+EPS)**2) * 1e-12
void_volume = np.sum(void_mask_permanent)*(x_axis[1]-x_axis[0])*(z_axis[1]-z_axis[0])
sigma1_act = np.where(void_mask_permanent, 0.0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0.0, sigma3_act)
sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)

# Gaz oqimi (mu qo'shilgan)
mu = 1.8e-5  # gas viscosity
pressure = temp_2d*10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx = -perm/mu * dp_dx
vz = -perm/mu * dp_dz
gas_velocity = np.sqrt(vx**2+vz**2)

# =========================== AI MODEL (Collapse prediction) ===========================
@st.cache_resource(show_spinner=False)
def get_nn_model():
    if not PT_AVAILABLE: return None
    def generate_ucg_dataset(n=10000):
        data = []
        for _ in range(n):
            T = np.random.uniform(20,1000); s1 = np.random.uniform(0,50); s3 = np.random.uniform(0,30); d = np.random.uniform(0,300)
            damage = 1 - np.exp(-0.002*max(T-100,0)); strength = 40*(1-damage); collapse = 1 if (s1>strength or T>700) else 0
            data.append([T,s1,s3,d,collapse])
        return np.array(data)
    class CollapseNet(nn.Module):
        def __init__(self): super().__init__(); self.net = nn.Sequential(nn.Linear(4,32), nn.ReLU(), nn.Linear(32,64), nn.ReLU(), nn.Linear(64,1), nn.Sigmoid())
        def forward(self,x): return self.net(x)
    data = generate_ucg_dataset()
    X = torch.tensor(data[:,:-1], dtype=torch.float32); y = torch.tensor(data[:,-1], dtype=torch.float32).view(-1,1)
    model = CollapseNet(); optimizer = torch.optim.Adam(model.parameters(), lr=0.001); loss_fn = nn.BCELoss()
    for epoch in range(50): pred = model(X); loss = loss_fn(pred,y); optimizer.zero_grad(); loss.backward(); optimizer.step()
    model.eval(); return model

def predict_nn(model, temp, s1, s3, depth):
    X = np.column_stack([temp.flatten(), s1.flatten(), s3.flatten(), depth.flatten()])
    # Batch prediction (agar katta bo'lsa)
    batch_size = 5000
    preds = []
    for i in range(0, len(X), batch_size):
        batch = X[i:i+batch_size]
        X_t = torch.tensor(batch, dtype=torch.float32)
        with torch.no_grad():
            preds.append(model(X_t).numpy())
    pred = np.concatenate(preds)
    return pred.reshape(temp.shape)

nn_model = get_nn_model()
if nn_model is not None and PT_AVAILABLE:
    try: collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)
    except: nn_model = None
if nn_model is None or not PT_AVAILABLE:
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai))>1:
        rf_model = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
        rf_model.fit(X_ai, y_ai); collapse_pred = rf_model.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
    else: collapse_pred = np.zeros_like(temp_2d)

# =========================== SELEK OPTIMIZATSIYASI ===========================
avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(), :])
strength_red = np.exp(-PHYSICS["strength_decay"]*(avg_t_p-20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(), :].max()
w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam*strength_red)*(w_sol/(H_seam+EPS))**0.5
    y_zone_calc = (H_seam/2)*(np.sqrt(sv_seam/(p_strength+EPS))-1)
    new_w = 2*max(y_zone_calc,1.5)+0.5*H_seam
    if abs(new_w-w_sol)<0.1: break
    w_sol = new_w
rec_width = np.round(w_sol,1)
pillar_strength = p_strength
y_zone = max(y_zone_calc,1.5)
fos_2d = np.clip(sigma1_limit/(sigma1_act+EPS),0,3.0)
fos_2d = np.where(void_mask_permanent,0.0,fos_2d)
void_frac_base = float(np.mean(void_mask_permanent))

def objective(w_arr):
    w = w_arr[0]; strength = (ucs_seam*strength_red)*(w/(H_seam+EPS))**0.5; risk = void_frac_base*np.exp(-0.01*(w-rec_width))
    return -(strength - 15.0*risk)

# w_range bo'yicha optimallashtirish (qo'shimcha)
w_range = np.linspace(5, 100, 50)
scores = [(w, objective([w])) for w in w_range]
optimal_width_ai = max(scores, key=lambda x: x[1])[0]

# =========================== METRIKALAR ===========================
st.subheader(t('monitoring_header', obj_name=obj_name))
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m", delta_color="off")

# =========================== CHO'KISH VA HOEK-BROWN GRAFIKALARI ===========================
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

# =========================== TM MAYDONI (checkbox bilan) ===========================
st.markdown("---")
c1, c2 = st.columns([1,2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    fig_s = go.Figure()
    for lyr in layers_data: fig_s.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)
with c2:
    st.subheader(t('tm_field_title'))
    show_ai = st.checkbox("AI layer", value=True)
    show_vectors = st.checkbox("Gas flow", value=True)
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=(t('temp_subplot'), t('fos_subplot')))
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, colorbar=dict(title="T (°C)", title_side="top", x=1.05, y=0.78, len=0.42, thickness=15), name=t('temp_subplot')), row=1, col=1)
    if show_vectors:
        step = 12
        qx,qz = grid_x[::step,::step].flatten(), grid_z[::step,::step].flatten()
        qu,qw = vx[::step,::step].flatten(), vz[::step,::step].flatten()
        qmag = gas_velocity[::step,::step].flatten()
        qmag_max = qmag.max()+EPS
        mask_q = qmag > qmag_max*0.05
        angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q]+EPS))
        fig_tm.add_trace(go.Scatter(x=qx[mask_q], y=qz[mask_q], mode='markers', marker=dict(symbol='arrow', size=10, color=qmag[mask_q], colorscale='ice', cmin=0, cmax=qmag_max, angle=angles, opacity=0.85, showscale=False, line=dict(width=0)), name=t('gas_flow')), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale=[[0,'red'],[0.33,'yellow'],[0.5,'green'],[1,'darkgreen']], zmin=0, zmax=3.0, contours_showlines=False, colorbar=dict(title="FOS", title_side="top", x=1.05, y=0.22, len=0.42, thickness=15), name="FOS"), row=2, col=1)
    void_visual = np.where(void_mask_permanent>0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis, colorscale=[[0,'black'],[1,'black']], showscale=False, opacity=0.9, hoverinfo='skip'), row=2, col=1)
    fig_tm.add_trace(go.Contour(z=void_mask_permanent.astype(int), x=x_axis, y=z_axis, showscale=False, contours=dict(coloring='lines'), line=dict(color='white',width=2), hoverinfo='skip'), row=2, col=1)
    shear_disp = np.copy(shear_failure); shear_disp[void_mask_permanent]=False
    tens_disp = np.copy(tensile_failure); tens_disp[void_mask_permanent]=False
    fig_tm.add_trace(go.Scatter(x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2], mode='markers', marker=dict(color='red',size=3,symbol='x'), name=t('shear')), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2], mode='markers', marker=dict(color='blue',size=3,symbol='cross'), name=t('tensile')), row=2, col=1)
    for px in [-total_depth/3, 0, total_depth/3]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime",width=3), row=2, col=1)
    if show_ai:
        fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name=t('ai_collapse')), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(r=150,t=80,b=100), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# =========================== KOMPLEKS MONITORING PANELI ===========================
st.header(t('monitoring_panel', obj_name=obj_name))
def calculate_live_metrics(h, layers, T_max):
    target = layers[-1]; ucs_0, H_l = target['ucs'], target['t']
    curr_T = (25 + (T_max-25)*(min(h,40)/40) if h<=40 else T_max*np.exp(-0.001*(h-40)))
    str_red = np.exp(-0.0025*(curr_T-20))
    w_rec = 15.0 + (h/150)*10
    p_str = (ucs_0*str_red)*(w_rec/(H_l+EPS))**0.5
    max_sub = (H_l*0.05)*(min(h,120)/120)
    return p_str, w_rec, curr_T, max_sub
p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max)
mk1,mk2,mk3,mk4 = st.columns(4)
mk1.metric(t('pillar_live'), f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric(t('rec_width_live'), f"{w_rec_live:.1f} m")
mk3.metric(t('max_subsidence_live'), f"{s_max_3d*100:.1f} cm")
mk4.metric(t('process_stage'), t('stage_active') if time_h<100 else t('stage_cooling'))
st.markdown("---")

# ====================== YANGI QO'SHIMCHA: AI RISK PREDICTION (SENSOR CSV) ======================
class SimpleRiskNN(nn.Module):
    def __init__(self, input_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 1), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

@st.cache_resource
def get_risk_model():
    model = SimpleRiskNN().to(device)
    model.eval()
    return model

risk_model = get_risk_model()

def predict_risk_from_sensor(model, temp, stress, ucs_lab):
    X = np.column_stack([temp, stress, ucs_lab])
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.flatten()

with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    st.markdown("Yuklangan sensor ma'lumotlari asosida **SimpleRiskNN** modeli yordamida xavf indeksini bashorat qilish.")
    sensor_file = st.file_uploader("Sensor CSV faylini yuklang (kerakli ustunlar: 'temp', 'stress', 'ucs_lab')", type=['csv'], key="sensor_ai")
    if sensor_file:
        df_sensor = pd.read_csv(sensor_file)
        required_cols = ['temp', 'stress', 'ucs_lab']
        missing = [c for c in required_cols if c not in df_sensor.columns]
        if missing:
            st.error(f"Faylda quyidagi ustunlar yo‘q: {missing}. Iltimos, to‘g‘ri formatda yuklang.")
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
                st.error("⚠️ Yuqori xavf! Tez choralar ko‘rish kerak.")
            elif avg_risk > 0.5:
                st.warning("⚠️ O‘rtacha xavf. Monitoringni kuchaytirish tavsiya etiladi.")
            else:
                st.success("✅ Xavf past. Hozircha xavfsiz.")

# ====================== QO'SHIMCHA BLOKLAR (KOMPOZIT XAVF, FOS TREND, 3D, MONTE CARLO, SSENARIY, SEZGIRLIK, ISO) ======================
# (Ushbu bloklar asosiy koddan o'zgarishsiz qoldiriladi, chunki ular allaqachon mavjud)
# ... Qisqartirish maqsadida ularni qayta yozmayman, asl kodda bor.

# =========================== LIVE MONITORING (yangilangan RF, IsolationForest, LinearRegression, risk indeksi) ===========================
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
    if 'live_history_df' not in st.session_state: st.session_state.live_history_df = pd.DataFrame(columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m'])
    if 'rf_live' not in st.session_state:
        st.session_state.rf_live = RandomForestRegressor(n_estimators=50, random_state=42)
    if 'iso_model' not in st.session_state:
        st.session_state.iso_model = IsolationForest(contamination=0.05, random_state=42)
    if 'twin_state' not in st.session_state:
        st.session_state.twin_state = {"temperature": [], "stress": [], "risk": []}
    if run_live:
        st.session_state.stop_flag_live = False
        X_live = np.linspace(-20,20,50); Y_live = np.linspace(-20,20,50); X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_history_live = []; fos_history_live = []; width_history_live = []; temp_history_live = []; steps_done = 0
        # Dastlabki RF o'rgatish uchun dummy ma'lumot
        dummy_X = np.random.rand(10,3); dummy_y = np.random.rand(10); st.session_state.rf_live.fit(dummy_X, dummy_y)
        for t_step in range(TIME_STEPS):
            if st.session_state.stop_flag_live: break
            Z_subs = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*(5+t_step*0.1)**2))*5*t_step/TIME_STEPS
            Z_temp = np.exp(-(X_grid_live**2+Y_grid_live**2)/(2*8**2))*T_source_max*t_step/TIME_STEPS
            Z_filtered = gaussian_filter(Z_subs, sigma=1); anomalies = Z_subs-Z_filtered; anomaly_points = np.where(np.abs(anomalies)>0.2)
            avg_ucs = np.mean([l['ucs'] for l in layers_data]); X_feat = np.array([[burn_duration, T_source_max, avg_ucs]]).reshape(1,-1)
            # Live RF update (agar tarix yetarlicha bo'lsa)
            if len(st.session_state.live_history_df) > 10:
                X_train = st.session_state.live_history_df[['max_temp_c','FOS','mean_subsidence_cm']].values
                y_train = st.session_state.live_history_df['pillar_width_m'].values
                st.session_state.rf_live.fit(X_train, y_train)
                pillar_width_pred = st.session_state.rf_live.predict(X_feat)[0]
            else:
                pillar_width_pred = 15.0 + t_step*0.1
            # FOS hisoblash
            sigma_v_live = (layers_data[-1]['rho']*9.81*(H_seam + t_step*0.1))/1e6
            pillar_strength_live = (ucs_seam*np.exp(-0.0025*(np.mean(Z_temp)-20))) * (rec_width/(H_seam+EPS))**0.5
            FOS_live = np.clip(pillar_strength_live/(sigma_v_live+EPS), 0, 3)
            mean_subs = np.mean(Z_subs)
            subs_history_live.append(mean_subs); fos_history_live.append(FOS_live); width_history_live.append(pillar_width_pred); temp_history_live.append(np.mean(Z_temp))
            MAX_HISTORY = 1000
            new_row = pd.DataFrame({'step':[t_step+1],'mean_subsidence_cm':[mean_subs*100],'max_temp_c':[np.max(Z_temp)],'FOS':[FOS_live],'pillar_width_m':[pillar_width_pred]})
            st.session_state.live_history_df = pd.concat([st.session_state.live_history_df, new_row], ignore_index=True).tail(MAX_HISTORY)
            # Downsampling
            step_ds = 2
            Z_subs_ds = Z_subs[::step_ds, ::step_ds]
            X_live_ds = X_live[::step_ds]
            Y_live_ds = Y_live[::step_ds]
            fig_subs = go.Figure(go.Heatmap(z=Z_subs_ds*100, x=X_live_ds, y=Y_live_ds, colorscale='Viridis')).update_layout(title='Surface Subsidence (cm)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
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
            # Alerts
            alerts = []
            if FOS_live<1.2: alerts.append("⚠️ FOS Critical!")
            if mean_subs*100>3: alerts.append("⚠️ High Subsidence!")
            if np.max(Z_temp)>1100: alerts.append("🔥 Overheating Alert!")
            if alerts: alert_box_live.markdown("### 🔴 ALERTS\n"+"\n".join(alerts))
            else: alert_box_live.markdown("### 🟢 All systems normal")
            # Risk indeksi (twin_state)
            risk_live = 0.4*(1 - FOS_live/2) + 0.3*(np.mean(Z_temp)/T_source_max) + 0.3*(mean_subs/5)
            st.session_state.twin_state["temperature"].append(np.mean(Z_temp))
            st.session_state.twin_state["stress"].append(sigma_v_live)
            st.session_state.twin_state["risk"].append(risk_live)
            st.metric("⚠️ Risk Index", f"{risk_live:.2f}")
            if risk_live > 0.7: st.error("🚨 CRITICAL COLLAPSE RISK")
            elif risk_live > 0.5: st.warning("⚠️ MEDIUM RISK")
            else: st.success("✅ SAFE")
            # LinearRegression trend
            if len(subs_history_live) > 10:
                X_t = np.arange(len(subs_history_live)).reshape(-1,1)
                y_t = np.array(subs_history_live)
                model_lr = LinearRegression().fit(X_t, y_t)
                future = model_lr.predict([[len(subs_history_live)+10]])[0]
                st.metric("📈 Predicted Subsidence", f"{future:.2f} cm")
            time.sleep(0.1); steps_done+=1
        st.success(f"✅ Live monitoring completed after {steps_done} steps.")
    if not st.session_state.live_history_df.empty:
        st.markdown("---"); st.subheader("📥 Download Monitoring Results (CSV)")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(label=t('download_data'), data=csv_data, file_name="ucg_live_monitoring.csv", mime="text/csv")

# AI Monitoring (tab_ai_orig) va Advanced Analysis (tab_advanced) qismlari asl kodda mavjud, ularni o'zgartirmayman.
# Qisqartirish uchun ularni bu yerda to'liq takrorlamayman, lekin ular asl kodda bor.

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")
