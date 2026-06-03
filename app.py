"""
UCG SCI-Grade Platform — TUZATILGAN ASOSIY FUNKSIYALAR
PhD Himoya va Patent uchun 60-tuzatish qo'llangan versiya
Muallif: Saitov Dilshodbek | Versiya: v2.0 | 2026-06-03
"""

# ============================================================
# FIX #1-7: IMPORT TOZALASH
# ============================================================
import io
from io import BytesIO          # FIX #1: ikkilanishni oldini olish
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.stats import linregress   # FIX #3: gaussian_dist o'chirildi
# FIX #2: trapezoid o'chirildi (foydalanilmagan)
import time
import hashlib                  # FIX #22-23: caching uchun
import logging
import os                       # FIX #46: URL configurable
from dataclasses import dataclass  # FIX #39: PARAMS dataclass
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)   # FIX #4
# FIX #5: sys o'chirildi (foydalanilmagan)

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, roc_auc_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter

from docx import Document
from docx.shared import Pt, RGBColor, Inches   # FIX #7: Cm o'chirildi (unused)
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn                     # FIX #6: ishlatiladi (border)
from docx.oxml import OxmlElement              # FIX #6: ishlatiladi (border)
import qrcode
import matplotlib.pyplot as plt
import streamlit as st

logger = logging.getLogger(__name__)

# ============================================================
# FIX #41: GLOBAL REPRODUCIBILITY SEED
# ============================================================
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ============================================================
# FIX #8: EPSILON CONSTANTS
# ============================================================
EPS = 1e-6        # Umumiy epsilon (division by zero)
GEOM_EPS = 1e-3   # Geometrik hisoblashlar (fizik ma'noga ega)
T_REF_AMBIENT = 20.0   # FIX #10: ambient harorat konstanta

# ============================================================
# FIX #39: PARAMS DATACLASS (immutable, type-safe)
# ============================================================
@dataclass(frozen=True)
class UCGPhysicsParams:
    """UCG fizik parametrlari — immutable dataclass"""
    phi_deg: float = 35.0
    cohesion: float = 5e6
    alpha_thermal: float = 3e-5
    gas_temp: int = 1100
    subsidence_rate: float = 0.012
    thermal_damage_beta: float = 0.002
    extraction_ratio: float = 0.6
    E_mass: float = 25e9
    CONFINEMENT: float = 0.65
    RELAX: float = 0.15
    THERMAL_DIFFUSIVITY: float = 8.5e-7
    GAS_VISCOSITY: float = 3e-5
    MOLAR_MASS_GAS: float = 0.028
    R_UNIVERSAL: float = 8.314
    K_VOID: float = 0.35         # FIX #18: void correction factor

PARAMS = UCGPhysicsParams()

# ============================================================
# FIX #40: WILSON CONSTANTS DOCUMENTED
# ============================================================
WILSON_C1 = 0.64   # Edge coal coefficient (Wilson, 1972)
WILSON_C2 = 0.36   # Core coal coefficient (Wilson, 1972)

# ============================================================
# FIX #46: CONFIGURABLE URL
# ============================================================
APP_URL = os.environ.get(
    "UCG_APP_URL",
    "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app/"
)


# ============================================================
# ILMIY HISOBLASH FUNKSIYALARI (TUZATILGAN)
# ============================================================

def thermal_damage(T, beta, T_ref=T_REF_AMBIENT):
    """
    Eksponensial termal zarar funksiyasi
    D(T) = 1 - exp(-β*(T - T_ref))
    Ref: Shao et al. (2015), IJRMMS 74, Eq.4
    """
    return 1.0 - np.exp(-beta * np.maximum(T - T_ref, 0.0))


def apply_thermal_degradation(ucs0, T, beta):
    """UCS(T) = UCS_0 * exp(-β*(T-T0)) | Shao et al. (2015)"""
    dmg = thermal_damage(T, beta)
    return np.clip(ucs0 * (1.0 - dmg), 0.5, None)


# FIX #33: Hoek-Brown 2018 — GSI < 25 case included
def hoek_brown_params(gsi, mi, D):
    """
    Hoek-Brown (2018) parametrlari
    GSI < 25: s = 0 (heavily fractured rock)
    Ref: Hoek & Brown (2018), JRMGE, Table 1
    """
    mb = mi * np.exp((gsi - 100.0) / (28.0 - 14.0 * D))
    if np.isscalar(gsi):
        s = np.exp((gsi - 100.0) / (9.0 - 3.0 * D)) if gsi > 25 else 0.0
    else:
        s = np.where(gsi > 25,
                     np.exp((gsi - 100.0) / (9.0 - 3.0 * D)),
                     0.0)
    a = 0.5 + (1.0 / 6.0) * (np.exp(-gsi / 15.0) - np.exp(-20.0 / 3.0))
    return mb, s, a


def hoek_brown(sigma3, sigma_ci, mb, s, a):
    """Hoek-Brown failure criterion — Hoek & Brown (2018)"""
    sigma3_eff = np.maximum(sigma3, 0.0)
    term = np.maximum(mb * (sigma3_eff / (sigma_ci + EPS)) + s, 0.0)
    return sigma3_eff + sigma_ci * term ** a


# FIX #9: Renamed and documented correctly
def compute_demand_capacity_ratio(sigma1_applied, sigma3_confining,
                                   sigma_ci, mb, s, a):
    """
    Demand-to-Capacity Ratio (DCR) = sigma1_applied / sigma1_failure
    DCR > 1.0 → FAILURE | DCR < 1.0 → STABLE
    Bu Wilson pillar FOS bilan ARALASHTIRILMASIN.
    Ref: Hoek & Brown (2018), Eq.11
    """
    sigma3_eff = np.maximum(sigma3_confining, 0.0)
    sigma1_failure = sigma3_eff + sigma_ci * (
        np.maximum(mb * (sigma3_eff / (sigma_ci + EPS)) + s, 0.0) ** a
    )
    return sigma1_applied / (sigma1_failure + EPS)


def von_mises_stress(sigma_x, sigma_z, tau_xz, nu=None):
    """Von Mises equivalent stress"""
    sigma_y = nu * (sigma_x + sigma_z) if nu is not None else sigma_z
    return np.sqrt(np.maximum(
        sigma_x**2 - sigma_x*sigma_y + sigma_y**2 + 3*tau_xz**2, 0.0
    ))


def thermal_conductivity(T, k0=2.5):
    """k(T) = k0*(1 - 0.0004*(T-20)) | Clauser & Huenges (1995)"""
    return np.clip(k0 * (1.0 - 0.0004 * (T - T_REF_AMBIENT)), 0.5, None)


def specific_heat(T):
    """cp(T) = 960 + 0.14*T [J/kg/K]"""
    return np.clip(960.0 + 0.14 * T, 900.0, 2200.0)


# FIX #11: corrected clip boundary
def density_temperature(rho0, T):
    """
    ρ(T) = ρ0*(1 - α_v*(T-T0))
    α_v = 3.6e-5 /°C (volumetric, coal)
    Ref: Yang (2010), TU Delft PhD, Table 3.2
    """
    T_clamped = np.clip(T, T_REF_AMBIENT, 1200.0)
    alpha_v = 3.6e-5
    rho_T = rho0 * (1.0 - alpha_v * (T_clamped - T_REF_AMBIENT))
    return np.clip(rho_T, 0.80 * rho0, rho0)   # FIX #11: 0.80 (was 0.85)


# FIX #12: E0 now uses PARAMS.E_mass
def young_modulus_temperature(T, E0=None):
    """
    E(T) = E0 * exp(-c_E*(T-T0))
    c_E = 0.0018 /°C (coal, Wu et al. 2013)
    Ref: Shao et al. (2015), Table 1
    """
    E0_val = E0 if E0 is not None else PARAMS.E_mass   # FIX #12
    c_E = 0.0018
    E_T = E0_val * np.exp(-c_E * np.maximum(T - T_REF_AMBIENT, 0.0))
    return np.clip(E_T, 0.10 * E0_val, E0_val)


def thermal_expansion_temperature(T):
    """α(T) — temperature-dependent linear thermal expansion"""
    T_clamped = np.clip(T, T_REF_AMBIENT, 1200.0)
    return PARAMS.alpha_thermal * (1.0 + 0.002*(T_clamped-T_REF_AMBIENT)
                                   + 1e-6*(T_clamped-T_REF_AMBIENT)**2)


def vertical_stress(depth, density):
    """σ_v = ρ*g*H (MPa)"""
    return density * 9.81 * depth / 1e6


def principal_stresses(sx, sy, txy):
    """Principal stresses from 2D stress state"""
    avg = (sx + sy) / 2.0
    radius = np.sqrt(((sx - sy) / 2.0)**2 + txy**2)
    return avg + radius, avg - radius


# FIX #15: added source location parameter
def evolving_cavity_radius(time_h, T_field, beta, grid_z=None,
                            source_z=None, H_seam=None):
    """
    Kamera radiusining vaqt bo'yicha o'sishi
    Faqat yonish zonasi (source_z ± 1.5*H_seam) da zarar hisoblanadi
    Ref: Yang (2010), TU Delft, Chapter 4
    """
    if grid_z is not None and source_z is not None and H_seam is not None:
        source_mask = np.abs(grid_z - source_z) < 1.5 * H_seam
        if np.any(source_mask):
            T_source = T_field[source_mask]
        else:
            T_source = T_field.flatten()
    else:
        T_source = T_field.flatten()

    thermal_dam_local = thermal_damage(T_source, beta)
    growth_rate = 0.015 * np.mean(thermal_dam_local)
    return float(np.clip(5.0 + growth_rate * time_h, 5.0, 40.0))


# FIX #13: CFL stability fix
def solve_heat_equation_dynamic(T, Q, rho_field, cp_field, k_field,
                                 dx, dz, total_time, T_air, h=10.0):
    """
    2D Heat equation FDM (explicit, Fourier stability)
    CFL: dt <= 1/(2*α_max*(1/dx²+1/dz²))
    """
    alpha_field = k_field / (rho_field * cp_field)
    alpha_max = float(np.max(alpha_field))
    dt_max = 1.0 / (2.0 * alpha_max * (1.0/dx**2 + 1.0/dz**2))
    dt_safe = 0.8 * dt_max
    n_steps = max(int(np.ceil(total_time / dt_safe)), 1)
    dt = total_time / n_steps   # FIX #13: verify dt <= dt_max
    if dt > dt_max * 1.001:
        logger.warning(f"CFL marginal: dt={dt:.3e} > dt_max={dt_max:.3e}")

    for _ in range(n_steps):
        T_old = T.copy()
        Txx = (T_old[1:-1, 2:] - 2*T_old[1:-1, 1:-1] + T_old[1:-1, :-2]) / dx**2
        Tzz = (T_old[2:, 1:-1] - 2*T_old[1:-1, 1:-1] + T_old[:-2, 1:-1]) / dz**2
        T_new = T_old.copy()
        T_new[1:-1, 1:-1] = (T_old[1:-1, 1:-1] +
            dt * (alpha_field[1:-1, 1:-1] * (Txx + Tzz) +
                  Q[1:-1, 1:-1] / (rho_field[1:-1, 1:-1] * cp_field[1:-1, 1:-1] + EPS)))
        T_new[:, 0] = T_new[:, 1]
        T_new[:, -1] = T_new[:, -2]
        T_new[-1, :] = T_new[-2, :]
        k_surface = k_field[0, :]
        T_new[0, :] = (k_surface * T_new[1, :] + dz * h * T_air) / (k_surface + dz * h + EPS)
        T = T_new.copy()
    return T


# FIX #14: corrected pore pressure units
def pore_pressure_field(T, depth, permeability=None,
                         water_table=20.0, rho_water=1000.0):
    """
    Pore pressure: hydrostatic + gas thermal components (MPa)
    Ref: Terzaghi (1943); Darcy (1856)
    FIX: removed dimensionally inconsistent permeability term
    """
    h_water = np.maximum(depth - water_table, 0.0)
    P_hydro = rho_water * 9.81 * h_water / 1e6   # MPa

    T_kelvin = np.maximum(T + 273.15, 293.15)
    P_gas = (101325.0 * T_kelvin / 293.15) / 1e6   # Pa → MPa (ideal gas)

    return P_hydro + P_gas


def kirsch_stress_field(x, z, sigma_H, sigma_h, cavity_radius,
                         pore_pressure=0.0):
    """
    Kirsch (1898) solution for circular cavity in biaxial stress field
    """
    r = np.sqrt(x**2 + z**2)
    r = np.maximum(r, cavity_radius + GEOM_EPS)   # FIX #8
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


# FIX #38: Terzaghi effective stress in FOS
def fos_with_pore_pressure(pillar_strength, sigma_v, pore_pressure,
                            B_skempton=0.9):
    """
    FOS bilan Terzaghi effective stress
    σ_v_eff = σ_v - B*P_pore
    Ref: Terzaghi (1943); Skempton (1954)
    """
    sigma_v_eff = max(sigma_v - B_skempton * pore_pressure, 0.01)
    return pillar_strength / sigma_v_eff


# FIX #32: corrected Monte Carlo with seed and reproducibility
def monte_carlo_fos(ucs_mean, ucs_std, gsi_mean, gsi_std, mi_val, D,
                    T_avg, H_seam, depth, density, rec_width, beta_th,
                    n_sim=1000, random_seed=RANDOM_SEED):
    """
    Monte Carlo FOS Distribution (reproducible)
    Ref: Ang & Tang (2007), Probability Concepts in Engineering
    """
    rng = np.random.default_rng(seed=random_seed)   # FIX #32
    cov_ucs_gsi = 0.3 * ucs_std * gsi_std
    cov = np.array([[ucs_std**2, cov_ucs_gsi],
                    [cov_ucs_gsi, gsi_std**2]])
    min_eig = np.min(np.linalg.eigvalsh(cov))
    if min_eig < 0:
        cov -= np.eye(2) * min_eig * 1.01

    samples = rng.multivariate_normal([ucs_mean, gsi_mean], cov, n_sim)
    ucs_samples = samples[:, 0]
    gsi_samples = np.clip(samples[:, 1], 10, 100)

    fos = []
    for ucs, gsi in zip(ucs_samples, gsi_samples):
        mb, s, a = hoek_brown_params(gsi, mi_val, D)   # FIX #33
        ucs_T = apply_thermal_degradation(ucs, T_avg, beta_th)
        sigma_cm = ucs_T * (s ** a)
        pillar_s = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS))
        sv = density * 9.81 * depth / 1e6
        fos.append(float(np.clip(pillar_s / (sv + EPS), 0, 3)))

    fos = np.array(fos)
    return fos, float(np.mean(fos < 1.0))


# FIX #34-35: Corrected tau_thermal and sigma_thermal
def compute_thermal_stresses(E_field, alpha_field, delta_T, nu_poisson,
                               dT_dx, dT_dz):
    """
    Termal kuchlanishlar (to'g'ri formula)
    σ_th = E*α*ΔT / (1-ν)   [Pa → MPa]
    τ_th: deviatoric gradient (Noda, 1983)
    """
    # Normal thermal stress (FIX #37: relax_factor removed — E_field already degraded)
    sigma_thermal = (E_field * alpha_field * delta_T) / (1.0 - nu_poisson + EPS) / 1e6

    # Shear thermal stress — deviatoric gradient (FIX #34)
    dT_deviatoric = (dT_dx - dT_dz) / 2.0
    tau_thermal = (E_field * alpha_field * dT_deviatoric * nu_poisson) / \
                  (2.0 * (1.0 - nu_poisson**2) + EPS) / 1e6

    return sigma_thermal, tau_thermal


# FIX #36: O'Reilly & New horizontal displacement
def horizontal_displacement_oreilly(x, S_x, i_inflection):
    """
    O'Reilly & New (1982) horizontal displacement
    u_h(x) = -(x / i) * S(x)
    Ref: O'Reilly & New (1982), Tunnelling '82, p.173
    """
    return -(x / (i_inflection + EPS)) * S_x


# FIX #54: Time-dependent creep
def pillar_creep_strength(sigma_p0, time_h, A_creep=0.05, n_creep=0.3):
    """
    Vaqtga bog'liq pillar mustahkamligi
    σ_p(t) = σ_p0*(1 - A*t^n)
    Ref: Pappas & Mark (1993), USBM RI 9445
    """
    reduction = min(A_creep * (time_h ** n_creep), 0.40)
    return sigma_p0 * (1.0 - reduction)


# FIX #55: Gas migration risk
def gas_migration_risk(T_field, perm_field, fos_field):
    """
    Yer usti gaz ko'chish xavfi
    Ref: Kapusta & Stanczyk (2011), Energy
    """
    thermal_path = T_field > 300.0
    perm_path = perm_field > 1e-14
    structural_fail = fos_field < 1.5
    gas_risk = (thermal_path & perm_path & structural_fail).astype(float)
    return gaussian_filter(gas_risk, sigma=2.0)


# FIX #6: ISO table borders using qn and OxmlElement
def set_table_border(table, color="2E74B5"):
    """ISO 9001 jadvali uchun professional border"""
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:color'), color)
        tblBorders.append(border)
    tblPr.append(tblBorders)


# FIX #45: CSV validation
def validate_sensor_csv(uploaded_file, required_cols, max_size_mb=10):
    """Sensor CSV fayl validatsiyasi"""
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"Fayl {file_size_mb:.1f} MB > {max_size_mb} MB!")
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='latin-1')
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Ustunlar yo'q: {missing}")
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna(subset=required_cols)


# FIX #22-23: Array hashing for cache
def _array_hash(*arrays) -> str:
    """Numpy arraylar uchun stabil MD5 hash"""
    h = hashlib.md5()
    for arr in arrays:
        h.update(np.ascontiguousarray(arr).tobytes())
        h.update(str(arr.shape).encode())
    return h.hexdigest()[:16]


# FIX #28: corrected collapse label
def create_collapse_label(fos, temp, sigma1, sigma_ci):
    """
    Multi-criteria collapse labeling
    Ref: Hoek & Brown (2018); Wilson (1972)
    """
    criterion1 = fos < 1.0
    criterion2 = sigma1 > (0.90 * sigma_ci)
    criterion3 = (temp > 800.0) & (fos < 1.3)
    return (criterion1 | criterion2 | criterion3).astype(int)


# FIX #57: Formal uncertainty propagation
def propagate_uncertainty_analytical(ucs_mean, ucs_cov, gsi_mean, gsi_cov,
                                      T_mean, T_cov, H_seam, rec_width,
                                      mi_val=10.0, D_factor=0.7,
                                      depth=200.0, rho=2500.0):
    """
    First-order Taylor uncertainty propagation
    Ref: Ang & Tang (2007), Probability Concepts, Ch.4
    """
    def _fos(ucs, gsi, T):
        mb, s, a = hoek_brown_params(gsi, mi_val, D_factor)
        ucs_T = apply_thermal_degradation(ucs, T, PARAMS.thermal_damage_beta)
        sigma_cm = ucs_T * (s ** a)
        p_str = sigma_cm * (WILSON_C1 + WILSON_C2 * rec_width / (H_seam + EPS))
        sv = rho * 9.81 * depth / 1e6
        return float(np.clip(p_str / (sv + EPS), 0, 5))

    eps = 0.01
    fos_base = _fos(ucs_mean, gsi_mean, T_mean)
    dfos_ducs = (_fos(ucs_mean*(1+eps), gsi_mean, T_mean) - fos_base) / (eps*ucs_mean)
    dfos_dgsi = (_fos(ucs_mean, gsi_mean*(1+eps), T_mean) - fos_base) / (eps*gsi_mean)
    dfos_dT   = (_fos(ucs_mean, gsi_mean, T_mean*(1+eps)) - fos_base) / (eps*T_mean + EPS)

    var_fos = (dfos_ducs * ucs_mean * ucs_cov)**2 + \
              (dfos_dgsi * gsi_mean * gsi_cov)**2 + \
              (dfos_dT * T_mean * T_cov)**2

    return fos_base, float(np.sqrt(var_fos))


print("✅ UCG v2.0 core functions loaded successfully (60 fixes applied)")
print(f"   Random seed: {RANDOM_SEED}")
print(f"   PARAMS.E_mass: {PARAMS.E_mass:.2e} Pa")
print(f"   WILSON_C1={WILSON_C1}, WILSON_C2={WILSON_C2} (Wilson 1972)")
