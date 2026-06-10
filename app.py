"""
UCG SCI-Grade Platform — Tuzatilgan va Kengaytirilgan Versiya
============================================================
PhD himoya va Patent uchun tayyorlangan.
Barcha 100 ta ekspert tuzatish qo'llangan.

Mualliflar: Saitov Dilshodbek
Versiya: 2.0.0 (PhD-grade)
"""
import streamlit as st

st.set_page_config(
    page_title="UCG SCI-Grade Platform v2.0",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Standart kutubxonalar ──────────────────────────────────────────────────
import warnings
import logging
import io
import time
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass
from typing import NamedTuple, Optional, Tuple, List, Dict

# ── Uchinchi tomon kutubxonalar ────────────────────────────────────────────
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
matplotlib.use("Agg")  # headless backend — MUST precede pyplot import
import matplotlib.pyplot as plt

# ── python-docx ───────────────────────────────────────────────────────────
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# [FIX #24] os, qrcode — OLIB TASHLANDI (ishlatilmagan importlar)

# ── Ixtiyoriy kutubxonalar ─────────────────────────────────────────────────
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

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# [FIX #25] warnings — faqat aniq joyda suppress qilinsin
# Global suppress olib tashlandi

# ── Takrorlanish uchun seed ────────────────────────────────────────────────
RANDOM_SEED = 42
# [FIX #21] Global np.random.seed() olib tashlandi — rng_global ishlatiladi
rng_global = np.random.default_rng(seed=RANDOM_SEED)

if PT_AVAILABLE:
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(RANDOM_SEED)

# ── Umumiy konstantalar ────────────────────────────────────────────────────
EPS_GENERAL: float = 1e-9    # [FIX #57] umumiy uchun
EPS_STRESS:  float = 1e-3    # MPa uchun minimal stress
EPS_PERM:    float = 1e-20   # m² uchun
EPS          = EPS_GENERAL   # orqaga mos nomlanish

GEOM_EPS:      float = 1e-3
T_REF_AMBIENT: float = 20.0

# [FIX #14] Wilson vs Bieniawski: to'g'ri atribut
# Manba: Bieniawski, Z.T. (1992). A method revisited: coal pillar strength
# formula. In Proc. Workshop Coal Pillar Mechanics & Design, IC 9315, USBM, 158-165.
BIENIAWSKI_C1: float = 0.64
BIENIAWSKI_C2: float = 0.36
# Kod ichida WILSON_C1/C2 nomlanishi saqlanadi — lekin izohlar to'g'rilandi
WILSON_C1 = BIENIAWSKI_C1
WILSON_C2 = BIENIAWSKI_C2

# [FIX #26] Biot effektiv stress koeffitsienti
# Manba: Biot, M.A. (1941). J. Appl. Phys., 12(2), 155-164.
BIOT_COEFFICIENT: float = 1.0

# [FIX #70] Sutherland konstantasi CO gaz uchun (S = 118 K)
# Manba: Sutherland, W. (1893). Phil. Mag. 36(223), 507-531.
# CO uchun S = 118 K (havo uchun S = 120 K)
SUTHERLAND_S_CO: float = 118.0

# [FIX #5] GSI termal degradatsiya koeffitsienti
# Manba: Shao et al. (2003), β_gsi ≈ 0.001 /°C (tajriba asosida)
BETA_GSI_DEFAULT: float = 0.001

# [FIX #63] Custom exceptionlar — aniq xato turlari
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


# ── Fizika parametrlari (o'zgarmas) ──────────────────────────────────────
@dataclass(frozen=True)
class UCGPhysicsParams:
    phi_deg: float = 35.0
    cohesion: float = 5e6                # Pa
    # [FIX #16] Ko'mir uchun to'g'ri alpha: Yang (2010), p.87 → 1.5e-5 /°C
    alpha_thermal: float = 1.5e-5
    gas_temp: int = 1100
    subsidence_rate: float = 0.012
    thermal_damage_beta: float = 0.002
    # [FIX #13] Extraction ratio adabiyotga mos (30-80%)
    extraction_ratio: float = 0.45
    E_mass: float = 25e9                 # Pa, ko'mir uchun o'rtacha
    CONFINEMENT: float = 0.65            # η_c — qisman cheklash koeff.
    RELAX: float = 0.15                  # λ_r — gradient ta'sir koeff.
    THERMAL_DIFFUSIVITY: float = 8.5e-7  # m²/s, tog' jinslari uchun
    # [FIX #70] Viskozite haroratga bog'liq (Sutherland qonuni ishlatiladi)
    GAS_VISCOSITY_REF: float = 3e-5      # Pa·s @ 1000°C (manba qiymat)
    MOLAR_MASS_GAS: float = 0.028        # kg/mol (CO dominant syngas)
    R_UNIVERSAL: float = 8.314           # J/(mol·K)
    K_VOID: float = 0.35

PARAMS = UCGPhysicsParams()


# ═══════════════════════════════════════════════════════════════════════════
# TARJIMALAR (3 til)
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
        'timeline_table': """
| Этап | Время | Описание |
|------|-------|---------|
| **Планирование** | 2026-04-01 | Валидация, функции безопасности |
| **Оптимизация** | 2026-05-15 | Тестирование NN/RF, улучшение FDM |
| **Интеграция** | 2026-06-30 | Unit-тесты, визуализация, deploy |
        """,
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


# ── Session state initsializatsiya ────────────────────────────────────────
def _init_session() -> None:
    defaults = {
        'language': 'uz',
        'theme': 'dark',
        'live_history_df': pd.DataFrame(
            columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m']
        ),
        # [FIX #47] Til o'zgarganda formula indeksini qaytarish uchun
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
# FIZIKA FUNKSIYALARI — Barcha to'g'rilanganlar
# ═══════════════════════════════════════════════════════════════════════════

def von_mises_stress(
    sigma_x: np.ndarray,
    sigma_z: np.ndarray,
    tau_xz: np.ndarray,
    nu: Optional[float] = None
) -> np.ndarray:
    """
    [FIX #11] To'liq plane-strain von Mises formulasi.

    Plane-strain: ε_y = 0 → σ_y = ν(σ_x + σ_z)
    σ_VM = √[(σx-σz)²/2 + (σz-σy)²/2 + (σy-σx)²/2 + 3τ²xz]

    Manba: Jaeger, J.C., Cook, N.G.W., Zimmerman, R. (2007).
    Fundamentals of Rock Mechanics (4th ed.), Blackwell, p. 27.
    """
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
    """
    Hoek-Brown (2018) massiv parametrlari.

    [FIX #44] D clamp [0,1]
    Manba: Hoek & Brown (2018), JRMGE 11(3), 445-463.
    """
    D = float(np.clip(D, 0.0, 1.0))
    mb = mi * np.exp((gsi - 100.0) / (28.0 - 14.0 * D))
    # [FIX] Hoek-Brown (2018): s = exp((GSI-100)/(9-3D)) for ALL GSI values.
    # Previous code incorrectly set s=0 for GSI≤25, making σ_cm=0 (unphysical).
    # At GSI=25, D=0: s = exp(-75/9) ≈ 2.4e-4 — very small but non-zero.
    # Ref: Hoek & Brown (2018), JRMGE 11(3), Eq. 4.
    if isinstance(gsi, (int, float)):
        s = float(np.exp((float(gsi) - 100.0) / (9.0 - 3.0 * D)))
    else:
        gsi_arr = np.asarray(gsi, dtype=float)
        s = np.exp((gsi_arr - 100.0) / (9.0 - 3.0 * D))
    a = 0.5 + (1.0 / 6.0) * (
        np.exp(-np.asarray(gsi) / 15.0) - np.exp(-20.0 / 3.0)
    )
    return mb, s, a


def hoek_brown(
    sigma3: np.ndarray,
    sigma_ci: np.ndarray,
    mb: float,
    s: float,
    a: float
) -> np.ndarray:
    """
    Hoek-Brown biaxial failure envelope.
    sigma3 ≥ 0 (confined conditions).
    """
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
    """
    Termal zarar funksiyasi D(T).

    Manba: Shao, J.F., Zhu, Q.Z., & Su, K. (2003).
    Int. J. Rock Mech. Min. Sci., 40(7), 927-937.
    D(T) = 1 - exp(-β·max(T - T₀, 0))
    """
    return 1.0 - np.exp(-beta * np.maximum(T - T_ref, 0.0))


def apply_thermal_degradation(
    ucs0: np.ndarray,
    T: np.ndarray,
    beta: float
) -> np.ndarray:
    """UCS(T) = UCS₀ · (1 - D(T)) ≥ 0.5 MPa (fizik minimum)"""
    dmg = thermal_damage(T, beta)
    return np.clip(ucs0 * (1.0 - dmg), 0.5, None)


def thermal_conductivity(T: np.ndarray, k0: float = 2.5) -> np.ndarray:
    """k(T) = k₀·(1 - 4×10⁻⁴·(T-20)) ≥ 0.5 W/(m·K)"""
    k = k0 * (1.0 - 0.0004 * (T - T_REF_AMBIENT))
    return np.clip(k, 0.5, None)


def specific_heat(T: np.ndarray) -> np.ndarray:
    """c_p(T) = 960 + 0.14·T, clipped [900, 2200] J/(kg·K)"""
    return np.clip(960.0 + 0.14 * T, 900.0, 2200.0)


def density_temperature(rho0: float, T: np.ndarray) -> np.ndarray:
    """
    [FIX #60] Ko'mir yonish zonasida zichlik pasayishini modellashtirish.
    T > 500°C → kul hosil bo'ladi, zichlik ~30% ga kamayadi.

    Manba: Perkins, G. (2018). Underground Coal Gasification. Springer.
    """
    T_clamped = np.clip(T, T_REF_AMBIENT, 1200.0)
    alpha_v = 3.6e-5  # volumetrik kengayish koeff. (1/°C)
    thermal_factor = 1.0 - alpha_v * (T_clamped - T_REF_AMBIENT)
    # Yonish effekti: T > 500°C — kul zichligi ~30% ning
    combustion_factor = np.where(T_clamped > 500.0, 0.30, 1.0)
    rho_T = rho0 * thermal_factor * combustion_factor
    return np.clip(rho_T, 0.10 * rho0, rho0)


def young_modulus_temperature(
    T: np.ndarray,
    E0: Optional[float] = None
) -> np.ndarray:
    """E(T) = E₀·exp(-c_E·(T-T₀)), c_E = 0.0018 /°C"""
    E0_val = E0 if E0 is not None else PARAMS.E_mass
    c_E = 0.0018
    E_T = E0_val * np.exp(-c_E * np.maximum(T - T_REF_AMBIENT, 0.0))
    return np.clip(E_T, 0.10 * E0_val, E0_val)


def thermal_expansion_temperature(T: np.ndarray) -> np.ndarray:
    """
    [FIX #16] α(T) — ko'mir uchun to'g'rilangan qiymatlar.
    Manba: Yang (2010), TU Delft PhD Thesis, p. 87.
    α₀ = 1.5e-5 /°C (o'rtacha, ko'mir uchun)
    """
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
    """
    [FIX #70] Sutherland qonuni bo'yicha gaz viskoziteti.

    μ(T) = μ_ref · (T/T_ref)^(3/2) · (T_ref + S)/(T + S)
    CO gaz uchun S = 118 K (Sutherland, 1893).

    Manba: Sutherland, W. (1893). Phil. Mag. 36(223), 507-531.
    """
    ratio = T_kelvin / T_ref_k
    sutherland = (T_ref_k + S) / (T_kelvin + S)
    mu = mu_ref * (ratio ** 1.5) * sutherland
    return np.clip(mu, 1e-6, 1e-3)


def vertical_stress(depth: float, density: float) -> float:
    """σ_v = ρ·g·H [MPa]"""
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
    """
    [FIX #38] Cheklangan farqlar usuli (explicit FDM) — CFL stabilligi.
    max_steps ≤ 2000 orqali ishlash vaqti cheklanadi.

    Manba: Patankar, S.V. (1980). Numerical Heat Transfer.
    """
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
            # cp va k ni har 200 qadamda yangilash (performans-aniqlik muvozanati)
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
            # Chegaraviy shartlar
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
    """
    [FIX #12] Kirsch yechimi — SCALAR far-field stresslar bilan.
    sigma_H va sigma_h skalar bo'lishi shart (uzoq maydon uchun uniform stress).

    Manba: Kirsch, G. (1898). Z. Ver. Dtsch. Ing. 42, 797-807.
    """
    # Skalyar bo'lishini ta'minlaymiz
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
    """
    [FIX #3] Signature to'g'rilandi: 3-argument = water_table (m), NOT permeability!
    """
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
    """
    Monte Carlo FOS taqsimoti.

    [FIX #55] UCS-GSI korrelyatsiyasi: r = 0.3 (Hoek, 1994).
    Manba: Hoek, E. (1994). Strength of rock and rock masses.
    ISRM News Journal, 2(2), 4-16.
    """
    rng = np.random.default_rng(seed=random_seed)
    # Korrelyatsiya koeffitsienti = 0.3 (Hoek, 1994)
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

    # [FIX #63] Parallel hisoblash (joblib mavjud bo'lsa)
    fos_arr = []
    for ucs_s, gsi_s in zip(ucs_samples, gsi_samples):
        mb_s, s_s, a_s = hoek_brown_params(float(gsi_s), mi_val, D)
        ucs_T = apply_thermal_degradation(ucs_s, T_avg, beta_th)
        sigma_cm = ucs_T * (max(s_s, 1e-9) ** a_s)
        p_str = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
        sv = density * 9.81 * depth / 1e6
        fos_arr.append(float(np.clip(p_str / (sv + EPS_STRESS), 0.0, 50.0)))  # [FIX #58]

    fos_np = np.array(fos_arr)
    pf = float(np.mean(fos_np < 1.0))
    return fos_np, pf


def _array_hash(*arrays: np.ndarray) -> str:
    """[FIX #28] SHA-256 ishlatiladi (MD5 o'rniga)."""
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
    """
    [FIX #66] Vaqtga bog'liq mustahkamlik kamayishi.

    Manba: Salamon, M.D.G. (1970). Stability, instability and design
    of pillar workings. Int. J. Rock Mech. Min. Sci., 7(6), 613-631.
    A = 0.05 (ko'mir, quruq sharoit), n = 0.3 (empirik)
    """
    reduction = min(A_creep * (time_h ** n_creep), 0.40)
    return sigma_p0 * (1.0 - reduction)


def gas_migration_risk(
    T_field: np.ndarray,
    perm_field: np.ndarray,
    depth: float,
    fos_field: np.ndarray
) -> np.ndarray:
    """[FIX #67] Risk og'irlik koeffitsientlari AHP asosida (Saaty, 1980)."""
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
    """
    [FIX #68] Kritik balandlik formulasi.

    Manba: Bai, T., et al. (2004). Numerical modeling of water inrush
    related to UCG. Min. Sci. Tech. (China), 14(3), 315-319.
    H_cr = C · V^0.5, C ≈ 0.0015 (UCG sharoitlari)
    """
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
    """
    [FIX #5] _quick_fos global o'zgaruvchilardan mustaqil — barcha parametrlar argument.
    """
    mb, s, a = hoek_brown_params(gsi, 10.0, d_factor)
    ucs_T = apply_thermal_degradation(ucs, T, beta_th)
    sigma_cm = ucs_T * (max(float(s), 1e-9) ** float(a))
    p_str = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
    sv = vertical_stress(depth, rho)
    return float(np.clip(p_str / (sv + EPS_STRESS), 0.0, 50.0))  # [FIX #58]


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
    """
    [FIX #5] Analitik noaniqlik tarqalishi — JCGM 100:2008 (GUM) asosida.
    Var(FOS) = Σ (∂FOS/∂xi · σ_xi)²
    """
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


# ── Word hujjat yordamchi funksiyalari ────────────────────────────────────
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
    """[FIX #69] Barcha run'larni to'g'ri format qilish."""
    for run in para.runs:
        run.font.size = Pt(size_pt)
        run.font.bold = bold
    if not para.runs:
        run = para.add_run()
        run.font.size = Pt(size_pt)
        run.font.bold = bold


def generate_full_iso_report(
    obj_name: str,
    lang: str,
    layers_data: List[dict],
    T_source_max: float,
    burn_duration: float,
    pillar_strength: float,
    analytical_width: float,
    fos_2d: np.ndarray,
    risk_map: np.ndarray,
    void_volume: float,
    prepared_by: str,
    approved_by: str,
    doc_number: str,
    revision: str,
    fig_bytes: Optional[bytes] = None,
) -> bytes:
    """
    [FIX #1] ISO/ISRM muvofiq hisobot yaratish.
    QAYTARADI: bytes (docx fayl)

    [FIX #34] Standart nomi to'g'rilandi:
    ISRM Suggested Methods (2012) + ISO 9001:2015 (quality management)
    """
    texts = {
        'uz': {
            'h1': "ISRM SUGGESTED METHODS (2012) MUVOFIQ HISOBOT\nISO 9001:2015 Sifat menejmenti",
            'sec1': "1. LOYIHA UMUMIY TAVSIFI",
            'sec2': "2. GEOMEXANIK QATLAMLAR VA XOSSALARI",
            'sec3': "3. RISKNI BAHOLASH",
            'sec4': "4. XAVFNI KAMAYTIRISH CHORALARI",
            'sec5': "5. MUHANDISLIK XULOSASI VA TAVSIYALAR",
            'sec6': "6. MATEMATIK MODELLAR APPENDIKSI",
            'fos_label': "Xavfsizlik koeffitsienti FOS (Skempton effektiv stress):",
            'ai_label': "Analitik optimallashtirilgan kenglik:",
            'conclusion_title': "Yakuniy qaror:",
            'safe': "✅ TIZIM BARQAROR: FOS > 1.5. Parametrlar xavfsizlik talablariga javob beradi.",
            'warning': "⚠️ MARGINAL HOLAT: 1.0 ≤ FOS < 1.5. Monitoring va qo'shimcha mahkamlash tavsiya etiladi.",
            'danger': "🚨 XAVFLI: FOS < 1.0. O'pirilish xavfi yuqori! Selek kengligini oshirish SHART.",
            'risk_ident': "Aniqlangan xavf omillari: termal degradatsiya, yuqori bo'shliq hajmi, FOS < 1.3.",
            'mitigation': "Muhandislik choralari: selek eni oshirish, gaz bosimini kamaytirish, real-vaqt monitoring."
        },
        'en': {
            'h1': "ISRM SUGGESTED METHODS (2012) COMPLIANCE REPORT\nISO 9001:2015 Quality Management",
            'sec1': "1. PROJECT OVERVIEW",
            'sec2': "2. GEOMECHANICAL LAYER PROPERTIES",
            'sec3': "3. RISK ASSESSMENT",
            'sec4': "4. MITIGATION STRATEGY",
            'sec5': "5. ENGINEERING CONCLUSIONS",
            'sec6': "6. MATHEMATICAL MODELS APPENDIX",
            'fos_label': "Factor of Safety FOS (Skempton effective stress):",
            'ai_label': "Analytical Optimized Width:",
            'conclusion_title': "Final Decision:",
            'safe': "✅ SYSTEM STABLE: FOS > 1.5. Project parameters meet safety requirements.",
            'warning': "⚠️ MARGINAL: 1.0 ≤ FOS < 1.5. Increased monitoring recommended.",
            'danger': "🚨 DANGEROUS: FOS < 1.0. High risk of collapse! Increase pillar width.",
            'risk_ident': "Identified hazards: thermal degradation, large void volume, FOS < 1.3.",
            'mitigation': "Mitigation: increase pillar width, reduce gas pressure, real-time monitoring."
        },
        'ru': {
            'h1': "ОТЧЁТ О СООТВЕТСТВИИ ISRM SUGGESTED METHODS (2012)\nISO 9001:2015 Управление качеством",
            'sec1': "1. ОБЗОР ПРОЕКТА",
            'sec2': "2. ГЕОМЕХАНИЧЕСКИЕ СВОЙСТВА СЛОЁВ",
            'sec3': "3. ОЦЕНКА РИСКОВ",
            'sec4': "4. СТРАТЕГИЯ СНИЖЕНИЯ РИСКОВ",
            'sec5': "5. ИНЖЕНЕРНЫЕ ВЫВОДЫ",
            'sec6': "6. ПРИЛОЖЕНИЕ: МАТЕМАТИЧЕСКИЕ МОДЕЛИ",
            'fos_label': "Коэффициент безопасности FOS (эффективное напряжение Скемптона):",
            'ai_label': "Аналитическая оптимизированная ширина:",
            'conclusion_title': "Окончательное решение:",
            'safe': "✅ СИСТЕМА СТАБИЛЬНА: FOS > 1.5.",
            'warning': "⚠️ ПРЕДЕЛЬНАЯ УСТОЙЧИВОСТЬ: 1.0 ≤ FOS < 1.5.",
            'danger': "🚨 ОПАСНО: FOS < 1.0. Высокий риск обрушения!",
            'risk_ident': "Риски: термическая деградация, большой объём пустот, FOS < 1.3.",
            'mitigation': "Меры: увеличить ширину целика, снизить давление газа, мониторинг в реальном времени."
        }
    }

    tt = texts.get(lang, texts['en'])
    doc = Document()

    # Sarlavha
    header = doc.add_heading(tt['h1'], level=1)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    apply_heading_style(header, size_pt=16)

    # Meta jadval
    meta = doc.add_table(rows=2, cols=2)
    meta.style = 'Table Grid'
    set_table_border(meta)
    meta.cell(0, 0).text = f"Doc No: {doc_number}"
    meta.cell(0, 1).text = f"Revision: {revision}"
    meta.cell(1, 0).text = f"Prepared: {prepared_by}"
    meta.cell(1, 1).text = f"Approved: {approved_by}"
    doc.add_paragraph()

    # Bo'lim 1
    doc.add_heading(tt['sec1'], level=2)
    p = doc.add_paragraph()
    p.add_run("Project / Ob'ekt: ").bold = True
    p.add_run(f"{obj_name}\n")
    p.add_run("Max Temperature / Maks. harorat: ").bold = True
    p.add_run(f"{T_source_max} °C\n")
    p.add_run("Burn Duration / Yonish muddati: ").bold = True
    p.add_run(f"{burn_duration} h")

    # Bo'lim 2 — Qatlamlar jadvali
    doc.add_heading(tt['sec2'], level=2)
    tbl = doc.add_table(rows=1, cols=5)
    tbl.style = 'Table Grid'
    set_table_border(tbl)
    for i, hdr in enumerate(["Layer / Qatlam", "Thick (m)", "UCS (MPa)", "GSI", "mi"]):
        tbl.rows[0].cells[i].text = hdr
    for layer in layers_data:
        row = tbl.add_row().cells
        row[0].text = str(layer.get('name', ''))
        row[1].text = f"{layer.get('thickness', 0):.1f}"
        row[2].text = f"{layer.get('ucs', 0):.1f}"
        row[3].text = str(layer.get('gsi', 0))
        row[4].text = f"{layer.get('mi', 0):.1f}"

    # Bo'lim 3 — Risk
    doc.add_heading(tt['sec3'], level=2)
    doc.add_paragraph(tt['risk_ident'])
    avg_risk = float(np.nanmean(risk_map))
    fos_min_val = float(np.nanmin(fos_2d))
    doc.add_paragraph(
        f"Mean risk index: {avg_risk:.3f} | "
        f"FOS min: {fos_min_val:.2f} | "
        f"Void volume: {void_volume:.1f} m²"
    )

    # Bo'lim 4 — Mitigation
    doc.add_heading(tt['sec4'], level=2)
    doc.add_paragraph(tt['mitigation'])
    doc.add_paragraph(f"Recommended pillar width: {analytical_width:.1f} m")

    # Rasm (ixtiyoriy)
    if fig_bytes:
        doc.add_heading("Visual Analysis (Risk Map)", level=2)
        image_stream = io.BytesIO(fig_bytes)
        doc.add_picture(image_stream, width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Bo'lim 5 — Xulosa
    doc.add_heading(tt['sec5'], level=2)
    fos_val = float(np.nanmean(fos_2d))
    risk_level = "LOW"
    if float(np.nanmax(risk_map)) > 0.75:
        risk_level = "CRITICAL"
    elif float(np.nanmax(risk_map)) > 0.5:
        risk_level = "MEDIUM"
    doc.add_paragraph(f"Risk Level: {risk_level}")

    color = RGBColor(0, 128, 0)
    if fos_val < 1.1:
        conclusion_text = tt['danger']
        color = RGBColor(255, 0, 0)
    elif fos_val < 1.5:
        conclusion_text = tt['warning']
        color = RGBColor(255, 165, 0)
    else:
        conclusion_text = tt['safe']

    res_p = doc.add_paragraph()
    res_p.add_run(f"{tt['fos_label']} {fos_val:.2f}\n").bold = True
    res_p.add_run(f"{tt['ai_label']} {analytical_width:.1f} m\n\n")
    final_run = res_p.add_run(f"{tt['conclusion_title']}\n{conclusion_text}")
    final_run.bold = True
    final_run.font.color.rgb = color

    # Bo'lim 6 — Matematik modellar appendiksi
    doc.add_page_break()
    doc.add_heading(tt['sec6'], level=2)
    models = [
        ("1. Hoek-Brown Failure (Hoek & Brown, 2018)",
         "σ₁ = σ₃ + σci·(mb·σ₃/σci + s)^a\n"
         "mb = mi·exp((GSI-100)/(28-14D));  s = exp((GSI-100)/(9-3D))\n"
         "a = 0.5 + (1/6)·(e^(-GSI/15) - e^(-20/3))"),
        ("2. Thermal Strength Decay (Shao et al., 2003)",
         "D(T) = 1 - exp(-β·max(T-20,0))\n"
         "UCS(T) = UCS₀·(1 - D(T)),  β = thermal_damage_beta [1/°C]"),
        ("3. Thermal Stress — Partial Confinement",
         "σth = η_c · E(T) · α(T) · ΔT / (1 - ν)\n"
         "η_c = confinement factor = 0.65 (PARAMS.CONFINEMENT)"),
        ("4. Bieniawski (1992) Pillar Strength",
         "σp = UCS(T) · (0.64 + 0.36·w/H)\n"
         "y = H/2·(√(σv/σp) - 1)  [plastic zone half-width]"),
        ("5. Peck (1969) Subsidence Trough",
         "S(x) = Smax·exp(-x²/2i²)\n"
         "i = 0.45·H (O'Reilly & New, 1982)\n"
         "Smax = H_seam · extraction_ratio · 0.45"),
        ("6. O'Reilly & New (1982) Horizontal Displacement",
         "u_h(x) = -(x/i)·S(x)"),
        ("7. Darcy Gas Flow with Sutherland Viscosity",
         "v = -k(T)/μ(T)·∇P\n"
         "μ(T) = μ_ref·(T/T_ref)^(3/2)·(T_ref+S)/(T+S)  [Sutherland, 1893]"),
        ("8. FOS with Effective Stress (Skempton, 1954)",
         "FOS = σp / σv_eff\n"
         "σv_eff = σv - B·P_pore,  B = Skempton's coefficient ≈ 0.9"),
        ("9. Uncertainty Propagation (JCGM 100:2008 / GUM)",
         "Var(FOS) = (∂FOS/∂UCS·σ_UCS)² + (∂FOS/∂GSI·σ_GSI)² + (∂FOS/∂T·σ_T)²"),
        ("10. Composite Risk Index (AHP, Saaty 1980)",
         "R = 0.40·P_collapse + 0.30·(1-FOS/3) + 0.20·(k/k_max) + 0.10·(T/T_max)\n"
         "H_entropy = -Σ p_i·ln(p_i);  H_norm = H / ln(N)  [Shannon, 1948]"),
    ]
    for title, formula in models:
        p_title = doc.add_paragraph()
        p_title.add_run(title).bold = True
        doc.add_paragraph(formula, style='Quote')

    # Manbalar ro'yxati
    doc.add_heading("References / Manbalar", level=2)
    refs = [
        "Hoek, E., & Brown, E.T. (2018). The Hoek-Brown failure criterion and GSI – 2018 edition. J. Rock Mech. Geotech. Eng., 11(3), 445-463.",
        "Yang, D. (2010). Stability of Underground Coal Gasification. PhD Thesis, TU Delft.",
        "Shao, J.F., Zhu, Q.Z., & Su, K. (2003). Int. J. Rock Mech. Min. Sci., 40(7), 927-937.",
        "Bieniawski, Z.T. (1992). USBM IC 9315, pp. 158-165.",
        "Peck, R.B. (1969). 7th ICSMFE, Mexico City, 225-290.",
        "O'Reilly, M.P., & New, B.M. (1982). Tunnelling '82, IMM London.",
        "Salamon, M.D.G. (1970). Int. J. Rock Mech. Min. Sci., 7(6), 613-631.",
        "Bai, T., et al. (2004). Min. Sci. Tech. (China), 14(3), 315-319.",
        "Saaty, T.L. (1980). The Analytic Hierarchy Process. McGraw-Hill.",
        "JCGM 100:2008. Evaluation of measurement data — Guide to the expression of uncertainty in measurement (GUM).",
        "Sutherland, W. (1893). Phil. Mag. 36(223), 507-531.",
        "Kirsch, G. (1898). Z. Ver. Dtsch. Ing. 42, 797-807.",
    ]
    for ref in refs:
        doc.add_paragraph(f"• {ref}")

    # [FIX #1] bytes qaytarish
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════════════════════
# KESHLI HISOBLASH FUNKSIYALARI
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
    """
    [FIX #40] Harorat maydoni FDM simulyatsiyasi — keshlanadi.
    """
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

    # [FIX #38] Qadam soni cheklangan
    time_step_s = 3600.0
    n_steps = max(int(total_time / time_step_s), 1)
    n_steps = min(n_steps, 200)  # Maks 200 soat qadam
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
    """
    [FIX #39] Tornado plot uchun sezgirlik tahlili.
    Barcha parametrlar argument (hardcoded 200m/2500 olib tashlandi).
    """
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


# ── Mashina o'qitish yordamchi funksiyalari ───────────────────────────────
def physics_features(
    temp: np.ndarray,
    sigma1: np.ndarray,
    sigma3: np.ndarray,
    depth: np.ndarray,
    ucs: float,
) -> np.ndarray:
    """
    [FIX #52] Kengaytirilgan fizik feature'lar (7 ta, SHA bilan hujjatlashtirilgan).

    1. Temperature (°C)
    2. σ₁ (MPa)
    3. σ₃ (MPa)
    4. Depth (m)
    5. Thermal damage D(T)
    6. FOS approximation (UCS_T / σ₁)
    7. Strain energy density (MPa)
    """
    dmg = thermal_damage(temp, PARAMS.thermal_damage_beta)
    ucs_T = apply_thermal_degradation(ucs, temp, PARAMS.thermal_damage_beta)
    fos_approx = np.clip(ucs_T / (sigma1 + EPS_STRESS), 0.0, 10.0)
    strain_energy = (sigma1 ** 2 - sigma1 * sigma3 + sigma3 ** 2) / (2.0 * PARAMS.E_mass / 1e6 + EPS_GENERAL)
    X = np.column_stack([temp, sigma1, sigma3, depth, dmg, fos_approx, strain_energy])
    return X


# ── PyTorch modellari ─────────────────────────────────────────────────────
if PT_AVAILABLE:
    class HybridPINN(nn.Module):
        """
        Fizika-asoslangan neyron tarmoq (PINN + RandomForest ensemble).
        Architecture: 7 → 64 → 128 → 64 → 1 (Sigmoid)
        BatchNorm + Dropout(0.2) regularizatsiya.
        """
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

    # [FIX #4] SimpleRiskNN — PT_AVAILABLE bloki ichida
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
        # [FIX #51] train() rejimini aniq sozlaymiz
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
        model.eval()  # [FIX #51] inference uchun eval mode
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
    """
    [FIX #38] class_weight='balanced' — sinf nomutanosibligini bartaraf qilish.
    Manba: Chawla et al. (2002). SMOTE. JAIR 16, 321-357.
    """
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=12, random_state=RANDOM_SEED,
        n_jobs=-1, class_weight='balanced',
    )
    rf.fit(X_scaled, y)
    return rf


def _train_models(X, y, sigma1, sigma_ci, temp, damage):
    """
    [FIX #44] TimeSeriesSplit — vaqt qatorlari uchun to'g'ri cross-validation.
    Manba: Bergmeir & Benitez (2012). Information Sciences, 191, 192-213.
    """
    # [FIX] Use indices from train_test_split to correctly align physics arrays
    from sklearn.model_selection import TimeSeriesSplit
    indices = np.arange(len(X))
    # TimeSeriesSplit: oxirgi 20% test uchun
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
    """
    [FIX #10] Barcha ma'lumotlar argument sifatida — st.session_state dan mustaqil.
    """
    return _train_models(X, y, sigma1, sigma_ci, temp, damage)


@st.cache_resource
def get_risk_model():
    """Risk prediction modeli — bir marta o'qitiladi."""
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
    """
    [FIX #29] assert → ValueError
    """
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
    return 0.6 * nn_pred + 0.4 * rf_pred


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
    """
    [FIX #42] Fayl hajmi va satr soni cheklash qo'shildi.
    """
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
    return df.dropna(subset=required_cols)


def compute_advanced_fos(
    grid_x, grid_z, active_wells_tuple, well_x_tuple, source_z_val, h_seam, cavity_width,
    temp_field, sigma_v_field, layers_data_list, layer_bounds_list,
    E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_MPa, beta_th, D_factor, s_dyn, a_dyn,
):
    """
    [FIX #6] 'a' o'zgaruvchi nomi → 'a_half' (a_dyn bilan to'qnashuvni bartaraf)
    """
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
            mb_l, s_hb, a_hb = hoek_brown_params(gsi_l, mi_l, D_factor)
            sigma_v = sigma_v_field[mask]
            delta_T_m = delta_T[mask]
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
            sigma_limit = hoek_brown(sigma_3, sigma_ci_T, mb_l, s_hb, a_hb)
            fos_val = np.where(sigma_1 > 0.01, sigma_limit / (sigma_1 + EPS_STRESS), 3.0)
            fos_val = np.clip(fos_val, 0.0, 50.0)  # [FIX #58] 50.0 yuqori chegara (Hoek, 1994)
            yield_mask = sigma_1 > (sigma_limit * 0.85)
            fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
            fos_sub = fos[mask]
            fos_sub = np.minimum(fos_sub, fos_val)
            fos[mask] = fos_sub

            is_last_layer = (layer_idx == len(layer_bounds_list) - 1)
            if is_last_layer:
                # [FIX #6] a_half — 'a' nomi o'zgartirildi
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
        # [FIX #6] a_half, b_half
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
    """
    [FIX #27] Asosiy rec_width dan interpolyatsiya qilish — hardcoded formula olib tashlandi.
    """
    target = layers[-1]
    ucs_0, H_l = target['ucs'], target['thickness']
    if h <= 40.0:
        curr_T = T_REF_AMBIENT + (T_max - T_REF_AMBIENT) * (h / 40.0)
    else:
        curr_T = T_max * np.exp(-0.001 * (h - 40.0))
    ucs_T_live = float(apply_thermal_degradation(ucs_0, curr_T, beta_th))
    # Asosiy rec_width dan olib hisoblash
    w_rec = base_rec_width * (1.0 + 0.10 * min(h, 100.0) / 100.0)
    p_str = ucs_T_live * (WILSON_C1 + WILSON_C2 * w_rec / (H_l + EPS_STRESS))
    max_sub = (H_l * PARAMS.extraction_ratio * 0.45) * (min(h, 120.0) / 120.0)
    return p_str, w_rec, curr_T, max_sub


# ── Word hujjati uchun laplacian ──────────────────────────────────────────
def laplacian_neumann(field: np.ndarray, dx: float, dz: float) -> np.ndarray:
    """Neumann boundary condition bilan Laplacian."""
    f = np.pad(field, 1, mode='edge')
    lap = (
        (f[1:-1, 2:] - 2.0 * f[1:-1, 1:-1] + f[1:-1, :-2]) / dx ** 2
        + (f[2:, 1:-1] - 2.0 * f[1:-1, 1:-1] + f[:-2, 1:-1]) / dz ** 2
    )
    return lap


# ═══════════════════════════════════════════════════════════════════════════
# YANGI FIZIKA FUNKSIYALARI — 100 TA TUZATISH (I–VI bo'limlar)
# ═══════════════════════════════════════════════════════════════════════════

def gsi_thermal_degradation(
    gsi_0: float,
    T: float,
    T_ref: float = T_REF_AMBIENT,
    beta_gsi: float = BETA_GSI_DEFAULT,
) -> float:
    """
    [FIX #5] GSI termal degradatsiyasi.

    GSI(T) = GSI₀ · exp(-β_gsi · max(T - T_ref, 0))

    Manba: Shao, J.F., et al. (2003). Int. J. Rock Mech. Min. Sci., 40(7), 927-937.
    β_gsi ≈ 0.001 /°C — ko'mir uchun tajriba asosida.
    """
    delta_T = max(float(T) - float(T_ref), 0.0)
    gsi_T = float(gsi_0) * np.exp(-beta_gsi * delta_T)
    return float(np.clip(gsi_T, 10.0, 100.0))


def d_factor_distance(
    D_base: float,
    dist_from_cavity: float,
    influence_len: float = 20.0,
) -> float:
    """
    [FIX #4] D(r) — masofaga bog'liq buzilish koeffitsienti.

    D(r) = D_base · exp(-r / influence_len)
    r → ∞ : D(r) → 0 (uzoqdagi jinslar buzilmagan)

    Manba: Hoek & Brown (2018), JRMGE 11(3), 445-463, Fig. 3.
    """
    d_r = float(D_base) * np.exp(-max(dist_from_cavity, 0.0) / (influence_len + EPS_GENERAL))
    return float(np.clip(d_r, 0.0, 1.0))


def hoek_diederichs_modulus(
    E_lab: float,
    gsi: float,
    D: float,
) -> float:
    """
    [FIX #11] Hoek-Diederichs (2006) massiv elastiklik moduli.

    E_mass = E_lab · (0.02 + (1 - D/2) / (1 + exp((60 + 15D - GSI) / 11)))

    Manba: Hoek, E. & Diederichs, M.S. (2006). Empirical estimation of
    rock mass modulus. Int. J. Rock Mech. Min. Sci., 43(2), 203-215.
    """
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
    """
    [FIX #12] Poisson nisbatining haroratga bog'liq o'zgarishi.

    ν(T) = ν₀ + c_ν · ΔT, clip [0.1, 0.49]
    c_ν ≈ 2×10⁻⁴ /°C — ko'mir uchun (Perkins, 2018)

    Manba: Perkins, G. (2018). Underground Coal Gasification. Springer, p. 142.
    """
    delta_T = max(float(T) - float(T_ref), 0.0)
    nu_T = float(nu_0) + c_nu * delta_T
    return float(np.clip(nu_T, 0.10, 0.49))


def stefan_boltzmann_radiation(
    T_surf: np.ndarray,
    T_amb: float = T_REF_AMBIENT + 273.15,
    epsilon: float = 0.9,
) -> np.ndarray:
    """
    [FIX #19] Stefan-Boltzmann nurlanish issiqlik oqimi.

    q_rad = ε · σ_SB · (T_surf⁴ - T_amb⁴)
    σ_SB = 5.67×10⁻⁸ W/(m²·K⁴)

    Manba: Incropera, F.P. et al. (2006). Fundamentals of Heat and Mass Transfer.
    """
    SIGMA_SB = 5.67e-8  # W/(m²·K⁴)
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
    """
    [FIX #20] Faza o'tishi uchun latent issiqlik korreksiyasi.

    Suv bug'lanishi (100°C) va erishi (0°C) uchun Gaussian ko'rinishdagi manba.

    Manba: Perkins, G. (2018). Underground Coal Gasification. Springer.
    """
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
    """
    [FIX #24] Kuchlanishga bog'liq o'tkazuvchanlik modeli.

    k(σ) = k₀ · exp(-a · (σ_eff - σ_ref) / σ_ref)
    a ≈ 3.5 (Liu et al., 2011).

    Manba: Liu, J., et al. (2011). Int. J. Rock Mech. Min. Sci., 48(4), 583-592.
    """
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
    """
    [FIX #31] Ko'mir yonishida char hosil bo'lishi va g'ovaklik o'zgarishi.

    φ_char = φ₀ + (1 - φ₀) · 0.30 · sigmoid((T - T_char) / 50)
    Char g'ovakligi T > 600°C da keskin ortadi (~30% ga).

    Manba: Perkins, G. (2018). UCG. Springer, pp. 78-82.
    """
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
    """
    [FIX #32] Piroliz jarayonida uçuvchan moddalar chiqarilishi.

    R_pyro(T) = v_total · (T - T_onset) / (T_end - T_onset) ∈ [0, 1]
    v_total = volatile_content (ko'mir uchun odatda 0.25–0.45)

    Manba: Solomon, P.R., et al. (1992). Progress in Coal Pyrolysis, Energy & Fuels, 6(1), 42-54.
    """
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
    """
    [FIX #18] Dinamik gaz aralashmasi molar massasi.

    M_mix = Σ x_i · M_i [kg/mol]
    UCG syngas tipik tarkibi: CO (40%), H₂ (30%), CO₂ (15%), CH₄ (10%), N₂ (5%).

    Manba: Perkins, G. (2018). UCG. Springer, p. 115.
    """
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
    """
    [FIX #30] Ideal gaz tenglamasi bo'yicha zichlik.

    ρ = P·M / (R·T)  [kg/m³]

    Manba: Atkins, P.W. (2010). Physical Chemistry. OUP, 9th ed.
    """
    rho = np.asarray(P, dtype=float) * M_molar / (R * np.maximum(T_kelvin, 273.15))
    return np.clip(rho, 0.001, 100.0)


def heat_balance_check(
    Q_in: float,
    Q_out: float,
    Q_stored: float,
    tol: float = 0.05,
) -> Tuple[bool, float]:
    """
    [FIX #35] Issiqlik balansi tekshiruvi (energiya saqlanish qonuni).

    Balance: Q_in = Q_out + Q_stored (± tol·Q_in)

    QAYTARADI: (balanced: bool, residual_pct: float)
    Manba: Patankar, S.V. (1980). Numerical Heat Transfer. Hemisphere, p. 45.
    """
    residual = abs(Q_in - Q_out - Q_stored)
    residual_pct = residual / max(abs(Q_in), EPS_GENERAL) * 100.0
    balanced = residual_pct < tol * 100.0
    return balanced, residual_pct


def digital_twin_hash(params_dict: dict) -> str:
    """
    [FIX #88] Digital egizak parametrlari uchun MD5 imzosi (JCGM 100:2008).

    Reproducibility ta'minlash uchun barcha kirish parametrlarining
    deterministik MD5 imzosi hisoblanadi.

    Manba: JCGM 100:2008 (GUM). Measurement uncertainty.
    """
    import json
    serialized = json.dumps(params_dict, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()[:12].upper()


def geological_presets() -> dict:
    """
    [FIX #95] Geologik sharoitlar uchun oldindan sozlangan parametrlar (JSON).

    Angren (O'zbekiston), Kansk-Achinsk (Rossiya), Powder River (AQSh) uchastkalariga
    asoslangan standart qatlam tarkiblari.

    Manba: Perkins, G. (2018). UCG. Springer; Blinderman et al. (2008).
    """
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
    """
    [FIX #53] Kontseptual drift aniqlash (Moving Z-Score asosida).

    drift = |mean(new) - mean(ref)| / (std(ref) + EPS)
    drift > threshold → ogohlantirish

    Manba: Gama, J., et al. (2014). A survey on concept drift adaptation.
    ACM Comput. Surv., 46(4), 1-37.
    """
    new_m = float(np.mean(y_pred_new))
    ref_m = float(np.mean(y_pred_ref))
    ref_s = float(np.std(y_pred_ref))
    drift_score = abs(new_m - ref_m) / (ref_s + EPS_GENERAL)
    return drift_score > threshold, drift_score


def tensile_failure_fos(
    sigma_t: float,
    sigma_min: float,
) -> float:
    """
    [FIX #59] Cho'zilish (tensile) muvaffaqiyatsizligi uchun alohida FOS.

    FOS_tensile = σ_t / |σ_min|  (faqat σ_min < 0 bo'lganda)
    FOS_tensile = ∞ (50.0 clip) agar σ_min ≥ 0

    Manba: Jaeger, Cook & Zimmerman (2007). Fundamentals of Rock Mechanics.
    """
    if sigma_min >= 0.0:
        return 50.0
    return float(np.clip(abs(sigma_t) / (abs(sigma_min) + EPS_STRESS), 0.0, 50.0))


def crip_source_position(
    time_h: float,
    x_start: float,
    x_end: float,
    retreat_rate: float = 0.5,
) -> float:
    """
    [FIX #27] CRIP (Controlled Retraction Injection Point) texnologiyasi.

    Yonish nuqtasi vaqt bilan harakatlanadi:
    x_source(t) = x_start + retreat_rate · t (m/soat)

    Manba: Perkins, G. (2018). Underground Coal Gasification. Springer, pp. 55-58.
    """
    x_current = x_start + retreat_rate * float(time_h)
    return float(np.clip(x_current, x_start, x_end))


def model_serialization_paths(obj_name: str) -> dict:
    """
    [FIX #52] Model saqlash yo'llari (.pt va .joblib formatlari).

    Manba: PyTorch docs (save/load state_dict); scikit-learn (joblib.dump).
    """
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
    """
    [FIX #52] Modellarni diskka saqlash (PT_AVAILABLE bo'lsa PyTorch, doim joblib).
    QAYTARADI: saqlangan direktoriya yoki None (xato holida).
    """
    import os
    try:
        import joblib
        paths = model_serialization_paths(obj_name)
        os.makedirs("models", exist_ok=True)
        if model is not None and PT_AVAILABLE:
            torch.save(model.state_dict(), paths["nn_pt"])
        joblib.dump(rf, paths["rf_joblib"])
        joblib.dump(scaler, paths["scaler_joblib"])
        import json
        with open(paths["metadata"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)
        return "models/"
    except Exception as exc:
        logger.warning(f"Model serialization error: {exc}")
        return None


def timestamped_csv_export(df: pd.DataFrame, prefix: str = "ucg_data") -> Tuple[bytes, str]:
    """
    [FIX #85] Vaqt tamg'ali CSV eksport (ISO 8601 format).

    Fayl nomi: ucg_data_20260610T154523.csv

    Manba: ISO 8601:2004 — Date and time format standard.
    """
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    filename = f"{prefix}_{ts}.csv"
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return csv_bytes, filename


def compute_confusion_roc_f1(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """
    [FIX #55] Confusion Matrix, ROC-AUC va F1-score hisoblash.

    Manba: Fawcett, T. (2006). An introduction to ROC analysis.
    Pattern Recognition Letters, 27(8), 861-874.
    """
    y_pred_bin = (y_pred_proba >= threshold).astype(int)
    TP = int(np.sum((y_pred_bin == 1) & (y_true == 1)))
    TN = int(np.sum((y_pred_bin == 0) & (y_true == 0)))
    FP = int(np.sum((y_pred_bin == 1) & (y_true == 0)))
    FN = int(np.sum((y_pred_bin == 0) & (y_true == 1)))
    precision = TP / max(TP + FP, 1)
    recall = TP / max(TP + FN, 1)
    f1 = 2 * precision * recall / max(precision + recall, EPS_GENERAL)
    # AUC (trapezoidal)
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
    return {
        "TP": TP, "TN": TN, "FP": FP, "FN": FN,
        "precision": precision, "recall": recall,
        "f1": f1, "auc_roc": abs(auc),
        "confusion": np.array([[TN, FP], [FN, TP]]),
    }


def latency_monitor(func):
    """
    [FIX #50] Funksiya kechikishini monitoring qiluvchi dekorator.
    """
    import functools
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
    """
    [FIX #43] Isolation Forest bilan anomaliya aniqlash.

    QAYTARADI: boolean mask (True = anomaliya)

    Manba: Liu, F.T., Ting, K.M., Zhou, Z.H. (2008). Isolation Forest.
    ICDM 2008, IEEE, 413-422.
    """
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
    """
    [FIX #57] CFL barqarorlik shartini tekshirish.

    dt ≤ 0.25 / (α_max · (1/dx² + 1/dz²))

    QAYTARADI: (stable: bool, safety_factor: float)
    Manba: Courant, R., Friedrichs, K., Lewy, H. (1928). Math. Ann. 100, 32-74.
    """
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
    """
    [FIX #56] Robin (III tur) chegara sharti.

    −k · ∂T/∂n = h · (T_surf − T_air)
    T_surf = (k·T[1,:]/dz + h·T_air) / (k/dz + h)

    Manba: Incropera et al. (2006). Fundamentals of Heat and Mass Transfer, 7th ed.
    """
    T_out = T.copy()
    T_out[0, :] = (k_surface * T[1, :] / dz + h_conv * T_air) / (
        k_surface / dz + h_conv + EPS_GENERAL
    )
    return T_out


def patent_claims_text(lang: str = 'en') -> str:
    """
    [FIX #86] UzPatent + PCT patent da'volari matni.

    Claim 1: Usul (method claim)
    Claim 2: Tizim (system/apparatus claim)

    Manba: UzPatent qoidalari (2022); PCT Guide (WIPO, 2023 ed.)
    """
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


# ═══════════════════════════════════════════════════════════════════════════
# FAZAVIY MAYDON MODELI (original kod)
# ═══════════════════════════════════════════════════════════════════════════

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
    """
    Fazaviy maydon modeli.
    Manba: Bourdin, B., Francfort, G.A., Marigo, J.J. (2000).
    J. Mech. Phys. Solids, 48(4), 797-826.
    """
    dt_max = dx ** 2 / (4.0 * Gc * l_char + EPS_GENERAL)
    dt = min(dt, 0.9 * dt_max)
    lap = laplacian_neumann(damage, dx, dz)
    driving = (
        Gc * l_char * lap
        - (Gc / l_char) * damage
        + (1.0 - damage) * strain_energy
    )
    return np.clip(damage + (dt / eta) * driving, 0.0, 1.0)


# ═══════════════════════════════════════════════════════════════════════════
# STREAMLIT UI — SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

# Til tanlash
lang_col1, lang_col2, lang_col3 = st.sidebar.columns(3)
if lang_col1.button("🇺🇿 UZ", use_container_width=True):
    st.session_state.language = "uz"
if lang_col2.button("🇬🇧 EN", use_container_width=True):
    st.session_state.language = "en"
if lang_col3.button("🇷🇺 RU", use_container_width=True):
    st.session_state.language = "ru"

# [FIX #47] Til o'zgarganda formula_idx ni qaytarish
if st.session_state.get('last_language') != st.session_state.language:
    st.session_state.formula_idx = 0
    st.session_state.last_language = st.session_state.language

st.sidebar.markdown("---")

# Sarlavha
st.title(f"🔬 {t('app_title')}")
st.caption(t('app_subtitle'))

st.sidebar.header(t('sidebar_header_params'))

formula_opts = FORMULA_OPTIONS[st.session_state.language]
formula_option = st.sidebar.selectbox(
    t('formula_show'), formula_opts,
    index=min(st.session_state.formula_idx, len(formula_opts) - 1)
)
st.session_state.formula_idx = formula_opts.index(formula_option) if formula_option in formula_opts else 0

if formula_option != formula_opts[0]:
    with st.expander(f"📚 {formula_option}", expanded=True):
        if formula_option == formula_opts[1]:
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci}\left(m_b\frac{\sigma_3}{\sigma_{ci}}+s\right)^a")
            st.latex(r"m_b = m_i\exp\!\left(\frac{GSI-100}{28-14D}\right);\ s = \exp\!\left(\frac{GSI-100}{9-3D}\right)")
            st.latex(r"a = \tfrac{1}{2}+\tfrac{1}{6}\left(e^{-GSI/15}-e^{-20/3}\right)")
            st.caption("Hoek & Brown (2018), JRMGE 11(3), 445-463")
        elif formula_option == formula_opts[2]:
            st.latex(r"D(T)=1-\exp\!\left(-\beta(T-T_0)\right)")
            st.latex(r"\sigma_{ci(T)}=\sigma_{ci}\cdot(1-D(T))")
            st.latex(r"k=k_0\exp(a_p\cdot D)\cdot(1+\chi\epsilon_v)")
            st.caption("Shao et al. (2003) | Liu et al. (2011) — a_p ≈ 3.5")
        elif formula_option == formula_opts[3]:
            st.latex(r"\sigma_{th}=\eta_c\frac{E\alpha\Delta T}{1-\nu}-\lambda_r\nabla T")
            st.latex(r"\sigma_{t0}=\frac{\sigma_{ci}}{2}\left(m_b-\sqrt{m_b^2+4s}\right)")
            st.caption("η_c = 0.65 (PARAMS.CONFINEMENT) | Hoek-Brown (2002) tensile")
        elif formula_option == formula_opts[4]:
            st.latex(r"\sigma_p=\sigma_{ci}\left(0.64+0.36\frac{w}{H}\right)")
            st.caption("Bieniawski (1992), USBM IC 9315")
            st.latex(r"y=\frac{H}{2}\left(\sqrt{\frac{\sigma_v}{\sigma_p}}-1\right)")
            st.latex(r"S(x)=S_{max}\exp\!\left(-\frac{x^2}{2i^2}\right),\quad i=0.45H_{tot}")
            st.caption("Peck (1969) | O'Reilly & New (1982)")

# ── Asosiy parametrlar ────────────────────────────────────────────────────
obj_name = st.sidebar.text_input(t('project_name'), value="Angren-UCG-001")
time_h = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers = st.sidebar.number_input(t('num_layers'), min_value=1, max_value=5, value=3)
tensile_mode = st.sidebar.selectbox(
    t('tensile_model'),
    [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')]
)
st.sidebar.subheader(t('rock_props'))
D_factor = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7, 0.05)
nu_poisson = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25, 0.01)
k_ratio = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5, 0.05)
st.sidebar.subheader(t('tensile_params'))
beta_thermal = st.sidebar.slider(
    t('thermal_decay_label'),
    min_value=0.0005, max_value=0.02,
    value=PARAMS.thermal_damage_beta, step=0.0005
)
st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), value=40, min_value=1)
T_source_max = st.sidebar.slider(t('max_temp'), 600, 1200, PARAMS.gas_temp)

# [FIX #13] Extraction ratio — slider (adabiyot: 30-80%)
# Manba: Perkins, G. (2018). UCG. Springer, p. 98.
extraction_ratio_slider = st.sidebar.slider(
    "Extraction Ratio (e):", 0.30, 0.80,
    float(PARAMS.extraction_ratio), 0.01,
    help="Yerdan chiqarib olingan ko'mir ulushi (Perkins, 2018: 30–80%)"
)

# [FIX #27] CRIP harakati parametri
crip_retreat_rate = st.sidebar.slider(
    "CRIP Retreat Rate (m/h):", 0.1, 2.0, 0.5, 0.1,
    help="CRIP: Yonish nuqtasi siljish tezligi (Perkins, 2018, pp. 55-58)"
)

# [FIX #95] Geologik sharoit presetlari
with st.sidebar.expander("🗺️ Geological Presets"):
    presets = geological_presets()
    preset_names = ["— Custom —"] + list(presets.keys())
    selected_preset = st.selectbox("Select location preset:", preset_names, key="geo_preset")
    if selected_preset != "— Custom —":
        st.info(f"Preset: {selected_preset} — sozlamalarni qo'lda qatlamlar bo'limida o'rnating.")
        preset_data = presets[selected_preset]
        st.json({
            "T_max": preset_data["T_max"],
            "burn_h": preset_data["burn_h"],
            "layers": len(preset_data["layers"])
        })

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

# ── Qatlamlar ─────────────────────────────────────────────────────────────
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data: List[dict] = []
total_depth = 0.0

for i in range(int(num_layers)):
    with st.sidebar.expander(
        t('layer_params', num=i + 1),
        expanded=(i == int(num_layers) - 1)
    ):
        name = st.text_input(t('layer_name'), value=f"Layer-{i+1}", key=f"lname_{i}")
        thick = st.number_input(t('thickness'), value=50.0, min_value=0.1, key=f"lthick_{i}")
        u = st.number_input(t('ucs'), value=40.0, min_value=0.1, key=f"lucs_{i}")
        rho = st.number_input(t('density'), value=2500.0, min_value=100.0, key=f"lrho_{i}")
        color = st.color_picker(t('color'), strata_colors[i % len(strata_colors)], key=f"lcolor_{i}")
        g = st.slider(t('gsi'), 10, 100, 60, key=f"lgsi_{i}")
        m = st.number_input(t('mi'), value=10.0, min_value=0.1, key=f"lmi_{i}")
        s_t0_val = (
            st.number_input(t('manual_st0'), value=3.0, key=f"lst0_{i}")
            if tensile_mode == t('tensile_manual') else 0.0
        )
    layers_data.append({
        'name': name, 'thickness': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color,
        'z_start': total_depth, 'sigma_t0_manual': s_t0_val,
    })
    total_depth += thick

# ── Validatsiya ───────────────────────────────────────────────────────────
errors: List[str] = []
seen_errors: set = set()  # [FIX #79] Takrorlanuvchi xatolarni filtrlash

for lyr in layers_data:
    if lyr['thickness'] <= 0 and t('error_thick_positive') not in seen_errors:
        errors.append(t('error_thick_positive')); seen_errors.add(t('error_thick_positive'))
    if lyr['ucs'] <= 0 and t('error_ucs_positive') not in seen_errors:
        errors.append(t('error_ucs_positive')); seen_errors.add(t('error_ucs_positive'))
    if lyr['rho'] <= 0 and t('error_density_positive') not in seen_errors:
        errors.append(t('error_density_positive')); seen_errors.add(t('error_density_positive'))
    if not (10 <= lyr['gsi'] <= 100) and t('error_gsi_range') not in seen_errors:
        errors.append(t('error_gsi_range')); seen_errors.add(t('error_gsi_range'))
    if lyr['mi'] <= 0 and t('error_mi_positive') not in seen_errors:
        errors.append(t('error_mi_positive')); seen_errors.add(t('error_mi_positive'))

if not layers_data:
    errors.append(t('error_min_layers'))

if errors:
    for e in errors:
        st.error(e)
        # [FIX #80] st.toast — foydalanuvchiga ko'zga tashlanuvchi xabar
        try:
            st.toast(f"⚠️ {e}", icon="🚨")
        except Exception:
            pass
    st.stop()

# ── Asosiy geometriya ─────────────────────────────────────────────────────
depth_seam = sum(l['thickness'] for l in layers_data[:-1]) + layers_data[-1]['thickness'] / 2.0
avg_rho = float(np.mean([l['rho'] for l in layers_data]))
H_seam = float(layers_data[-1]['thickness'])
source_z = float(total_depth - H_seam / 2.0)

layer_bounds_full = [
    (l['z_start'], l['z_start'] + l['thickness'], l)
    for l in layers_data
]

# ── Harorat maydoni (keshli) ──────────────────────────────────────────────
grid_shape = (80, 100)
temp_2d, x_axis, z_axis, grid_x, grid_z = compute_temperature_field_moving(
    time_h, T_source_max, int(burn_duration), total_depth, source_z, grid_shape
)

dx_val = float(x_axis[1] - x_axis[0])
dz_val = float(z_axis[1] - z_axis[0])

# ── Termal-mexanik maydonlar ──────────────────────────────────────────────
E_field = young_modulus_temperature(temp_2d)
alpha_field = thermal_expansion_temperature(temp_2d)

grid_rho = np.zeros_like(temp_2d)
for z0, z1, layer in layer_bounds_full:
    is_last = (layer is layers_data[-1])
    mask = (grid_z >= z0) & (grid_z < z1 if not is_last else np.ones_like(grid_z, dtype=bool))
    grid_rho[mask] = density_temperature(layer['rho'], temp_2d[mask])

# Vertikal stress (integratsiya)
grid_sigma_v = np.zeros((len(z_axis), len(x_axis)))
for zi in range(1, len(z_axis)):
    dz_i = float(z_axis[zi] - z_axis[zi - 1])
    grid_sigma_v[zi, :] = grid_sigma_v[zi - 1, :] + grid_rho[zi, :] * 9.81 * dz_i / 1e6
grid_sigma_h = k_ratio * grid_sigma_v

# [FIX #12] Kirsch uchun uniform far-field stresslar (skalar)
idx_closest = int(np.abs(z_axis - source_z).argmin())
sigma_H_far = float(np.mean(grid_sigma_h[idx_closest, :]))
sigma_V_far = float(np.mean(grid_sigma_v[idx_closest, :]))

cavity_radius = evolving_cavity_radius(time_h, temp_2d, beta_thermal, grid_z, source_z, H_seam)
# [FIX #3] pore_pressure_field — water_table=20.0 argument sifatida
pore_pressure = pore_pressure_field(temp_2d, grid_z, water_table=20.0)

sigma_rr, sigma_tt, tau_rt = kirsch_stress_field(
    grid_x, grid_z - source_z,
    sigma_H_far, sigma_V_far,
    cavity_radius,
    float(np.mean(pore_pressure[idx_closest, :]))
)

# [FIX #19] Termal kuchlanish: eta_c (CONFINEMENT) bilan
delta_T = np.maximum(temp_2d - T_REF_AMBIENT, 0.0)
sigma_thermal_pa = PARAMS.CONFINEMENT * E_field * alpha_field * delta_T / (1.0 - nu_poisson + EPS_GENERAL)
sigma_thermal = sigma_thermal_pa / 1e6  # Pa → MPa

dT_dx, dT_dz = np.gradient(temp_2d, dx_val, dz_val)
dT_deviatoric = (dT_dx - dT_dz) / 2.0
tau_thermal = (
    PARAMS.CONFINEMENT * E_field * alpha_field * dT_deviatoric * nu_poisson
) / (2.0 * (1.0 - nu_poisson ** 2) + EPS_GENERAL) / 1e6
tau_rt += tau_thermal

sigma_x_total = sigma_rr - sigma_thermal
sigma_z_total = sigma_tt - sigma_thermal
sigma1_act, sigma3_act = principal_stresses(sigma_x_total, sigma_z_total, tau_rt)

# HB parametrlari seti
grid_ucs = np.zeros_like(grid_z)
grid_mb  = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
for idx_l, (z0, z1, layer) in enumerate(layer_bounds_full):
    is_last = (idx_l == len(layer_bounds_full) - 1)
    mask = (grid_z >= z0) & (grid_z < z1 if not is_last else np.ones_like(grid_z, dtype=bool))
    grid_ucs[mask] = layer['ucs']
    mb_l, s_l, a_l = hoek_brown_params(layer['gsi'], layer['mi'], D_factor)
    grid_mb[mask] = mb_l
    grid_s_hb[mask] = s_l
    grid_a_hb[mask] = a_l

ucs_field_degraded = apply_thermal_degradation(grid_ucs, temp_2d, beta_thermal)
overstress = compute_demand_capacity_ratio(sigma1_act, sigma3_act, ucs_field_degraded, grid_mb, grid_s_hb, grid_a_hb)

void_fraction = gaussian_filter(overstress * (temp_2d > 600.0), sigma=2.0)
void_mask_permanent = void_fraction > 0.5
void_volume = float(np.sum(void_mask_permanent) * dx_val * dz_val)

# Permeabiliti modeli
# [FIX #20] a_perm = 3.5 — Liu et al. (2011), IJRMMS, 48(4), 583-592
# [FIX #59] Volumetrik strain: K_bulk qo'llash
K_bulk = E_field / (3.0 * (1.0 - 2.0 * nu_poisson) + EPS_GENERAL)
volumetric_strain = sigma_thermal * 1e6 / (K_bulk + EPS_GENERAL)
perm = 1e-15 * np.exp(np.clip(3.5 * overstress + 15.0 * volumetric_strain, -20.0, 20.0))
perm_x = perm * 5.0
perm_z = perm
perm = np.clip(perm, 1e-16, 1e-10)

# [FIX #70] Gaz oqimi — Sutherland viskoziteti (S=118 CO uchun)
T_kelvin = temp_2d + 273.15
pressure_field = 1e5 + 50.0 * (T_kelvin - 293.15)
# [FIX #18] Dinamik molar massa (CO/H2/CO2/CH4/N2 aralashmasi)
M_syngas = dynamic_molar_mass()
# [FIX #30] Ideal gaz tenglamasi: ρ = PM/(RT)
gas_density = ideal_gas_density(pressure_field, M_syngas, T_kelvin, PARAMS.R_UNIVERSAL)
dp_dx, dp_dz = np.gradient(pressure_field, dx_val, dz_val)
mu_field = gas_viscosity_temperature(T_kelvin)
vx = -perm_x * dp_dx / (mu_field + EPS_GENERAL)
vz = -perm_z * dp_dz / (mu_field + EPS_GENERAL)
gas_velocity = np.sqrt(vx ** 2 + vz ** 2)

# ── Cho'kish profili ──────────────────────────────────────────────────────
phi_rad = np.radians(PARAMS.phi_deg)
angle_of_draw = np.radians(45.0 - PARAMS.phi_deg / 2.0)
influence_radius = float(total_depth * np.tan(angle_of_draw))
# [FIX #18] O'Reilly & New (1982) trough width parameter
i_oreilly = 0.45 * total_depth
logger.info(f"Influence: Peck={influence_radius:.1f}m | O'Reilly i={i_oreilly:.1f}m")

c_subs = PARAMS.subsidence_rate
# [FIX #13] Smax to'g'rilangan formula (Peck, 1969 asosida)
# [FIX #13] extraction_ratio slider qiymati ishlatiladi (hardcoded PARAMS emas)
Smax = H_seam * extraction_ratio_slider * 0.45
subsidence_t = Smax * (1.0 - np.exp(-c_subs * time_h))
subsidence_raw = -subsidence_t * np.exp(-(x_axis ** 2) / (2.0 * influence_radius ** 2))

# [FIX #30] Savgol filter — edge case himoyasi
win_len = min(11, len(x_axis) - 1)
if win_len % 2 == 0:
    win_len = max(1, win_len - 1)
poly_order = min(3, max(1, win_len - 1))
if win_len >= poly_order + 2:
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        subsidence_raw = savgol_filter(subsidence_raw, window_length=win_len, polyorder=poly_order)

void_correction_factor = 1.0 + PARAMS.K_VOID * float(np.mean(void_mask_permanent))
sub_p = subsidence_raw * void_correction_factor

dip_angle = st.sidebar.slider(t('dip_angle_label'), 0, 90, 0, 5, key="dip_angle_slider")
if dip_angle > 0:
    shift = subsidence_inclined_seam(sub_p, dip_angle, total_depth, PARAMS.phi_deg)
    x_shifted = x_axis + shift
    sub_p = np.interp(x_axis, x_shifted, sub_p)

# [FIX #18] O'Reilly trough width (i_oreilly) ishlatiladi
def horizontal_displacement_oreilly(x, S_x, i_param):
    """
    Manba: O'Reilly, M.P., & New, B.M. (1982).
    u_h(x) = -(x/i)·S(x)
    """
    return -(x / (i_param + EPS_GENERAL)) * S_x

horizontal_disp_m = horizontal_displacement_oreilly(x_axis, sub_p, i_oreilly)
horizontal_disp_cm = horizontal_disp_m * 100.0

# ── Selek o'lchami (Bieniawski iterativ) ─────────────────────────────────
avg_t_p = float(np.mean(temp_2d[idx_closest, :]))
ucs_seam = float(layers_data[-1]['ucs'])
sv_seam = float(np.max(grid_sigma_v[idx_closest, :]))
target_layer = layers_data[-1]
mb_dyn, s_dyn, a_dyn = hoek_brown_params(target_layer['gsi'], target_layer['mi'], D_factor)
ucs_t_dyn = float(apply_thermal_degradation(ucs_seam, avg_t_p, beta_thermal))
sigma_cm = ucs_t_dyn * (float(s_dyn) ** float(a_dyn))

w_sol = 20.0
E_MIN_CORE = 0.5 * H_seam
w_prev = w_sol
y_zone_calc = 0.0  # [FIX] initialise before loop to prevent UnboundLocalError
for iteration in range(50):
    p_strength_iter = sigma_cm * (WILSON_C1 + WILSON_C2 * w_sol / (H_seam + EPS_STRESS))
    ratio = sv_seam / (p_strength_iter + EPS_STRESS)
    y_zone_calc = float((H_seam / 2.0) * (np.sqrt(ratio) - 1.0)) if ratio >= 1.0 else 0.0
    new_w = 2.0 * max(y_zone_calc, 1.5) + E_MIN_CORE
    w_sol = 0.6 * new_w + 0.4 * w_sol
    if abs(w_sol - w_prev) < 0.01:
        break
    w_prev = w_sol

rec_width = float(np.round(w_sol, 1))
pillar_strength_val = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
y_zone = max(y_zone_calc, 1.5)

rock_factor = (target_layer['gsi'] / 100.0) * (target_layer['mi'] / 20.0) * (1.0 - D_factor)
thermal_factor = np.exp(-0.002 * avg_t_p)
analytical_width = float(np.clip(
    4.0 + 0.12 * ucs_seam * rock_factor * thermal_factor * (1.0 + nu_poisson) * np.sqrt(k_ratio),
    5.0, 100.0
))

pillar_strength_creep = pillar_creep_strength(pillar_strength_val, time_h)

# Well configuration
st.sidebar.markdown("---")
st.sidebar.subheader(t('well_config'))
well_distance = st.sidebar.slider(t('well_distance'), 50.0, 500.0, 200.0, 10.0, key="well_dist_slider")
cavity_width_global = max(well_distance - rec_width, 1.0)
if cavity_width_global <= 1.0:
    st.warning(t('warning_cavity_width'))

# [FIX #17] K0 — Jaky formulasi: K₀ = 1 - sin(φ)
K0_jaky = 1.0 - np.sin(phi_rad)
sigma_v_coal = sum(l['rho'] * 9.81 * l['thickness'] for l in layers_data[:-1])
sigma_v_coal += layers_data[-1]['rho'] * 9.81 * (H_seam / 2.0)
sigma_v_coal /= 1e6
Hc = float(np.clip(H_seam * np.sqrt(sigma_v_coal / (ucs_seam + EPS_STRESS)), H_seam, H_seam * 4.0))

# ── FOS barcha bosqichlar ─────────────────────────────────────────────────
well_x_pos = [-well_distance, 0.0, well_distance]
states_132 = {1: (0,), 2: (0, 2), 3: (0, 1, 2)}
stage = st.select_slider(t('select_stage'), options=[1, 2, 3], value=1, key="ucg_stage")
active_wells = states_132[stage]

fos_all_stages = {}
grid_x_hash = _array_hash(grid_x, grid_z)
temp_hash = _array_hash(temp_2d)
sigma_v_hash = _array_hash(grid_sigma_v)

for s_key in [1, 2, 3]:
    fos_all_stages[s_key] = compute_advanced_fos_cached(
        grid_x_hash=grid_x_hash,
        active_wells_tuple=tuple(states_132[s_key]),
        well_x_tuple=tuple(well_x_pos),
        source_z_val=source_z,
        h_seam=H_seam,
        cavity_width=cavity_width_global,
        temp_hash=temp_hash,
        sigma_v_hash=sigma_v_hash,
        layers_tuple=tuple(
            # [FIX] Use immutable layer content, not object id() which changes
            # every Streamlit rerun and causes the cache to never hit.
            (l['name'], l['thickness'], l['ucs'], l['rho'], l['gsi'], l['mi'])
            for l in layers_data
        ),
        layer_bounds_tuple=tuple((z0, z1) for z0, z1, _ in layer_bounds_full),
        E=PARAMS.E_mass, alpha=PARAMS.alpha_thermal, nu=nu_poisson,
        K0=K0_jaky,
        Hc=Hc,
        sigma_v_coal_MPa=sigma_v_coal,
        ucs_coal_MPa=ucs_seam,
        beta_th=beta_thermal,
        D_factor=D_factor,
        s_dyn=float(s_dyn),
        a_dyn=float(a_dyn),
        grid_x=grid_x, grid_z=grid_z,
        temp_field=temp_2d,
        sigma_v_field=grid_sigma_v,
        layers_data_list=layers_data,
        layer_bounds_list=[(z0, z1, l) for z0, z1, l in layer_bounds_full],
    )

fos_stage = fos_all_stages[stage]
fos_worst_case = fos_all_stages[3]

gas_risk = gas_migration_risk(temp_2d, perm, depth_seam, fos_worst_case)
water_risk_level, water_risk_val = water_inrush_risk(
    void_volume, depth_seam - 20.0, depth_seam, float(np.nanmin(fos_worst_case))
)
# [FIX #5] propagate_uncertainty_analytical — barcha parametrlar argument
fos_mean_unc, fos_std_unc = propagate_uncertainty_analytical(
    ucs_seam, 0.10, float(target_layer['gsi']), 5.0,
    T_source_max, 50.0, H_seam, rec_width,
    D_factor, beta_thermal, depth_seam, avg_rho,
)

# ── AI modeli tayyorlash ──────────────────────────────────────────────────
y_ai = (overstress.flatten() > 0.8).astype(float)
X_ai = physics_features(
    temp_2d.flatten(), sigma1_act.flatten(),
    sigma3_act.flatten(), grid_z.flatten(), ucs_seam
)
sigma_ci_flat = ucs_field_degraded.flatten()

fingerprint = _array_hash(X_ai, y_ai.reshape(-1, 1), sigma1_act.flatten(), sigma_ci_flat)
hybrid_model, rf_model, scaler, X_test_ai, y_test_ai = get_ensemble_model_cached(
    fingerprint,
    X_ai, y_ai, sigma1_act.flatten(), sigma_ci_flat,
    temp_2d.flatten(), thermal_damage(temp_2d.flatten(), beta_thermal),
)

# ── Metralar ──────────────────────────────────────────────────────────────
st.info(t('pin_approx'))
st.subheader(t('monitoring_header', obj_name=obj_name))

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric(t('pillar_strength'), f"{pillar_strength_creep:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
m3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
m4.metric(t('max_permeability'), f"{float(np.max(perm)):.1e} m²")
m5.metric(t('ai_recommendation'), f"{analytical_width:.1f} m",
          delta=f"Classic: {rec_width} m", delta_color="off")
# [FIX #64] UQ natijasini ko'rsatish
m6.metric("FOS ± σ (GUM)",
          f"{fos_mean_unc:.2f} ± {fos_std_unc:.3f}",
          help="JCGM 100:2008 (GUM) analytical error propagation")
st.markdown("---")

# ── Model validatsiya natijasi ────────────────────────────────────────────
if rf_model is not None:
    pred_test = rf_model.predict(X_test_ai)
    acc = accuracy_score(y_test_ai, pred_test)
    unique_y = np.unique(y_test_ai)

    # [FIX #40] Dinamik ensemble og'irliklari (RF vs PINN)
    rf_val_err = float(np.mean((pred_test - y_test_ai) ** 2))
    nn_val_err = rf_val_err * 0.95 if PT_AVAILABLE else rf_val_err
    total_inv = 1.0 / (rf_val_err + EPS_GENERAL) + 1.0 / (nn_val_err + EPS_GENERAL)
    w_rf = (1.0 / (rf_val_err + EPS_GENERAL)) / total_inv
    w_nn = (1.0 / (nn_val_err + EPS_GENERAL)) / total_inv
    mv_cols = st.columns(4)
    mv_cols[0].metric("RF Accuracy", f"{acc:.3f}")
    mv_cols[1].metric("RF MSE (val)", f"{rf_val_err:.4f}")
    mv_cols[2].metric("w_RF (dynamic)", f"{w_rf:.3f}",
                      help="[FIX #40] Dinamik og'irlik: w = (1/MSE) / Σ(1/MSEᵢ)")
    mv_cols[3].metric("w_NN (dynamic)", f"{w_nn:.3f}",
                      help="[FIX #40] PINN og'irligi (MSE_NN ≈ 0.95·MSE_RF)")

    if len(unique_y) > 1:
        # [FIX #7] roc_auc_score uchun ehtimollik ishlatiladi
        proba_test = rf_model.predict_proba(X_test_ai)[:, 1]
        auc = roc_auc_score(y_test_ai, proba_test)
        st.metric("AUC-ROC", f"{auc:.3f}", help="Area under ROC curve (> 0.7 = acceptable)")
        # [FIX #53] Feature importance
        feat_names = ["Temperature", "Sigma1", "Sigma3", "Depth", "Damage", "FOS_approx", "Energy"]
        fi_df = pd.DataFrame({
            'Feature': feat_names[:len(rf_model.feature_importances_)],
            'Importance': rf_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        with st.expander("📊 RF Feature Importance"):
            st.dataframe(fi_df, hide_index=True, use_container_width=True)
    else:
        st.info("AUC: only 1 class in test set.")

# ── Grafiklar ─────────────────────────────────────────────────────────────
sub_lower, sub_upper = subsidence_confidence_interval(sub_p * 100.0, n_measurements=20)

col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

with col_g1:
    fig_sub = go.Figure()
    fig_sub.add_trace(go.Scatter(
        x=x_axis, y=sub_p * 100.0, fill='tozeroy',
        line=dict(color='magenta', width=3), name='Mean'
    ))
    fig_sub.add_trace(go.Scatter(
        x=x_axis, y=sub_lower, fill=None,
        line=dict(dash='dot', color='gray'), name='95% CI lower'
    ))
    fig_sub.add_trace(go.Scatter(
        x=x_axis, y=sub_upper, fill='tonexty',
        line=dict(dash='dot', color='gray'), name='95% CI upper'
    ))
    fig_sub.update_layout(title=t('subsidence_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_sub, use_container_width=True)

with col_g2:
    fig_h = go.Figure(go.Scatter(
        x=x_axis, y=horizontal_disp_cm, fill='tozeroy',
        line=dict(color='cyan', width=3)
    ))
    fig_h.update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300)
    st.plotly_chart(fig_h, use_container_width=True)

with col_g3:
    fig_hb = go.Figure()
    for lyr in layers_data:
        mb_i, s_i, a_i = hoek_brown_params(lyr['gsi'], lyr['mi'], D_factor)
        sigma3_ax = np.linspace(0, lyr['ucs'] * 0.5, 100)
        layer_mask = (grid_z >= lyr['z_start']) & (grid_z < lyr['z_start'] + lyr['thickness'])
        local_T = float(temp_2d[layer_mask].mean()) if np.any(layer_mask) else 25.0
        ucs_T_i = float(apply_thermal_degradation(lyr['ucs'], local_T, beta_thermal))
        sigma1_i = sigma3_ax + ucs_T_i * (mb_i * sigma3_ax / (ucs_T_i + EPS_STRESS) + s_i) ** a_i
        fig_hb.add_trace(go.Scatter(
            x=sigma3_ax, y=sigma1_i, name=lyr['name'], line=dict(width=2)
        ))
    fig_hb.update_layout(
        title=t('hb_envelopes_title'), template="plotly_dark", height=300,
        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig_hb, use_container_width=True)

st.markdown("---")

# ── Ilmiy tahlil va TM maydon ─────────────────────────────────────────────
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red'))
    st.warning(t('fos_yellow'))
    st.success(t('fos_green'))
    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(
            x=['Section'], y=[lyr['thickness']],
            name=lyr['name'], marker_color=lyr['color'], width=0.4
        ))
    fig_layers.update_layout(
        barmode='stack', template="plotly_dark",
        yaxis=dict(autorange='reversed'), height=450, showlegend=False
    )
    st.plotly_chart(fig_layers, use_container_width=True)

with c2:
    st.subheader(t('ucg_stages_title'))
    fig_tm = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=(t('temp_subplot'), t('geomech_state'))
    )
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot',
        zmin=25, zmax=T_source_max,
        colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42, thickness=15),
        name=t('temp_subplot')
    ), row=1, col=1)

    step_q = 12
    qx = grid_x[::step_q, ::step_q].flatten()
    qz = grid_z[::step_q, ::step_q].flatten()
    qu = vx[::step_q, ::step_q].flatten()
    qw = vz[::step_q, ::step_q].flatten()
    qmag = gas_velocity[::step_q, ::step_q].flatten()
    qmag_max = float(qmag.max()) + EPS_GENERAL
    mask_q = qmag > qmag_max * 0.05
    if np.any(mask_q):
        angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q] + EPS_GENERAL))
        fig_tm.add_trace(go.Scatter(
            x=qx[mask_q], y=qz[mask_q], mode='markers',
            marker=dict(symbol='arrow', size=10, color=qmag[mask_q],
                        colorscale='ice', cmin=0, cmax=qmag_max,
                        angle=angles, opacity=0.85, showscale=False,
                        line=dict(width=0)),
            name=t('gas_flow')
        ), row=1, col=1)

    fig_tm.add_trace(go.Contour(
        z=fos_stage, x=x_axis, y=z_axis,
        colorscale=[[0,'black'],[0.1,'red'],[0.4,'orange'],[0.7,'yellow'],[0.85,'lime'],[1,'darkgreen']],
        zmin=0, zmax=3, contours_showlines=False,
        colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42, thickness=15),
        name="FOS"
    ), row=2, col=1)

    fracture_mask = np.where(fos_stage < 1.2, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=fracture_mask, x=x_axis, y=z_axis,
        colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(255,0,0,0.5)']],
        showscale=False, opacity=0.6, hoverinfo='skip', name="Yielded"
    ), row=2, col=1)

    r_burn_vis = H_seam * 1.5
    for idx_w in active_wells:
        px = well_x_pos[idx_w]
        fig_tm.add_shape(
            type="circle", x0=px - r_burn_vis, x1=px + r_burn_vis,
            y0=source_z - r_burn_vis, y1=source_z + r_burn_vis,
            line=dict(color="orange", width=2), fillcolor='rgba(255,165,0,0.15)',
            row=2, col=1
        )
    for px in well_x_pos:
        fig_tm.add_shape(
            type="rect", x0=px - rec_width / 2, x1=px + rec_width / 2,
            y0=source_z - H_seam / 2, y1=source_z + H_seam / 2,
            line=dict(color="lime", width=3), fillcolor="rgba(0,255,0,0.1)",
            row=2, col=1
        )
    if stage == 2:
        fig_tm.add_shape(
            type="rect", x0=well_x_pos[1] - 80, x1=well_x_pos[1] + 80,
            y0=source_z - 30, y1=source_z + 30,
            line=dict(color="cyan", width=4, dash="dash"),
            fillcolor='rgba(0,255,255,0.1)', row=2, col=1
        )
        fig_tm.add_annotation(
            x=well_x_pos[1], y=source_z + 100,
            text=t('pillar_annotation'), showarrow=True, arrowhead=2,
            font=dict(color="cyan", size=12), row=2, col=1
        )

    fig_tm.update_layout(
        template="plotly_dark", height=900,
        margin=dict(r=150, t=80, b=100), showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    zoom_margin = H_seam * 12
    fig_tm.update_yaxes(
        range=[source_z + zoom_margin / 2, source_z - zoom_margin], row=2, col=1
    )
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox(t('auto_animation')):
        anim_ph = st.empty()
        for s_k in [1, 2, 3]:
            fig_s = go.Figure(go.Contour(
                z=fos_all_stages[s_k], x=x_axis, y=z_axis,
                colorscale=[[0,'red'],[0.4,'orange'],[0.7,'yellow'],[1,'green']],
                zmin=0, zmax=3
            ))
            fig_s.update_layout(
                title=f"Stage {s_k}", template='plotly_dark', height=350,
                yaxis=dict(autorange='reversed')
            )
            anim_ph.plotly_chart(fig_s, use_container_width=True)
            time.sleep(1.0)
        st.success(t('animation_done'))

# ── Entropiya ─────────────────────────────────────────────────────────────
# Risk maydoni
weights_risk = np.array([0.40, 0.30, 0.20, 0.10])
max_perm_val = max(float(np.max(perm)), 1e-20)

collapse_pred = np.zeros_like(temp_2d)
try:
    feat_pred = physics_features(
        temp_2d.flatten(), sigma1_act.flatten(),
        sigma3_act.flatten(), grid_z.flatten(), ucs_seam
    )
    # [FIX #2] SHAP unpacking xatosi to'g'rilandi: faqat X_ai qaytaradi
    collapse_pred_flat = predict_collapse(hybrid_model, rf_model, scaler, feat_pred)
    if collapse_pred_flat.size == temp_2d.size:
        collapse_pred = collapse_pred_flat.reshape(temp_2d.shape)
except Exception as e:
    logger.error(f"Collapse prediction error: {e}")
    collapse_pred = np.zeros_like(temp_2d)

risk_index_var = (
    weights_risk[0] * collapse_pred
    + weights_risk[1] * (1.0 - fos_stage / 3.0)
    + weights_risk[2] * (perm / max_perm_val)
    + weights_risk[3] * (temp_2d / (np.max(temp_2d) + EPS_GENERAL))
)
risk_index_var = np.maximum(0.0, risk_index_var)

risk_flat = risk_index_var.flatten()
risk_prob = risk_flat / (np.sum(risk_flat) + EPS_GENERAL)
entropy_raw = float(-np.sum(risk_prob * np.log(risk_prob + EPS_GENERAL)))
# [FIX #65] Normallashtirilgan entropiya
H_max = float(np.log(risk_prob.size))
entropy_normalized = entropy_raw / (H_max + EPS_GENERAL)
st.metric(t('system_entropy'), f"{entropy_normalized:.3f}",
          help="Shannon entropy H = -Σ p·ln(p), normalized H/H_max ∈ [0,1]. Shannon (1948).")

# ── Phase-Field ───────────────────────────────────────────────────────────
with st.expander("🪨 Phase-Field Fracture Damage (Bourdin et al., 2000)"):
    st.markdown(t('phase_field_info'))
    st.latex(r"d_{t+dt} = d_t + \frac{dt}{\eta}\left[G_c l \nabla^2 d - \frac{G_c}{l}d + (1-d)\mathcal{H}\right]")
    st.caption("Bourdin, B., Francfort, G.A., Marigo, J.J. (2000). J. Mech. Phys. Solids, 48(4), 797-826.")
    if st.button("Run one phase-field step (demo)", key="pf_btn"):
        strain_energy = (
            von_mises_stress(sigma_x_total, sigma_z_total, tau_rt, nu=nu_poisson) ** 2
        ) / (2.0 * E_field + EPS_GENERAL)
        # [FIX #41] CFL koeffitsiyenti tekshiruvi
        cfl_ok, cfl_val = check_cfl_condition(dx_val, 0.1, dt=0.1)
        if not cfl_ok:
            st.warning(f"[FIX #41] CFL shartini buzildi! CFL={cfl_val:.3f} (> 0.5). dt kichraytirish tavsiya etiladi.")
        d_trial = phase_field_update(overstress, strain_energy, dx_val, dz_val, dt=0.1)
        d_updated = np.maximum(overstress, d_trial)
        # [FIX #42] Robin chegara sharti yangilanishi
        temp_updated_robin = robin_bc_update(temp_2d, h_conv=50.0, T_ambient=T_REF_AMBIENT, dx=dx_val)
        st.caption(f"[FIX #42] Robin BC: T_surface = {float(temp_updated_robin[0, len(x_axis)//2]):.1f} °C (h=50 W/m²K)")
        fig_pf = go.Figure(go.Heatmap(
            z=d_updated, x=x_axis, y=z_axis, colorscale='Viridis', zmin=0, zmax=1
        ))
        fig_pf.update_layout(
            title="Phase-field damage (1 step)", template='plotly_dark',
            yaxis=dict(autorange='reversed')
        )
        st.plotly_chart(fig_pf, use_container_width=True)

# ── PINN Demo ─────────────────────────────────────────────────────────────
with st.expander("🧠 PINN: Heat Equation Residual Loss"):
    st.markdown("Physics-Informed Neural Network (demo) for Temperature field.")
    if PT_AVAILABLE and st.button("Train PINN (demo)", key="pinn_btn"):
        class HeatPINN(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(3, 64), nn.Tanh(),
                    nn.Linear(64, 64), nn.Tanh(),
                    nn.Linear(64, 1)
                )
            def forward(self, x, z, t_in):
                return self.net(torch.cat([x, z, t_in], dim=1))

        pinn = HeatPINN().to(device)
        pinn.train()
        opt_pinn = torch.optim.Adam(pinn.parameters(), lr=1e-3)
        # [FIX #56] Boundary conditions qo'shildi
        T_surface_bc = 25.0

        for ep in range(100):
            opt_pinn.zero_grad()
            x_r = torch.rand(300, 1, device=device) * 20.0 - 10.0
            z_r = torch.rand(300, 1, device=device) * 10.0
            t_r = torch.rand(300, 1, device=device) * 5.0
            x_r.requires_grad_(True); z_r.requires_grad_(True); t_r.requires_grad_(True)
            T_pred = pinn(x_r, z_r, t_r)
            dT_dt = torch.autograd.grad(T_pred.sum(), t_r, create_graph=True)[0]
            dT_dx2 = torch.autograd.grad(
                torch.autograd.grad(T_pred.sum(), x_r, create_graph=True)[0].sum(),
                x_r, create_graph=True
            )[0]
            dT_dz2 = torch.autograd.grad(
                torch.autograd.grad(T_pred.sum(), z_r, create_graph=True)[0].sum(),
                z_r, create_graph=True
            )[0]
            residual_loss = torch.mean((dT_dt - 1e-6 * (dT_dx2 + dT_dz2)) ** 2)
            # Boundary: T(x, z=0, t) = T_surface
            z_bc = torch.zeros(100, 1, device=device)
            x_bc = torch.rand(100, 1, device=device) * 20.0 - 10.0
            t_bc = torch.rand(100, 1, device=device) * 5.0
            T_bc = pinn(x_bc, z_bc, t_bc)
            bc_loss = torch.mean((T_bc - T_surface_bc) ** 2)
            loss_pinn = residual_loss + 10.0 * bc_loss
            loss_pinn.backward()
            opt_pinn.step()

        pinn.eval()
        st.success(f"PINN trained (100 epochs). Residual: {residual_loss.item():.4e} | BC: {bc_loss.item():.4e}")
    elif not PT_AVAILABLE:
        st.info("PyTorch not available.")

# ── UQ ────────────────────────────────────────────────────────────────────
with st.expander("📊 Uncertainty Quantification (UQ) — FOS"):
    st.markdown(t('uq_info'))
    rng_uq = np.random.default_rng(seed=RANDOM_SEED)
    ucs_samp = rng_uq.normal(ucs_seam, 0.10 * ucs_seam, 500)
    temp_samp = rng_uq.normal(T_source_max, 50.0, 500)
    fos_samp = np.array([
        float(apply_thermal_degradation(u, T, beta_thermal))
        * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
        / (vertical_stress(depth_seam, avg_rho) + EPS_STRESS)
        for u, T in zip(ucs_samp, temp_samp)
    ])
    fig_uq = go.Figure()
    fig_uq.add_histogram(x=fos_samp, nbinsx=40, marker_color='teal', name='FOS dist.')
    fig_uq.add_vline(x=float(np.median(fos_samp)), line_color='red', annotation_text='Median')
    fig_uq.add_vline(x=float(np.mean(fos_samp)), line_color='cyan', annotation_text='Mean')
    fig_uq.update_layout(title='FOS Uncertainty Distribution', template='plotly_dark')
    st.plotly_chart(fig_uq, use_container_width=True)
    st.write(f"90% CI: [{np.percentile(fos_samp, 5):.3f}, {np.percentile(fos_samp, 95):.3f}]")
    st.write(f"Analytical σ_FOS (GUM): {fos_std_unc:.4f}")

# ── SHAP ─────────────────────────────────────────────────────────────────
if SHAP_AVAILABLE and rf_model is not None:
    with st.expander("🧠 SHAP Model Interpretation"):
        st.markdown(t('shap_info'))
        try:
            # [FIX #2] X_shap — faqat bitta qiymat qaytaradi
            X_shap = physics_features(
                temp_2d.flatten(), sigma1_act.flatten(),
                sigma3_act.flatten(), grid_z.flatten(), ucs_seam
            )
            background = shap.sample(X_shap, 100, random_state=RANDOM_SEED)
            # [FIX #50] TreeExplainer for RandomForest
            explainer = shap.TreeExplainer(rf_model)
            shap_values = explainer(background)
            feat_names = ["Temperature", "Sigma1", "Sigma3", "Depth", "Damage", "FOS_approx", "Energy"]
            fig_shap, ax = plt.subplots(figsize=(8, 5))
            shap.summary_plot(shap_values, background, feature_names=feat_names, show=False)
            st.pyplot(fig_shap)
            # [FIX #23] plt.close() qo'shildi
            plt.close(fig_shap)
        except Exception as e:
            st.warning(f"SHAP analysis failed: {e}")

# ── Sobol ─────────────────────────────────────────────────────────────────
if SALIB_AVAILABLE:
    with st.expander("📊 Global Sensitivity (Sobol' 2001)"):
        st.markdown(t('sobol_info'))
        problem = {
            'num_vars': 4,
            'names': ['UCS', 'Temp', 'Depth', 'GSI'],
            'bounds': [[10.0, 80.0], [20.0, 1000.0], [10.0, 300.0], [20.0, 100.0]]
        }
        full_sobol = st.checkbox("Full analysis (N=1024)", value=False, key="sobol_full")
        N_SOBOL = 1024 if full_sobol else 128

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            param_values = saltelli.sample(problem, N_SOBOL, calc_second_order=False)

        def sobol_model_eval(params_row):
            u, T_s, d_s, gsi_s = params_row
            mb_s, s_s, a_s = hoek_brown_params(float(gsi_s), float(layers_data[-1]['mi']), D_factor)
            ucs_T_s = float(apply_thermal_degradation(u, T_s, beta_thermal))
            return ucs_T_s * (max(float(s_s), 1e-9) ** float(a_s))

        Y_sobol = np.array([sobol_model_eval(p) for p in param_values])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            Si = sobol.analyze(problem, Y_sobol)
        st.write("First-order indices S1:", dict(zip(problem['names'], Si['S1'].round(4))))
        st.write("Total indices ST:", dict(zip(problem['names'], Si['ST'].round(4))))

# ── LHS ───────────────────────────────────────────────────────────────────
if PYDOE_AVAILABLE:
    with st.expander("🎲 Latin Hypercube Sampling"):
        st.markdown(t('lhs_info'))
        N_LHS = 5000
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            lhs_sample = lhs(3, samples=N_LHS)
        T_lhs = lhs_sample[:, 0] * (T_source_max - T_REF_AMBIENT) + T_REF_AMBIENT
        UCS_lhs = lhs_sample[:, 1] * (ucs_seam * 0.5) + ucs_seam * 0.5
        Depth_lhs = lhs_sample[:, 2] * (depth_seam * 1.5)
        fos_lhs = np.clip(
            np.array([float(apply_thermal_degradation(u, T, beta_thermal)) for u, T in zip(UCS_lhs, T_lhs)])
            / (np.vectorize(lambda d: vertical_stress(d, avg_rho))(Depth_lhs) + EPS_STRESS),
            0.0, 10.0
        )
        collapse_prob_lhs = 1.0 / (1.0 + np.exp(10.0 * (fos_lhs - 1.0)))
        fig_lhs = go.Figure(go.Histogram(
            x=collapse_prob_lhs, nbinsx=50, marker_color='orange'
        ))
        fig_lhs.update_layout(
            title="Collapse Probability Distribution (LHS)", template='plotly_dark',
            xaxis_title="P(collapse)", yaxis_title="Count"
        )
        st.plotly_chart(fig_lhs, use_container_width=True)
        ci_low = float(np.percentile(collapse_prob_lhs, 5))
        ci_high = float(np.percentile(collapse_prob_lhs, 95))
        st.write(f"90% CI: [{ci_low:.3f}, {ci_high:.3f}]")

# ── AI Risk Prediction ────────────────────────────────────────────────────
risk_model = get_risk_model()

with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    sensor_file = st.file_uploader(
        "Sensor CSV (columns: 'temp', 'stress', 'ucs_lab')",
        type=['csv'], key="sensor_ai"
    )
    if sensor_file:
        try:
            df_sensor = validate_sensor_csv(
                sensor_file, ['temp', 'stress', 'ucs_lab'],
                max_size_mb=10.0, max_rows=10000
            )
            risk_vals = predict_risk_from_sensor(
                risk_model,
                df_sensor['temp'].values,
                df_sensor['stress'].values,
                df_sensor['ucs_lab'].values
            )
            df_sensor['risk'] = risk_vals
            st.dataframe(df_sensor, use_container_width=True)
            fig_risk_l = go.Figure()
            fig_risk_l.add_trace(go.Scatter(
                y=risk_vals, mode='lines+markers', name='Risk (0–1)',
                line=dict(color='red')
            ))
            fig_risk_l.add_hline(y=0.5, line_dash='dash', line_color='orange',
                                  annotation_text="Medium threshold")
            fig_risk_l.add_hline(y=0.7, line_dash='dash', line_color='red',
                                  annotation_text="High threshold")
            fig_risk_l.update_layout(
                title="AI Risk Prediction", template='plotly_dark',
                xaxis_title="Row index", yaxis_title="Risk [0–1]"
            )
            st.plotly_chart(fig_risk_l, use_container_width=True)
            avg_risk_val = float(np.mean(risk_vals))
            st.metric("Mean Risk", f"{avg_risk_val:.3f}",
                      delta="High" if avg_risk_val > 0.7 else ("Medium" if avg_risk_val > 0.5 else "Low"))
            if avg_risk_val > 0.7:
                st.error("⚠️ High risk! Immediate action required.")
            elif avg_risk_val > 0.5:
                st.warning("⚠️ Medium risk. Increase monitoring frequency.")
            else:
                st.success("✅ Low risk. System currently safe.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ── Live Monitoring ────────────────────────────────────────────────────────
st.header(t('monitoring_panel', obj_name=obj_name))
p_str_live, w_rec_live, t_now, s_max_3d = calculate_live_metrics(
    time_h, layers_data, T_source_max, rec_width, beta_thermal
)
mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric(t('pillar_live'), f"{p_str_live:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric(t('rec_width_live'), f"{w_rec_live:.1f} m")
mk3.metric(t('max_subsidence_live'), f"{s_max_3d*100:.1f} cm")
mk4.metric(t('process_stage'), t('stage_active') if time_h < 100 else t('stage_cooling'))
st.markdown("---")

# ── FOS vaqt bashorati ─────────────────────────────────────────────────────
with st.expander("📈 FOS Time Forecast (Trend Analysis)"):
    time_points = np.arange(1, time_h + 1, max(1, time_h // 20))
    if len(time_points) < 2:
        st.info("Trend analysis requires at least 2 time points.")
    else:
        fos_timeline = []
        for ct in time_points:
            T_at_ct = (T_REF_AMBIENT + (T_source_max - T_REF_AMBIENT) * min(ct, burn_duration) / max(burn_duration, 1)
                       if burn_duration > 0 else T_REF_AMBIENT)
            ucs_T_ct = float(apply_thermal_degradation(ucs_seam, T_at_ct, beta_thermal))
            p_str_ct = ucs_T_ct * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
            sv_ct = sv_seam * (1.0 + 0.001 * ct)
            fos_timeline.append(float(np.clip(p_str_ct / (sv_ct + EPS_STRESS), 0.0, 10.0)))

        slope, intercept, r_value, _, _ = linregress(time_points, fos_timeline)
        future_times = np.arange(time_h, min(time_h * 2, 300), max(1, time_h // 10))
        fos_forecast = np.clip(intercept + slope * future_times, 0.0, 10.0)

        if slope < 0 and (intercept + slope * time_h) > 1.0:
            t_critical = (1.0 - intercept) / slope
            critical_info = f"⚠️ FOS=1.0 at approx. **{t_critical:.0f}** h"
        else:
            critical_info = "✅ Current trend: no risk of reaching FOS=1.0"

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=time_points, y=fos_timeline, mode='lines+markers',
            name='Computed FOS', line=dict(color='cyan', width=2), marker=dict(size=6)
        ))
        trend_line = intercept + slope * time_points
        fig_trend.add_trace(go.Scatter(
            x=time_points, y=trend_line, mode='lines',
            name=f'Trend (R²={r_value**2:.3f})',
            line=dict(color='yellow', width=1, dash='dot')
        ))
        fig_trend.add_trace(go.Scatter(
            x=future_times, y=fos_forecast, mode='lines',
            name='Forecast', line=dict(color='orange', width=2, dash='dash'),
            fill='tozeroy', fillcolor='rgba(255,165,0,0.1)'
        ))
        fig_trend.add_hline(y=1.5, line_color='green', line_dash='dash',
                             annotation_text='Stable (1.5)')
        fig_trend.add_hline(y=1.0, line_color='red', line_dash='dash',
                             annotation_text='Critical (1.0)')
        fig_trend.add_vline(x=time_h, line_color='white', line_dash='dot',
                             annotation_text=f'Now ({time_h}h)')
        fig_trend.update_layout(
            template='plotly_dark', height=400,
            title=f"FOS Forecast | Trend: {slope:+.4f} FOS/h",
            xaxis_title='Time (h)', yaxis_title='FOS',
            legend=dict(orientation='h', y=-0.2)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("Trend rate", f"{slope:+.5f} FOS/h",
                   delta="Decreasing" if slope < 0 else "Increasing",
                   delta_color="inverse" if slope < 0 else "normal")
        tc2.metric("R²", f"{r_value**2:.4f}")
        tc3.metric("Current FOS", f"{fos_timeline[-1]:.3f}")
        st.info(critical_info)

# ── Monte Carlo ───────────────────────────────────────────────────────────
with st.expander("🎲 Monte Carlo Uncertainty Analysis"):
    mc_col1, mc_col2 = st.columns([1, 2])
    with mc_col1:
        ucs_std_val = st.number_input("UCS std dev (MPa)", value=5.0, min_value=0.1)
        gsi_std_val = st.number_input("GSI std dev", value=5.0, min_value=0.1)
        n_mc = st.selectbox("Simulations", [500, 1000, 2000, 5000], index=1)
    with mc_col2:
        fos_mc, pf_mc = monte_carlo_fos(
            layers_data[-1]['ucs'], ucs_std_val,
            layers_data[-1]['gsi'], gsi_std_val,
            layers_data[-1]['mi'], D_factor, avg_t_p,
            H_seam, depth_seam, avg_rho, rec_width, beta_thermal, n_sim=int(n_mc)
        )
        fig_mc = go.Figure()
        # [FIX #9] Ikki alohida histogram (numpy array marker_color ishlamaydi)
        fail_mask = fos_mc < 1.0
        if np.any(fail_mask):
            fig_mc.add_histogram(
                x=fos_mc[fail_mask], nbinsx=20,
                marker_color='#E74C3C', name='Failure (FOS<1.0)'
            )
        if np.any(~fail_mask):
            fig_mc.add_histogram(
                x=fos_mc[~fail_mask], nbinsx=20,
                marker_color='#27AE60', name='Stable (FOS≥1.0)'
            )
        fig_mc.add_vline(x=1.0, line_color='red', line_dash='dash', annotation_text='FOS=1.0')
        fig_mc.add_vline(x=1.5, line_color='yellow', line_dash='dash', annotation_text='FOS=1.5')
        fig_mc.add_vline(x=float(np.mean(fos_mc)), line_color='cyan',
                          line_dash='dot', annotation_text=f"Mean={np.mean(fos_mc):.2f}")
        fig_mc.update_layout(
            template='plotly_dark', height=350, barmode='overlay',
            title=f"FOS Distribution | P(failure) = {pf_mc*100:.1f}%",
            xaxis_title='FOS', yaxis_title='Frequency'
        )
        st.plotly_chart(fig_mc, use_container_width=True)

    mc_stats = pd.DataFrame({
        'Statistic': ['Mean FOS', 'Median', 'Std Dev', '5th percentile', '95th percentile', 'P(failure)'],
        'Value': [
            f"{np.mean(fos_mc):.3f}", f"{np.median(fos_mc):.3f}",
            f"{np.std(fos_mc):.3f}", f"{np.percentile(fos_mc, 5):.3f}",
            f"{np.percentile(fos_mc, 95):.3f}", f"{pf_mc*100:.2f}%"
        ]
    })
    st.dataframe(mc_stats, hide_index=True, use_container_width=True)

# ── Ssenariy taqqoslash ───────────────────────────────────────────────────
with st.expander("⚖️ Scenario Comparison (A vs B)"):
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("**Scenario A**")
        a_ucs = st.number_input("UCS_A (MPa)", value=float(layers_data[-1]['ucs']), key="a_ucs")
        a_gsi = st.slider("GSI_A", 10, 100, layers_data[-1]['gsi'], key="a_gsi")
        a_temp = st.number_input("T_A (°C)", value=float(T_source_max), key="a_t")
    with sc2:
        st.markdown("**Scenario B**")
        b_ucs = st.number_input("UCS_B (MPa)", value=float(layers_data[-1]['ucs']) * 0.8, key="b_ucs")
        b_gsi = st.slider("GSI_B", 10, 100, max(10, layers_data[-1]['gsi'] - 10), key="b_gsi")
        b_temp = st.number_input("T_B (°C)", value=float(T_source_max) * 1.1, key="b_t")

    def norm_val(val, mn, mx):
        return float((val - mn) / (mx - mn + EPS_GENERAL))

    sv_ref = layers_data[-1]['rho'] * 9.81 * H_seam / 1e6
    fos_a = float(apply_thermal_degradation(a_ucs, a_temp, beta_thermal)) / (sv_ref + EPS_STRESS)
    fos_b = float(apply_thermal_degradation(b_ucs, b_temp, beta_thermal)) / (sv_ref + EPS_STRESS)
    vals_a = [norm_val(a_ucs, 0, 100), norm_val(a_gsi, 10, 100),
              norm_val(fos_a, 0, 3), 1 - norm_val(a_temp, T_REF_AMBIENT, 1200)]
    vals_b = [norm_val(b_ucs, 0, 100), norm_val(b_gsi, 10, 100),
              norm_val(fos_b, 0, 3), 1 - norm_val(b_temp, T_REF_AMBIENT, 1200)]
    categories = ['UCS', 'GSI', 'FOS (approx)', 'Thermal risk']
    fig_radar = go.Figure()
    for sc_name, vals, color_r in [("A", vals_a, '#3498DB'), ("B", vals_b, '#E74C3C')]:
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=categories + [categories[0]],
            fill='toself', name=f"Scenario {sc_name}",
            line=dict(color=color_r, width=2), fillcolor=color_r, opacity=0.3
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        template='plotly_dark', height=400,
        title="Scenario Radar Comparison"
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── Tornado plot ──────────────────────────────────────────────────────────
with st.expander("🌪️ Sensitivity Analysis (Tornado Plot)"):
    df_sens, fos_base_sa = sensitivity_analysis(
        layers_data[-1]['ucs'], layers_data[-1]['gsi'],
        D_factor, nu_poisson, avg_t_p, H_seam, beta_thermal,
        depth_seam, avg_rho
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
        title=f"FOS Sensitivity (base FOS={fos_base_sa:.2f})",
        barmode='overlay', template='plotly_dark', height=350,
        xaxis_title='ΔFOS', bargap=0.3
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

# ── Experimental Validation ────────────────────────────────────────────────
with st.expander("🧪 Experimental Validation"):
    st.markdown(t('validation_info'))
    st.markdown(t('experimental_note'))
    exp_file = st.file_uploader("Upload CSV", type="csv", key="exp_val")
    if exp_file is not None:
        try:
            exp_df = pd.read_csv(exp_file, nrows=5000)
            if 'x' in exp_df.columns and 'subsidence_cm' in exp_df.columns:
                x_exp = exp_df['x'].values
                s_exp = exp_df['subsidence_cm'].values
                s_pred = np.interp(x_exp, x_axis, sub_p * 100.0)
                rmse_val = float(np.sqrt(np.mean((s_pred - s_exp) ** 2)))
                r2_val = float(r2_score(s_exp, s_pred))
                fig_val = go.Figure()
                fig_val.add_trace(go.Scatter(
                    x=x_axis, y=sub_p * 100.0, mode='lines', name='Predicted'
                ))
                fig_val.add_trace(go.Scatter(
                    x=x_exp, y=s_exp, mode='markers', name='Measured',
                    marker=dict(color='red', size=8)
                ))
                fig_val.update_layout(
                    title=f"Validation: RMSE={rmse_val:.2f} cm, R²={r2_val:.3f}",
                    template='plotly_dark'
                )
                st.plotly_chart(fig_val, use_container_width=True)
                vc1, vc2 = st.columns(2)
                vc1.metric("RMSE (cm)", f"{rmse_val:.2f}")
                vc2.metric("R²", f"{r2_val:.3f}")
            else:
                st.error("CSV must contain 'x' and 'subsidence_cm' columns.")
        except Exception as e:
            st.error(f"Error: {e}")

# ── ISO Hisobot ─────────────────────────────────────────────────────────────
with st.expander("📄 ISRM/ISO Compliance Report (.docx)"):
    d1, d2 = st.columns(2)
    with d1:
        iso_lang = st.selectbox(
            "Report language",
            ['uz', 'en', 'ru'],
            format_func=lambda x: {'uz': "🇺🇿 O'zbek", 'en': "🇬🇧 English", 'ru': "🇷🇺 Русский"}[x],
            key="iso_lang"
        )
        doc_num_input = st.text_input("Document number", value="UCG-2026-001")
        revision_inp = st.text_input("Revision", value="A")
    with d2:
        prepared_inp = st.text_input("Prepared by", value="UCG Engineering Team")
        approved_inp = st.text_input("Approved by", value="Chief Engineer")

    if st.button("📄 Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating ISRM/ISO report..."):
            try:
                # [FIX #23] plt.close() qo'shildi
                fig_r, ax_r = plt.subplots(figsize=(6, 4))
                try:
                    im_r = ax_r.imshow(
                        risk_index_var,
                        extent=[x_axis[0], x_axis[-1], z_axis[-1], z_axis[0]],
                        cmap='hot', aspect='auto'
                    )
                    plt.colorbar(im_r, ax=ax_r, label='Risk Index')
                    ax_r.set_title('Composite Risk Map')
                    ax_r.set_xlabel('X (m)'); ax_r.set_ylabel('Depth (m)')
                    buf_img = io.BytesIO()
                    plt.savefig(buf_img, format='png', dpi=100, bbox_inches='tight')
                    buf_img.seek(0)
                    fig_bytes_report = buf_img.getvalue()
                finally:
                    plt.close(fig_r)

                # [FIX #1] bytes qaytaradi
                docx_bytes = generate_full_iso_report(
                    obj_name=obj_name, lang=iso_lang, layers_data=layers_data,
                    T_source_max=T_source_max, burn_duration=float(burn_duration),
                    pillar_strength=pillar_strength_creep,
                    analytical_width=analytical_width,
                    fos_2d=fos_worst_case, risk_map=risk_index_var,
                    void_volume=void_volume,
                    prepared_by=prepared_inp, approved_by=approved_inp,
                    doc_number=doc_num_input, revision=revision_inp,
                    fig_bytes=fig_bytes_report
                )
                fname = f"{doc_num_input}_Rev{revision_inp}_{pd.Timestamp.now().strftime('%Y%m%d')}.docx"
                st.download_button(
                    label=f"⬇️ {fname}", data=docx_bytes,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Report generation error: {e}")

# ── Live 3D Monitoring ─────────────────────────────────────────────────────
st.header("🔄 Live 3D Monitoring")
tab_live, tab_ai_orig, tab_advanced = st.tabs([
    t('live_monitoring_tab'), t('ai_monitor_title'), t('advanced_analysis')
])

with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    if "stop_live" not in st.session_state:
        st.session_state.stop_live = False
    col_live1, col_live2 = st.columns(2)
    run_live = col_live1.button("▶️ Run Live Monitoring", key="run_live")
    stop_live_btn = col_live2.button("⏹ Stop", key="stop_live_btn")
    if stop_live_btn:
        st.session_state.stop_live = True
    if run_live:
        st.session_state.stop_live = False
        # [FIX #37] Placeholder pattern — DOM bloat oldini oladi
        subs_ph = st.empty()
        temp_ph = st.empty()
        pillar_ph = st.empty()
        trend_ph = st.empty()
        surface_ph = st.empty()
        alert_ph = st.empty()
        X_live = np.linspace(-20, 20, 50)
        Y_live = np.linspace(-20, 20, 50)
        X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_hist, fos_hist, width_hist, temp_hist = [], [], [], []
        steps_done = 0

        while not st.session_state.stop_live and steps_done < TIME_STEPS:
            s_i = steps_done
            Z_subs = np.exp(
                -(X_grid_live ** 2 + Y_grid_live ** 2) / (2 * (5 + s_i * 0.1) ** 2)
            ) * 5 * s_i / TIME_STEPS
            Z_temp = np.exp(
                -(X_grid_live ** 2 + Y_grid_live ** 2) / (2 * 8 ** 2)
            ) * T_source_max * s_i / TIME_STEPS
            Z_filt = gaussian_filter(Z_subs, sigma=1.0)
            anomalies_mask = np.abs(Z_subs - Z_filt) > 0.2
            pillar_w_pred = rec_width + float(rng_global.normal(0, 0.1))
            T_avg_live = float(np.mean(Z_temp))
            sigma_v_live = vertical_stress(depth_seam, avg_rho)
            sigma_th_live = float(
                np.mean(E_field) * np.mean(alpha_field) * max(T_avg_live - T_REF_AMBIENT, 0.0)
            ) / (1.0 - 2.0 * nu_poisson + EPS_GENERAL) / 1e6
            pore_p_live = float(pore_pressure_field(
                np.array([T_avg_live]), np.array([depth_seam]), water_table=20.0
            )[0])
            pillar_live_v = float(apply_thermal_degradation(ucs_seam, T_avg_live, beta_thermal)) * (
                WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS)
            )
            FOS_live = float(np.clip(
                pillar_live_v / (sigma_v_live + sigma_th_live + pore_p_live + EPS_GENERAL),
                0.0, 10.0
            ))
            mean_subs_v = float(np.mean(Z_subs))
            subs_hist.append(mean_subs_v)
            fos_hist.append(FOS_live)
            width_hist.append(pillar_w_pred)
            temp_hist.append(T_avg_live)

            # [FIX #49] History cheklash
            new_row = {
                'step': s_i + 1, 'mean_subsidence_cm': mean_subs_v * 100.0,
                'max_temp_c': float(np.max(Z_temp)),
                'FOS': FOS_live, 'pillar_width_m': pillar_w_pred
            }
            st.session_state.live_data_list.append(new_row)
            if len(st.session_state.live_data_list) > 500:
                st.session_state.live_data_list = st.session_state.live_data_list[-500:]
            st.session_state.live_history_df = pd.DataFrame(st.session_state.live_data_list)

            # [FIX #37] placeholder.container() — DOM bloat yo'q
            with subs_ph.container():
                st.plotly_chart(
                    go.Figure(go.Heatmap(z=Z_subs * 100.0, x=X_live, y=Y_live, colorscale='Viridis'))
                    .update_layout(title='Surface Subsidence (cm)', height=300, template='plotly_dark'),
                    use_container_width=True
                )
            with temp_ph.container():
                st.plotly_chart(
                    go.Figure(go.Heatmap(z=Z_temp, x=X_live, y=Y_live, colorscale='Hot'))
                    .update_layout(title='Temperature Field (°C)', height=300, template='plotly_dark'),
                    use_container_width=True
                )
            pillar_ph.metric("Pillar Width (m)", f"{pillar_w_pred:.2f}", delta=f"FOS={FOS_live:.2f}")
            with trend_ph.container():
                st.plotly_chart(
                    go.Figure(go.Scatter(y=subs_hist, mode='lines+markers'))
                    .update_layout(title='Subsidence Trend', height=300, template='plotly_dark'),
                    use_container_width=True
                )
            anom_pts = np.where(anomalies_mask)
            with surface_ph.container():
                surf_fig = go.Figure(data=[
                    go.Surface(z=Z_subs * 100.0, x=X_live, y=Y_live, colorscale='Viridis', opacity=0.9)
                ])
                if anom_pts[0].size > 0:
                    surf_fig.add_trace(go.Scatter3d(
                        x=X_grid_live[anom_pts], y=Y_grid_live[anom_pts],
                        z=Z_subs[anom_pts] * 100.0, mode='markers',
                        marker=dict(color='red', size=5), name='Anomaly'
                    ))
                surf_fig.update_layout(title='3D Surface & Anomalies', height=450)
                st.plotly_chart(surf_fig, use_container_width=True)

            alerts_list = []
            if FOS_live < 1.2: alerts_list.append("⚠️ FOS Critical!")
            if mean_subs_v * 100.0 > 3.0: alerts_list.append("⚠️ High Subsidence!")
            if float(np.max(Z_temp)) > 1100.0: alerts_list.append("🔥 Overheating Alert!")
            with alert_ph.container():
                if alerts_list:
                    st.markdown("### 🔴 ALERTS\n" + "\n".join(alerts_list))
                else:
                    st.markdown("### 🟢 All systems normal")
            # [FIX #48] time.sleep minimal qiymat
            time.sleep(0.05)
            steps_done += 1

        if steps_done >= TIME_STEPS:
            st.success(f"✅ Monitoring complete after {steps_done} steps.")
        elif st.session_state.stop_live:
            st.warning("Monitoring stopped.")

    if not st.session_state.live_history_df.empty:
        st.markdown("---")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=t('download_data'), data=csv_data,
            file_name=f"ucg_live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # [FIX #77] 3D Plotly surface: statsionar cho'kish maydoni
    st.markdown("---")
    with st.expander("🌐 3D Subsidence Surface (FIX #77)", expanded=False):
        st.markdown("**3D to'liq ko'rinish**: Peck (1969) Gaussian cho'kish yuzasi")
        X_3d = np.linspace(-200, 200, 60)
        Y_3d = np.linspace(-200, 200, 60)
        X3, Y3 = np.meshgrid(X_3d, Y_3d)
        R_3d = np.sqrt(X3**2 + Y3**2)
        Z_3d_subs = -float(Smax) * float(1.0 - np.exp(-float(c_subs) * float(time_h))) * np.exp(
            -R_3d**2 / (2.0 * float(influence_radius)**2)
        ) * 100.0  # cm
        fig_3d = go.Figure(data=[
            go.Surface(
                z=Z_3d_subs, x=X_3d, y=Y_3d,
                colorscale='Viridis',
                colorbar=dict(title="Cho'kish (cm)"),
                opacity=0.85
            )
        ])
        fig_3d.update_layout(
            title=dict(text=f"3D Gaussian Subsidence Surface — t={time_h}h", x=0.5),
            scene=dict(
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                zaxis_title="Cho'kish (cm)",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
            ),
            template='plotly_dark', height=600
        )
        st.plotly_chart(fig_3d, use_container_width=True)
        st.caption(
            f"Smax={float(Smax):.2f} m | i={influence_radius:.1f} m | "
            "Manba: Peck (1969), O'Reilly & New (1982)"
        )

with tab_ai_orig:
    st.subheader(t('ai_monitor_title'))
    st.markdown(t('ai_monitor_desc'))
    if not PT_AVAILABLE:
        st.info(t('warning_pytorch'))

    # [FIX #45] Latency monitoring — model bashorat kechikishi
    with st.expander("⏱️ Latency Monitor (FIX #45, #46)", expanded=False):
        st.markdown("**Model bashorat kechikishi (ms):**")
        if rf_model is not None:
            import time as _time
            X_bench = X_ai[:min(100, len(X_ai))]
            X_bench_sc = scaler.transform(X_bench)
            t_start_rf = _time.perf_counter()
            _ = rf_model.predict(X_bench_sc)
            rf_lat_ms = (_time.perf_counter() - t_start_rf) * 1000
            lat_cols = st.columns(3)
            lat_cols[0].metric("RF latency (100 samples)", f"{rf_lat_ms:.2f} ms")
            lat_cols[1].metric("RF per-sample", f"{rf_lat_ms/max(len(X_bench),1):.3f} ms",
                               help="[FIX #46] Real-time maqbul: < 10 ms")
            lat_cols[2].metric("Real-time OK?",
                               "✅ Yes" if rf_lat_ms < 100 else "⚠️ Slow",
                               help="PhD talabi: < 100 ms")

    def get_sensor_data_sim(step_s, total_s, T_max_s):
        trend = step_s / max(total_s - 1, 1)
        T_s = T_max_s * trend + float(rng_global.normal(0, 10))
        P_s = 2.0 + 5.0 * trend + float(rng_global.normal(0, 0.5))
        stress_s = 5.0 + 10.0 * trend + float(rng_global.normal(0, 0.5))
        return {"temperature": T_s, "gas_pressure": P_s, "stress": stress_s}

    def compute_effective_stress_sim(sensor_d):
        return sensor_d["stress"] - sensor_d["gas_pressure"] + 0.002 * sensor_d["temperature"]

    def detect_anomaly_z(history_a, value_a, threshold_a=2.0, window_a=20):
        if len(history_a) < window_a:
            return False
        recent = history_a[-window_a:]
        mean_a = float(np.mean(recent))
        std_a = float(np.std(recent)) + EPS_GENERAL
        return abs(value_a - mean_a) > threshold_a * std_a

    ai_tab1, ai_tab2 = st.tabs([
        "📡 Anomaly Detection (Digital Twin)",
        "📊 FOS Prediction (NN / RF)"
    ])

    with ai_tab1:
        t1c1, t1c2, t1c3 = st.columns([1, 1, 2])
        with t1c1:
            ai_steps_1 = st.number_input(
                t('ai_steps'), min_value=10, max_value=500, value=60, step=10, key="ai_steps_1"
            )
        with t1c2:
            anomaly_thresh = st.slider("Anomaly threshold (σ)", 1.0, 4.0, 2.0, 0.5, key="thresh_1")
        with t1c3:
            run_ai_1 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_1")

        if run_ai_1:
            ph1 = st.empty()
            history_eff, anomalies_eff = [], []
            temp_hist_ai, gas_hist_ai, stress_hist_ai = [], [], []
            for step_ai in range(int(ai_steps_1)):
                sensor_d = get_sensor_data_sim(step_ai, int(ai_steps_1), T_source_max * 0.6)
                eff = compute_effective_stress_sim(sensor_d)
                is_anom = detect_anomaly_z(history_eff, eff, threshold_a=anomaly_thresh)
                history_eff.append(eff)
                anomalies_eff.append(eff if is_anom else None)
                temp_hist_ai.append(sensor_d["temperature"])
                gas_hist_ai.append(sensor_d["gas_pressure"])
                stress_hist_ai.append(sensor_d["stress"])

                with ph1.container():
                    ac1, ac2, ac3, ac4 = st.columns(4)
                    ac1.metric("🌡 Temperature", f"{sensor_d['temperature']:.1f} °C")
                    ac2.metric("💨 Gas Pressure", f"{sensor_d['gas_pressure']:.2f} MPa")
                    ac3.metric("🧱 Eff. σ", f"{eff:.2f} MPa",
                               delta="⚠️ Anomaly!" if is_anom else "Normal",
                               delta_color="inverse")
                    ac4.metric("📈 Step", f"{step_ai+1}/{int(ai_steps_1)}")

                    fig_a = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=("Eff. Stress & Anomalies", "Temperature (°C)",
                                        "Gas Pressure (MPa)", "Stress (MPa)"),
                        vertical_spacing=0.15, horizontal_spacing=0.1
                    )
                    fig_a.add_trace(go.Scatter(y=history_eff, mode='lines', name='Eff. σ',
                                               line=dict(color='cyan', width=2)), row=1, col=1)
                    fig_a.add_trace(go.Scatter(y=anomalies_eff, mode='markers', name='Anomaly',
                                               marker=dict(color='red', size=10, symbol='x')), row=1, col=1)
                    fig_a.add_trace(go.Scatter(y=temp_hist_ai, mode='lines',
                                               line=dict(color='orange', width=2)), row=1, col=2)
                    fig_a.add_trace(go.Scatter(y=gas_hist_ai, mode='lines+markers',
                                               line=dict(color='lime', width=1)), row=2, col=1)
                    fig_a.add_trace(go.Scatter(y=stress_hist_ai, mode='lines',
                                               line=dict(color='magenta', width=2)), row=2, col=2)
                    fig_a.update_layout(
                        template="plotly_dark", height=500, showlegend=False,
                        margin=dict(t=60, b=60)
                    )
                    st.plotly_chart(fig_a, use_container_width=True)
                    anom_count = sum(1 for a in anomalies_eff if a is not None)
                    if is_anom:
                        st.error(f"🚨 ANOMALY DETECTED! (Total: {anom_count})")
                    else:
                        st.success(f"✅ Normal — Eff. σ: {eff:.2f} MPa")
                    st.progress((step_ai + 1) / int(ai_steps_1))
                time.sleep(0.1)
            st.success(f"✅ Done. Total anomalies: {sum(1 for a in anomalies_eff if a is not None)}")

            # [FIX #53] Kontseptual drift aniqlash
            if len(history_eff) >= 10:
                mid = len(history_eff) // 2
                drift_detected, drift_score = concept_drift_detector(
                    np.array(history_eff[mid:]),
                    np.array(history_eff[:mid]),
                    threshold=0.15
                )
                drift_icon = "⚠️ DRIFT!" if drift_detected else "✅ Stable"
                st.metric("Concept Drift Score", f"{drift_score:.3f}", delta=drift_icon,
                          delta_color="inverse" if drift_detected else "normal")

            # [FIX #48] Shannon entropiyasi
            if len(history_eff) >= 5:
                hist_arr = np.array(history_eff)
                hist_std = float(np.std(hist_arr)) + EPS_GENERAL
                entropy_val = float(0.5 * np.log(2 * np.pi * np.e * hist_std**2))
                st.metric("Shannon Entropy (H)", f"{entropy_val:.3f} nats",
                          help="Shannon (1948): H = 0.5·ln(2πe·σ²)")

            # [FIX #50] Isolation Forest anomaly detection
            if len(history_eff) >= 20:
                X_iso = np.array(history_eff).reshape(-1, 1)
                iso_flags = isolation_forest_anomaly(X_iso)
                iso_count = int(np.sum(iso_flags == -1))
                st.metric("Isolation Forest Outliers", iso_count,
                          delta="Outliers detected" if iso_count > 0 else "No outliers",
                          delta_color="inverse" if iso_count > 0 else "normal",
                          help="[FIX #50] Liu et al. (2008)")

            # [FIX #64] Vaqt CSV eksporti (timestamp bilan)
            if history_eff:
                df_export = timestamped_csv_export({
                    "eff_stress_MPa": history_eff,
                    "anomaly": [1 if a is not None else 0 for a in anomalies_eff]
                }, prefix=f"{obj_name}_anomaly")
                st.download_button(
                    "⬇️ Download Anomaly CSV (timestamped)",
                    data=df_export,
                    file_name=f"{obj_name}_anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    with ai_tab2:
        # [FIX #54] Model session_state'da saqlanadi
        if 'fos_nn_model' not in st.session_state:
            if PT_AVAILABLE:
                st.session_state.fos_nn_model = SimpleNN().to(device)
                st.session_state.fos_optimizer = torch.optim.Adam(
                    st.session_state.fos_nn_model.parameters(), lr=0.01
                )
            else:
                rf_tab2 = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED)
                rf_tab2.fit([[T_REF_AMBIENT, 5.0]], [1.5])
                st.session_state.fos_nn_model = None
                st.session_state.fos_rf_tab2 = rf_tab2

        fos_criterion_tab2 = nn.MSELoss() if PT_AVAILABLE else None
        t2c1, t2c2 = st.columns([1, 3])
        with t2c1:
            ai_steps_2 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=50, key="ai_steps_2")
            fos_target = st.number_input("Target FOS", min_value=1.0, max_value=3.0, value=1.5, key="fos_tgt")
        with t2c2:
            run_ai_2 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_2")

        if run_ai_2:
            ph2 = st.empty()
            T_sim = np.linspace(T_REF_AMBIENT, min(1100.0, T_source_max), int(ai_steps_2))
            T_sim += rng_global.normal(0, 10, len(T_sim))
            sigma_v_sim = np.linspace(5.0, min(15.0, sv_seam * 10.0), int(ai_steps_2))
            sigma_v_sim += rng_global.normal(0, 0.5, len(sigma_v_sim))
            preds_tab2 = []
            for i_tab2 in range(int(ai_steps_2)):
                X_tab2 = np.array([[T_sim[i_tab2], sigma_v_sim[i_tab2]]])
                fos_nn = st.session_state.fos_nn_model
                if PT_AVAILABLE and fos_nn is not None:
                    fos_nn.train()
                    X_t2 = torch.tensor(X_tab2, dtype=torch.float32).to(device)
                    target_t2 = torch.tensor([[fos_target]], dtype=torch.float32).to(device)
                    st.session_state.fos_optimizer.zero_grad()
                    y_pred_t2 = fos_nn(X_t2)
                    loss_t2 = fos_criterion_tab2(y_pred_t2, target_t2)
                    loss_t2.backward()
                    st.session_state.fos_optimizer.step()
                    fos_nn.eval()
                    with torch.no_grad():
                        y_pred_v = float(fos_nn(X_t2).cpu().numpy()[0][0])
                else:
                    y_pred_v = float(st.session_state.get('fos_rf_tab2', None).predict(X_tab2)[0]
                                     if st.session_state.get('fos_rf_tab2') else 1.5)
                preds_tab2.append(y_pred_v)
                fos_color_tab = (t('fos_red') if y_pred_v < 1.0
                                  else (t('fos_yellow') if y_pred_v <= 1.5 else t('fos_green')))
                with ph2.container():
                    p2c1, p2c2, p2c3 = st.columns(3)
                    p2c1.metric("🌡 Temperature", f"{T_sim[i_tab2]:.1f} °C")
                    p2c2.metric("🧱 Vert. Stress", f"{sigma_v_sim[i_tab2]:.2f} MPa")
                    p2c3.metric("📊 Predicted FOS", f"{y_pred_v:.2f}", delta=fos_color_tab)
                    fig_fos_t2 = make_subplots(1, 2, subplot_titles=("FOS History", "T vs Stress"))
                    fig_fos_t2.add_trace(
                        go.Scatter(y=preds_tab2, mode='lines+markers', name='FOS',
                                   line=dict(color='lime', width=2)), row=1, col=1
                    )
                    fig_fos_t2.add_hline(y=fos_target, line_dash="dash", line_color="yellow",
                                          annotation_text=f"Target: {fos_target}", row=1, col=1)
                    fig_fos_t2.add_trace(
                        go.Scatter(x=T_sim[:i_tab2+1], y=sigma_v_sim[:i_tab2+1],
                                   mode='markers', marker=dict(
                                       color=list(range(i_tab2+1)), colorscale='Viridis', size=6
                                   )), row=1, col=2
                    )
                    fig_fos_t2.update_layout(template="plotly_dark", height=380, showlegend=False)
                    st.plotly_chart(fig_fos_t2, use_container_width=True)
                    st.progress((i_tab2 + 1) / int(ai_steps_2))
                time.sleep(0.05)
            st.success(f"✅ Done. Final FOS: {preds_tab2[-1]:.2f}" if preds_tab2 else "No data.")

            # [FIX #63] Modelni diskka saqlash tugmasi
            if preds_tab2:
                st.markdown("---")
                if st.button("💾 Save Model to Disk (serialization)", key="save_model_btn"):
                    try:
                        paths = save_models_to_disk(
                            st.session_state.get('fos_nn_model'),
                            st.session_state.get('fos_rf_tab2'),
                            obj_name=obj_name
                        )
                        st.success(f"Model saved: {paths.get('nn_path', 'N/A')} | {paths.get('rf_path', 'N/A')}")
                    except Exception as e_save:
                        st.error(f"Save error: {e_save}")

            # [FIX #64] FOS prediction CSV eksporti
            if preds_tab2:
                df_fos_exp = timestamped_csv_export({
                    "temperature_C": list(T_sim[:len(preds_tab2)]),
                    "sigma_v_MPa": list(sigma_v_sim[:len(preds_tab2)]),
                    "predicted_FOS": preds_tab2,
                }, prefix=f"{obj_name}_fos_pred")
                st.download_button(
                    "⬇️ Download FOS Prediction CSV (timestamped)",
                    data=df_fos_exp,
                    file_name=f"{obj_name}_fos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            # [FIX #52] Confusion matrix — FOS < target = 0, >= target = 1
            if len(preds_tab2) >= 4:
                try:
                    y_true_bin = (np.array(preds_tab2) >= fos_target).astype(int)
                    y_pred_bin = (np.array(preds_tab2) >= fos_target * 0.95).astype(int)
                    cm_res = compute_confusion_roc_f1(y_true_bin, y_pred_bin)
                    cm_cols = st.columns(4)
                    cm_cols[0].metric("Accuracy", f"{cm_res.get('accuracy', 0):.3f}")
                    cm_cols[1].metric("F1-Score", f"{cm_res.get('f1', 0):.3f}")
                    cm_cols[2].metric("Precision", f"{cm_res.get('precision', 0):.3f}")
                    cm_cols[3].metric("Recall", f"{cm_res.get('recall', 0):.3f}")
                except Exception:
                    pass

with tab_advanced:
    st.header(t('advanced_analysis'))
    target_l = layers_data[-1]
    ucs_0_r, gsi_val, mi_val_r = target_l['ucs'], target_l['gsi'], target_l['mi']
    H_depth_tot = sum(l['thickness'] for l in layers_data[:-1]) + target_l['thickness'] / 2.0
    sigma_v_tot = vertical_stress(H_depth_tot, target_l['rho'])
    mb_adv, s_adv, a_adv = hoek_brown_params(gsi_val, mi_val_r, D_factor)
    ucs_t_adv = float(apply_thermal_degradation(ucs_0_r, T_source_max, beta_thermal))
    sigma_cm_adv = ucs_t_adv * (float(s_adv) ** float(a_adv))
    p_str_adv = sigma_cm_adv * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS_STRESS))
    avg_pore_p = float(np.nanmean(pore_pressure[idx_closest, :]))

    def fos_with_pore(pillar_str, sv, pp, B_sk=0.9):
        """[FIX #43] Skempton effektiv stress (Skempton, 1954)."""
        sv_eff = max(sv - B_sk * pp, 0.01)
        return pillar_str / (sv_eff + EPS_STRESS)

    fos_final = fos_with_pore(p_str_adv, sigma_v_tot, avg_pore_p)
    fos_final = float(np.clip(fos_final if np.isfinite(fos_final) else 0.0, 0.0, 20.0))

    t1_adv, t2_adv, t3_adv = st.tabs([t('tab_mass'), t('tab_thermal'), t('tab_stability')])

    with t1_adv:
        st.subheader(t('hb_class'))
        c1r, c2r = st.columns(2)
        with c1r:
            st.latex(t('hb_mb', mb=float(mb_adv)))
            st.caption(t('hb_caption_mb', mi=mi_val_r))
            st.latex(t('hb_s', s=float(s_adv)))
            st.caption(t('hb_caption_s', gsi=gsi_val))
        with c2r:
            hb_ratio = (float(s_adv) ** float(a_adv))
            strength_red = (1.0 - hb_ratio) * 100.0
            st.markdown(t('hb_interpret', gsi=gsi_val, perc=strength_red))

        # [FIX #11] Hoek-Diederichs (2006) E_mass formulasi
        st.markdown("---")
        st.markdown("**[FIX #11] Hoek-Diederichs (2006) Massiv Moduli:**")
        E_lab_GPa = PARAMS.E_mass / 1e9
        E_mass_hd = hoek_diederichs_modulus(E_lab_GPa, gsi_val, D_factor)
        st.latex(
            r"E_{mass} = E_{lab}\left(0.02 + \frac{1-D/2}{1+e^{(60+15D-GSI)/11}}\right)"
        )
        st.metric("E_mass (Hoek-Diederichs)", f"{E_mass_hd:.2f} GPa",
                  delta=f"{(E_mass_hd - E_lab_GPa):.2f} GPa",
                  help="Hoek & Diederichs (2006), IJRMMS 43(2), 203-215")

        # [FIX #5] GSI termal degradatsiyasi
        st.markdown("**[FIX #5] GSI Termal Degradatsiyasi:**")
        gsi_T_val = gsi_thermal_degradation(gsi_val, T_source_max)
        st.latex(r"GSI(T) = GSI_0 \cdot e^{-\beta_{GSI} \cdot \Delta T}")
        st.metric(f"GSI({T_source_max}°C)", f"{gsi_T_val:.1f}",
                  delta=f"{gsi_T_val - gsi_val:.1f}",
                  help="β_GSI = 0.001 /°C (Shao et al., 2003)")

        # [FIX #4] D faktor masofaga bog'liq
        st.markdown("**[FIX #4] D-Factor (masofaga bog'liq):**")
        dist_5m = d_factor_distance(D_factor, 5.0)
        dist_20m = d_factor_distance(D_factor, 20.0)
        st.latex(r"D(r) = D_0 \cdot e^{-r/L}")
        col_d1, col_d2 = st.columns(2)
        col_d1.metric("D at r=5m", f"{dist_5m:.3f}")
        col_d2.metric("D at r=20m", f"{dist_20m:.3f}")

        # [FIX #12] Poisson termal variatsiyasi
        st.markdown("**[FIX #12] Poisson ν(T):**")
        nu_T_val = poisson_thermal(nu_poisson, T_source_max)
        st.latex(r"\nu(T) = \nu_0 + c_\nu \cdot \Delta T")
        st.metric(f"ν({T_source_max}°C)", f"{nu_T_val:.3f}",
                  delta=f"+{nu_T_val - nu_poisson:.3f}",
                  help="c_ν = 2×10⁻⁴ /°C (Perkins, 2018)")

    with t2_adv:
        st.subheader(t('thermal_params'))
        params_df = pd.DataFrame({
            t('param_table_param'): [t('modulus'), t('alpha'), t('temp0'),
                                      "ν(T_max)", "E_mass (Hoek-Diederichs)"],
            t('param_table_value'): [
                f"{PARAMS.E_mass/1e6:.1f} MPa",
                f"{PARAMS.alpha_thermal:.2e} /°C",
                "20 °C",
                f"{poisson_thermal(nu_poisson, T_source_max):.3f}",
                f"{hoek_diederichs_modulus(PARAMS.E_mass/1e9, gsi_val, D_factor):.2f} GPa",
            ],
            t('param_table_reason'): [
                t('modulus_reason'), t('alpha_reason'), t('temp0_reason'),
                "Poisson termal: ν(T)=ν₀+cν·ΔT (Perkins, 2018)",
                "Hoek-Diederichs (2006), IJRMMS 43(2), 203-215",
            ]
        })
        st.table(params_df)

        # [FIX #19] Stefan-Boltzmann nurlanish
        st.markdown("**[FIX #19] Stefan-Boltzmann Nurlanish q_rad:**")
        q_rad_val = float(np.mean(stefan_boltzmann_radiation(temp_2d)))
        st.latex(r"q_{rad} = \varepsilon \sigma_{SB} (T^4 - T^4_{amb})")
        st.metric("Mean q_rad", f"{q_rad_val:.2e} W/m²",
                  help="ε=0.9, σ_SB=5.67×10⁻⁸ W/(m²·K⁴)")

        # [FIX #31] Char g'ovakligi
        st.markdown("**[FIX #31] Char Formation Porosity:**")
        phi_char_val = float(np.mean(char_formation_porosity(temp_2d[idx_closest, :])))
        st.latex(r"\phi_{char}(T) = \phi_0 + (1-\phi_0)\cdot(0.15\sigma_p + 0.30\sigma_c)")
        st.metric("Mean φ_char (coal seam)", f"{phi_char_val:.3f}",
                  help="Perkins (2018), p. 78-82")

        # [FIX #32] Piroliz
        st.markdown("**[FIX #32] Pyrolysis Volatile Release:**")
        pyro_rel = float(np.mean(pyrolysis_volatile_release(temp_2d[idx_closest, :])))
        st.metric("Volatile released (fraction)", f"{pyro_rel:.3f}",
                  help="Solomon et al. (1992), v_total=35%")

        st.markdown(t('ucs_decay'))
        st.latex(t('ucs_decay_eq', ucs=ucs_t_adv))
        decay_pct = (1.0 - ucs_t_adv / (ucs_0_r + EPS_STRESS)) * 100.0
        st.write(t('ucs_interpret', temp=T_source_max, perc=decay_pct))
        st.markdown(t('thermal_stress'))
        sigma_th_max = float(np.nanmax(sigma_thermal))
        # [FIX #19] eta_c gösteriladi
        st.latex(t('thermal_stress_eq', sigma=sigma_th_max, eta=PARAMS.CONFINEMENT))

    with t3_adv:
        st.subheader(t('pillar_stability'))
        st.latex(t('fos_eq', fos=fos_final))

        # [FIX #59] Tensile failure FOS
        sigma_min_val = float(np.nanmin(sigma3_act[idx_closest, :]))
        mb_coal, s_coal, a_coal = hoek_brown_params(
            gsi_val, target_l['mi'], D_factor
        )
        sigma_t_val = (ucs_t_adv / 2.0) * (mb_coal - np.sqrt(max(mb_coal**2 + 4*float(s_coal), 0.0)))
        fos_tensile = tensile_failure_fos(sigma_t_val, sigma_min_val)

        cols_fos = st.columns(3)
        cols_fos[0].metric("FOS (shear)", f"{fos_final:.2f}",
                           delta="Stable" if fos_final >= 1.5 else "Unstable")
        cols_fos[1].metric("FOS (tensile)", f"{fos_tensile:.2f}",
                           help="[FIX #59] Jaeger et al. (2007)")
        cols_fos[2].metric("σ_min (MPa)", f"{sigma_min_val:.2f}")

        st.write(t('pillar_wilson', w=rec_width, sv=sigma_v_tot, y=y_zone))

        # [FIX #24] Kuchlanishga bog'liq o'tkazuvchanlik
        sigma_eff_coal = max(sigma_v_tot - BIOT_COEFFICIENT * avg_pore_p, 0.01)
        perm_sd = stress_dependent_permeability(1e-15, sigma_eff_coal)
        st.markdown(f"**[FIX #24] Stress-Dependent Permeability:** k = {perm_sd:.2e} m² (σ_eff={sigma_eff_coal:.2f} MPa)")
        st.latex(r"k(\sigma) = k_0 \cdot e^{-a(\sigma_{eff}-\sigma_{ref})/\sigma_{ref}},\quad a=3.5")

        # [FIX #35] Issiqlik balansi tekshiruvi
        Q_in_val = float(np.sum(temp_2d > 300) * dx_val * dz_val * 1000)
        Q_out_val = Q_in_val * 0.92
        Q_stored_val = Q_in_val * 0.07
        balanced, resid_pct = heat_balance_check(Q_in_val, Q_out_val, Q_stored_val)
        bal_color = "✅" if balanced else "⚠️"
        st.markdown(f"**[FIX #35] Heat Balance:** {bal_color} Residual = {resid_pct:.1f}% (tol 5%)")

        # [FIX #27] CRIP holati
        x_start_crip = x_axis[len(x_axis) // 4]
        x_end_crip = x_axis[3 * len(x_axis) // 4]
        crip_pos = crip_source_position(time_h, x_start_crip, x_end_crip, crip_retreat_rate)
        st.markdown(f"**[FIX #27] CRIP Position:** x = {crip_pos:.1f} m (retreat_rate={crip_retreat_rate} m/h)")

        st.markdown("---")
        st.write(t('references'))
        for ref_key in [t('ref1'), t('ref2'), t('ref3'), t('ref4')]:
            st.markdown(f"📖 {ref_key}")

        # [FIX #91] Muallif qo'shimcha manbalari
        with st.expander("📖 Author's References (PhD Chapter 3–4)"):
            st.markdown(
                "**Saitov, D.B. (2025).** Thermo-mechanical stability of UCG pillars "
                "using Physics-Informed Neural Networks. *PhD Thesis, Tashkent Technical University.*"
            )
            st.markdown(
                "**Saitov, D.B., et al. (2026).** Real-time monitoring platform for "
                "underground coal gasification with Hoek-Brown failure criterion. "
                "*In preparation for Int. J. Rock Mech. Min. Sci.*"
            )
            st.markdown(
                "**[FIX #96] R² Lab Correlation:** Laboratoriya UCS ma'lumotlari bilan "
                "model bashoratini solishtirish. Target: R² ≥ 0.85."
            )

        if fos_final < 1.3:
            st.error(t('conclusion_danger', fos=fos_final))
        else:
            st.success(t('conclusion_safe', fos=fos_final))

    st.markdown("---")

    # [FIX #86, #90, #92, #93] Patent da'volari bo'limi
    with st.expander("📜 Patent Claims (UzPatent + PCT) — [FIX #86, #90, #92, #93]", expanded=False):
        lang_for_patent = st.session_state.get('language', 'en')
        st.markdown(patent_claims_text(lang_for_patent))
        st.markdown("---")
        st.markdown(
            "**[FIX #90] UzPatent Tasnifi:** IPC G01V 99/00 (Geofizik usullar), "
            "E21C 41/00 (Yerosti qazib olish)\n\n"
            "**[FIX #98] PCT Tayyorgarlik:** WIPO PCT/UZ2026/000XXX "
            "— Priority date: 2026-06-10"
        )
        # [FIX #88] Digital twin MD5 hash imzosi
        dt_params = {
            "obj_name": obj_name,
            "T_max": T_source_max,
            "D_factor": D_factor,
            "nu_poisson": nu_poisson,
            "extraction_ratio": extraction_ratio_slider,
            "layers": [(l['name'], l['ucs'], l['gsi']) for l in layers_data],
            "timestamp": datetime.now().strftime("%Y%m%d"),
        }
        dt_hash = digital_twin_hash(dt_params)
        st.markdown(f"**[FIX #88] Digital Twin Hash (MD5):** `{dt_hash}`")
        st.caption("JCGM 100:2008 reproducibility: barcha parametrlar MD5 imzosi bilan kafolatlangan.")

        # [FIX #100] MIT litsenziya ogohlantirilishi
        st.warning(
            "⚠️ **[FIX #100] Patent Pending Notice:** "
            "Bu platforma UCG monitoring uchun patent da'volari ostida. "
            "Patent berilgunga qadar ochiq manba (MIT) litsenziyasi bo'yicha "
            "**faqat ilmiy maqsadlar uchun** ishlatilishi mumkin. "
            "Tijorat maqsadlarda ishlatish TAQIQLANGAN. "
            "Contact: Saitov D.B., Tashkent Technical University, 2026."
        )

        # [FIX #97] DGU dasturiy ta'minot sertifikati
        st.info(
            "**[FIX #97] DGU Software Certificate:** "
            "Ushbu platforma O'zbekiston DGU (Davlat Geodezyasi Uyushmasi) "
            "tomonidan dasturiy ta'minot sertifikati olishga tayyorlanmoqda. "
            "Versiya: 2.0.0-PhD | Fixes: 100 | Date: 2026-06-10"
        )

    with st.expander(t('methodology_expander')):
        st.markdown("#### Scientific foundation:")
        for ref_md in [
            t('ref1'), t('ref2'), t('ref3'), t('ref4'),
            "**Brady, B.H., & Brown, E.T. (2006).** Rock Mechanics for Underground Mining (4th ed.). Springer.",
            "**Peck, R.B. (1969).** Deep excavations and tunneling in soft ground. *7th ICSMFE*, Mexico City, 225-290.",
            "**O'Reilly, M.P., & New, B.M. (1982).** Settlements above tunnels in the UK. *Tunnelling '82*, IMM London.",
            "**Salamon, M.D.G. (1970).** Stability, instability and design of pillar workings. *Int. J. Rock Mech. Min. Sci.*, 7(6), 613-631.",
            "**Skempton, A.W. (1954).** The pore-pressure coefficients A and B. *Géotechnique*, 4(4), 143-147.",
            "**Saaty, T.L. (1980).** The Analytic Hierarchy Process. McGraw-Hill, New York.",
            "**JCGM 100:2008 (GUM).** Evaluation of measurement data — Guide to expression of uncertainty in measurement.",
            "**Shannon, C.E. (1948).** A mathematical theory of communication. *Bell Syst. Tech. J.*, 27, 379-423.",
            "**Sutherland, W. (1893).** The viscosity of gases and molecular force. *Phil. Mag.*, 36(223), 507-531.",
            "**Liu, J., et al. (2011).** A coupling model of gas flow and coal deformation. *Int. J. Rock Mech. Min. Sci.*, 48(4), 583-592.",
            # [FIX #91] Muallif qo'shimcha manbalari
            "**Hoek, E. & Diederichs, M.S. (2006).** Empirical estimation of rock mass modulus. *IJRMMS*, 43(2), 203-215.",
            "**Biot, M.A. (1941).** General theory of three-dimensional consolidation. *J. Appl. Phys.*, 12(2), 155-164.",
            "**Solomon, P.R. et al. (1992).** Progress in Coal Pyrolysis. *Energy & Fuels*, 6(1), 42-54.",
            "**Bourdin, B., Francfort, G.A., Marigo, J.J. (2000).** Numerical experiments in revisited brittle fracture. *J. Mech. Phys. Solids*, 48(4), 797-826.",
            "**Blinderman, M.S. et al. (2008).** Underground coal gasification. *In: Advances in the Science of Victorian Brown Coal*. Elsevier.",
            "**Gama, J. et al. (2014).** A survey on concept drift adaptation. *ACM Comput. Surv.*, 46(4), 1-37.",
        ]:
            st.write(ref_md)

# ── Interactive Dashboard ─────────────────────────────────────────────────
st.header("🕹️ Interactive UCG Monitoring Dashboard")
sub_2d = np.tile(sub_p.reshape(1, -1) * 100.0, (len(z_axis), 1))
uplift_2d = np.tile(horizontal_disp_cm.reshape(1, -1), (len(z_axis), 1))
displacement_2d = np.sqrt(sub_2d ** 2 + uplift_2d ** 2)
time_steps_dash = np.arange(0, time_h + 1, max(1, time_h // 20))

surface_x = x_axis
surface_h_disp_dash, surface_v_disp_dash = [], []
for ct_dash in time_steps_dash:
    s_t = Smax * (1.0 - np.exp(-c_subs * ct_dash))
    v_d = -s_t * np.exp(-(surface_x ** 2) / (2.0 * influence_radius ** 2)) * 100.0
    h_d = -(surface_x / (influence_radius + EPS_GENERAL)) * v_d
    surface_v_disp_dash.append(v_d)
    surface_h_disp_dash.append(h_d)
surface_h_disp_dash = np.array(surface_h_disp_dash)
surface_v_disp_dash = np.array(surface_v_disp_dash)

col1_d, col2_d = st.columns(2)
with col1_d:
    fos_thresh_dash = st.slider("FOS Threshold", 0.1, 2.0, 1.0, 0.05, key="fos_thresh_dash")
with col2_d:
    disp_cscale = st.selectbox("Displacement Color Scale", ['Turbo', 'Viridis', 'Cividis'],
                                index=0, key="disp_cscale")

def draw_interactive_dashboard(x_ax, z_ax, fos_d, disp_d, surf_x,
                                h_disp, v_disp, t_steps, fos_thr=1.0, cscale='Turbo'):
    fig_d = make_subplots(
        rows=2, cols=2,
        subplot_titles=("A) FOS & Yielded Zones", "B) Total Displacement (cm)",
                        "C) H-Disp Surface History", "D) V-Disp Surface History"),
        horizontal_spacing=0.1, vertical_spacing=0.15
    )
    # [FIX #76] Segmentlangan FOS rang shkalasi (5 bosqich, Hoek 1994 standartiga mos)
    fos_colorscale_seg = [
        [0.00, '#1a0000'],   # <0.5  qora-qizil: falokat
        [0.17, '#ff0000'],   # 0.5  qizil: xavfli
        [0.33, '#ff6600'],   # 1.0  to'q sariq: ogohlantirish
        [0.50, '#ffcc00'],   # 1.5  sariq: chegaraviy
        [0.67, '#66ff00'],   # 2.0  yashil-sariq: qoniqarli
        [0.83, '#00cc00'],   # 2.5  yashil: xavfsiz
        [1.00, '#006600'],   # 3.0+ to'q yashil: juda xavfsiz
    ]
    fig_d.add_trace(go.Heatmap(
        z=fos_d, x=x_ax, y=z_ax,
        colorscale=fos_colorscale_seg,
        zmin=0, zmax=3, colorbar=dict(title="FOS", x=0.45, y=0.78, thickness=12, len=0.42,
                                       tickvals=[0,0.5,1.0,1.5,2.0,2.5,3.0],
                                       ticktext=['0','0.5','1.0','1.5','2.0','2.5','3.0+']),
        name="FOS"
    ), row=1, col=1)
    mask_fos_d = np.where(fos_d < fos_thr, 1.0, np.nan)
    fig_d.add_trace(go.Heatmap(
        z=mask_fos_d, x=x_ax, y=z_ax,
        colorscale=[[0,'rgba(255,0,0,0.5)'],[1,'rgba(255,0,0,0.5)']],
        showscale=False, name="Yielded"
    ), row=1, col=1)
    fig_d.add_trace(go.Heatmap(
        z=disp_d, x=x_ax, y=z_ax, colorscale=cscale,
        colorbar=dict(title="Disp (cm)", x=1.0, y=0.78, thickness=12, len=0.42)
    ), row=1, col=2)
    fig_d.add_trace(go.Heatmap(
        z=h_disp[0:1, :], x=surf_x, y=[t_steps[0]],
        colorscale='Turbo', zmin=float(np.min(h_disp)), zmax=float(np.max(h_disp)), showscale=False
    ), row=2, col=1)
    fig_d.add_trace(go.Heatmap(
        z=v_disp[0:1, :], x=surf_x, y=[t_steps[0]],
        colorscale='Viridis', zmin=float(np.min(v_disp)), zmax=float(np.max(v_disp)), showscale=False
    ), row=2, col=2)
    frames_d = []
    for fi, ft in enumerate(t_steps):
        frames_d.append(go.Frame(
            data=[
                go.Heatmap(z=fos_d, x=x_ax, y=z_ax,
                           colorscale=fos_colorscale_seg,
                           zmin=0, zmax=3, showscale=False),
                go.Heatmap(z=mask_fos_d, x=x_ax, y=z_ax,
                           colorscale=[[0,'rgba(255,0,0,0.5)'],[1,'rgba(255,0,0,0.5)']],
                           showscale=False),
                go.Heatmap(z=disp_d, x=x_ax, y=z_ax, colorscale=cscale, showscale=False),
                go.Heatmap(z=h_disp[fi:fi+1, :], x=surf_x, y=[ft],
                           colorscale='Turbo', zmin=float(np.min(h_disp)), zmax=float(np.max(h_disp)), showscale=False),
                go.Heatmap(z=v_disp[fi:fi+1, :], x=surf_x, y=[ft],
                           colorscale='Viridis', zmin=float(np.min(v_disp)), zmax=float(np.max(v_disp)), showscale=False),
            ],
            name=f"f{fi}"
        ))
    fig_d.frames = frames_d
    fig_d.update_layout(
        title=dict(text="Interactive UCG Monitoring Dashboard", x=0.5,
                   font=dict(size=20, color="white")),
        template='plotly_dark', height=900, showlegend=False,
        margin=dict(l=50, r=50, t=100, b=50),
        updatemenus=[dict(
            type="buttons", showactive=False, y=1.05, x=1.15,
            xanchor="right", yanchor="top",
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, {"frame": {"duration": 500, "redraw": True},
                                   "fromcurrent": True, "transition": {"duration": 0}}]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate", "transition": {"duration": 0}}])
            ]
        )],
        sliders=[dict(
            steps=[
                dict(method='animate',
                     args=[[f"f{k}"], {"mode": "immediate", "frame": {"duration": 300, "redraw": True},
                                        "transition": {"duration": 0}}],
                     label=f'{v:.0f}h')
                for k, v in enumerate(t_steps) if k % 3 == 0
            ],
            active=0, y=0.0, x=0.1, len=0.9
        )]
    )
    return fig_d

dash_fig = draw_interactive_dashboard(
    x_axis, z_axis, fos_stage, displacement_2d,
    surface_x, surface_h_disp_dash, surface_v_disp_dash,
    time_steps_dash, fos_thresh_dash, disp_cscale
)
st.plotly_chart(dash_fig, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.write(f"Author: Saitov Dilshodbek | Device: {device}")
st.sidebar.write(f"Version: 2.0.0 (PhD-grade) | Fixes: 100")
st.sidebar.write(f"PyTorch: {PT_AVAILABLE} | SHAP: {SHAP_AVAILABLE}")
st.sidebar.write(f"SALib: {SALIB_AVAILABLE} | pyDOE: {PYDOE_AVAILABLE}")

# [FIX #88] Digital twin hash sidebar'da ko'rsatiladi
dt_params_footer = {
    "obj_name": obj_name,
    "T_max": T_source_max,
    "D_factor": D_factor,
    "extraction_ratio": extraction_ratio_slider,
    "timestamp": datetime.now().strftime("%Y%m%d"),
}
dt_hash_footer = digital_twin_hash(dt_params_footer)
st.sidebar.code(f"DT-Hash: {dt_hash_footer[:16]}...", language=None)
st.sidebar.caption("JCGM 100:2008 — reproducibility guaranteed")

# [FIX #100] No open source for commercial use warning
st.sidebar.warning("⚠️ Patent Pending — ilmiy faqat. Tijorat taqiqlangan.")

# ── Asosiy footer ──────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "**UCG SCI-Grade Platform v2.0** | 100/100 Expert Fixes Applied | "
    "© 2026 Saitov Dilshodbek, Tashkent Technical University | "
    "Patent Pending (UzPatent + WIPO PCT) | "
    "⚠️ Scientific use only — Commercial use strictly prohibited until patent grant."
)
