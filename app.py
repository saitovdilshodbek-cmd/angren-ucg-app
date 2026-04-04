import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize

# ==============================================================================
# --- SAHIFA SOZLAMALARI ---
# ==============================================================================
st.set_page_config(page_title="UCG Geomechanical Monitor", layout="wide")
st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# --- 🧮 MATEMATIK METODOLOGIYA (PhD LEVEL) ---
# ==============================================================================
st.sidebar.header("🧮 Matematik Metodologiya")
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

# ==============================================================================
# --- 🏭 MINE DATA (Preset konlar) ---
# ==============================================================================
mine_data = {
    "Angren (Ko'mir)": {"UCS": 40,  "GSI": 55, "mi": 10, "rho": 1400},
    "Sharqiy blok":    {"UCS": 55,  "GSI": 60, "mi": 12, "rho": 1600},
    "G'arbiy blok":    {"UCS": 35,  "GSI": 50, "mi": 9,  "rho": 1350},
    "Qo'shimcha kon":  {"UCS": 60,  "GSI": 70, "mi": 14, "rho": 1700},
    "Foydalanuvchi":   {"UCS": None,"GSI": None,"mi": None,"rho": None},
}

# ==============================================================================
# --- ⚙️ SIDEBAR: UMUMIY PARAMETRLAR ---
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
mine_preset = st.sidebar.selectbox(
    "🏭 Kon Preseti:",
    list(mine_data.keys()),
    index=0,
    help="Tanlangan kon uchun UCS/GSI/mi/rho qiymatlarini avtomat to'ldiradi"
)
_md = mine_data[mine_preset]

obj_name      = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h        = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers    = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)
tensile_mode  = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor      = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.7)
nu_poisson    = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, 0.25)
k_ratio       = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, 0.5)

st.sidebar.subheader("📐 Cho'zilish va Selek")
tensile_ratio = st.sidebar.slider("Tensile Ratio (σt0/UCS):", 0.03, 0.15, 0.08)
beta_thermal  = st.sidebar.number_input("Thermal Decay (β):", value=0.0035, format="%.4f")

st.sidebar.subheader("🔥 Yonish va Termal")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)
T_source_max  = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

# --- Qatlamlar (layers_data) ---
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0

for i in range(int(num_layers)):
    _ucs_def = float(_md["UCS"]) if _md["UCS"] is not None else 40.0
    _rho_def = float(_md["rho"]) if _md["rho"] is not None else 2500.0
    _gsi_def = int(_md["GSI"])   if _md["GSI"] is not None else 60
    _mi_def  = float(_md["mi"])  if _md["mi"]  is not None else 10.0

    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        name  = st.text_input(f"Nomi:",         value=f"Qatlam-{i+1}", key=f"name_{i}")
        thick = st.number_input(f"Qalinlik (m):", value=50.0,          key=f"t_{i}")
        u     = st.number_input(f"UCS (MPa):",   value=_ucs_def,       key=f"u_{i}")
        rho   = st.number_input(f"Zichlik (kg/m³):", value=_rho_def,   key=f"rho_{i}")
        color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
        g     = st.slider(f"GSI:", 10, 100, _gsi_def,                  key=f"g_{i}")
        m     = st.number_input(f"mi:",           value=_mi_def,        key=f"m_{i}")
        s_t0_val = st.number_input(f"σt0 (MPa):", value=3.0, key=f"st_{i}") if tensile_mode == "Manual" else 0.0

    layers_data.append({
        'name': name, 't': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

# ==============================================================================
# --- 📐 ASOSIY GRID VA MANBA HISOB-KITOBLARI ---
# ==============================================================================
x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam   = layers_data[-1]['t']

grid_sigma_v, grid_ucs, grid_mb, grid_s_hb, grid_a_hb, grid_sigma_t0_manual = [
    np.zeros_like(grid_z) for _ in range(6)
]

# Session state: maksimal harorat xaritasi (kumulativ)
if ('max_temp_map' not in st.session_state
        or st.session_state.max_temp_map.shape != grid_z.shape):
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
if ('last_obj_name' not in st.session_state
        or st.session_state.last_obj_name != obj_name):
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name

# Hoek-Brown parametrlari qatlam bo'yicha
for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1:
        mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask]     = layer['ucs']
    grid_mb[mask]      = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask]    = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask]    = 0.5 + (1/6) * (np.exp(-layer['gsi'] / 15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

# Gaussan harorat tarqalishi (manbalar)
alpha_rock = 1.0e-6
sources = {
    '1': {'x': -total_depth/3, 'start': 0},
    '2': {'x': 0,              'start': 40},
    '3': {'x':  total_depth/3, 'start': 80},
}
temp_2d = np.ones_like(grid_x) * 25
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec   = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
        elapsed  = time_h - val['start']
        curr_T   = (T_source_max if elapsed <= burn_duration
                    else 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration)))
        dist_sq  = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

# ==============================================================================
# --- 🔥 PDE HEAT SOLVER — 2D sonli issiqlik tenglamasi (FDM) ---
# ==============================================================================
def solve_heat_step(T, Q, alpha, dx, dt):
    """2D issiqlik diffuziya tenglamasining bir vaqt qadami (sonli farqlar)."""
    Tn = T.copy()
    Tn[1:-1, 1:-1] = (
        T[1:-1, 1:-1]
        + alpha * dt * (
            (T[2:, 1:-1] - 2*T[1:-1, 1:-1] + T[:-2, 1:-1]) / dx**2
            + (T[1:-1, 2:] - 2*T[1:-1, 1:-1] + T[1:-1, :-2]) / dx**2
        )
        + Q[1:-1, 1:-1] * dt
    )
    return Tn

Q_heat = np.zeros_like(temp_2d)
for val in sources.values():
    Q_heat += 500 * np.exp(
        -((grid_x - val['x'])**2 + (grid_z - source_z)**2) / 200
    )

for _ in range(10):
    temp_2d = solve_heat_step(temp_2d, Q_heat, alpha_rock, dx=1.0, dt=0.1)

# Kumulativ maksimal harorat
st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25

# ==============================================================================
# --- 🧱 TM TAHLIL: KUCHLANISH, DAMAGE, FAILURE ---
# ==============================================================================
temp_eff       = np.maximum(st.session_state.max_temp_map - 100, 0)
damage         = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
sigma_ci       = grid_ucs * (1 - damage)

E                  = 5000
alpha_T_coeff      = 1e-5
constraint_factor  = 0.7

dT_dx          = np.gradient(temp_2d, axis=1)
dT_dz          = np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)

sigma_thermal  = constraint_factor * (E * alpha_T_coeff * delta_T) / (1 - nu_poisson)
sigma_thermal += 0.3 * thermal_gradient

grid_sigma_h   = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act     = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act     = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field      = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
thermal_boost      = 1 + 0.6 * (1 - np.exp(-delta_T / 200))
sigma_t_field_eff  = sigma_t_field / thermal_boost

# Failure zonalari
tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50) & (sigma1_act > sigma3_act)
sigma3_safe     = np.maximum(sigma3_act, 0.01)
sigma1_limit    = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + 1e-6) + grid_s_hb) ** grid_a_hb
shear_failure   = sigma1_act >= sigma1_limit

spalling  = tensile_failure & (temp_2d > 400)
crushing  = shear_failure   & (temp_2d > 600)

depth_factor     = np.exp(-grid_z / total_depth)
local_collapse_T = np.clip((st.session_state.max_temp_map - 600) / 300, 0, 1)
time_factor      = np.clip((time_h - 40) / 60, 0, 1)
collapse_final   = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw       = spalling | crushing | (st.session_state.max_temp_map > 900)
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_permanent > 0.3) & (collapse_final > 0.05)

perm        = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)
void_volume = np.sum(void_mask_permanent) * (x_axis[1] - x_axis[0]) * (z_axis[1] - z_axis[0])

# ==============================================================================
# --- 💨 GAS FLOW (DARCY QONUNI) ---
# ==============================================================================
def gas_flow(k, pressure):
    """Darcy qonuni: gaz oqim tezlik komponentlari.
    k        — o'tkazuvchanlik (m²)
    pressure — bosim matritsasi
    Returns    vx, vz"""
    dp_dx = np.gradient(pressure, axis=1)
    dp_dz = np.gradient(pressure, axis=0)
    return -k * dp_dx, -k * dp_dz

pressure_field  = temp_2d * 10
vx_gas, vz_gas  = gas_flow(perm, pressure_field)
gas_velocity    = np.sqrt(vx_gas**2 + vz_gas**2)

# Void sohasida kuchlanish nolga tushiriladi
sigma1_act = np.where(void_mask_permanent, 0,    sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0,    sigma3_act)
sigma_ci   = np.where(void_mask_permanent, 0.01, sigma_ci)

# ==============================================================================
# --- 🧠 AI MODEL — RandomForest Collapse Prediction ---
# ==============================================================================
try:
    from sklearn.ensemble import RandomForestRegressor
    X_ai = np.column_stack([
        temp_2d.flatten(),
        sigma1_act.flatten(),
        sigma3_act.flatten(),
        grid_z.flatten()
    ])
    y_ai     = void_mask_permanent.flatten().astype(int)
    rf_model = RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42)
    rf_model.fit(X_ai, y_ai)
    collapse_pred = rf_model.predict(X_ai).reshape(temp_2d.shape)
except Exception:
    collapse_pred = np.zeros_like(temp_2d)

# ==============================================================================
# --- ⚙️ SELEK OPTIMIZATSIYASI ---
# ==============================================================================
# Klassik iterativ yechim
avg_t_p      = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam     = layers_data[-1]['ucs']
sv_seam      = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0
for _ in range(15):
    p_strength   = (ucs_seam * strength_red) * (w_sol / H_seam) ** 0.5
    y_zone_calc  = (H_seam / 2) * (np.sqrt(sv_seam / (p_strength + 1e-6)) - 1)
    new_w        = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1:
        break
    w_sol = new_w

rec_width, pillar_strength, y_zone = np.round(w_sol, 1), p_strength, max(y_zone_calc, 1.5)
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0, fos_2d)

# AI optimizatsiya (Scipy minimize + SLSQP)
def _objective(w):
    strength = ucs_seam * (w[0] / H_seam) ** 0.5
    risk     = float(np.mean(void_mask_permanent))
    return -(strength - 15 * risk)

opt_result       = minimize(_objective, x0=[rec_width], bounds=[(5, 100)], method='SLSQP')
optimal_width_ai = float(np.clip(opt_result.x[0], 5, 100))

# ==============================================================================
# --- 📊 VIZUALIZATSIYA: METRIKALAR ---
# ==============================================================================
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)",      f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi",          f"{void_volume:.1f} m³")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("AI Tavsiya (Selek)",    f"{optimal_width_ai:.1f} m",
          delta=f"Klassik: {rec_width} m", delta_color="off")

# ==============================================================================
# --- 📈 CHO'KISH VA HOEK-BROWN GRAFIKLARI ---
# ==============================================================================
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

s_max  = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p  = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth / 2)**2))
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth * 10)) * (time_h / 150) * 100

with col_g1:
    st.plotly_chart(
        go.Figure(go.Scatter(x=x_axis, y=sub_p * 100, fill='tozeroy',
                             line=dict(color='magenta', width=3)))
        .update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300),
        use_container_width=True
    )
with col_g2:
    st.plotly_chart(
        go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy',
                             line=dict(color='cyan', width=3)))
        .update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300),
        use_container_width=True
    )
with col_g3:
    sigma3_ax  = np.linspace(0, ucs_seam * 0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20      = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + 1e-6) + s_s) ** a_s
    ucs_burn   = ucs_seam * np.exp(-0.0025 * (T_source_max - 20))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + 1e-6) + s_s) ** a_s
    s1_sov     = sigma3_ax + (ucs_seam * strength_red) * (mb_s * sigma3_ax / (ucs_seam * strength_red + 1e-6) + s_s) ** a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20,      name='20°C',       line=dict(color='red',    width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov,     name='Zararlangan', line=dict(color='cyan',   width=2, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish',      line=dict(color='orange', width=4)))
    st.plotly_chart(
        fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300,
                             legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")),
        use_container_width=True
    )

# ==============================================================================
# --- 🔥 TM MAYDONI (fig_tm) — BARCHA TRACE QATLAMLAR ---
# ==============================================================================
st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("📋 Ilmiy Tahlil")
    st.error("🔴 FOS < 1.0: Failure")
    st.warning("🟡 FOS 1.0–1.5: Unstable")
    st.success("🟢 FOS > 1.5: Stable")
    fig_s = go.Figure()
    for l in layers_data:
        fig_s.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'],
                               marker_color=l['color'], width=0.4))
    st.plotly_chart(
        fig_s.update_layout(barmode='stack', template="plotly_dark",
                            yaxis=dict(autorange='reversed'), height=450, showlegend=False),
        use_container_width=True
    )

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi")

    fig_tm = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.15,
        subplot_titles=(
            "Harorat Maydoni (°C) + Gaz Oqimi Tezligi",
            "FOS + AI Collapse Prediction + Yielded Zones"
        )
    )

    # --- ROW 1: Harorat heatmap ---
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis,
        colorscale='Hot', zmin=25, zmax=T_source_max,
        colorbar=dict(title="T (°C)", title_side="top",
                      x=1.05, y=0.78, len=0.42, thickness=15),
        name="Harorat"
    ), row=1, col=1)

    # --- ROW 1 (overlay): Gaz oqimi tezligi (Blues heatmap) ---
    # ESLATMA: go.Cone 3D trace bo'lib, 2D subplotga mos kelmaydi.
    # gas_velocity normalized Blues heatmap sifatida ko'rsatiladi.
    gas_vel_norm = gas_velocity / (gas_velocity.max() + 1e-30)
    fig_tm.add_trace(go.Heatmap(
        z=gas_vel_norm, x=x_axis, y=z_axis,
        colorscale='Blues', opacity=0.35,
        showscale=False, name='Gaz Oqimi Tezligi'
    ), row=1, col=1)

    # --- ROW 2: FOS Contour ---
    fig_tm.add_trace(go.Contour(
        z=fos_2d, x=x_axis, y=z_axis,
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']],
        zmin=0, zmax=3.0, contours_showlines=False,
        colorbar=dict(title="FOS", title_side="top",
                      x=1.05, y=0.22, len=0.42, thickness=15),
        name="FOS"
    ), row=2, col=1)

    # --- ROW 2: Void (qora) ---
    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=void_visual, x=x_axis, y=z_axis,
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False, opacity=0.9, hoverinfo='skip'
    ), row=2, col=1)

    # --- ROW 2: Void kontur chegarasi ---
    fig_tm.add_trace(go.Contour(
        z=void_mask_permanent.astype(int), x=x_axis, y=z_axis,
        showscale=False, contours=dict(coloring='lines'),
        line=dict(color='white', width=2), hoverinfo='skip'
    ), row=2, col=1)

    # --- ROW 2: Failure nuqtalari ---
    shear_disp = np.copy(shear_failure);   shear_disp[void_mask_permanent] = False
    tens_disp  = np.copy(tensile_failure); tens_disp[void_mask_permanent]  = False
    fig_tm.add_trace(go.Scatter(
        x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2],
        mode='markers', marker=dict(color='red',  size=3, symbol='x'),     name='Shear'
    ), row=2, col=1)
    fig_tm.add_trace(go.Scatter(
        x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2],
        mode='markers', marker=dict(color='blue', size=3, symbol='cross'),  name='Tensile'
    ), row=2, col=1)

    # --- ROW 2: Selek to'rtburchagi ---
    for px in [(sources['1']['x'] + sources['2']['x']) / 2,
               (sources['2']['x'] + sources['3']['x']) / 2]:
        fig_tm.add_shape(
            type="rect",
            x0=px - rec_width/2, x1=px + rec_width/2,
            y0=source_z - H_seam/2, y1=source_z + H_seam/2,
            line=dict(color="lime", width=3),
            row=2, col=1
        )

    # --- ROW 2 (overlay): AI Collapse Prediction (Viridis) ---
    fig_tm.add_trace(go.Heatmap(
        z=collapse_pred, x=x_axis, y=z_axis,
        colorscale='Viridis', opacity=0.4,
        showscale=False, name='AI Collapse'
    ), row=2, col=1)

    fig_tm.update_layout(
        template="plotly_dark", height=850,
        margin=dict(r=150, t=80, b=100),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# ==============================================================================
# --- 🌀 UCG: 3D DINAMIK MODEL (SOATBAY) ---
# ==============================================================================
st.header("🌀 UCG: Termo-Mexanik Dinamik 3D Model")


def generate_hourly_3d_model(h, layers):
    grid_res   = 45
    x_3d       = np.linspace(-100, 100, grid_res)
    y_3d       = np.linspace(-60,   60, grid_res)
    gx3, gy3   = np.meshgrid(x_3d, y_3d)
    centers_x  = [-60, 0, 60]
    radii, temp_states = [], []

    for i, cx in enumerate(centers_x):
        start_h = i * 40
        if h <= start_h:
            radii.append(0); temp_states.append("Sovuq")
        elif start_h < h <= start_h + 40:
            radii.append(2 + (h - start_h) / 40 * 10); temp_states.append("Faol")
        else:
            radii.append(12); temp_states.append("Soviyotgan")

    total_subs = np.zeros_like(gx3)
    for i in range(3):
        if radii[i] > 0:
            amp = (radii[i] / 12) * 5.0 * min(h / 150, 1.0)
            total_subs += -amp * np.exp(-((gx3 - centers_x[i])**2 + gy3**2) / 600)

    fig = go.Figure()
    curr_depth = 0
    for i, layer in enumerate(layers):
        layer_deform = total_subs * (0.85 ** i)
        fig.add_trace(go.Surface(
            x=gx3, y=gy3, z=-curr_depth + layer_deform,
            colorscale=[[0, layer['color']], [1, layer['color']]],
            opacity=0.8 if i == 0 else 0.5,
            showscale=False, name=layer['name'],
            hoverinfo='text',
            text=f"Qatlam: {layer['name']} | {layer['t']}m"
        ))
        curr_depth += layer['t']

    coal_z_c = -(sum(l['t'] for l in layers[:-1]) + layers[-1]['t'] / 2)
    u_a, v_a = np.mgrid[0:2*np.pi:18j, 0:np.pi:18j]
    for i, cx in enumerate(centers_x):
        if radii[i] > 0:
            r    = radii[i]
            cmap = 'YlOrRd' if temp_states[i] == "Faol" else 'Greys'
            op   = 0.9      if temp_states[i] == "Faol" else 0.6
            fig.add_trace(go.Surface(
                x=r*np.cos(u_a)*np.sin(v_a) + cx,
                y=(r*0.8)*np.sin(u_a)*np.sin(v_a),
                z=(r*0.5)*np.cos(v_a) + coal_z_c,
                colorscale=cmap, opacity=op,
                showscale=False, name=f"Kamera {i+1}"
            ))

    if "Faol" in temp_states:
        act_i = temp_states.index("Faol")
        np.random.seed(int(h))
        n_pts = int(5 + (h % 30))
        st_x = np.random.uniform(centers_x[act_i]-20, centers_x[act_i]+20, n_pts)
        st_y = np.random.uniform(-20, 20, n_pts)
        st_z = np.random.uniform(coal_z_c, coal_z_c + 15, n_pts)
        fig.add_trace(go.Scatter3d(
            x=st_x, y=st_y, z=st_z, mode='markers',
            marker=dict(size=4, color='cyan', symbol='diamond'),
            name="Termal Kuchlanish"
        ))

    total_h_depth = sum(l['t'] for l in layers)
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (m)", range=[-100, 100]),
            yaxis=dict(title="Y (m)", range=[-60, 60]),
            zaxis=dict(title="Chuqurlik Z (m)", range=[-total_h_depth - 10, 20]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=0.6, z=0.4)
        ),
        margin=dict(l=0, r=0, b=0, t=50),
        title=f"Angren-UCG: {h}-soatdagi 3D Geomexanik holat"
    )
    return fig


fig_3d = generate_hourly_3d_model(time_h, layers_data)
st.plotly_chart(fig_3d, use_container_width=True)
st.info(f"ℹ️ Sidebar'dagi jarayon vaqti ({time_h}-soat) asosida "
        f"kameralarning termal kengayishi va qatlamlar deformatsiyasi qayta hisoblandi.")

# ==============================================================================
# --- 📊 KOMPLEKS MONITORING PANELI ---
# ==============================================================================
st.header(f"📊 {obj_name}: Kompleks Monitoring Paneli")


def calculate_live_metrics(h, layers, T_max):
    target  = layers[-1]
    ucs_0_l = target['ucs']
    H_l     = target['t']
    curr_T_l = (25 + (T_max - 25) * (min(h, 40) / 40)
                if h <= 40 else T_max * np.exp(-0.001 * (h - 40)))
    str_red_l  = np.exp(-0.0025 * (curr_T_l - 20))
    w_rec_l    = 15.0 + (h / 150) * 10
    p_str_l    = (ucs_0_l * str_red_l) * (w_rec_l / H_l) ** 0.5
    s_max_l    = (H_l * 0.05) * (min(h, 120) / 120)
    return p_str_l, w_rec_l, curr_T_l, s_max_l


p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max)

mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric("Pillar Strength",     f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric("Tavsiya: Selek Eni",  f"{w_rec_live:.1f} m")
mk3.metric("Maks. Cho'kish",      f"{s_max_3d * 100:.1f} cm")
mk4.metric("Jarayon bosqichi",    "Faol" if time_h < 100 else "Sovish")

st.markdown("---")


def generate_integrated_3d(h, layers, s_max):
    grid_res = 35
    x_i = np.linspace(-100, 100, grid_res)
    y_i = np.linspace(-60, 0, grid_res)
    gx, gy = np.meshgrid(x_i, y_i)
    subs_map = -s_max * np.exp(-(gx**2 + gy**2) / 800)
    fig = go.Figure()
    curr_z = 0
    for i, layer in enumerate(layers):
        z_top    = -curr_z              + subs_map * (0.85 ** i)
        z_bottom = -(curr_z + layer['t']) + subs_map * (0.85 ** (i+1))
        cs = [[0, layer['color']], [1, layer['color']]]
        fig.add_trace(go.Surface(x=gx, y=gy, z=z_top,
                                 colorscale=cs, opacity=1.0,
                                 showscale=False, name=layer['name'], hoverinfo='skip'))
        for side in range(3):
            if side == 0:
                sx, sy, szt, szb = gx[:, 0],  gy[:, 0],  z_top[:, 0],  z_bottom[:, 0]
            elif side == 1:
                sx, sy, szt, szb = gx[:, -1], gy[:, -1], z_top[:, -1], z_bottom[:, -1]
            else:
                sx, sy, szt, szb = gx[-1, :], gy[-1, :], z_top[-1, :], z_bottom[-1, :]
            fig.add_trace(go.Surface(
                x=np.array([sx, sx]), y=np.array([sy, sy]),
                z=np.array([szt, szb]),
                colorscale=cs, opacity=1.0, showscale=False, hoverinfo='skip'
            ))
        curr_z += layer['t']

    coal_z = -(sum(l['t'] for l in layers[:-1]) + layers[-1]['t'] / 2)
    r_c    = min(h / 10, 13)
    if r_c > 1:
        u_c, v_c = np.mgrid[0:2*np.pi:20j, 0:np.pi/2:20j]
        fig.add_trace(go.Surface(
            x=r_c * np.cos(u_c) * np.sin(v_c),
            y=(r_c * 0.8) * np.sin(u_c) * np.sin(v_c),
            z=(r_c * 0.6) * np.cos(v_c) + coal_z,
            colorscale='Hot', opacity=1.0, showscale=False,
            name="Yonish kamerasi",
            lighting=dict(ambient=0.7, diffuse=1.0, specular=0.5)
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (m)", backgroundcolor="black", showbackground=True),
            yaxis=dict(title="Y", range=[-60, 20], backgroundcolor="black", showbackground=True),
            zaxis=dict(title="Chuqurlik",
                       range=[-sum(l['t'] for l in layers) - 10, 20]),
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.0))
        ),
        height=750, margin=dict(l=0, r=0, b=0, t=0),
        template="plotly_dark"
    )
    return fig


col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("🌐 3D Geomexanik Massiv")
    st.plotly_chart(generate_integrated_3d(time_h, layers_data, s_max_3d), use_container_width=True)

with col_right:
    st.subheader("📈 Dinamik Trendlar")
    h_axis   = np.linspace(0, 150, 50)
    st_trend = [calculate_live_metrics(v, layers_data, T_source_max)[0] for v in h_axis]
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=h_axis, y=st_trend, name="Mustahkamlik",
                                   line=dict(color='orange', width=3)))
    fig_trend.add_vline(x=time_h, line_dash="dash", line_color="red")
    fig_trend.update_layout(template="plotly_dark", height=250,
                            title="Mustahkamlik pasayishi (MPa/h)",
                            margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_trend, use_container_width=True)
    st.write("**Qatlamlar tuzilishi:**")
    for l in layers_data:
        st.caption(f"• {l['name']}: {l['t']} m (UCS: {l['ucs']} MPa)")

st.markdown("---")
with st.expander("📝 Avtomatik Ilmiy Interpretatsiya", expanded=True):
    risk_level = "YUQORI" if p_str < 15 else "O'RTA" if p_str < 25 else "PAST"
    st.write(f"""
**Tahlil natijasi ({time_h}-soat):**
1. **Termal degradatsiya:** Harorat {t_now:.1f} °C ga yetishi natijasida ko'mir mustahkamligi
   boshlang'ich holatga nisbatan {((1 - p_str / layers_data[-1]['ucs']) * 100):.1f}% ga kamaygan.
2. **Yer yuzasi:** {s_max_3d * 100:.1f} cm lik vertikal cho'kish kutilmoqda.
   Bu {layers_data[0]['name']} qatlamida plastik deformatsiyalarni yuzaga keltirishi mumkin.
3. **Xavf darajasi:** **{risk_level}**. Tavsiya: Selek eni **{w_rec_live:.1f} m**
   (AI optimizatsiya: **{optimal_width_ai:.1f} m**).
""")

# ==============================================================================
# --- 📑 CHUQURLASHTIRILGAN ILMIY HISOBOT (PhD EDITION) ---
# ==============================================================================
st.markdown("---")
st.header("🔍 Chuqurlashtirilgan Dinamik Tahlil va Metodik Asoslash")

E_MODULUS    = 5000
ALPHA_THERM  = 1.0e-5
BETA_CONST   = beta_thermal

target_l     = layers_data[-1]
ucs_0_r      = target_l['ucs']
gsi_val      = target_l['gsi']
mi_val       = target_l['mi']
gamma_kn     = target_l['rho'] * 9.81 / 1000
H_depth_tot  = sum(l['t'] for l in layers_data[:-1]) + target_l['t'] / 2

sigma_v_tot  = (gamma_kn * H_depth_tot) / 1000
mb_dyn       = mi_val  * np.exp((gsi_val - 100) / (28 - 14 * D_factor))
s_dyn        = np.exp((gsi_val - 100) / (9 - 3 * D_factor))
ucs_t_dyn    = ucs_0_r * np.exp(-BETA_CONST * (T_source_max - 20))
p_str_final  = ucs_t_dyn * (rec_width / H_seam) ** 0.5
fos_final    = p_str_final / (sigma_v_tot + 1e-6)

t1, t2, t3 = st.tabs(["🏗️ Massiv Parametrlari", "🔥 Termal Degradatsiya", "⚖️ Barqarorlik & Manbalar"])

with t1:
    st.subheader("1. Hoek-Brown (2018) Klassifikatsiyasi")
    c1r, c2r = st.columns(2)
    with c1r:
        st.latex(r"m_b = " + f"{mb_dyn:.3f}")
        st.caption(f"Massiv ishqalanish burchagi funksiyasi ($m_i={mi_val}$)")
        st.latex(r"s = " + f"{s_dyn:.4f}")
        st.caption(f"Yoriqlilik darajasi (GSI={gsi_val})")
    with c2r:
        st.markdown(f"""
**Ilmiy izoh:** **Hoek & Brown (2018)** mezoniga ko'ra, $m_b$ va $s$
koeffitsiyentlari laboratoriya namunasining butunligini massivdagi yoriqlarga
nisbatini ko'rsatadi. Angren konida GSI={gsi_val} bo'lishi massivning o'rta
darajadagi blokli tuzilishga ega ekanligini va mustahkamligi laboratoriyaga
nisbatan **{((1-s_dyn)*100):.1f}%** ga pastligini anglatadi.
""")

with t2:
    st.subheader("2. Termo-Mexanik Koeffitsiyentlar Tahlili")
    st.table({
        "Parametr":         ["Elastiklik Moduli (E)", "Termal kengayish (α)", "Boshlang'ich T₀"],
        "Qiymat":           [f"{E_MODULUS} MPa",     f"{ALPHA_THERM} 1/°C", "20 °C"],
        "Tanlanish sababi": [
            "Ko'mir uchun xos o'rtacha deformatsiya koeffitsiyenti.",
            "Ko'mirning issiqlikdan chiziqli kengayish ko'rsatkichi (Yang, 2010).",
            "Kon qatlamining boshlang'ich tabiiy harorati."
        ]
    })
    st.markdown("**A) Termal UCS pasayishi:**")
    st.latex(r"\sigma_{ci(T)} = \sigma_{ci(0)} \cdot e^{-\beta(T-T_0)} = "
             + f"{ucs_t_dyn:.2f}" + r" \text{ MPa}")
    st.write(f"**Interpretatsiya:** {T_source_max}°C haroratda jins mustahkamligi "
             f"{((1 - ucs_t_dyn/ucs_0_r)*100):.1f}% ga pasaydi.")
    st.markdown("**B) Termal kuchlanish ($\\sigma_{th}$):**")
    st.latex(r"\sigma_{th} \approx \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu} = "
             + f"{sigma_thermal.max():.2f}" + r" \text{ MPa}")

with t3:
    st.subheader("3. Selek Barqarorligi va Bibliografiya")
    st.latex(r"FOS = \frac{\sigma_p}{\sigma_v} = " + f"{fos_final:.2f}")
    st.write("**Wilson (1972) Yield Pillar nazariyasiga binoan:**")
    st.write(f"Selek o'lchami $w={rec_width}$ m bo'lganda, uning markaziy yadrosi "
             f"{sigma_v_tot:.2f} MPa lik geostatik yukni ko'tarishga qodir. "
             f"Plastik zona: $y = {y_zone:.1f}$ m.")
    st.markdown("---")
    st.write("#### 📚 Asosiy Ilmiy Manbalar:")
    for ref in [
        "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*.",
        "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft.",
        "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*.",
        "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*."
    ]:
        st.markdown(f"📖 {ref}")

    if fos_final < 1.3:
        st.error(f"🔴 **Ilmiy Xulosa:** FOS={fos_final:.2f}. Termal degradatsiya yuqori. "
                 f"Selek enini oshirish yoki gazlashtirish tezligini nazorat qilish tavsiya etiladi.")
    else:
        st.success(f"🟢 **Ilmiy Xulosa:** FOS={fos_final:.2f}. "
                   f"Tanlangan parametrlar massiv barqarorligini ta'minlaydi.")

st.markdown("---")
with st.expander("📚 Ilmiy Metodologiya va Manbalar (PhD Research References)"):
    st.markdown("#### Ushbu model quyidagi fundamental ilmiy ishlar asosida tuzilgan:")
    for r in [
        "1. **Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI.",
        "2. **Yang, D. (2010).** Stability of underground coal gasification. PhD Thesis.",
        "3. **Shao, S. et al. (2015).** A thermal damage constitutive model for rock.",
        "4. **Cui, X. et al. (2017).** Permeability evolution of coal under thermal-mechanical coupling.",
        "5. **Kratzsch, H. (2012).** Mining Subsidence Engineering.",
        "6. **Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics for Underground Mining."
    ]:
        st.write(r)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
