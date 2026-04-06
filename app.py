import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
import time

# =========================== TIL QO'LLAB-QUVVATLASH ===========================
if 'language' not in st.session_state:
    st.session_state.language = 'uz'

LANGUAGES = {
    'uz': "🇺🇿 O'zbek",
    'en': '🇬🇧 English',
    'ru': '🇷🇺 Русский'
}

lang = st.sidebar.selectbox(
    "Til / Language / Язык",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x],
    index=list(LANGUAGES.keys()).index(st.session_state.language)
)
st.session_state.language = lang

def t(key, **kwargs):
    translations = {
        'uz': {
            'app_title': "Universal Yer yuzasi Deformatsiyasi Monitoringi",
            'app_subtitle': "Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi",
            'sidebar_header_params': "⚙️ Umumiy parametrlar",
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
        },
        'en': {
            'app_title': "Universal Surface Deformation Monitoring",
            'app_subtitle': "Thermo-Mechanical (TM) Analysis and Pillar Size Optimization",
            'sidebar_header_params': "⚙️ General Parameters",
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
        },
        'ru': {
            'app_title': "Универсальный мониторинг деформации земной поверхности",
            'app_subtitle': "Термо-механический (ТМ) анализ и оптимизация размера целика",
            'sidebar_header_params': "⚙️ Общие параметры",
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
        }
    }
    current = translations.get(st.session_state.language, translations['uz'])
    text = current.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# =========================== PYTORCH ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
except ImportError:
    PT_AVAILABLE = False
    st.warning(t('warning_pytorch'))
    from sklearn.ensemble import RandomForestClassifier

EPS = 1e-12

st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

# =========================== MATEMATIK METODOLOGIYA ===========================
st.sidebar.header(t('sidebar_header_params'))
formula_option = st.sidebar.selectbox(
    "Formulalarni ko'rish:",
    ["Yopish", "1. Hoek-Brown Failure (2018)",
     "2. Thermal Damage & Permeability",
     "3. Thermal Stress & Tension",
     "4. Pillar & Subsidence"]
)

if formula_option != "Yopish":
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == "1. Hoek-Brown Failure (2018)":
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.latex(r"m_b = m_i \exp\left(\frac{GSI-100}{28-14D}\right); \quad s = \exp\left(\frac{GSI-100}{9-3D}\right)")
            st.latex(r"a = \frac{1}{2} + \frac{1}{6} \left( e^{-GSI/15} - e^{-20/3} \right)")
            st.info("**Hoek-Brown:** GSI va Disturbance (D) faktorlari asosida massiv mustahkamligini hisoblash.")
        elif formula_option == "2. Thermal Damage & Permeability":
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
            st.latex(r"\sigma_{ci(T)} = \sigma_{ci} \cdot (1 - D(T))")
            st.latex(r"k = k_0 \left[ 1 + 20 \cdot D(T) + 50 \cdot V_{void} \right]")
            st.info("**Termal degradatsiya:** Harorat ta'sirida jins strukturasining emirilishi va o'tkazuvchanlik ortishi.")
        elif formula_option == "3. Thermal Stress & Tension":
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu} + \xi \cdot \nabla T")
            st.latex(r"\sigma_{t(T)} = \sigma_{t0} \cdot \exp\left(-\beta_{th} (T - 20)\right)")
            st.latex(r"FOS = \frac{\sigma_{limit}}{\sigma_{actual}}")
            st.info("**Termo-mexanika:** Termal kengayish kuchlanishi va cho'zilish mustahkamligining kamayishi.")
        elif formula_option == "4. Pillar & Subsidence":
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
        col1, col2 = st.columns([2, 1])
        with col1:
            name  = st.text_input(t('layer_name'), value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(t('thickness'), value=50.0, key=f"t_{i}")
            u     = st.number_input(t('ucs'), value=40.0, key=f"u_{i}")
            rho   = st.number_input(t('density'), value=2500.0, key=f"rho_{i}")
        with col2:
            color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g     = st.slider(t('gsi'), 10, 100, 60, key=f"g_{i}")
            m     = st.number_input(t('mi'), value=10.0, key=f"m_{i}")
        s_t0_val = st.number_input(t('manual_st0'), value=3.0, key=f"st_{i}") if tensile_mode == t('tensile_manual') else 0.0

    layers_data.append({
        'name': name, 't': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

# =========================== VALIDATSIYA ===========================
def validate_layer(layer: dict) -> list:
    errors = []
    if layer['t'] <= 0: errors.append(t('error_thick_positive'))
    if layer['ucs'] <= 0: errors.append(t('error_ucs_positive'))
    if layer['rho'] <= 0: errors.append(t('error_density_positive'))
    if not (10 <= layer['gsi'] <= 100): errors.append(t('error_gsi_range'))
    if layer['mi'] <= 0: errors.append(t('error_mi_positive'))
    return errors

for lyr in layers_data:
    errs = validate_layer(lyr)
    if errs:
        st.error(f"❌ {lyr['name']} qatlamida xato: {', '.join(errs)}")
        st.stop()
if not layers_data:
    st.error(t('error_min_layers'))
    st.stop()

# =========================== GRID VA MANBA ===========================
x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam   = layers_data[-1]['t']

grid_sigma_v = np.zeros_like(grid_z)
grid_ucs     = np.zeros_like(grid_z)
grid_mb      = np.zeros_like(grid_z)
grid_s_hb    = np.zeros_like(grid_z)
grid_a_hb    = np.zeros_like(grid_z)
grid_sigma_t0_manual = np.zeros_like(grid_z)

if ('max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape):
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name
elif st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1:
        mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask]     = layer['ucs']
    grid_mb[mask]      = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask]    = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask]    = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

alpha_rock = 1.0e-6
sources = {
    '1': {'x': -total_depth/3, 'start': 0},
    '2': {'x': 0, 'start': 40},
    '3': {'x': total_depth/3, 'start': 80},
}
temp_2d = np.ones_like(grid_x) * 25.0

for val in sources.values():
    if time_h > val['start']:
        dt_sec = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
        elapsed = time_h - val['start']
        curr_T = (T_source_max if elapsed <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration)))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

# =========================== HEAT SOLVER ===========================
def solve_heat_step(T, Q, alpha, dx, dt):
    Tn = T.copy()
    Tn[1:-1,1:-1] = (T[1:-1,1:-1] + alpha*dt*((T[2:,1:-1]-2*T[1:-1,1:-1]+T[:-2,1:-1])/(dx**2+EPS) + (T[1:-1,2:]-2*T[1:-1,1:-1]+T[1:-1,:-2])/(dx**2+EPS)) + Q[1:-1,1:-1]*dt)
    return Tn

Q_heat = np.zeros_like(temp_2d)
for val in sources.values():
    if time_h > val['start']:
        elapsed = time_h - val['start']
        curr_T = (T_source_max if elapsed <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration)))
        Q_heat += (curr_T/10.0) * np.exp(-((grid_x - val['x'])**2 + (grid_z - source_z)**2)/(2*30**2))

DX, DT, N_STEPS = 1.0, 0.1, 20
for _ in range(N_STEPS):
    temp_2d = solve_heat_step(temp_2d, Q_heat, alpha_rock, dx=DX, dt=DT)

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25.0

# =========================== TM TAHLIL ===========================
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)

sigma_thermal = CONSTRAINT_FACTOR * (E_MODULUS * ALPHA_T_COEFF * delta_T) / (1 - nu_poisson + EPS)
sigma_thermal += 0.3 * thermal_gradient

grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == t('tensile_empirical'):
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == t('tensile_hb'):
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb + EPS)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
thermal_boost = 1 + 0.6 * (1 - np.exp(-delta_T/200))
sigma_t_field_eff = sigma_t_field / (thermal_boost + EPS)

tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50) & (sigma1_act > sigma3_act)
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe/(sigma_ci+EPS) + grid_s_hb) ** grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > 400)
crushing = shear_failure & (temp_2d > 600)

depth_factor = np.exp(-grid_z/(total_depth+EPS))
local_collapse_T = np.clip((st.session_state.max_temp_map - 600)/300, 0, 1)
time_factor = np.clip((time_h - 40)/60, 0, 1)
collapse_final = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw = spalling | crushing | (st.session_state.max_temp_map > 900)
void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth > 0.3) & (collapse_final > 0.05)

perm = 1e-15 * (1 + 20*damage + 50*void_mask_permanent.astype(float))
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])

sigma1_act = np.where(void_mask_permanent, 0.0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0.0, sigma3_act)
sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)

# =========================== GAS FLOW ===========================
pressure = temp_2d * 10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx, vz = -perm * dp_dx, -perm * dp_dz
gas_velocity = np.sqrt(vx**2 + vz**2)

# =========================== AI MODEL ===========================
@st.cache_resource(show_spinner=False)
def get_nn_model():
    if not PT_AVAILABLE:
        return None
    def generate_ucg_dataset(n=10000):
        data = []
        for _ in range(n):
            T = np.random.uniform(20,1000)
            sigma1 = np.random.uniform(0,50)
            sigma3 = np.random.uniform(0,30)
            depth = np.random.uniform(0,300)
            damage = 1 - np.exp(-0.002*max(T-100,0))
            strength = 40*(1-damage)
            collapse = 1 if (sigma1>strength or T>700) else 0
            data.append([T,sigma1,sigma3,depth,collapse])
        return np.array(data)
    class CollapseNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(4,32), nn.ReLU(), nn.Linear(32,64), nn.ReLU(), nn.Linear(64,1), nn.Sigmoid())
        def forward(self,x): return self.net(x)
    data = generate_ucg_dataset()
    X = torch.tensor(data[:,:-1], dtype=torch.float32)
    y = torch.tensor(data[:,-1], dtype=torch.float32).view(-1,1)
    model = CollapseNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.BCELoss()
    for epoch in range(50):
        pred = model(X); loss = loss_fn(pred,y)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
    model.eval()
    return model

def predict_nn(model, temp, s1, s3, depth):
    X = np.column_stack([temp.flatten(), s1.flatten(), s3.flatten(), depth.flatten()])
    X_t = torch.tensor(X, dtype=torch.float32)
    with torch.no_grad():
        pred = model(X_t).numpy()
    return pred.reshape(temp.shape)

nn_model = get_nn_model()
if nn_model is not None and PT_AVAILABLE:
    try:
        collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)
    except Exception as e:
        st.warning(f"PyTorch xatosi: {e}. RandomForest ishlatiladi.")
        nn_model = None
if nn_model is None or not PT_AVAILABLE:
    from sklearn.ensemble import RandomForestClassifier
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai))>1:
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
    p_strength = (ucs_seam*strength_red) * (w_sol/(H_seam+EPS))**0.5
    y_zone_calc = (H_seam/2)*(np.sqrt(sv_seam/(p_strength+EPS))-1)
    new_w = 2*max(y_zone_calc,1.5) + 0.5*H_seam
    if abs(new_w-w_sol)<0.1: break
    w_sol = new_w
rec_width = np.round(w_sol,1)
pillar_strength = p_strength
y_zone = max(y_zone_calc,1.5)

fos_2d = np.clip(sigma1_limit/(sigma1_act+EPS),0,3.0)
fos_2d = np.where(void_mask_permanent,0.0,fos_2d)
void_frac_base = float(np.mean(void_mask_permanent))

def objective(w_arr):
    w = w_arr[0]
    strength = (ucs_seam*strength_red)*(w/(H_seam+EPS))**0.5
    risk = void_frac_base * np.exp(-0.01*(w-rec_width))
    return -(strength - 15.0*risk)

opt_result = minimize(objective, x0=[rec_width], bounds=[(5.0,100.0)], method='SLSQP')
optimal_width_ai = float(np.clip(opt_result.x[0],5.0,100.0))

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

# =========================== TM MAYDONI ===========================
st.markdown("---")
c1, c2 = st.columns([1,2.5])
with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red'))
    st.warning(t('fos_yellow'))
    st.success(t('fos_green'))
    fig_s = go.Figure()
    for lyr in layers_data:
        fig_s.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

with c2:
    st.subheader(t('tm_field_title'))
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=(t('temp_subplot'), t('fos_subplot')))
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, colorbar=dict(title="T (°C)", title_side="top", x=1.05, y=0.78, len=0.42, thickness=15), name=t('temp_subplot')), row=1, col=1)
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
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime",width=3), row=2, col=1)
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name=t('ai_collapse')), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(r=150,t=80,b=100), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

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
mk1,mk2,mk3,mk4 = st.columns(4)
mk1.metric(t('pillar_live'), f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric(t('rec_width_live'), f"{w_rec_live:.1f} m")
mk3.metric(t('max_subsidence_live'), f"{s_max_3d*100:.1f} cm")
mk4.metric(t('process_stage'), t('stage_active') if time_h<100 else t('stage_cooling'))
st.markdown("---")

# ====================== AI PREDICTIVE MONITORING ======================
st.header(t('ai_monitor_title'))
st.markdown(f"*{t('ai_monitor_desc')}*")

# ---- Umumiy yordamchi funksiyalar ----
def get_sensor_data_sim(base_temp=None):
    """Sensor ma'lumotlarini simulyatsiya qiladi (UCG parametrlariga bog'liq)"""
    base = base_temp if base_temp else T_source_max * 0.6
    return {
        "temperature": np.random.uniform(base * 0.4, min(base * 1.1, T_source_max)),
        "gas_pressure": np.random.uniform(1, 8),
        "stress": np.random.uniform(5, min(15, sv_seam * 10))
    }

def compute_effective_stress(sensor):
    """Digital Twin: effektiv kuchlanish hisoblash"""
    thermo    = sensor["stress"] + 0.01 * sensor["temperature"]
    effective = thermo - sensor["gas_pressure"]
    return effective

def detect_anomaly_z(history, value, threshold=2.0):
    """Z-score asosida anomaliya aniqlash"""
    if len(history) < 10:
        return False
    std = np.std(history)
    if std < 1e-9:
        return False
    return abs(value - np.mean(history)) > threshold * std

def simulate_sensors_fos(n_steps):
    """FOS Prediction uchun sensor ma'lumotlari"""
    T      = np.linspace(20, min(1100, T_source_max), n_steps) + np.random.normal(0, 10, n_steps)
    sigma_v = np.linspace(5, min(15, sv_seam * 10), n_steps) + np.random.normal(0, 0.5, n_steps)
    return pd.DataFrame({'Temperature': T, 'VerticalStress': sigma_v})

# ---- SimpleNN (FOS Prediction uchun) ----
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
            return self.fc3(x)
    fos_nn_model  = SimpleNN()
    fos_criterion = nn.MSELoss()
    fos_optimizer = torch.optim.Adam(fos_nn_model.parameters(), lr=0.01)
else:
    from sklearn.ensemble import RandomForestRegressor
    fos_rf_model = RandomForestRegressor(n_estimators=50, random_state=42)

# ---- Ikkita tab: birinchisi Anomaly Detection, ikkinchisi FOS Prediction ----
ai_tab1, ai_tab2 = st.tabs([
    "📡 Anomaliya Aniqlash (Digital Twin)",
    "📊 FOS Prediction (SimpleNN / RF)"
])

# ==== TAB 1: Anomaliya aniqlash ====
with ai_tab1:
    st.markdown("#### Sensor ma'lumotlari asosida real-vaqt anomaliya aniqlash")
    t1_col1, t1_col2, t1_col3 = st.columns([1, 1, 2])
    with t1_col1:
        ai_steps_1 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=60, step=10, key="ai_steps_1")
    with t1_col2:
        anomaly_threshold = st.slider("Anomaliya chegarasi (σ)", 1.0, 4.0, 2.0, 0.5, key="thresh_1")
    with t1_col3:
        run_ai_1 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_1")

    if run_ai_1:
        placeholder_1  = st.empty()
        history_eff    = []
        anomalies_eff  = []
        temp_history   = []
        gas_history    = []
        stress_history = []

        for step in range(int(ai_steps_1)):
            sensor     = get_sensor_data_sim(base_temp=T_source_max * 0.6)
            effective  = compute_effective_stress(sensor)
            is_anomaly = detect_anomaly_z(history_eff, effective, threshold=anomaly_threshold)

            history_eff.append(effective)
            anomalies_eff.append(effective if is_anomaly else None)
            temp_history.append(sensor["temperature"])
            gas_history.append(sensor["gas_pressure"])
            stress_history.append(sensor["stress"])

            with placeholder_1.container():
                acol1, acol2, acol3, acol4 = st.columns(4)
                acol1.metric("🌡 Harorat", f"{sensor['temperature']:.1f} °C",
                             delta=f"{sensor['temperature'] - np.mean(temp_history):.1f}" if len(temp_history) > 1 else None)
                acol2.metric("💨 Gaz bosimi", f"{sensor['gas_pressure']:.2f} MPa")
                acol3.metric("🧱 Effektiv σ", f"{effective:.2f} MPa",
                             delta_color="inverse",
                             delta="⚠️ Anomaliya!" if is_anomaly else "Normal")
                acol4.metric("📈 Qadam", f"{step+1}/{int(ai_steps_1)}")

                fig_a = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(
                        "Effektiv Kuchlanish & Anomaliyalar",
                        "Harorat Tarixi (°C)",
                        "Gaz Bosimi (MPa)",
                        "Stress Tarixi (MPa)"
                    ),
                    vertical_spacing=0.15, horizontal_spacing=0.1
                )
                fig_a.add_trace(go.Scatter(y=history_eff, mode='lines', name='Effektiv σ',
                                           line=dict(color='cyan', width=2)), row=1, col=1)
                fig_a.add_trace(go.Scatter(y=anomalies_eff, mode='markers', name='Anomaliya',
                                           marker=dict(color='red', size=10, symbol='x')), row=1, col=1)
                fig_a.add_trace(go.Scatter(y=temp_history, mode='lines', name='Harorat',
                                           line=dict(color='orange', width=2)), row=1, col=2)
                fig_a.add_trace(go.Scatter(y=gas_history, mode='lines+markers', name='Gaz bosimi',
                                           line=dict(color='lime', width=1), marker=dict(size=4)), row=2, col=1)
                fig_a.add_trace(go.Scatter(y=stress_history, mode='lines', name='Stress',
                                           line=dict(color='magenta', width=2)), row=2, col=2)
                fig_a.update_layout(template="plotly_dark", height=500, showlegend=True,
                                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                                    margin=dict(t=60, b=60))
                st.plotly_chart(fig_a, use_container_width=True)

                anomaly_count = sum(1 for a in anomalies_eff if a is not None)
                if is_anomaly:
                    st.error(f"🚨 ANOMALIYA ANIQLANDI! (Jami: {anomaly_count}) — Collapse ehtimoli yuqori!")
                elif effective > pillar_strength * 0.8:
                    st.warning(f"⚠️ Kuchlanish Pillar Strength ({pillar_strength:.1f} MPa) ning 80% dan oshdi!")
                else:
                    st.success(f"✅ Normal holat — Effektiv σ: {effective:.2f} MPa")

                st.progress((step + 1) / int(ai_steps_1))

            time.sleep(0.15)

        st.balloons()
        st.success(f"✅ Monitoring yakunlandi! Jami anomaliyalar: {sum(1 for a in anomalies_eff if a is not None)}")

# ==== TAB 2: FOS Prediction ====
with ai_tab2:
    st.markdown("#### SimpleNN yoki RandomForest yordamida FOS (Factor of Safety) bashorati")

    t2_col1, t2_col2 = st.columns([1, 3])
    with t2_col1:
        ai_steps_2 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=50, step=10, key="ai_steps_2")
        fos_target = st.number_input("Maqsad FOS qiymati", min_value=5.0, max_value=30.0, value=12.0, step=0.5)
    with t2_col2:
        run_ai_2 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_2")

    if run_ai_2:
        placeholder_2       = st.empty()
        sensor_data_fos     = simulate_sensors_fos(int(ai_steps_2))
        pillar_strength_pred = []
        fos_rf_trained       = False

        for i in range(int(ai_steps_2)):
            row = sensor_data_fos.iloc[i]
            X   = np.array([[row.Temperature, row.VerticalStress]])

            if PT_AVAILABLE:
                X_t    = torch.tensor(X, dtype=torch.float32)
                y_pred = fos_nn_model(X_t).detach().numpy()[0][0]
                target = torch.tensor([[fos_target]], dtype=torch.float32)
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

            # FOS rangini aniqlash
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

                fig_fos = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=("FOS Bashorati (Tarixiy)", "Sensor: Harorat vs Stress")
                )
                fig_fos.add_trace(go.Scatter(
                    y=pillar_strength_pred, mode='lines+markers',
                    name=t('pillar_live'),
                    line=dict(color='lime', width=2),
                    marker=dict(size=5)
                ), row=1, col=1)
                # Maqsad chizig'i
                fig_fos.add_hline(y=fos_target, line_dash="dash", line_color="yellow",
                                  annotation_text=f"Maqsad: {fos_target}", row=1, col=1)
                # Harorat vs Stress scatter
                fig_fos.add_trace(go.Scatter(
                    x=sensor_data_fos['Temperature'].iloc[:i+1].tolist(),
                    y=sensor_data_fos['VerticalStress'].iloc[:i+1].tolist(),
                    mode='markers',
                    name='Sensor yo\'li',
                    marker=dict(
                        color=list(range(i+1)),
                        colorscale='Viridis',
                        size=6,
                        showscale=False
                    )
                ), row=1, col=2)

                fig_fos.update_layout(
                    template="plotly_dark", height=420,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                    margin=dict(t=60, b=60)
                )
                fig_fos.update_xaxes(title_text="Qadam", row=1, col=1)
                fig_fos.update_yaxes(title_text="FOS / Strength", row=1, col=1)
                fig_fos.update_xaxes(title_text="Harorat (°C)", row=1, col=2)
                fig_fos.update_yaxes(title_text="Vertikal Stress (MPa)", row=1, col=2)
                st.plotly_chart(fig_fos, use_container_width=True)

                st.info(f"Qadam {i+1}/{int(ai_steps_2)} | Model: {'PyTorch SimpleNN' if PT_AVAILABLE else 'RandomForest'} | {fos_color}")
                st.progress((i + 1) / int(ai_steps_2))

            time.sleep(0.05)

        st.balloons()
        final_fos = pillar_strength_pred[-1] if pillar_strength_pred else 0
        if final_fos < 10:
            st.error(f"🔴 Yakuniy FOS: {final_fos:.2f} — Xavfli zona!")
        elif final_fos <= 15:
            st.warning(f"🟡 Yakuniy FOS: {final_fos:.2f} — Noaniq holat")
        else:
            st.success(f"🟢 Yakuniy FOS: {final_fos:.2f} — Barqaror!")

st.markdown("---")

# =========================== ILMIY HISOBOT ===========================
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
    params_df = pd.DataFrame({
        t('param_table_param'): [t('modulus'), t('alpha'), t('temp0')],
        t('param_table_value'): [f"{E_MODULUS_R} MPa", f"{ALPHA_THERM} 1/°C", "20 °C"],
        t('param_table_reason'): [t('modulus_reason'), t('alpha_reason'), t('temp0_reason')]
    })
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

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
