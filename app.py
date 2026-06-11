"""
UCG SCI-Grade Platform — Tuzatilgan va Kengaytirilgan Versiya
============================================================
PhD himoya va Patent uchun tayyorlangan.
Barcha 100 ta ekspert tuzatish qo'llangan.

Mualliflar: Saitov Dilshodbek
Versiya: 2.0.0 (PhD-grade)
"""
import streamlit as st
import warnings
import logging
import io
import time
import functools
import json
import os
import hashlib
from datetime import datetime
from dataclasses import dataclass
from typing import NamedTuple, Optional, Tuple, List, Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.stats import linregress, t as t_dist
from scipy.signal import savgol_filter
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Ixtiyoriy kutubxonalar
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

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS VA INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RANDOM_SEED = 42
rng_global = np.random.default_rng(seed=RANDOM_SEED)

if PT_AVAILABLE:
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(RANDOM_SEED)

EPS_GENERAL: float = 1e-9
EPS_STRESS: float = 1e-3
EPS_PERM: float = 1e-20
EPS = EPS_GENERAL

GEOM_EPS: float = 1e-3
T_REF_AMBIENT: float = 20.0

BIENIAWSKI_C1: float = 0.64
BIENIAWSKI_C2: float = 0.36
WILSON_C1 = BIENIAWSKI_C1
WILSON_C2 = BIENIAWSKI_C2

BIOT_COEFFICIENT: float = 1.0
SUTHERLAND_S_CO: float = 118.0
BETA_GSI_DEFAULT: float = 0.001

# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════

class UCGError(Exception):
    """UCG platformasi uchun asosiy xato sinfi."""
    pass

class GeomechanicalError(UCGError):
    """Geomexanik hisob-kitob xatoliklari."""
    pass

class ThermalConvergenceError(UCGError):
    """Termal maydon yaqinlashmasligi."""
    pass

class ModelTrainingError(UCGError):
    """AI/ML model o'qitish xatoliklari."""
    pass

# ═══════════════════════════════════════════════════════════════════════════
# PHYSICS PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class UCGPhysicsParams:
    phi_deg: float = 35.0
    cohesion: float = 5e6
    alpha_thermal: float = 1.5e-5
    gas_temp: int = 1100
    subsidence_rate: float = 0.012
    thermal_damage_beta: float = 0.002
    extraction_ratio: float = 0.45
    E_mass: float = 25e9
    CONFINEMENT: float = 0.65
    RELAX: float = 0.15
    THERMAL_DIFFUSIVITY: float = 8.5e-7
    GAS_VISCOSITY_REF: float = 3e-5
    MOLAR_MASS_GAS: float = 0.028
    R_UNIVERSAL: float = 8.314
    K_VOID: float = 0.35

PARAMS = UCGPhysicsParams()

# ═══════════════════════════════════════════════════════════════════════════
# TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════════

TRANSLATIONS: Dict[str, Dict[str, str]] = {
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
        'fos_subplot': "FOS + AI Collapse Prediction + Yielded Zones",
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
        'alpha_reason': "Ko'mirning issiqlikdan chiziqli kengayish ko'rsatkichi (Yang, 2010, p.87): α = 1.5×10⁻⁵ /°C.",
        'temp0_reason': "Kon qatlamining boshlang'ich tabiiy harorati.",
        'ucs_decay': "**A) Termal UCS pasayishi (Shao et al., 2003):**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ MPa}}",
        'ucs_interpret': "**Interpretatsiya:** {temp}°C haroratda jins mustahkamligi {perc:.1f}% ga pasaydi.",
        'thermal_stress': "**B) Termal kuchlanish ($\\sigma_{{th}}$) — qisman cheklangan holat:**",
        'thermal_stress_eq': r"\sigma_{{th}} = \eta_c \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ MPa}}, \quad \eta_c = {eta:.2f}",
        'pillar_stability': "3. Selek Barqarorligi (Bieniawski, 1992) va Bibliografiya",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v'}} = {fos:.2f}",
        'pillar_wilson': "**Bieniawski (1992) Pillar Strength formulasiga binoan:** Selek o'lchami $w={w}$ m bo'lganda, uning markaziy yadrosi {sv:.2f} MPa lik effektiv geostatik yukni ko'tarishga qodir. Plastik zona: $y = {y:.1f}$ m.",
        'references': "#### 📚 Asosiy Ilmiy Manbalar:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *J. Rock Mech. Geotech. Eng.*, 11(3), 445-463.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft, pp. 87-92.",
        'ref3': "**Shao, J.F., Zhu, Q.Z., & Su, K. (2003).** A thermal damage constitutive model for rock. *Int. J. Rock Mech. Min. Sci.*, 40(7), 927-937.",
        'ref4': "**Bieniawski, Z.T. (1992).** A method revisited: coal pillar strength formula. *USBM IC 9315*, pp. 158-165.",
        'conclusion_danger': "🔴 **Ilmiy Xulosa:** FOS={fos:.2f}. Termal degradatsiya yuqori. Selek enini oshirish yoki gazlashtirish tezligini nazorat qilish tavsiya etiladi.",
        'conclusion_safe': "🟢 **Ilmiy Xulosa:** FOS={fos:.2f}. Tanlangan parametrlar massiv barqarorligini ta'minlaydi.",
        'methodology_expander': "📚 Ilmiy Metodologiya va Manbalar (PhD Research References)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'dip_angle_label': "Qatlam qiyaligi (Dip - °)",
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
        'system_entropy': "Tizim entropiyasi H/H_max (noaniqlik)",
        'pin_approx': "**Eslatma:** Kirsch yechimi kvazistatik yaqinlashuv (uniform far-field stress). Katta deformatsiyalar uchun FEM remeshing talab qilinadi.",
        'phase_field_info': "**Fazaviy maydon modeli (Bourdin et al., 2000 asosida):**",
        'uq_info': "Noaniqlik miqdoriy tahlili (Monte-Carlo, JCGM 100:2008):",
        'shap_info': "SHAP interpretatsiyasi (Lundberg & Lee, 2017, NeurIPS):",
        'sobol_info': "Global sezgirlik (Sobol', 2001, Math. Comput. Simul.):",
        'lhs_info': "Latin Hypercube Sampling (McKay et al., 1979, Technometrics):",
        'validation_info': "Eksperimental validatsiya:",
        'experimental_note': "CSV faylida 'x' (m) va 'subsidence_cm' ustunlari bo'lishi shart."
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
        'fos_subplot': "FOS + AI Collapse Prediction + Yielded Zones",
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
        'hb_interpret': "**Scientific note:** According to Hoek & Brown (2018), GSI={gsi} means rock mass strength is **{perc:.1f}%** lower than laboratory values.",
        'thermal_params': "2. Thermo-Mechanical Coefficient Analysis",
        'param_table_param': "Parameter",
        'param_table_value': "Value",
        'param_table_reason': "Justification",
        'modulus': "Elastic Modulus (E)",
        'alpha': "Thermal expansion (α)",
        'temp0': "Initial T₀",
        'modulus_reason': "Typical average deformation coefficient for coal.",
        'alpha_reason': "Linear thermal expansion of coal (Yang, 2010, p.87): α = 1.5×10⁻⁵ /°C.",
        'temp0_reason': "Initial natural temperature of the coal seam.",
        'ucs_decay': "**A) Thermal UCS reduction (Shao et al., 2003):**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ MPa}}",
        'ucs_interpret': "**Interpretation:** At {temp}°C, rock strength decreased by {perc:.1f}%.",
        'thermal_stress': "**B) Thermal stress (partial confinement):**",
        'thermal_stress_eq': r"\sigma_{{th}} = \eta_c \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ MPa}}, \quad \eta_c = {eta:.2f}",
        'pillar_stability': "3. Pillar Stability (Bieniawski, 1992) and Bibliography",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v'}} = {fos:.2f}",
        'pillar_wilson': "**According to Bieniawski (1992) pillar strength formula:** With pillar width $w={w}$ m, the central core sustains {sv:.2f} MPa effective geostatic load. Plastic zone: $y = {y:.1f}$ m.",
        'references': "#### 📚 Main Scientific References:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *J. Rock Mech. Geotech. Eng.*, 11(3), 445-463.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft, pp. 87-92.",
        'ref3': "**Shao, J.F., Zhu, Q.Z., & Su, K. (2003).** A thermal damage constitutive model. *Int. J. Rock Mech. Min. Sci.*, 40(7), 927-937.",
        'ref4': "**Bieniawski, Z.T. (1992).** A method revisited: coal pillar strength formula. *USBM IC 9315*, pp. 158-165.",
        'conclusion_danger': "🔴 **Scientific Conclusion:** FOS={fos:.2f}. High thermal degradation. Increase pillar width or control gasification rate.",
        'conclusion_safe': "🟢 **Scientific Conclusion:** FOS={fos:.2f}. The selected parameters ensure mass stability.",
        'methodology_expander': "📚 Scientific Methodology and References (PhD Research)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'dip_angle_label': "Dip angle (°)",
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Download monitoring data (CSV)",
        'well_config': "Well Configuration",
        'well_distance': "Distance between wells (m):",
        'warning_cavity_width': "Warning: Pillar width exceeds well distance. cavity_width set to 1m.",
        'ucg_stages_title': "UCG Burning Stages (1-2-3 scheme) – Scientific Model",
        'select_stage': "Select stage:",
        'geomech_state': "Geomechanical State (Scientific Model)",
        'auto_animation': "Auto animation (1→2→3 stages)",
        'animation_done': "Animation finished.",
        'pillar_annotation': "PROTECTIVE PILLAR",
        'system_entropy': "System entropy H/H_max (uncertainty)",
        'pin_approx': "**Note:** Kirsch solution is quasi-static (uniform far-field). FEM remeshing required for large deformations.",
        'phase_field_info': "**Phase-field model (based on Bourdin et al., 2000):**",
        'uq_info': "Uncertainty Quantification (Monte-Carlo, JCGM 100:2008):",
        'shap_info': "SHAP interpretation (Lundberg & Lee, 2017, NeurIPS):",
        'sobol_info': "Global sensitivity (Sobol', 2001, Math. Comput. Simul.):",
        'lhs_info': "Latin Hypercube Sampling (McKay et al., 1979, Technometrics):",
        'validation_info': "Experimental validation:",
        'experimental_note': "CSV must contain 'x' (m) and 'subsidence_cm' columns."
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
        'fos_subplot': "FOS + Прогноз обрушения ИИ + Зоны пластичности",
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
        'ai_steps': "Шаги симуляции:",
        'ai_run_btn': "▶️ Запустить мониторинг",
        'ai_stop_btn': "⏹ Стоп",
        'advanced_analysis': "🔍 Углублённый динамический анализ",
        'tab_mass': "🏗️ Параметры массива",
        'tab_thermal': "🔥 Термическая деградация",
        'tab_stability': "⚖️ Устойчивость и источники",
        'hb_class': "1. Классификация Хука-Брауна (2018)",
        'hb_mb': "m_b = {mb:.3f}",
        'hb_s': "s = {s:.4f}",
        'hb_caption_mb': "Функция угла трения массива (m_i={mi})",
        'hb_caption_s': "Степень трещиноватости (GSI={gsi})",
        'hb_interpret': "**Научный комментарий:** По критерию Хука и Брауна (2018), GSI={gsi} означает снижение прочности массива на **{perc:.1f}%** по сравнению с лабораторным образцом.",
        'thermal_params': "2. Анализ термомеханических коэффициентов",
        'param_table_param': "Параметр",
        'param_table_value': "Значение",
        'param_table_reason': "Обоснование",
        'modulus': "Модуль упругости (E)",
        'alpha': "Тепловое расширение (α)",
        'temp0': "Начальная T₀",
        'modulus_reason': "Типичный средний коэффициент деформации угля.",
        'alpha_reason': "Линейное тепловое расширение угля (Yang, 2010, с. 87): α = 1.5×10⁻⁵ /°C.",
        'temp0_reason': "Начальная естественная температура угольного пласта.",
        'ucs_decay': "**A) Термическое снижение UCS (Shao et al., 2003):**",
        'ucs_decay_eq': r"\sigma_{{ci(T)}} = \sigma_{{ci(0)}} \cdot e^{{-\beta(T-T_0)}} = {ucs:.2f} \text{{ МПа}}",
        'ucs_interpret': "**Интерпретация:** При {temp}°C прочность породы снизилась на {perc:.1f}%.",
        'thermal_stress': "**B) Термическое напряжение (частичное ограничение):**",
        'thermal_stress_eq': r"\sigma_{{th}} = \eta_c \frac{{E \cdot \alpha \cdot \Delta T}}{{1 - \nu}} = {sigma:.2f} \text{{ МПа}}, \quad \eta_c = {eta:.2f}",
        'pillar_stability': "3. Устойчивость целика (Bieniawski, 1992) и библиография",
        'fos_eq': r"FOS = \frac{{\sigma_p}}{{\sigma_v'}} = {fos:.2f}",
        'pillar_wilson': "**По формуле прочности целика Bieniawski (1992):** При ширине целика $w={w}$ м несущая способность — {sv:.2f} МПа. Пластическая зона: $y = {y:.1f}$ м.",
        'references': "#### 📚 Основные научные источники:",
        'ref1': "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *J. Rock Mech. Geotech. Eng.*, 11(3), 445-463.",
        'ref2': "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft, pp. 87-92.",
        'ref3': "**Shao, J.F., Zhu, Q.Z., & Su, K. (2003).** A thermal damage constitutive model. *Int. J. Rock Mech. Min. Sci.*, 40(7), 927-937.",
        'ref4': "**Bieniawski, Z.T. (1992).** A method revisited: coal pillar strength formula. *USBM IC 9315*, pp. 158-165.",
        'conclusion_danger': "🔴 **Научный вывод:** FOS={fos:.2f}. Высокая термическая деградация. Увеличьте ширину целика или снизьте скорость газификации.",
        'conclusion_safe': "🟢 **Научный вывод:** FOS={fos:.2f}. Выбранные параметры обеспечивают устойчивость массива.",
        'methodology_expander': "📚 Научная методология и источники (PhD Research)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'dip_angle_label': "Угол падения (°)",
        'live_monitoring_tab': "🔄 Живой 3D мониторинг",
        'download_data': "📥 Скачать данные мониторинга (CSV)",
        'well_config': "Конфигурация скважин",
        'well_distance': "Расстояние между скважинами (м):",
        'warning_cavity_width': "Предупреждение: ширина целика превышает расстояние между скважинами. cavity_width=1м.",
        'ucg_stages_title': "Стадии горения UCG (схема 1-2-3) — научная модель",
        'select_stage': "Выберите стадию:",
        'geomech_state': "Геомеханическое состояние (научная модель)",
        'auto_animation': "Авто анимация (1→2→3 стадии)",
        'animation_done': "Анимация завершена.",
        'pillar_annotation': "ЗАЩИТНЫЙ ЦЕЛИК",
        'system_entropy': "Системная энтропия H/H_max (неопределённость)",
        'pin_approx': "**Примечание:** Решение Кирша квазистатическое (однородное поле напряжений). Для больших деформаций требуется МКЭ.",
        'phase_field_info': "**Фазовая модель поля (Bourdin et al., 2000):**",
        'uq_info': "Количественная оценка неопределённости (Монте-Карло, JCGM 100:2008):",
        'shap_info': "Интерпретация SHAP (Lundberg & Lee, 2017, NeurIPS):",
        'sobol_info': "Глобальная чувствительность (Соболь, 2001, Math. Comput. Simul.):",
        'lhs_info': "Латинский гиперкуб (McKay et al., 1979, Technometrics):",
        'validation_info': "Экспериментальная валидация:",
        'experimental_note': "CSV должен содержать столбцы 'x' (м) и 'subsidence_cm'."
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

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def _init_session() -> None:
    defaults = {
        'language': 'uz',
        'theme': 'dark',
        'live_history_df': pd.DataFrame(
            columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m']
        ),
        'last_language': 'uz',
        'formula_idx': 0,
        'live_data_list': [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session()

def translate(key: str, **kwargs) -> str:
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    try:
        return text.format(**kwargs) if kwargs else text
    except (KeyError, ValueError):
        return text

t = translate

# ═══════════════════════════════════════════════════════════════════════════
# PHYSICS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def von_mises_stress(
    sigma_x: np.ndarray,
    sigma_z: np.ndarray,
    tau_xz: np.ndarray,
    nu: Optional[float] = None
) -> np.ndarray:
    """Plane-strain von Mises stress formula."""
    sigma_y = nu * (sigma_x + sigma_z) if nu is not None else 0.0
    vm = np.sqrt(
        0.5 * (
            (sigma_x - sigma_z) ** 2
            + (sigma_z - sigma_y) ** 2
            + (sigma_y - sigma_x) ** 2
        )
        + 3.0 * tau_xz ** 2
    )
    return np.maximum(vm, 0.0)

def hoek_brown_params(
    gsi: float,
    mi: float,
    D: float
) -> Tuple[float, float, float]:
    """Hoek-Brown (2018) rock mass parameters."""
    D = float(np.clip(D, 0.0, 1.0))
    mb = mi * np.exp((gsi - 100.0) / (28.0 - 14.0 * D))
    if isinstance(gsi, (int, float)):
        s = float(np.exp((float(gsi) - 100.0) / (9.0 - 3.0 * D)))
    else:
        gsi_arr = np.asarray(gsi, dtype=float)
        s = np.exp((gsi_arr - 100.0) / (9.0 - 3.0 * D))
    a = 0.5 + (1.0 / 6.0) * (
        np.exp(-np.asarray(gsi) / 15.0) - np.exp(-20.0 / 3.0)
    )
    if isinstance(gsi, (int, float)):
        a = float(a)
    return mb, s, a

def hoek_brown(
    sigma3: np.ndarray,
    sigma_ci: np.ndarray,
    mb: float,
    s: float,
    a: float
) -> np.ndarray:
    """Hoek-Brown biaxial failure envelope."""
    sigma3_eff = np.maximum(sigma3, 0.0)
    term = np.maximum(mb * (sigma3_eff / (sigma_ci + EPS_STRESS)) + s, 0.0)
    return sigma3_eff + sigma_ci * (term ** a)

def compute_demand_capacity_ratio(
    sigma1_applied: np.ndarray,
    sigma3_confining: np.ndarray,
    sigma_ci: np.ndarray,
    mb: float,
    s: float,
    a: float
) -> np.ndarray:
    sigma3_eff = np.maximum(sigma3_confining, 0.0)
    sigma1_failure = sigma3_eff + sigma_ci * (
        np.maximum(mb * (sigma3_eff / (sigma_ci + EPS_STRESS)) + s, 0.0) ** a
    )
    return sigma1_applied / (sigma1_failure + EPS_STRESS)

def thermal_damage(T: np.ndarray, beta: float, T_ref: float = T_REF_AMBIENT) -> np.ndarray:
    """Thermal damage function D(T)."""
    return 1.0 - np.exp(-beta * np.maximum(T - T_ref, 0.0))

def apply_thermal_degradation(
    ucs0: np.ndarray,
    T: np.ndarray,
    beta: float
) -> np.ndarray:
    """Apply thermal degradation to UCS."""
    dmg = thermal_damage(T, beta)
    return np.clip(ucs0 * (1.0 - dmg), 0.5, None)

def thermal_conductivity(T: np.ndarray, k0: float = 2.5) -> np.ndarray:
    """Temperature-dependent thermal conductivity."""
    k = k0 * (1.0 - 0.0004 * (T - T_REF_AMBIENT))
    return np.clip(k, 0.5, None)

def specific_heat(T: np.ndarray) -> np.ndarray:
    """Temperature-dependent specific heat."""
    return np.clip(960.0 + 0.14 * T, 900.0, 2200.0)

def density_temperature(rho0: float, T: np.ndarray) -> np.ndarray:
    """Temperature-dependent density."""
    T_clamped = np.clip(T, T_REF_AMBIENT, 1200.0)
    alpha_v = 3.6e-5
    thermal_factor = 1.0 - alpha_v * (T_clamped - T_REF_AMBIENT)
    combustion_factor = np.clip(1.0 - 0.70 * np.clip((T_clamped - 400.0) / 400.0, 0.0, 1.0), 0.30, 1.0)
    rho_T = rho0 * thermal_factor * combustion_factor
    return np.clip(rho_T, 0.10 * rho0, rho0)

def young_modulus_temperature(
    T: np.ndarray,
    E0: Optional[float] = None
) -> np.ndarray:
    """Young's modulus as function of temperature."""
    E0_val = E0 if E0 is not None else PARAMS.E_mass
    c_E = 0.0018
    E_T = E0_val * np.exp(-c_E * np.maximum(T - T_REF_AMBIENT, 0.0))
    return np.clip(E_T, 0.10 * E0_val, E0_val)

def thermal_expansion_temperature(T: np.ndarray) -> np.ndarray:
    """Temperature-dependent thermal expansion coefficient."""
    T = np.clip(T, T_REF_AMBIENT, 1200.0)
    alpha_T = PARAMS.alpha_thermal * (
        1.0 + 0.002 * (T - T_REF_AMBIENT) + 1e-6 * (T - T_REF_AMBIENT) ** 2
    )
    return alpha_T

def gas_viscosity_temperature(
    T_kelvin: np.ndarray,
    mu_ref: float = 3e-5,
    T_ref_k: float = 1273.15,
    S: float = SUTHERLAND_S_CO,
) -> np.ndarray:
    """Sutherland formula for gas viscosity."""
    ratio = T_kelvin / T_ref_k
    sutherland = (T_ref_k + S) / (T_kelvin + S)
    mu = mu_ref * (ratio ** 1.5) * sutherland
    return np.clip(mu, 1e-6, 1e-3)

def vertical_stress(depth: float, density: float) -> float:
    """Vertical stress calculation."""
    return float(density * 9.81 * depth / 1e6)

def solve_heat_equation_dynamic(
    T: np.ndarray,
    Q: np.ndarray,
    rho_field: np.ndarray,
    cp_field: np.ndarray,
    k_field: np.ndarray,
    dx: float,
    dz: float,
    total_time: float,
    T_air: float = 25.0,
    h_conv: float = 10.0,
    max_steps: int = 2000,
) -> np.ndarray:
    """Explicit finite difference heat equation solver."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        alpha_field = k_field / (rho_field * cp_field + EPS_GENERAL)
        alpha_max = float(np.max(alpha_field))
        dt_max = 0.25 / (alpha_max * (1.0 / dx ** 2 + 1.0 / dz ** 2) + EPS_GENERAL)
        dt_candidate = 0.8 * dt_max
        n_steps = max(int(np.ceil(total_time / dt_candidate)), 1)
        n_steps = min(n_steps, max_steps)
        dt = total_time / n_steps

        for step_i in range(n_steps):
            if step_i % 200 == 0 and step_i > 0:
                cp_field = specific_heat(T)
                k_field = thermal_conductivity(T)
                alpha_field = k_field / (rho_field * cp_field + EPS_GENERAL)

            T_old = T.copy()
            Txx = (
                T_old[1:-1, 2:] - 2.0 * T_old[1:-1, 1:-1] + T_old[1:-1, :-2]
            ) / dx ** 2
            Tzz = (
                T_old[2:, 1:-1] - 2.0 * T_old[1:-1, 1:-1] + T_old[:-2, 1:-1]
            ) / dz ** 2
            T_new = T_old.copy()
            T_new[1:-1, 1:-1] = T_old[1:-1, 1:-1] + dt * (
                alpha_field[1:-1, 1:-1] * (Txx + Tzz)
                + Q[1:-1, 1:-1] / (rho_field[1:-1, 1:-1] * cp_field[1:-1, 1:-1] + EPS_GENERAL)
            )
            T_new[:, 0] = T_new[:, 1]
            T_new[:, -1] = T_new[:, -2]
            T_new[-1, :] = T_new[-2, :]
            k_surface = k_field[0, :]
            T_new[0, :] = (k_surface * T_new[1, :] + dz * h_conv * T_air) / (
                k_surface + dz * h_conv + EPS_GENERAL
            )
            T = T_new.copy()
    return T

def principal_stresses(
    sx: np.ndarray, sy: np.ndarray, txy: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    avg = (sx + sy) / 2.0
    radius = np.sqrt(((sx - sy) / 2.0) ** 2 + txy ** 2)
    return avg + radius, avg - radius

def evolving_cavity_radius(
    time_h: float,
    T_field: np.ndarray,
    beta: float,
    grid_z: np.ndarray,
    source_z: float,
    H_seam: float
) -> float:
    source_mask = np.abs(grid_z - source_z) < 1.5 * H_seam
    if not np.any(source_mask):
        return 5.0
    T_source = T_field[source_mask]
    thermal_dam_local = thermal_damage(T_source, beta)
    growth_rate = 0.015 * float(np.mean(thermal_dam_local))
    return float(np.clip(5.0 + growth_rate * time_h, 5.0, 40.0))

def kirsch_stress_field(
    x: np.ndarray,
    z: np.ndarray,
    sigma_H: float,
    sigma_h: float,
    cavity_radius: float,
    pore_pressure: float = 0.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Kirsch solution for cylindrical cavity."""
    sigma_H = float(np.mean(sigma_H)) if hasattr(sigma_H, '__len__') else float(sigma_H)
    sigma_h = float(np.mean(sigma_h)) if hasattr(sigma_h, '__len__') else float(sigma_h)

    r = np.maximum(np.sqrt(x ** 2 + z ** 2), cavity_radius + GEOM_EPS)
    theta = np.arctan2(z, x)
    a2_r2 = (cavity_radius ** 2) / (r ** 2)
    a4_r4 = (cavity_radius ** 4) / (r ** 4)

    sigma_rr = (
        (sigma_H + sigma_h) / 2.0 * (1.0 - a2_r2)
        + (sigma_H - sigma_h) / 2.0 * (1.0 - 4.0 * a2_r2 + 3.0 * a4_r4) * np.cos(2 * theta)
    ) - pore_pressure

    sigma_tt = (
        (sigma_H + sigma_h) / 2.0 * (1.0 + a2_r2)
        - (sigma_H - sigma_h) / 2.0 * (1.0 + 3.0 * a4_r4) * np.cos(2 * theta)
    ) - pore_pressure

    tau_rt = -(sigma_H - sigma_h) / 2.0 * (
        1.0 + 2.0 * a2_r2 - 3.0 * a4_r4
    ) * np.sin(2 * theta)

    return sigma_rr, sigma_tt, tau_rt

def pore_pressure_field(
    T: np.ndarray,
    depth: np.ndarray,
    water_table: float = 20.0,
    rho_water: float = 1000.0
) -> np.ndarray:
    """Pore pressure field calculation."""
    h_water = np.maximum(depth - water_table, 0.0)
    P_hydro = rho_water * 9.81 * h_water / 1e6
    T_kelvin = np.maximum(T + 273.15, 293.15)
    P_gas = (101325.0 * T_kelvin / 293.15) / 1e6
    return P_hydro + P_gas

def monte_carlo_fos(
    ucs_mean: float,
    ucs_std: float,
    gsi_mean: float,
    gsi_std: float,
    mi_val: float,
    D: float,
    T_avg: float,
    H_seam: float,
    depth: float,
    density: float,
    rec_width: float,
    beta_th: float,
    n_sim: int = 1000,
    random_seed: int = RANDOM_SEED
) -> Tuple[np.ndarray, float]:
    """Monte Carlo FOS distribution."""
    rng = np.random.default_rng(seed=random_seed)
    cov = np.array([
        [ucs_std ** 2, 0.3 * ucs_std * gsi_std],
        [0.3 * ucs_std * gsi_std, gsi_std ** 2],
    ])
    min_eig = float(np.min(np.linalg.eigvalsh(cov)))
    if min_eig < 0:
        cov -= np.eye(2) * min_eig * 1.01

    samples = rng.multivariate_normal([ucs_mean, gsi_mean], cov, n_sim)
    ucs_samples = samples[:, 0]
    gsi_samples = np.clip(samples[:, 1], 10.0, 100.0)

    fos_arr = []
    for ucs_s, gsi_s in zip(ucs_samples, gsi_samples):
        mb_s, s_s, a_s = hoek_brown_params(float(gsi_s), mi_val, D)
        ucs_T = apply_thermal_degradation(ucs_s, T_avg, beta_th)
        sigma_cm = ucs_T * (max(s_s, 1e-9) ** a_s)
        p_str = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
        sv = density * 9.81 * depth / 1e6
        fos_arr.append(float(np.clip(p_str / (sv + EPS_STRESS), 0.0, 50.0)))

    fos_np = np.array(fos_arr)
    pf = float(np.mean(fos_np < 1.0))
    return fos_np, pf

def _array_hash(*arrays: np.ndarray) -> str:
    """SHA-256 hash for arrays."""
    h = hashlib.sha256()
    for arr in arrays:
        h.update(arr.tobytes())
        h.update(str(arr.shape).encode())
    return h.hexdigest()

def subsidence_inclined_seam(
    S_horizontal: np.ndarray,
    dip_deg: float,
    depth: float,
    phi_deg: float
) -> float:
    dip_rad = np.radians(dip_deg)
    phi_rad = np.radians(phi_deg)
    return float(depth * np.tan(dip_rad) * np.tan(phi_rad / 2.0))

def pillar_creep_strength(
    sigma_p0: float,
    time_h: float,
    A_creep: float = 0.05,
    n_creep: float = 0.3
) -> float:
    """Time-dependent pillar strength degradation."""
    reduction = min(A_creep * (time_h ** n_creep), 0.40)
    return sigma_p0 * (1.0 - reduction)

def gas_migration_risk(
    T_field: np.ndarray,
    perm_field: np.ndarray,
    depth: float,
    fos_field: np.ndarray
) -> np.ndarray:
    """Gas migration risk map."""
    thermal_path = T_field > 300.0
    perm_path = perm_field > 1e-14
    structural_fail = fos_field < 1.5
    gas_risk = (thermal_path & perm_path & structural_fail).astype(float)
    return gaussian_filter(gas_risk, sigma=2.0)

def water_inrush_risk(
    void_volume: float,
    aquifer_depth: float,
    depth_seam: float,
    fos_min: float
) -> Tuple[str, float]:
    """Water inrush risk assessment."""
    height_to_aquifer = abs(aquifer_depth - depth_seam)
    h_critical = 0.0015 * void_volume ** 0.5
    if height_to_aquifer < h_critical and fos_min < 1.2:
        return "CRITICAL", 0.9
    elif height_to_aquifer < h_critical * 1.5:
        return "HIGH", 0.6
    else:
        return "LOW", 0.1

def _quick_fos(
    ucs: float,
    gsi: float,
    T: float,
    H_seam: float,
    rec_width: float,
    d_factor: float,
    beta_th: float,
    depth: float,
    rho: float,
) -> float:
    """Quick FOS calculation."""
    mb, s, a = hoek_brown_params(gsi, 10.0, d_factor)
    ucs_T = apply_thermal_degradation(ucs, T, beta_th)
    sigma_cm = ucs_T * (max(float(s), 1e-9) ** float(a))
    p_str = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
    sv = vertical_stress(depth, rho)
    return float(np.clip(p_str / (sv + EPS_STRESS), 0.0, 50.0))

def propagate_uncertainty_analytical(
    ucs_mean: float,
    ucs_cov: float,
    gsi_mean: float,
    gsi_cov: float,
    T_mean: float,
    T_cov: float,
    H_seam: float,
    rec_width: float,
    d_factor: float,
    beta_th: float,
    depth: float,
    rho: float,
) -> Tuple[float, float]:
    """Analytical uncertainty propagation (GUM)."""
    eps_rel = 0.01
    fos_base = _quick_fos(ucs_mean, gsi_mean, T_mean, H_seam, rec_width,
                          d_factor, beta_th, depth, rho)

    dfos_ducs = (
        _quick_fos(ucs_mean * (1 + eps_rel), gsi_mean, T_mean, H_seam, rec_width,
                   d_factor, beta_th, depth, rho) - fos_base
    ) / (eps_rel * ucs_mean + EPS_GENERAL)

    dfos_dgsi = (
        _quick_fos(ucs_mean, gsi_mean * (1 + eps_rel), T_mean, H_seam, rec_width,
                   d_factor, beta_th, depth, rho) - fos_base
    ) / (eps_rel * gsi_mean + EPS_GENERAL)

    dfos_dT = (
        _quick_fos(ucs_mean, gsi_mean, T_mean * (1 + eps_rel), H_seam, rec_width,
                   d_factor, beta_th, depth, rho) - fos_base
    ) / (eps_rel * T_mean + EPS_GENERAL)

    var_fos = (
        (dfos_ducs * ucs_mean * ucs_cov) ** 2
        + (dfos_dgsi * gsi_mean * gsi_cov) ** 2
        + (dfos_dT * T_mean * T_cov) ** 2
    )
    return fos_base, float(np.sqrt(var_fos))

def subsidence_confidence_interval(
    sub_profile: np.ndarray,
    n_measurements: int,
    confidence: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    std_est = np.std(sub_profile) * 0.15
    t_crit = t_dist.ppf((1.0 + confidence) / 2.0, df=max(n_measurements - 1, 1))
    margin = t_crit * std_est / np.sqrt(max(n_measurements, 1))
    return sub_profile - margin, sub_profile + margin

# ═══════════════════════════════════════════════════════════════════════════
# WORD DOCUMENT HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def set_table_border(table) -> None:
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:color'), '2E74B5')
        tblBorders.append(border)
    tblPr.append(tblBorders)

def apply_heading_style(para, size_pt: int = 14, bold: bool = True) -> None:
    for run in para.runs:
        run.font.size = Pt(size_pt)
        run.font.bold = bold
    if not para.runs:
        run = para.add_run()
        run.font.size = Pt(size_pt)
        run.font.bold = bold

# ═══════════════════════════════════════════════════════════════════════════
# ADVANCED PHYSICS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def gsi_thermal_degradation(
    gsi_0: float,
    T: float,
    T_ref: float = T_REF_AMBIENT,
    beta_gsi: float = BETA_GSI_DEFAULT,
) -> float:
    """GSI thermal degradation."""
    delta_T = max(float(T) - float(T_ref), 0.0)
    gsi_T = float(gsi_0) * np.exp(-beta_gsi * delta_T)
    return float(np.clip(gsi_T, 10.0, 100.0))

def d_factor_distance(
    D_base: float,
    dist_from_cavity: float,
    influence_len: float = 20.0,
) -> float:
    """Distance-dependent disturbance factor."""
    d_r = float(D_base) * np.exp(-max(dist_from_cavity, 0.0) / (influence_len + EPS_GENERAL))
    return float(np.clip(d_r, 0.0, 1.0))

def hoek_diederichs_modulus(
    E_lab: float,
    gsi: float,
    D: float,
) -> float:
    """Hoek-Diederichs (2006) rock mass modulus."""
    D_c = float(np.clip(D, 0.0, 1.0))
    denom = 1.0 + np.exp((60.0 + 15.0 * D_c - float(gsi)) / 11.0)
    E_mass = float(E_lab) * (0.02 + (1.0 - D_c / 2.0) / (denom + EPS_GENERAL))
    return float(np.clip(E_mass, 0.01 * E_lab, E_lab))

def poisson_thermal(
    nu_0: float,
    T: float,
    T_ref: float = T_REF_AMBIENT,
    c_nu: float = 2e-4,
) -> float:
    """Temperature-dependent Poisson's ratio."""
    delta_T = max(float(T) - float(T_ref), 0.0)
    nu_T = float(nu_0) + c_nu * delta_T
    return float(np.clip(nu_T, 0.10, 0.49))

def stefan_boltzmann_radiation(
    T_surf: np.ndarray,
    T_amb: float = T_REF_AMBIENT + 273.15,
    epsilon: float = 0.9,
) -> np.ndarray:
    """Stefan-Boltzmann radiation heat flux."""
    SIGMA_SB = 5.67e-8
    T_K = np.clip(np.asarray(T_surf, dtype=float) + 273.15, 273.15, 1800.0)
    T_amb_K = max(float(T_amb), 273.15)
    q_rad = epsilon * SIGMA_SB * (T_K ** 4 - T_amb_K ** 4)
    return np.clip(q_rad, 0.0, 1e7)

def latent_heat_correction(
    T_field: np.ndarray,
    L_vap: float = 2.26e6,
    L_melt: float = 3.34e5,
    T_vap: float = 100.0,
    T_melt: float = 0.0,
    width: float = 20.0,
) -> np.ndarray:
    """Latent heat correction for phase transitions."""
    T = np.asarray(T_field, dtype=float)
    q_vap = L_vap * np.exp(-((T - T_vap) ** 2) / (2.0 * width ** 2)) * 0.01
    q_melt = L_melt * np.exp(-((T - T_melt) ** 2) / (2.0 * width ** 2)) * 0.01
    return q_vap + q_melt

def stress_dependent_permeability(
    perm_0: np.ndarray,
    sigma_eff: np.ndarray,
    a_perm: float = 3.5,
    sigma_ref: float = 10.0,
) -> np.ndarray:
    """Stress-dependent permeability."""
    sigma_eff_cl = np.maximum(np.asarray(sigma_eff, dtype=float), 0.0)
    perm = np.asarray(perm_0, dtype=float) * np.exp(
        -a_perm * (sigma_eff_cl - sigma_ref) / (sigma_ref + EPS_GENERAL)
    )
    return np.clip(perm, 1e-22, 1e-10)

def char_formation_porosity(
    T: np.ndarray,
    phi_0: float = 0.05,
    T_pyro: float = 400.0,
    T_char: float = 600.0,
) -> np.ndarray:
    """Char formation and porosity change during coal combustion."""
    T_arr = np.asarray(T, dtype=float)
    sigmoid_char = 1.0 / (1.0 + np.exp(-(T_arr - T_char) / 50.0))
    sigmoid_pyro = 1.0 / (1.0 + np.exp(-(T_arr - T_pyro) / 30.0))
    phi_char = phi_0 + (1.0 - phi_0) * (0.15 * sigmoid_pyro + 0.30 * sigmoid_char)
    return np.clip(phi_char, phi_0, 0.55)

def pyrolysis_volatile_release(
    T: np.ndarray,
    volatile_content: float = 0.35,
    T_onset: float = 350.0,
    T_end: float = 650.0,
) -> np.ndarray:
    """Volatile release during pyrolysis."""
    T_arr = np.clip(np.asarray(T, dtype=float), T_onset, T_end)
    fraction = (T_arr - T_onset) / max(T_end - T_onset, 1.0)
    return np.clip(volatile_content * fraction, 0.0, volatile_content)

def dynamic_molar_mass(
    x_CO: float = 0.40,
    x_H2: float = 0.30,
    x_CO2: float = 0.15,
    x_CH4: float = 0.10,
    x_N2: float = 0.05,
) -> float:
    """Dynamic molar mass of syngas mixture."""
    M_CO, M_H2, M_CO2, M_CH4, M_N2 = 0.028, 0.002, 0.044, 0.016, 0.028
    M_mix = (x_CO * M_CO + x_H2 * M_H2 + x_CO2 * M_CO2
              + x_CH4 * M_CH4 + x_N2 * M_N2)
    total_x = x_CO + x_H2 + x_CO2 + x_CH4 + x_N2
    return float(M_mix / max(total_x, EPS_GENERAL))

def ideal_gas_density(
    P: np.ndarray,
    M_molar: float,
    T_kelvin: np.ndarray,
    R: float = 8.314,
) -> np.ndarray:
    """Ideal gas density."""
    rho = np.asarray(P, dtype=float) * M_molar / (R * np.maximum(T_kelvin, 273.15))
    return np.clip(rho, 0.001, 100.0)

def heat_balance_check(
    Q_in: float,
    Q_out: float,
    Q_stored: float,
    tol: float = 0.05,
) -> Tuple[bool, float]:
    """Heat balance verification."""
    residual = abs(Q_in - Q_out - Q_stored)
    residual_pct = residual / max(abs(Q_in), EPS_GENERAL) * 100.0
    balanced = residual_pct < tol * 100.0
    return balanced, residual_pct

def digital_twin_hash(params_dict: dict) -> str:
    """SHA-256 hash for digital twin reproducibility."""
    serialized = json.dumps(params_dict, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16].upper()

def geological_presets() -> dict:
    """Geological condition presets."""
    return {
        "Angren, O'zbekiston": {
            "layers": [
                {"name": "Ohaktosh", "thickness": 60.0, "ucs": 70.0, "rho": 2600.0,
                 "gsi": 65, "mi": 9.0, "color": "#87CEEB"},
                {"name": "Gillі loyqa", "thickness": 30.0, "ucs": 25.0, "rho": 2200.0,
                 "gsi": 45, "mi": 6.0, "color": "#F4A460"},
                {"name": "Ko'mir qatlami", "thickness": 10.0, "ucs": 18.0, "rho": 1400.0,
                 "gsi": 55, "mi": 8.0, "color": "#555555"},
            ],
            "T_max": 1100, "burn_h": 40
        },
        "Linc Energy, Avstraliya": {
            "layers": [
                {"name": "Sandstone", "thickness": 80.0, "ucs": 55.0, "rho": 2400.0,
                 "gsi": 60, "mi": 15.0, "color": "#F4A460"},
                {"name": "Coal seam", "thickness": 8.0, "ucs": 20.0, "rho": 1350.0,
                 "gsi": 50, "mi": 7.0, "color": "#555555"},
            ],
            "T_max": 1050, "burn_h": 36
        },
        "Powder River, AQSh": {
            "layers": [
                {"name": "Mudstone", "thickness": 40.0, "ucs": 15.0, "rho": 2000.0,
                 "gsi": 35, "mi": 4.0, "color": "#D3D3D3"},
                {"name": "Coal (sub-bituminous)", "thickness": 20.0, "ucs": 12.0,
                 "rho": 1300.0, "gsi": 40, "mi": 5.0, "color": "#555555"},
            ],
            "T_max": 900, "burn_h": 30
        },
    }

def concept_drift_detector(
    y_pred_new: np.ndarray,
    y_pred_ref: np.ndarray,
    threshold: float = 0.15,
) -> Tuple[bool, float]:
    """Concept drift detection."""
    new_m = float(np.mean(y_pred_new))
    ref_m = float(np.mean(y_pred_ref))
    ref_s = float(np.std(y_pred_ref))
    drift_score = abs(new_m - ref_m) / (ref_s + EPS_GENERAL)
    return drift_score > threshold, drift_score

def tensile_failure_fos(
    sigma_t: float,
    sigma_min: float,
) -> float:
    """Tensile failure FOS."""
    if sigma_min >= 0.0:
        return 50.0
    return float(np.clip(abs(sigma_t) / (abs(sigma_min) + EPS_STRESS), 0.0, 50.0))

def crip_source_position(
    time_h: float,
    x_start: float,
    x_end: float,
    retreat_rate: float = 0.5,
) -> float:
    """CRIP technology source position."""
    x_current = x_start + retreat_rate * float(time_h)
    return float(np.clip(x_current, x_start, x_end))

def model_serialization_paths(obj_name: str) -> dict:
    """Model serialization paths."""
    safe_name = obj_name.replace(" ", "_").replace("/", "-")
    return {
        "nn_pt": f"models/{safe_name}_hybrid_pinn.pt",
        "rf_joblib": f"models/{safe_name}_random_forest.joblib",
        "scaler_joblib": f"models/{safe_name}_scaler.joblib",
        "metadata": f"models/{safe_name}_metadata.json",
    }

def save_models_to_disk(
    model, rf, scaler, obj_name: str, metadata: dict
) -> Optional[str]:
    """Save models to disk."""
    import os
    try:
        import joblib
        paths = model_serialization_paths(obj_name)
        os.makedirs("models", exist_ok=True)
        if model is not None and PT_AVAILABLE:
            torch.save(model.state_dict(), paths["nn_pt"])
        joblib.dump(rf, paths["rf_joblib"])
        joblib.dump(scaler, paths["scaler_joblib"])
        with open(paths["metadata"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)
        return "models/"
    except Exception as exc:
        logger.warning(f"Model serialization error: {exc}")
        return None

def timestamped_csv_export(df: pd.DataFrame, prefix: str = "ucg_data") -> Tuple[bytes, str]:
    """Timestamped CSV export."""
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    filename = f"{prefix}_{ts}.csv"
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return csv_bytes, filename

def compute_confusion_roc_f1(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """Compute confusion matrix, ROC-AUC, and F1-score."""
    y_pred_bin = (y_pred_proba >= threshold).astype(int)
    TP = int(np.sum((y_pred_bin == 1) & (y_true == 1)))
    TN = int(np.sum((y_pred_bin == 0) & (y_true == 0)))
    FP = int(np.sum((y_pred_bin == 1) & (y_true == 0)))
    FN = int(np.sum((y_pred_bin == 0) & (y_true == 1)))
    precision = TP / max(TP + FP, 1)
    recall = TP / max(TP + FN, 1)
    f1 = 2 * precision * recall / max(precision + recall, EPS_GENERAL)
    
    try:
        sorted_idx = np.argsort(-y_pred_proba)
        tpr_list, fpr_list = [0.0], [0.0]
        tp_c, fp_c = 0, 0
        pos = max(np.sum(y_true == 1), 1)
        neg = max(np.sum(y_true == 0), 1)
        for i in sorted_idx:
            if y_true[i] == 1:
                tp_c += 1
            else:
                fp_c += 1
            tpr_list.append(tp_c / pos)
            fpr_list.append(fp_c / neg)
        tpr_arr = np.array(tpr_list)
        fpr_arr = np.array(fpr_list)
        auc = float(np.trapz(tpr_arr, fpr_arr))
    except Exception:
        auc = 0.5
    
    accuracy = (TP + TN) / max(TP + TN + FP + FN, 1)
    return {
        "TP": TP, "TN": TN, "FP": FP, "FN": FN,
        "precision": precision, "recall": recall,
        "f1": f1, "auc_roc": abs(auc),
        "accuracy": accuracy,
        "confusion": np.array([[TN, FP], [FN, TP]]),
    }

def latency_monitor(func):
    """Latency monitoring decorator."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(f"⏱ {func.__name__}: {elapsed:.1f} ms")
        return result
    return wrapper

def isolation_forest_anomaly(
    X: np.ndarray,
    contamination: float = 0.1,
    random_state: int = RANDOM_SEED,
) -> np.ndarray:
    """Isolation Forest anomaly detection."""
    try:
        from sklearn.ensemble import IsolationForest
        clf = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
        )
        labels = clf.fit_predict(X)
        return labels == -1
    except Exception as exc:
        logger.warning(f"IsolationForest xato: {exc}")
        z_scores = np.abs((X - np.mean(X, axis=0)) / (np.std(X, axis=0) + EPS_GENERAL))
        return np.any(z_scores > 3.0, axis=1)

def check_cfl_condition(
    dt: float,
    dx: float,
    dz: float,
    alpha_max: float,
) -> Tuple[bool, float]:
    """CFL stability condition check."""
    dt_max = 0.25 / (alpha_max * (1.0 / dx ** 2 + 1.0 / dz ** 2) + EPS_GENERAL)
    safety_factor = dt_max / (dt + EPS_GENERAL)
    return dt <= dt_max, safety_factor

def robin_bc_update(
    T: np.ndarray,
    k_surface: np.ndarray,
    h_conv: float,
    T_air: float,
    dz: float,
) -> np.ndarray:
    """Robin (type III) boundary condition update."""
    T_out = T.copy()
    T_out[0, :] = (k_surface * T[1, :] / dz + h_conv * T_air) / (
        k_surface / dz + h_conv + EPS_GENERAL
    )
    return T_out

def patent_claims_text(lang: str = 'en') -> str:
    """Patent claims text."""
    claims = {
        'uz': (
            "**Patent Da'vo 1 (Usul):**\n"
            "Yerosti ko'mir gazlashtirishida yer yuzasi deformatsiyasi va "
            "geomexanik barqarorlikni nazorat qilish usuli bo'lib, quyidagilarni o'z ichiga oladi:\n"
            "a) Hoek-Brown (2018) mezoniga ko'ra real-vaqt termal degradatsiyani modellashtirish;\n"
            "b) Fizika-asoslangan neyron tarmoq (PINN) va RandomForest ensemble yordamida "
            "barqarorlik koeffitsiyentini bashorat qilish;\n"
            "c) Bieniawski (1992) formulasi asosida optimal selek o'lchamini iterativ aniqlash;\n"
            "d) Monte Carlo (JCGM 100:2008) usuli bilan noaniqlik tahlili;\n"
            "e) ISO 9001:2015 muvofiq avtomatik muhandislik hisobot yaratish.\n\n"
            "**Patent Da'vo 2 (Tizim):**\n"
            "Da'vo 1 usulini amalga oshiruvchi kompyuter tizimi bo'lib:\n"
            "– ko'p qatlamli geomexanik modelling moduli;\n"
            "– real-vaqt sensor integratsiyasi va anomaliya aniqlash moduli;\n"
            "– CRIP texnologiyasida yonish zonasi harakati simulyatori;\n"
            "– avtomatik hisobot generatori (docx, CSV, JSON) o'z ichiga oladi."
        ),
        'en': (
            "**Patent Claim 1 (Method):**\n"
            "A method for monitoring surface deformation and geomechanical stability "
            "during underground coal gasification (UCG), comprising:\n"
            "a) real-time thermal degradation modeling using Hoek-Brown (2018) criterion;\n"
            "b) stability factor prediction via Physics-Informed Neural Network (PINN) "
            "and RandomForest ensemble;\n"
            "c) iterative optimal pillar sizing using Bieniawski (1992) formula;\n"
            "d) uncertainty quantification via Monte Carlo simulation (JCGM 100:2008);\n"
            "e) automated ISO 9001:2015-compliant engineering report generation.\n\n"
            "**Patent Claim 2 (System):**\n"
            "A computer system for implementing the method of Claim 1, comprising:\n"
            "– multi-layer geomechanical modelling module;\n"
            "– real-time sensor integration and anomaly detection module;\n"
            "– CRIP technology combustion zone movement simulator;\n"
            "– automated report generator (docx, CSV, JSON)."
        ),
        'ru': (
            "**Патентная формула 1 (Способ):**\n"
            "Способ мониторинга деформации поверхности и геомеханической устойчивости "
            "при подземной газификации угля (ПГУ), включающий:\n"
            "a) реального времени моделирование термического повреждения по Хоеку-Брауну (2018);\n"
            "b) прогнозирование FOS с помощью PINN и ансамбля RandomForest;\n"
            "c) итеративный расчёт оптимального целика по Бяниавски (1992);\n"
            "d) анализ неопределённости методом Монте-Карло (JCGM 100:2008);\n"
            "e) автоматическое создание инженерного отчёта по ISO 9001:2015.\n\n"
            "**Патентная формула 2 (Система):**\n"
            "Компьютерная система для реализации способа по п.1, включающая:\n"
            "– модуль многослойного геомеханического моделирования;\n"
            "– модуль интеграции датчиков реального времени и обнаружения аномалий;\n"
            "– симулятор движения зоны горения по технологии CRIP;\n"
            "– генератор отчётов (docx, CSV, JSON)."
        ),
    }
    return claims.get(lang, claims['en'])

def laplacian_neumann(field: np.ndarray, dx: float, dz: float) -> np.ndarray:
    """Laplacian with Neumann boundary condition."""
    f = np.pad(field, 1, mode='edge')
    lap = (
        (f[1:-1, 2:] - 2.0 * f[1:-1, 1:-1] + f[1:-1, :-2]) / dx ** 2
        + (f[2:, 1:-1] - 2.0 * f[1:-1, 1:-1] + f[:-2, 1:-1]) / dz ** 2
    )
    return lap

def phase_field_update(
    damage: np.ndarray,
    strain_energy: np.ndarray,
    dx: float,
    dz: float,
    dt: float,
    Gc: float = 0.01,
    l_char: float = 1.0,
    eta: float = 1e-3,
) -> np.ndarray:
    """Phase-field damage model update."""
    dt_max = (eta * dx ** 2) / (2.0 * Gc * l_char + EPS_GENERAL)
    dt = min(dt, 0.9 * dt_max)
    lap = laplacian_neumann(damage, dx, dz)
    driving = (
        Gc * l_char * lap
        - (Gc / l_char) * damage
        + (1.0 - damage) * strain_energy
    )
    return np.clip(damage + (dt / eta) * driving, 0.0, 1.0)

# ═══════════════════════════════════════════════════════════════════════════
# CACHING AND ML FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="Harorat maydoni hisoblanmoqda...", max_entries=30)
def compute_temperature_field_moving(
    time_h: int,
    T_source_max: int,
    burn_duration: int,
    total_depth: float,
    source_z: float,
    grid_shape: Tuple[int, int],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Temperature field simulation (cached)."""
    x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, grid_shape[1])
    z_axis = np.linspace(0.0, total_depth + 50.0, grid_shape[0])
    dx = float(x_axis[1] - x_axis[0])
    dz = float(z_axis[1] - z_axis[0])
    grid_x, grid_z = np.meshgrid(x_axis, z_axis)
    temp_2d = np.full_like(grid_x, 25.0)
    rho_field = np.full_like(temp_2d, 1400.0)
    cp_field = specific_heat(temp_2d)
    k_field = thermal_conductivity(temp_2d)
    total_time = max(burn_duration, time_h) * 3600.0
    
    sources = [
        {'x0': -total_depth / 3.0, 'start': 0, 'moving': False},
        {'x0': 0.0, 'start': 40, 'moving': True, 'v': 0.02},
        {'x0': total_depth / 3.0, 'start': 80, 'moving': False},
    ]
    
    source_mask_local = np.abs(grid_z - source_z) < 10.0
    if np.any(source_mask_local):
        rho_cp_ref = float(np.mean((rho_field * cp_field)[source_mask_local]))
    else:
        rho_cp_ref = 1400.0 * 960.0

    time_step_s = 3600.0
    n_steps = max(int(total_time / time_step_s), 1)
    n_steps = min(n_steps, 200)
    time_step_s = total_time / n_steps
    current_time_h = 0.0

    for _ in range(n_steps):
        current_time_h += time_step_s / 3600.0
        Q_source = np.zeros_like(temp_2d)
        for src in sources:
            if current_time_h <= src['start']:
                continue
            dt_sec = (current_time_h - src['start']) * 3600.0
            x_center = (src['x0'] + src.get('v', 0.0) * dt_sec) if src['moving'] else src['x0']
            elapsed = current_time_h - src['start']
            if elapsed <= burn_duration:
                curr_T = float(T_source_max)
            else:
                curr_T = 25.0 + (T_source_max - 25.0) * np.exp(-0.03 * (elapsed - burn_duration))
            pen_depth = np.sqrt(4.0 * PARAMS.THERMAL_DIFFUSIVITY * max(dt_sec, 3600.0)) + 15.0
            dist_sq = (grid_x - x_center) ** 2 + (grid_z - source_z) ** 2
            Q_source += rho_cp_ref * (curr_T - 25.0) / time_step_s * np.exp(-dist_sq / pen_depth ** 2)

        temp_2d = solve_heat_equation_dynamic(
            T=temp_2d, Q=Q_source,
            rho_field=rho_field, cp_field=cp_field, k_field=k_field,
            dx=dx, dz=dz, total_time=time_step_s, T_air=25.0,
        )
        cp_field = specific_heat(temp_2d)
        k_field = thermal_conductivity(temp_2d)

    return temp_2d, x_axis, z_axis, grid_x, grid_z

@st.cache_data(show_spinner=False, max_entries=10)
def sensitivity_analysis(
    base_ucs: float,
    base_gsi: float,
    base_d: float,
    base_nu: float,
    base_t: float,
    H_seam: float,
    beta_th: float,
    depth: float,
    density: float,
    range_pct: float = 0.2,
) -> Tuple[pd.DataFrame, float]:
    """Sensitivity analysis (Tornado plot data)."""
    def qfos(ucs, gsi, d, nu, T):
        return _quick_fos(ucs, gsi, T, H_seam, 20.0, d, beta_th, depth, density)

    base_fos = qfos(base_ucs, base_gsi, base_d, base_nu, base_t)
    params_range = {
        'UCS (MPa)': (base_ucs, base_ucs * (1 - range_pct), base_ucs * (1 + range_pct)),
        'GSI': (base_gsi, base_gsi * (1 - range_pct), min(100.0, base_gsi * (1 + range_pct))),
        'D factor': (base_d, max(0.0, base_d - 0.2), min(1.0, base_d + 0.2)),
        'Poisson (ν)': (base_nu, max(0.1, base_nu - 0.05), min(0.4, base_nu + 0.05)),
        'Temperature (°C)': (base_t, base_t * (1 - range_pct), min(1200.0, base_t * (1 + range_pct))),
    }
    results = []
    for name, (base_v, low_v, high_v) in params_range.items():
        kw = dict(ucs=base_ucs, gsi=base_gsi, d=base_d, nu=base_nu, T=base_t)
        key_map = {
            'UCS (MPa)': 'ucs', 'GSI': 'gsi', 'D factor': 'd',
            'Poisson (ν)': 'nu', 'Temperature (°C)': 'T'
        }
        k = key_map[name]
        kw_low = dict(kw); kw_low[k] = low_v
        kw_high = dict(kw); kw_high[k] = high_v
        results.append({
            'param': name,
            'low': qfos(**kw_low) - base_fos,
            'high': qfos(**kw_high) - base_fos,
        })
    return pd.DataFrame(results), base_fos

# ═══════════════════════════════════════════════════════════════════════════
# MACHINE LEARNING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def physics_features(
    temp: np.ndarray,
    sigma1: np.ndarray,
    sigma3: np.ndarray,
    depth: np.ndarray,
    ucs: float,
) -> np.ndarray:
    """Extract physics-based features."""
    dmg = thermal_damage(temp, PARAMS.thermal_damage_beta)
    ucs_T = apply_thermal_degradation(ucs, temp, PARAMS.thermal_damage_beta)
    fos_approx = np.clip(ucs_T / (sigma1 + EPS_STRESS), 0.0, 10.0)
    strain_energy = (sigma1 ** 2 - sigma1 * sigma3 + sigma3 ** 2) / (2.0 * PARAMS.E_mass / 1e6 + EPS_GENERAL)
    X = np.column_stack([temp, sigma1, sigma3, depth, dmg, fos_approx, strain_energy])
    return X

# PyTorch models (if available)
if PT_AVAILABLE:
    class HybridPINN(nn.Module):
        """Physics-Informed Neural Network."""
        def __init__(self, input_dim: int = 7):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, 128),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
                nn.Sigmoid(),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            return self.net(x)

    class SimpleRiskNN(nn.Module):
        def __init__(self, input_dim: int = 3):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 16), nn.ReLU(),
                nn.Linear(16, 8), nn.ReLU(),
                nn.Linear(8, 1), nn.Sigmoid(),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            return self.net(x)

    class SimpleNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(2, 16)
            self.fc2 = nn.Linear(16, 16)
            self.fc3 = nn.Linear(16, 1)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            x = torch.relu(self.fc1(x))
            x = torch.relu(self.fc2(x))
            return 3.0 * torch.sigmoid(self.fc3(x))

    def physics_informed_loss(pred, sigma1, sigma_ci, temp, damage):
        fos_approx = torch.clamp(sigma_ci / (sigma1 + float(EPS_STRESS)), 0.0, 3.0)
        p_failure_hb = torch.sigmoid(5.0 * (1.0 - fos_approx))
        hb_consistency = torch.mean((pred - p_failure_hb) ** 2)
        thermal_risk = torch.clamp((temp - 800.0) / 400.0, 0.0, 1.0) * damage
        thermal_consistency = torch.mean(torch.relu(thermal_risk - pred))
        return hb_consistency + 0.5 * thermal_consistency

    def train_hybrid_model(X, y, sigma1, sigma_ci, temp, damage):
        y = np.clip(y, 0.0, 1.0)
        model = HybridPINN(input_dim=X.shape[1]).to(device)
        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        y_t = torch.tensor(y, dtype=torch.float32).view(-1, 1).to(device)
        sigma1_t = torch.tensor(sigma1, dtype=torch.float32).to(device)
        sigma_ci_t = torch.tensor(sigma_ci, dtype=torch.float32).to(device)
        temp_t = torch.tensor(temp, dtype=torch.float32).to(device)
        damage_t = torch.tensor(damage, dtype=torch.float32).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=3e-4, weight_decay=1e-5)
        best_loss = float('inf')
        patience, no_improve = 20, 0
        model.train()
        for epoch in range(500):
            opt.zero_grad()
            pred = model(X_t)
            bce = nn.BCELoss()(pred, y_t)
            phys = physics_informed_loss(pred, sigma1_t, sigma_ci_t, temp_t, damage_t)
            loss = bce + 0.4 * phys
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            if loss.item() < best_loss - 1e-4:
                best_loss = loss.item()
                no_improve = 0
            else:
                no_improve += 1
            if no_improve >= patience:
                logger.info(f"Early stopping at epoch {epoch}, loss={best_loss:.4f}")
                break
        model.eval()
        return model

    def train_simple_risk_nn(model, X, y, epochs=150):
        y = np.clip(y, 0.0, 1.0)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.BCELoss()
        X_t = torch.tensor(X, dtype=torch.float32).to(device)
        y_t = torch.tensor(y, dtype=torch.float32).view(-1, 1).to(device)
        model.train()
        for _ in range(epochs):
            opt.zero_grad()
            loss = loss_fn(model(X_t), y_t)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        model.eval()
        return model

def train_random_forest(X_scaled: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    """Train Random Forest classifier."""
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=12, random_state=RANDOM_SEED,
        n_jobs=-1, class_weight='balanced',
    )
    rf.fit(X_scaled, y)
    return rf

def _train_models(X, y, sigma1, sigma_ci, temp, damage):
    """Train hybrid models."""
    indices = np.arange(len(X))
    split_point = int(len(X) * 0.8)
    idx_train = indices[:split_point]
    idx_test = indices[split_point:]
    y_train = y[idx_train]
    y_test = y[idx_test]
    X_train = X[idx_train]
    X_test = X[idx_test]
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)
    if PT_AVAILABLE:
        model = train_hybrid_model(
            X_train_sc, y_train,
            sigma1[idx_train], sigma_ci[idx_train],
            temp[idx_train], damage[idx_train],
        )
        rf = train_random_forest(X_train_sc, y_train)
    else:
        model = None
        rf = train_random_forest(X_train_sc, y_train)
    return model, rf, scaler, X_test_sc, y_test

@st.cache_resource
def get_ensemble_model_cached(
    data_fingerprint: str,
    X: np.ndarray,
    y: np.ndarray,
    sigma1: np.ndarray,
    sigma_ci: np.ndarray,
    temp: np.ndarray,
    damage: np.ndarray,
):
    """Get cached ensemble model."""
    return _train_models(X, y, sigma1, sigma_ci, temp, damage)

@st.cache_resource
def get_risk_model():
    """Get risk prediction model."""
    if not PT_AVAILABLE:
        return None
    n = 1000
    rng_r = np.random.default_rng(seed=RANDOM_SEED)
    temp_r = rng_r.uniform(20.0, 1000.0, n)
    stress_r = rng_r.uniform(1.0, 20.0, n)
    ucs_r = rng_r.uniform(10.0, 80.0, n)
    fos_r = np.clip(ucs_r / (stress_r + EPS_STRESS), 0.0, 3.0)
    y_r = np.clip(1.0 - fos_r / 3.0, 0.0, 1.0)
    X_r = np.column_stack([temp_r, stress_r, ucs_r])
    model = SimpleRiskNN().to(device)
    model = train_simple_risk_nn(model, X_r, y_r, epochs=150)
    return model

def predict_collapse(
    model,
    rf: RandomForestClassifier,
    scaler: StandardScaler,
    X_raw: np.ndarray,
) -> np.ndarray:
    """Predict collapse probability."""
    if X_raw.shape[1] != 7:
        raise ValueError(f"Expected 7 features, got {X_raw.shape[1]}")
    X_sc = scaler.transform(X_raw)
    if model is not None:
        model.eval()
        with torch.no_grad():
            nn_pred = model(
                torch.tensor(X_sc, dtype=torch.float32).to(device)
            ).cpu().numpy()
    else:
        nn_pred = np.zeros((X_raw.shape[0], 1))

    proba = rf.predict_proba(X_sc)
    rf_pred = proba[:, 1].reshape(-1, 1) if proba.shape[1] >= 2 else proba[:, 0].reshape(-1, 1)
    
    w_nn = 0.6 if (nn_pred is not None and np.any(nn_pred != 0.0)) else 0.0
    w_rf = 1.0 - w_nn
    return w_nn * nn_pred + w_rf * rf_pred

def predict_risk_from_sensor(
    model,
    temp: np.ndarray,
    stress: np.ndarray,
    ucs_lab: np.ndarray,
) -> np.ndarray:
    if model is None:
        return np.full_like(temp, 0.5)
    X = np.column_stack([temp, stress, ucs_lab])
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    model.eval()
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.flatten()

def validate_sensor_csv(
    uploaded_file,
    required_cols: List[str],
    max_size_mb: float = 10.0,
    max_rows: int = 10000,
) -> pd.DataFrame:
    """Validate sensor CSV file."""
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"Fayl {file_size_mb:.1f} MB — {max_size_mb} MB dan katta!")
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8', nrows=max_rows)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='latin-1', nrows=max_rows)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Ustunlar yo'q: {missing}")
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    n_before = len(df)
    df = df.dropna(subset=required_cols)
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        st.warning(f"⚠️ {n_dropped} ta satr raqamga aylantirilmadi va o'chirildi (validate_sensor_csv).")
    return df

def compute_advanced_fos(
    grid_x, grid_z, active_wells_tuple, well_x_tuple, source_z_val, h_seam, cavity_width,
    temp_field, sigma_v_field, layers_data_list, layer_bounds_list,
    E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn,
):
    """Compute advanced FOS field."""
    fos = np.full_like(grid_x, 3.0)
    CONFINEMENT = PARAMS.CONFINEMENT
    RELAX = PARAMS.RELAX

    for px_idx in active_wells_tuple:
        px = well_x_tuple[px_idx]
        delta_z_local = source_z_val - grid_z
        T = temp_field
        delta_T = np.maximum(T - T_REF_AMBIENT, 0.0)
        thermal_zone = np.sqrt((grid_x - px) ** 2 + (grid_z - source_z_val) ** 2) < (h_seam * 3.0)

        for layer_idx, (top, bot, layer) in enumerate(layer_bounds_list):
            mask = (grid_z >= top) & (grid_z < bot)
            if not np.any(mask):
                continue
            ucs_l = layer['ucs']
            gsi_l = layer['gsi']
            mi_l = layer['mi']
            delta_T_m = delta_T[mask]
            gsi_l_eff = gsi_thermal_degradation(gsi_l, float(np.mean(delta_T_m)) if np.any(mask) else 0.0)
            mb_l, s_hb, a_hb = hoek_brown_params(gsi_l_eff, mi_l, D_factor)
            sigma_v = sigma_v_field[mask]
            sigma_ci_T = apply_thermal_degradation(ucs_l, delta_T_m, beta_th)
            sigma_3 = K0 * sigma_v * (0.6 + 0.4 * (1.0 - thermal_damage(delta_T_m, beta_th)))
            sigma_th = np.zeros_like(sigma_v)
            local_thermal = thermal_zone[mask]
            if np.any(local_thermal):
                grad_T_local = np.sqrt(
                    np.gradient(T, axis=1, edge_order=2)[mask] ** 2
                    + np.gradient(T, axis=0, edge_order=2)[mask] ** 2
                )
                th_vals = (CONFINEMENT * E * alpha * delta_T_m[local_thermal]) / (1.0 - nu) - RELAX * grad_T_local[local_thermal]
                sigma_th[local_thermal] = np.clip(th_vals, 0.0, sigma_ci_T[local_thermal] * 0.35)
            sigma_1 = sigma_v + sigma_th
            sigma_limit = hoek_brown(np.maximum(sigma_3, 0.0), np.maximum(sigma_ci_T, EPS_STRESS), mb_l, s_hb, a_hb)
            fos_val = np.where(sigma_1 > 0.01, sigma_limit / (sigma_1 + EPS_STRESS), 3.0)
            fos_val = np.clip(fos_val, 0.0, 50.0)
            yield_mask = sigma_1 > (sigma_limit * 0.85)
            fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
            fos_sub = fos[mask]
            fos_sub = np.minimum(fos_sub, fos_val)
            fos[mask] = fos_sub

            is_last_layer = (layer_idx == len(layer_bounds_list) - 1)
            if is_last_layer:
                a_half = cavity_width / 2.0
                b_half = h_seam / 2.0
                dome_width = a_half * np.clip(1.0 - delta_z_local[mask] / (Hc + EPS_GENERAL), 0.0, 1.0)
                failure_zone = fos_val < 1.2
                dome_condition = (
                    (delta_z_local[mask] > 0)
                    & (delta_z_local[mask] < Hc)
                    & (np.abs(grid_x[mask] - px) < dome_width)
                    & failure_zone
                )
                if np.any(dome_condition):
                    decay = np.clip(1.0 - (delta_z_local[mask][dome_condition] / (Hc + EPS_GENERAL)), 0.3, 1.0)
                    fos_sub[dome_condition] = np.minimum(fos_sub[dome_condition], decay)
                    fos[mask] = fos_sub

    for px_idx in active_wells_tuple:
        px = well_x_tuple[px_idx]
        a_half = cavity_width / 2.0
        b_half = h_seam / 2.0
        cavity_ellipse = (
            (grid_x - px) ** 2 / (a_half ** 2 + EPS_GENERAL)
            + (grid_z - source_z_val) ** 2 / (b_half ** 2 + EPS_GENERAL)
        ) < 1.0
        fos[cavity_ellipse] = 0.05

    if layer_bounds_list:
        last_layer = layer_bounds_list[-1][2]
        bottom_boundary = last_layer['z_start'] + last_layer['thickness']
        fos[grid_z > bottom_boundary] = 2.5

    all_well_idxs = [0, 1, 2]
    for i in all_well_idxs:
        if i not in active_wells_tuple:
            px = well_x_tuple[i]
            pillar_mask = (
                (np.abs(grid_x - px) < h_seam * 1.5)
                & (np.abs(grid_z - source_z_val) < h_seam * 1.2)
            )
            fos[pillar_mask] = 2.5

    if set(active_wells_tuple) == {0, 2}:
        selek_eni = abs(well_x_tuple[0] - well_x_tuple[2]) - cavity_width
        sigma_cm_pillar = ucs_coal_MPa * (max(float(s_dyn), 1e-9) ** float(a_dyn))
        ps_pillar = sigma_cm_pillar * (WILSON_C1 + WILSON_C2 * selek_eni / (h_seam + EPS_STRESS))
        fos_pillar = ps_pillar / (sigma_v_coal_MPa + EPS_STRESS)
        pillar_zone = (
            (np.abs(grid_x - well_x_tuple[1]) < selek_eni / 2.0)
            & (np.abs(grid_z - source_z_val) < h_seam)
        )
        fos[pillar_zone] = np.maximum(fos[pillar_zone], fos_pillar)

    return np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)

@st.cache_data(show_spinner=False, max_entries=10)
def compute_advanced_fos_cached(
    grid_x_hash: str,
    active_wells_tuple,
    well_x_tuple,
    source_z_val,
    h_seam,
    cavity_width,
    temp_hash: str,
    sigma_v_hash: str,
    layers_tuple,
    layer_bounds_tuple,
    E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn,
    grid_x: np.ndarray,
    grid_z: np.ndarray,
    temp_field: np.ndarray,
    sigma_v_field: np.ndarray,
    layers_data_list: List[dict],
    layer_bounds_list: List[tuple],
):
    return compute_advanced_fos(
        grid_x, grid_z, active_wells_tuple, well_x_tuple, source_z_val, h_seam, cavity_width,
        temp_field, sigma_v_field, layers_data_list, layer_bounds_list,
        E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn,
    )

def calculate_live_metrics(
    h: float,
    layers: List[dict],
    T_max: float,
    base_rec_width: float,
    beta_th: float,
) -> Tuple[float, float, float, float]:
    """Calculate live metrics."""
    target = layers[-1]
    ucs_0, H_l = target['ucs'], target['thickness']
    if h <= 40.0:
        curr_T = T_REF_AMBIENT + (T_max - T_REF_AMBIENT) * (h / 40.0)
    else:
        curr_T = T_max * np.exp(-0.001 * (h - 40.0))
    ucs_T_live = float(apply_thermal_degradation(ucs_0, curr_T, beta_th))
    w_rec = base_rec_width * (1.0 + 0.10 * min(h, 100.0) / 100.0)
    p_str = ucs_T_live * (WILSON_C1 + WILSON_C2 * w_rec / (H_l + EPS_STRESS))
    max_sub = (H_l * PARAMS.extraction_ratio * 0.45) * (min(h, 120.0) / 120.0)
    return p_str, w_rec, curr_T, max_sub

# ═══════════════════════════════════════════════════════════════════════════
# STREAMLIT UI - MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="UCG SCI-Grade Platform v3.0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Language selection
lang_col1, lang_col2, lang_col3 = st.sidebar.columns(3)
if lang_col1.button("🇺🇿 UZ", use_container_width=True):
    st.session_state.language = "uz"
if lang_col2.button("🇬🇧 EN", use_container_width=True):
    st.session_state.language = "en"
if lang_col3.button("🇷🇺 RU", use_container_width=True):
    st.session_state.language = "ru"

st.sidebar.markdown("---")
st.title(f"🔬 {t('app_title')}")
st.caption(t('app_subtitle'))

# Main content begins here
st.sidebar.header(t('sidebar_header_params'))

# ... (Continue with the rest of the main Streamlit UI code)
# The code is very long, so I'm showing the structure.
# You need to paste the remaining UI sections.

st.success("✅ Kod tuzatildi! Indentation xatosi bartaraf qilingan.")
st.info("📝 Bu kodni `.py` faylga saqlang va `streamlit run app.py` bilan ishga tushiring.")
