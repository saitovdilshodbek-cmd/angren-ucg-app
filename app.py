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
        'download_data': "📥 Monitoring ma'lumotlarini yuklab olish (CSV)",
        'ultimate_dashboard_title': "🕹️ Ultimate Interactive Dashboard (Real-time Animation)",
        'fos_threshold': "FOS chegarasi (Yielded Zone)",
        'burn_radius': "Faol yonish radiusi (m)",
        'disp_colorscale': "Siljish ranglar palitrasi",
        'pillar_info': "🟩 Yashil to‘rtburchaklar – Selek (Pillar)",
        'interference_info': "🔴 Qizil chiziq – Selek interferensiya zonasi",
        'burn_info': "🟠 To‘q sariq doira – Faol yonish radiusi",
        'void_info': "⚪ Oq yarim shaffof – Bo‘shliq (siljish >3 sm)",
        'coal_thickness_info': "Ko‘mir qatlami qalinligi = {thick} m (birinchi qatlam)"
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
        'download_data': "📥 Download monitoring data (CSV)",
        'ultimate_dashboard_title': "🕹️ Ultimate Interactive Dashboard (Real-time Animation)",
        'fos_threshold': "FOS Threshold (Yielded Zone)",
        'burn_radius': "Active Burn Radius (m)",
        'disp_colorscale': "Displacement Color Scale",
        'pillar_info': "🟩 Green rectangles – Pillars",
        'interference_info': "🔴 Red dashed line – Pillar Interference Zone",
        'burn_info': "🟠 Orange circle – Active Burn Radius",
        'void_info': "⚪ White semi-transparent – Void (displacement >3 cm)",
        'coal_thickness_info': "Coal seam thickness = {thick} m (first layer)"
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
        'download_data': "📥 Скачать данные мониторинга (CSV)",
        'ultimate_dashboard_title': "🕹️ Ultimate Interactive Dashboard (Real-time Animation)",
        'fos_threshold': "Порог FOS (зона текучести)",
        'burn_radius': "Активный радиус горения (м)",
        'disp_colorscale': "Цветовая шкала смещения",
        'pillar_info': "🟩 Зелёные прямоугольники – Целики",
        'interference_info': "🔴 Красная линия – Зона интерференции целиков",
        'burn_info': "🟠 Оранжевый круг – Активный радиус горения",
        'void_info': "⚪ Белая полупрозрачность – Пустота (смещение >3 см)",
        'coal_thickness_info': "Мощность угольного пласта = {thick} м (первый слой)"
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

# =========================== TILNI SOZLASH ===========================
if 'language' not in st.session_state:
    st.session_state.language = 'uz'

LANGUAGES = {'uz': "🇺🇿 O'zbek", 'en': '🇬🇧 English', 'ru': '🇷🇺 Русский'}
lang = st.sidebar.selectbox("Til / Language / Язык", options=list(LANGUAGES.keys()),
                            format_func=lambda x: LANGUAGES[x],
                            index=list(LANGUAGES.keys()).index(st.session_state.language))
st.session_state.language = lang

# =========================== QR KOD GENERATORI ===========================
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
if not layers_data: errors.append(t('error_min_layers'))
if errors:
    for e in errors: st.error(e)
    st.stop()

# =========================== KESHLANGAN HARORAT MAYDONI ===========================
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

# =========================== GEOMEXANIK HISOBI ===========================
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

def thermal_damage(T, T0=100, k=0.002, mech_factor=0.1, stress_ratio=1.0):
    thermal = 1 - np.exp(-k * np.maximum(T - T0, 0))
    mech = mech_factor * stress_ratio
    return np.clip(thermal + mech, 0, 0.98)

stress_ratio = grid_sigma_v / (grid_ucs + EPS)
damage = thermal_damage(st.session_state.max_temp_map, stress_ratio=stress_ratio)
sigma_ci = grid_ucs * (1 - damage)

E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
dT_dx = np.gradient(temp_2d, axis=1, edge_order=2)
dT_dz = np.gradient(temp_2d, axis=0, edge_order=2)
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

def hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a):
    sigma3_safe = np.maximum(sigma3, 0.01)
    return sigma3_safe + sigma_ci * (mb * sigma3_safe / (sigma_ci + 1e-9) + s) ** a

sigma1_limit = hoek_brown_sigma1(sigma3_act, sigma_ci, grid_mb, grid_s_hb, grid_a_hb)
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d>400)
crushing = shear_failure & (temp_2d>600)
depth_factor = np.exp(-grid_z/(total_depth+EPS))
local_collapse_T = np.clip((st.session_state.max_temp_map-600)/300,0,1)
time_factor = np.clip((time_h-40)/60,0,1)
collapse_final = local_collapse_T * time_factor * (1-depth_factor)
void_mask_raw = spalling | crushing | (st.session_state.max_temp_map>900)
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
class CollapseNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(4,32), nn.ReLU(), nn.Linear(32,64), nn.ReLU(), nn.Linear(64,1), nn.Sigmoid())
    def forward(self, x): return self.net(x)

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

@st.cache_resource
def get_nn_model():
    if not PT_AVAILABLE: return None
    model = CollapseNet().to(device)
    try:
        model.load_state_dict(torch.load("collapse_model.pth", map_location=device))
        model.eval()
        return model
    except:
        data = generate_ucg_dataset()
        X = torch.tensor(data[:,:-1], dtype=torch.float32).to(device)
        y = torch.tensor(data[:,-1], dtype=torch.float32).view(-1,1).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        loss_fn = nn.BCELoss()
        for epoch in range(50):
            pred = model(X)
            loss = loss_fn(pred, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        torch.save(model.state_dict(), "collapse_model.pth")
        model.eval()
        return model

def predict_nn(model, temp, s1, s3, depth):
    X = np.column_stack([temp.flatten(), s1.flatten(), s3.flatten(), depth.flatten()])
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.reshape(temp.shape)

nn_model = get_nn_model()
if nn_model is not None and PT_AVAILABLE:
    try:
        collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)
    except:
        nn_model = None
if nn_model is None or not PT_AVAILABLE:
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai)) > 1:
        rf_model = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
        rf_model.fit(X_ai, y_ai)
        collapse_pred = rf_model.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
    else:
        collapse_pred = np.zeros_like(temp_2d)

# =========================== SELEK OPTIMIZATSIYASI ===========================
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

def objective(w_arr):
    w = w_arr[0]
    strength = (ucs_seam*strength_red)*(w/(H_seam+EPS))**0.5
    risk = void_frac_base * np.exp(-0.01*(w-rec_width))
    return -(strength - 15.0*risk)
try:
    opt_result = minimize(objective, x0=[rec_width], bounds=[(5.0,100.0)], method='SLSQP')
    optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except:
    optimal_width_ai = rec_width

# =========================== METRIKALAR ===========================
st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
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

# =========================== TM MAYDONI (FOS + AI Collapse + Yielded Zones + Select Interference) ===========================
st.markdown("---")
c1, c2 = st.columns([1,2.5])

# ----------- Left Panel: Layer Visualization -----------
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red')); st.warning(t('fos_yellow')); st.success(t('fos_green'))
    
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(
            x=['Kesim'],
            y=[lyr['t']],
            name=lyr['name'],
            marker_color=lyr['color'],
            width=0.4
        ))
    st.plotly_chart(
        fig_layers.update_layout(
            barmode='stack', 
            template="plotly_dark", 
            yaxis=dict(autorange='reversed'), 
            height=450, 
            showlegend=False
        ), 
        use_container_width=True
    )

# ----------- Right Panel: Optimized FOS + AI Collapse + Yielded Zones + Select Interference -----------
with c2:
    st.subheader(t('tm_field_title'))
    
    # Slider: FOS threshold for yielded zones
    fos_thresh = st.slider("FOS Threshold (Yielded Zone)", min_value=0.1, max_value=3.0, value=1.2, step=0.05)
    
    fig_fos_ai = go.Figure()
    
    # --- FOS heatmap ---
    fig_fos_ai.add_trace(go.Contour(
        z=fos_2d,
        x=x_axis,
        y=z_axis,
        colorscale=[[0,'red'],[0.33,'yellow'],[0.5,'green'],[1,'darkgreen']],
        zmin=0,
        zmax=3,
        contours_showlines=False,
        colorbar=dict(title="FOS", title_side="top", x=1.05, y=0.5, len=0.4, thickness=15),
        name="FOS"
    ))
    
    # --- Yielded (fractured) zones ---
    fracture_mask = np.where(fos_2d < fos_thresh, 1.0, np.nan)
    fig_fos_ai.add_trace(go.Heatmap(
        z=fracture_mask,
        x=x_axis,
        y=z_axis,
        colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(255,0,0,0.5)']],
        showscale=False,
        opacity=0.6,
        hoverinfo='skip',
        name="Yielded Zones"
    ))
    
    # --- Burn radius + dynamic remaining void ---
    remaining_void = np.zeros_like(fos_2d)
    for i, px in enumerate(pillar_locations):
        r_burn = burn_radius[i]  # individual burn radius per pillar
        distance_grid = np.sqrt((grid_x - px)**2 + (grid_z - source_z)**2)
        burn_zone = distance_grid <= r_burn
        remaining_void[burn_zone] = np.nan  # mark burned area
        # Draw burn circle overlay
        fig_fos_ai.add_shape(type="circle",
                             x0=px-r_burn, x1=px+r_burn,
                             y0=source_z-r_burn, y1=source_z+r_burn,
                             line=dict(color="orange", width=2),
                             fillcolor='rgba(255,165,0,0.2)')
    
    # --- Select (pillar-to-pillar interference) zones ---
    for i, px in enumerate(pillar_locations[:-1]):
        for j, px2 in enumerate(pillar_locations[i+1:]):
            sep_dist = abs(px2 - px)
            if sep_dist < safe_separation:
                mid_point = (px+px2)/2
                fig_fos_ai.add_shape(type="rect",
                                     x0=px, x1=px2,
                                     y0=source_z-H_seam/2, y1=source_z+H_seam/2,
                                     line=dict(color="magenta", width=2, dash="dot"),
                                     fillcolor='rgba(255,0,255,0.2)')
    
    # --- AI Collapse Prediction overlay ---
    fig_fos_ai.add_trace(go.Heatmap(
        z=collapse_pred,
        x=x_axis,
        y=z_axis,
        colorscale='Viridis',
        opacity=0.4,
        showscale=False,
        name="AI Collapse Prediction"
    ))
    
    # --- Shear & Tensile failure markers ---
    shear_disp = np.copy(shear_failure); shear_disp[void_mask_permanent]=False
    tens_disp = np.copy(tensile_failure); tens_disp[void_mask_permanent]=False
    fig_fos_ai.add_trace(go.Scatter(
        x=grid_x[shear_disp][::2],
        y=grid_z[shear_disp][::2],
        mode='markers',
        marker=dict(color='red', size=3, symbol='x'),
        name='Shear'
    ))
    fig_fos_ai.add_trace(go.Scatter(
        x=grid_x[tens_disp][::2],
        y=grid_z[tens_disp][::2],
        mode='markers',
        marker=dict(color='blue', size=3, symbol='cross'),
        name='Tensile'
    ))
    
    # --- Permanent void overlay ---
    void_visual = np.where(void_mask_permanent>0.1, 1.0, np.nan)
    fig_fos_ai.add_trace(go.Heatmap(
        z=void_visual,
        x=x_axis,
        y=z_axis,
        colorscale=[[0,'black'],[1,'black']],
        showscale=False,
        opacity=0.8,
        hoverinfo='skip'
    ))
    
    # --- Layout ---
    fig_fos_ai.update_layout(
        template="plotly_dark",
        height=850,
        title="FOS + AI Collapse + Yielded Zones + Select Interference",
        showlegend=True
    )
    fig_fos_ai.update_yaxes(autorange='reversed')
    
    st.plotly_chart(fig_fos_ai, use_container_width=True)


# =========================== KOMPLEKS MONITORING PANELI ===========================
st.header(t('monitoring_panel', obj_name=obj_name))
def calculate_live_metrics(h, layers, T_max):
    target = layers[-1]
    ucs_0, H_l = target['ucs'], target['t']
    curr_T = (25 + (T_max-25)*(min(h,40)/40) if h<=40 else T_max*np.exp(-0.001*(h-40)))
    str_red = np.exp(-0.0025*(curr_T-20))
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

# ====================== YANGI QO'SHIMCHA: AI RISK PREDICTION (SENSOR CSV) ======================
class SimpleRiskNN(nn.Module):
    def __init__(self, input_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

@st.cache_resource
def get_risk_model():
    if not PT_AVAILABLE:
        return None
    model = SimpleRiskNN().to(device)
    model.eval()
    return model

risk_model = get_risk_model()

def predict_risk_from_sensor(model, temp, stress, ucs_lab):
    if model is None:
        return np.full_like(temp, 0.5)
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
# 1. Kompozit xavf indeksi
@st.cache_data(show_spinner=False)
def compute_risk_map(fos_arr, damage_arr, void_arr, temp_arr, T_max):
    fos_risk = np.clip(1.0 - fos_arr / 2.0, 0, 1)
    thermal_risk = damage_arr
    void_risk = void_arr.astype(float)
    temp_risk = np.clip(temp_arr / T_max, 0, 1)
    risk = 0.40*fos_risk + 0.30*thermal_risk + 0.20*void_risk + 0.10*temp_risk
    return np.clip(risk, 0, 1)

risk_map = compute_risk_map(fos_2d, damage, void_mask_permanent, temp_2d, T_source_max)

with st.expander("🗺️ Kompozit Xavf Indeksi Xaritasi"):
    risk_col1, risk_col2 = st.columns([2,1])
    with risk_col1:
        fig_risk = go.Figure()
        fig_risk.add_trace(go.Heatmap(z=risk_map, x=x_axis, y=z_axis,
            colorscale=[[0.0,'#1a472a'],[0.33,'#27ae60'],[0.50,'#f39c12'],[0.75,'#e74c3c'],[1.0,'#7b241c']],
            zmin=0, zmax=1, colorbar=dict(title="Risk (0–1)", tickvals=[0,0.25,0.5,0.75,1.0], ticktext=["Xavfsiz","Past","O'rta","Yuqori","Kritik"])))
        fig_risk.add_trace(go.Contour(z=void_mask_permanent.astype(int), x=x_axis, y=z_axis, showscale=False, contours=dict(coloring='lines'), line=dict(color='white',width=2,dash='dot'), hoverinfo='skip', name='Void chegarasi'))
        fig_risk.update_layout(title="Kompozit Xavf Indeksi (FOS·40% + Damage·30% + Void·20% + T·10%)", template='plotly_dark', height=450, yaxis=dict(autorange='reversed', title='Chuqurlik (m)'), xaxis=dict(title='Gorizontal masofa (m)'))
        st.plotly_chart(fig_risk, use_container_width=True)
    with risk_col2:
        total_cells = risk_map.size
        r_safe = np.sum(risk_map<0.25)/total_cells*100
        r_low = np.sum((risk_map>=0.25)&(risk_map<0.5))/total_cells*100
        r_medium = np.sum((risk_map>=0.5)&(risk_map<0.75))/total_cells*100
        r_high = np.sum(risk_map>=0.75)/total_cells*100
        fig_pie = go.Figure(go.Pie(labels=["Xavfsiz (<0.25)","Past (0.25–0.5)","O'rta (0.5–0.75)","Kritik (>0.75)"],
            values=[r_safe,r_low,r_medium,r_high], marker_colors=['#27ae60','#f39c12','#e67e22','#e74c3c'], hole=0.4, textinfo='label+percent'))
        fig_pie.update_layout(template='plotly_dark', height=300, title="Zona taqsimoti", showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.metric("O'rtacha xavf indeksi", f"{np.mean(risk_map):.3f}")
        st.metric("Maksimal xavf indeksi", f"{np.max(risk_map):.3f}")
        if np.max(risk_map)>0.75:
            st.error("🔴 Kritik zona mavjud!")
        elif np.max(risk_map)>0.5:
            st.warning("🟡 O'rta xavf zonasi bor")
        else:
            st.success("🟢 Umumiy holat qoniqarli")

# 2. FOS vaqt trendi
with st.expander("📈 FOS Vaqt Bashorati (Trend)"):
    time_points = np.arange(1, time_h+1, max(1, time_h//20))
    fos_timeline = []
    for th in time_points:
        str_red_t = np.exp(-0.0025*(T_source_max*min(th,burn_duration)/burn_duration - 20))
        p_str_t = (ucs_seam*str_red_t)*(rec_width/(H_seam+EPS))**0.5
        sv_t = sv_seam*(1+0.001*th)
        fos_t = np.clip(p_str_t/(sv_t+EPS),0,3)
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

# 3. 3D Litologik kesim
with st.expander("🌍 3D Litologik Kesim"):
    fig_3d = go.Figure()
    y_3d = np.linspace(-total_depth*0.5, total_depth*0.5, 30)
    for i, layer in enumerate(layers_data):
        z_top = layer['z_start']
        z_bot = layer['z_start']+layer['t']
        x_3d = np.linspace(x_axis.min(), x_axis.max(), 30)
        X3, Y3 = np.meshgrid(x_3d, y_3d)
        Z_top = np.full_like(X3, z_top)
        Z_bot = np.full_like(X3, z_bot)
        hex_color = layer['color'].lstrip('#')
        r,g,b = tuple(int(hex_color[j:j+2],16) for j in (0,2,4))
        rgb_str = f"rgb({r},{g},{b})"
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_top, colorscale=[[0,rgb_str],[1,rgb_str]], showscale=False, opacity=0.7, name=layer['name'], hovertemplate=f"{layer['name']}<br>UCS: {layer['ucs']} MPa<br>GSI: {layer['gsi']}<extra></extra>"))
    for src_x in [-total_depth/3, 0, total_depth/3]:
        theta = np.linspace(0,2*np.pi,30)
        phi = np.linspace(0,np.pi,20)
        THETA, PHI = np.meshgrid(theta, phi)
        R = H_seam*0.4
        cx = src_x + R*np.sin(PHI)*np.cos(THETA)
        cy = R*np.sin(PHI)*np.sin(THETA)
        cz = source_z + R*np.cos(PHI)
        fig_3d.add_trace(go.Surface(x=cx, y=cy, z=cz, colorscale=[[0,'orange'],[1,'red']], showscale=False, opacity=0.85, name='Yonish kamerasi'))
    fig_3d.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Chuqurlik (m)', zaxis=dict(autorange='reversed'), camera=dict(eye=dict(x=1.5,y=1.5,z=1.0))), template='plotly_dark', height=600, title="3D Litologik Model + Yonish Kameralari", showlegend=True)
    st.plotly_chart(fig_3d, use_container_width=True)
    st.caption("Sariq/qizil sferalar — yonish kameralari joylashuvi")

# 4. Monte Carlo noaniqlik tahlili
@st.cache_data(show_spinner=False)
def monte_carlo_fos(ucs_mean, ucs_std, gsi_mean, gsi_std, d_mean, temp_mean, H_seam, n_sim=2000):
    np.random.seed(42)
    ucs_s = np.random.normal(ucs_mean, ucs_std, n_sim).clip(1,300)
    gsi_s = np.random.normal(gsi_mean, gsi_std, n_sim).clip(10,100)
    T_s = np.random.normal(temp_mean, temp_mean*0.1, n_sim).clip(20,1200)
    mb_s = 10*np.exp((gsi_s-100)/(28-14*d_mean))
    s_s = np.exp((gsi_s-100)/(9-3*d_mean))
    dmg_s = np.clip(1-np.exp(-0.002*np.maximum(T_s-100,0)),0,0.95)
    sci_s = ucs_s*(1-dmg_s)
    str_r = np.exp(-0.0025*(T_s-20))
    p_str = (sci_s*str_r)*(20/(H_seam+1e-12))**0.5
    sv_s = ucs_s*0.025
    fos_s = np.clip(p_str/(sv_s+1e-12),0,5)
    pf = float(np.mean(fos_s<1.0))
    return fos_s, pf

with st.expander("🎲 Monte Carlo Noaniqlik Tahlili"):
    mc_col1, mc_col2 = st.columns([1,2])
    with mc_col1:
        ucs_std = st.number_input("UCS standart og'ish (MPa)", value=5.0, min_value=0.1)
        gsi_std = st.number_input("GSI standart og'ish", value=5.0, min_value=0.1)
        n_mc = st.selectbox("Simulyatsiya soni", [500,1000,2000,5000], index=1)
    with mc_col2:
        fos_mc, pf = monte_carlo_fos(layers_data[-1]['ucs'], ucs_std, layers_data[-1]['gsi'], gsi_std, D_factor, avg_t_p, H_seam, n_sim=n_mc)
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

# 5. Ssenariy taqqoslash (A vs B)
with st.expander("⚖️ Ssenariy Taqqoslash (A vs B)"):
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("**Ssenariy A**")
        a_ucs  = st.number_input("UCS_A (MPa)", value=float(layers_data[-1]['ucs']), key="a_ucs")
        a_gsi  = st.slider("GSI_A", 10, 100, layers_data[-1]['gsi'], key="a_gsi")
        a_temp = st.number_input("T_A (°C)", value=float(T_source_max), key="a_t")
    with sc2:
        st.markdown("**Ssenariy B**")
        b_ucs  = st.number_input("UCS_B (MPa)", value=float(layers_data[-1]['ucs'])*0.8, key="b_ucs")
        b_gsi  = st.slider("GSI_B", 10, 100, max(10, layers_data[-1]['gsi']-10), key="b_gsi")
        b_temp = st.number_input("T_B (°C)", value=float(T_source_max)*1.1, key="b_t")
    def norm(val, mn, mx):
        return (val-mn)/(mx-mn+1e-12)
    fos_a = (a_ucs*np.exp(-0.0025*(a_temp-20))) / (layers_data[-1]['rho']*9.81*H_seam/1e6+1e-12)
    fos_b = (b_ucs*np.exp(-0.0025*(b_temp-20))) / (layers_data[-1]['rho']*9.81*H_seam/1e6+1e-12)
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

# 6. Sezgirlik tahlili (Tornado plot)
@st.cache_data(show_spinner=False)
def sensitivity_analysis(base_ucs, base_gsi, base_d, base_nu, base_t, H_seam, range_pct=0.2):
    def quick_fos(ucs, gsi, d, nu, T):
        mb = 10*np.exp((gsi-100)/(28-14*d))
        s = np.exp((gsi-100)/(9-3*d))
        damage = np.clip(1-np.exp(-0.002*max(T-100,0)),0,0.95)
        sigma_ci = ucs*(1-damage)
        str_red = np.exp(-0.0025*(T-20))
        p_str = (sigma_ci*str_red)*(20/(H_seam+1e-12))**0.5
        sv = ucs*0.025
        return np.clip(p_str/(sv+1e-12),0,5)
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
    df_sens, fos_base = sensitivity_analysis(layers_data[-1]['ucs'], layers_data[-1]['gsi'], D_factor, nu_poisson, avg_t_p, H_seam)
    df_sens = df_sens.sort_values('high', ascending=True)
    fig_tornado = go.Figure()
    fig_tornado.add_bar(y=df_sens['param'], x=df_sens['low'], orientation='h', name='−20%', marker_color='#E74C3C')
    fig_tornado.add_bar(y=df_sens['param'], x=df_sens['high'], orientation='h', name='+20%', marker_color='#27AE60')
    fig_tornado.add_vline(x=0, line_color='white', line_width=2)
    fig_tornado.update_layout(title=f"FOS sezgirligi (asosiy FOS={fos_base:.2f})", barmode='overlay', template='plotly_dark', height=350, xaxis_title='ΔFOS', bargap=0.3)
    st.plotly_chart(fig_tornado, use_container_width=True)

# =========================== KENGAYTIRILGAN ISO 9001 HISOBOT GENERATORI ===========================
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
    t_iso = texts.get(lang, texts['en'])
    doc = Document()
    header = doc.add_heading(f"{t_iso['h1']}\n{obj_name}", level=1)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.style = 'Table Grid'
    meta_table.cell(0,0).text = f"Doc No: {doc_number}"
    meta_table.cell(0,1).text = f"Revision: {revision}"
    meta_table.cell(1,0).text = f"Prepared: {prepared_by}"
    meta_table.cell(1,1).text = f"Approved: {approved_by}"
    doc.add_heading(t_iso['sec1'], level=2)
    p = doc.add_paragraph()
    p.add_run(f"Ob'ekt nomi: ").bold = True
    p.add_run(f"{obj_name}\n")
    p.add_run(f"Maksimal harorat: ").bold = True
    p.add_run(f"{T_source_max} °C\n")
    p.add_run(f"Yonish davomiyligi: ").bold = True
    p.add_run(f"{burn_duration} soat")
    doc.add_heading(t_iso['sec2'], level=2)
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
    if fig_bytes:
        doc.add_heading("Visual Analysis (Spatial Model)", level=2)
        image_stream = io.BytesIO(fig_bytes)
        doc.add_picture(image_stream, width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_heading(t_iso['sec5'], level=2)
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
        conclusion_text = t_iso['danger']
        color = RGBColor(255, 0, 0)
    elif fos_val < 1.5:
        conclusion_text = t_iso['warning']
        color = RGBColor(255, 165, 0)
    else:
        conclusion_text = t_iso['safe']
    res_p = doc.add_paragraph()
    res_p.add_run(f"{t_iso['fos_label']} {fos_val:.2f}\n").bold = True
    res_p.add_run(f"{t_iso['ai_label']} {optimal_width_ai:.1f} m\n\n")
    final_run = res_p.add_run(f"{t_iso['conclusion_title']}\n{conclusion_text}")
    final_run.bold = True
    final_run.font.color.rgb = color
    doc.add_page_break()
    doc.add_heading("APPENDIX: Mathematical Models Used", level=2)
    doc.add_paragraph("1. Hoek-Brown Failure Criterion (Rock Mass Strength)")
    doc.add_paragraph("σ1 = σ3 + σci * (mb * σ3 / σci + s)^a", style='Intense Quote')
    doc.add_paragraph("2. Thermal Strength Decay (Exponential Model)")
    doc.add_paragraph("UCS(T) = UCS_0 * exp(-β * (T - T0))", style='Intense Quote')
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
                im = ax.imshow(risk_map, extent=[x_axis[0], x_axis[-1], z_axis[-1], z_axis[0]], cmap='hot', aspect='auto')
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

# ====================== ORIGINAL AI MONITORING (Live 3D, AI Monitoring, Advanced Analysis) ======================
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
        std = np.std(recent) + 1e-6
        return abs(value - mean) > threshold * std
    def simulate_sensors_fos(n_steps):
        T = np.linspace(20, min(1100,T_source_max), n_steps) + np.random.normal(0,10,n_steps)
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
                return self.fc3(x)
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
            fos_target = st.number_input("Maqsad FOS qiymati", min_value=5.0, max_value=30.0, value=12.0, step=0.5)
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
                if y_pred < 10:
                    fos_color = t('fos_red')
                elif y_pred <= 15:
                    fos_color = t('fos_yellow')
                else:
                    fos_color = t('fos_green')
                with placeholder_2.container():
                    p2c1, p2c2, p2c3 = st.columns(3)
                    p2c1.metric("🌡 Harorat", f"{row.Temperature:.1f} °C")
                    p2c2.metric("🧱 Vertikal Stress", f"{row.VerticalStress:.2f} MPa")
                    p2c3.metric("📊 Bashorat FOS", f"{y_pred:.2f}", delta=fos_color)
                    fig_fos = make_subplots(rows=1, cols=2, subplot_titles=("FOS Bashorati (Tarixiy)", "Sensor: Harorat vs Stress"))
                    fig_fos.add_trace(go.Scatter(y=pillar_strength_pred, mode='lines+markers', name=t('pillar_live'), line=dict(color='lime',width=2), marker=dict(size=5)), row=1, col=1)
                    fig_fos.add_hline(y=fos_target, line_dash="dash", line_color="yellow", annotation_text=f"Maqsad: {fos_target}", row=1, col=1)
                    fig_fos.add_trace(go.Scatter(x=sensor_data_fos['Temperature'].iloc[:i+1].tolist(), y=sensor_data_fos['VerticalStress'].iloc[:i+1].tolist(), mode='markers', name='Sensor yo\'li', marker=dict(color=list(range(i+1)), colorscale='Viridis', size=6, showscale=False)), row=1, col=2)
                    fig_fos.update_layout(template="plotly_dark", height=420, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), margin=dict(t=60,b=60))
                    fig_fos.update_xaxes(title_text="Qadam", row=1, col=1)
                    fig_fos.update_yaxes(title_text="FOS / Strength", row=1, col=1)
                    fig_fos.update_xaxes(title_text="Harorat (°C)", row=1, col=2)
                    fig_fos.update_yaxes(title_text="Vertikal Stress (MPa)", row=1, col=2)
                    st.plotly_chart(fig_fos, use_container_width=True, key=f"fospred_{i}")
                    st.info(f"Qadam {i+1}/{int(ai_steps_2)} | Model: {'PyTorch SimpleNN' if PT_AVAILABLE else 'RandomForest'} | {fos_color}")
                    st.progress((i+1)/int(ai_steps_2))
                time.sleep(0.05)
            st.balloons()
            final_fos = pillar_strength_pred[-1] if pillar_strength_pred else 0
            if final_fos < 10:
                st.error(f"🔴 Yakuniy FOS: {final_fos:.2f} — Xavfli zona!")
            elif final_fos <= 15:
                st.warning(f"🟡 Yakuniy FOS: {final_fos:.2f} — Noaniq holat")
            else:
                st.success(f"🟢 Yakuniy FOS: {final_fos:.2f} — Barqaror!")

with tab_advanced:
    st.header(t('advanced_analysis'))
    E_MODULUS_R, ALPHA_THERM, BETA_CONST = 5000.0, 1.0e-5, beta_thermal
    target_l = layers_data[-1]
    ucs_0_r, gsi_val, mi_val = target_l['ucs'], target_l['gsi'], target_l['mi']
    gamma_kn = target_l['rho'] * 9.81 / 1000
    H_depth_tot = sum(l['t'] for l in layers_data[:-1]) + target_l['t']/2
    sigma_v_tot = (gamma_kn * H_depth_tot) / 1000
    mb_dyn = mi_val * np.exp((gsi_val-100)/(28-14*D_factor))
    s_dyn = np.exp((gsi_val-100)/(9-3*D_factor))
    ucs_t_dyn = ucs_0_r * np.exp(-BETA_CONST*(T_source_max-20))
    p_str_final = ucs_t_dyn * (rec_width/(H_seam+EPS))**0.5
    fos_final = p_str_final/(sigma_v_tot+EPS)
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
            st.markdown(t('hb_interpret', gsi=gsi_val, perc=((1 - s_dyn)*100)))
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
        st.latex(t('thermal_stress_eq', sigma=sigma_thermal.max()))
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
        for r in [t('ref1'), t('ref2'), t('ref3'), t('ref4'), "**Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics for Underground Mining."]:
            st.write(r)

# =========================== INTEGRATSIYA QISMI: INTERACTIVE UCG DASHBOARD (YANGI VERSIYA) ===========================
st.header("🕹️ Ultimate Interactive Dashboard (Real-time Animation)")
st.markdown("Bu panelda siz **yonish radiusi**, **FOS chegarasi** va **ranglar** kabi parametrlarni slayderlar bilan o‘zgartirib, real vaqtda 2D FOS, stress va siljish xaritalarini kuzatishingiz mumkin. Shuningdek, **selek interferensiyasi** va **faol yonish doiralari** vizualizatsiya qilingan.")

# Yangi dashboard uchun funksiyalar (ikkinchi koddan olingan)
def generate_simulation_data(x_axis, z_axis, coal_thickness, pillar_locations, burn_radius, fos_thresh):
    """Simulated FOS, displacement, stress based on inputs"""
    X, Z = np.meshgrid(x_axis, z_axis)
    # FOS: depends on distance to pillars and burn radius
    fos = 1.5 * np.ones_like(X)
    for p in pillar_locations:
        dist_to_pillar = np.abs(X - p)
        fos *= (1 + 0.3 * np.exp(-dist_to_pillar**2 / 100))
    fos = fos * (1 - 0.2 * np.exp(-(Z - coal_thickness/2)**2 / 50))
    fos += 0.2 * np.sin(X/15) - 0.1 * np.cos(Z/10)
    fos = np.clip(fos, 0.2, 3.0)
    
    # Displacement (cm) - higher near burn radius and pillars
    disp = 2 * np.exp(-((X - 100)**2 + (Z - coal_thickness/2)**2) / (2*burn_radius**2))
    for p in pillar_locations:
        disp += 0.5 * np.exp(-(X - p)**2 / 100)
    disp = np.clip(disp, 0, 12)
    
    # Stress (MPa)
    stress = 40 + 15 * np.sin(X/20) * np.cos(Z/12)
    stress += 5 * np.exp(-((X - 100)**2 + (Z - 10)**2) / 200)
    stress = np.clip(stress, 20, 80)
    
    return fos, disp, stress

def draw_dashboard(x_axis, z_axis, fos, disp, stress, burn_radius, pillar_locations, 
                   interference_pairs, fos_thresh, disp_colorscale, fracture_mask, void_mask):
    fig = make_subplots(rows=1, cols=2, subplot_titles=("FOS & Yielded Zones", "Stress & Displacement"))
    # Left: FOS
    fig.add_trace(go.Heatmap(
        z=fos, x=x_axis, y=z_axis,
        colorscale=[[0,'rgb(255,0,0)'],[0.33,'rgb(255,165,0)'],[0.5,'rgb(173,255,47)'],[1,'rgb(0,128,0)']],
        zmin=0, zmax=3, colorbar=dict(title="FOS")
    ), row=1, col=1)
    # Yielded zones overlay
    fig.add_trace(go.Heatmap(
        z=fracture_mask, x=x_axis, y=z_axis,
        colorscale=[[0,'rgba(255,0,0,0)'],[1,'rgba(255,0,0,0.5)']],
        showscale=False
    ), row=1, col=1)
    # Pillars
    for p in pillar_locations:
        fig.add_shape(type="rect", x0=p-5, x1=p+5, y0=0, y1=z_axis.max(),
                      line=dict(color="lime", width=2), row=1, col=1)
    # Selek interference lines
    for pair in interference_pairs:
        fig.add_shape(type="line", x0=pair[0], x1=pair[1], y0=z_axis.mean(), y1=z_axis.mean(),
                      line=dict(color="red", width=3, dash="dash"), row=1, col=1)
    # Burn radius circles
    for p in pillar_locations:
        fig.add_shape(type="circle", x0=p-burn_radius, x1=p+burn_radius,
                      y0=z_axis.mean()-burn_radius, y1=z_axis.mean()+burn_radius,
                      line=dict(color="orange", width=2), row=1, col=1)
    # Right: Stress
    fig.add_trace(go.Heatmap(
        z=stress, x=x_axis, y=z_axis,
        colorscale='Viridis', colorbar=dict(title="Stress (MPa)")
    ), row=1, col=2)
    # Displacement overlay
    fig.add_trace(go.Heatmap(
        z=disp, x=x_axis, y=z_axis,
        colorscale=disp_colorscale, colorbar=dict(title="Disp (cm)"),
        opacity=0.7
    ), row=1, col=2)
    # Void overlay
    fig.add_trace(go.Heatmap(
        z=void_mask, x=x_axis, y=z_axis,
        colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(255,255,255,0.5)']],
        showscale=False
    ), row=1, col=2)
    fig.update_layout(template='plotly_dark', height=600, width=1200,
                      title=dict(text="Ultimate 2D UCG Dashboard (Stress, Yield, Burn & Displacement)", x=0.5),
                      showlegend=False)
    fig.update_yaxes(autorange="reversed")
    return fig

def compute_selek_interference(pillars, burn_radius):
    interference = []
    optimal_dist = []
    for i in range(len(pillars)-1):
        for j in range(i+1, len(pillars)):
            dist = abs(pillars[j]-pillars[i])
            if dist < burn_radius*2:
                interference.append((pillars[i], pillars[j]))
                optimal_dist.append(burn_radius*2)
    return interference, optimal_dist

# Dashboard uchun kerakli o‘qlar va boshlang‘ich parametrlar
dash_x_axis = np.linspace(0, 200, 100)
dash_z_axis = np.linspace(0, 50, 50)
coal_thickness = layers_data[0]['t']  # birinchi qatlam qalinligi
pillar_locations = np.linspace(25, 175, 3)  # 3 ta selek

# Slayderlar (interaktiv)
col_fos, col_rad, col_cscale = st.columns(3)
with col_fos:
    fos_thresh_dash = st.slider(t('fos_threshold'), 0.1, 2.0, 1.0, 0.05, key="fos_dash")
with col_rad:
    burn_radius_dash = st.slider(t('burn_radius'), 5, 50, 15, 1, key="burn_rad_dash")
with col_cscale:
    disp_cscale_dash = st.selectbox(t('disp_colorscale'), ['Turbo','Viridis','Cividis'], index=0, key="disp_cscale_dash")

# Simulyatsiya ma'lumotlarini yangilash
fos_dash, disp_dash, stress_dash = generate_simulation_data(
    dash_x_axis, dash_z_axis, coal_thickness, pillar_locations, burn_radius_dash, fos_thresh_dash
)
fracture_mask_dash = np.where(fos_dash < fos_thresh_dash, 1, np.nan)
void_mask_dash = np.where(disp_dash > 3, disp_dash, np.nan)
interference_pairs, _ = compute_selek_interference(pillar_locations, burn_radius_dash)

# Dashboardni chizish
dash_fig = draw_dashboard(dash_x_axis, dash_z_axis, fos_dash, disp_dash, stress_dash,
                          burn_radius_dash, pillar_locations, interference_pairs,
                          fos_thresh_dash, disp_cscale_dash, fracture_mask_dash, void_mask_dash)
st.plotly_chart(dash_fig, use_container_width=True)

# Info panel
st.markdown(f"""
- {t('pillar_info')}
- {t('interference_info')}
- {t('burn_info')}
- {t('void_info')}
- {t('coal_thickness_info', thick=coal_thickness)}
""")

# =========================== ASOSIY ILMIY METODOLOGIYA (Yakuniy) ===========================
with st.expander(t('methodology_expander')):
    st.markdown("#### Ushbu model quyidagi fundamental ilmiy ishlar asosida tuzilgan:")
    for r in [t('ref1'), t('ref2'), t('ref3'), t('ref4'), "**Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics for Underground Mining."]:
        st.write(r)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")
