import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize

# =========================== PYTORCH (agar mavjud bo'lsa) ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
except ImportError:
    PT_AVAILABLE = False
    st.warning("⚠️ PyTorch o'rnatilmagan. RandomForestClassifier ishlatiladi.")
    from sklearn.ensemble import RandomForestClassifier

# =========================== XAVFSIZLIK UCHUN KICHIK SON ===========================
EPS = 1e-12

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")
st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# --- 🧮 MATEMATIK METODOLOGIYA (o'zgarishsiz) ---
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
# --- ⚙️ SIDEBAR: PARAMETRLAR ---
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
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

# =========================== TIMELINE (LOYIHA BOSQICHLARI) ===========================
with st.sidebar.expander("📅 Loyiha bosqichlari (Timeline)"):
    st.markdown("""
| Bosqich | Vaqti | Tavsif |
|---------|-------|--------|
| **Rejalashtirish** | 2026-04-01 | Validatsiya, xavfsiz bo‘lish funksiyalarini ishlab chiqish |
| **Modellarni optimallashtirish** | 2026-05-15 | NN/RF testlash, FDM yaxshilash, keshlashtirish |
| **Integratsiya va testlash** | 2026-06-30 | Unit testlar, yakuniy vizualizatsiya, deploy |
    """)

# ==============================================================================
# --- QATLAM MA'LUMOTLARINI YIG'ISH ---
# ==============================================================================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data   = []
total_depth   = 0.0

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers) - 1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name  = st.text_input("Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input("Qalinlik (m):", value=50.0, key=f"t_{i}")
            u     = st.number_input("UCS (MPa):", value=40.0, key=f"u_{i}")
            rho   = st.number_input("Zichlik (kg/m³):", value=2500.0, key=f"rho_{i}")
        with col2:
            color = st.color_picker("Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g     = st.slider("GSI:", 10, 100, 60, key=f"g_{i}")
            m     = st.number_input("mi:", value=10.0, key=f"m_{i}")
        s_t0_val = st.number_input("σt0 (MPa):", value=3.0, key=f"st_{i}") if tensile_mode == "Manual" else 0.0

    layers_data.append({
        'name': name, 't': thick, 'ucs': u, 'rho': rho,
        'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
        'sigma_t0_manual': s_t0_val
    })
    total_depth += thick

# =========================== QATLAM VALIDATSIYASI ===========================
def validate_layer(layer: dict) -> list:
    errors = []
    if layer['t'] <= 0:
        errors.append("Qalinlik >0 bo‘lishi kerak")
    if layer['ucs'] <= 0:
        errors.append("UCS >0 MPa bo‘lishi kerak")
    if layer['rho'] <= 0:
        errors.append("Zichlik >0 kg/m³ bo‘lishi kerak")
    if not (10 <= layer['gsi'] <= 100):
        errors.append("GSI 10...100 oralig‘ida bo‘lishi kerak")
    if layer['mi'] <= 0:
        errors.append("mi >0 bo‘lishi kerak")
    return errors

for idx, lyr in enumerate(layers_data):
    errs = validate_layer(lyr)
    if errs:
        st.error(f"❌ {lyr['name']} qatlamida xato: {', '.join(errs)}")
        st.stop()

if not layers_data:
    st.error("❌ Kamida 1 ta qatlam kiriting!")
    st.stop()

# ==============================================================================
# --- 📐 GRID VA MANBA HISOB-KITOBLARI (xavfsiz bo'lish qo'shilgan) ---
# ==============================================================================
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

if ('max_temp_map' not in st.session_state
        or st.session_state.max_temp_map.shape != grid_z.shape):
    st.session_state.max_temp_map  = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name
elif st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map  = np.ones_like(grid_z) * 25
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
    grid_a_hb[mask]    = 0.5 + (1 / 6) * (np.exp(-layer['gsi'] / 15) - np.exp(-20 / 3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

alpha_rock = 1.0e-6
sources = {
    '1': {'x': -total_depth / 3, 'start': 0},
    '2': {'x': 0,                'start': 40},
    '3': {'x':  total_depth / 3, 'start': 80},
}
temp_2d = np.ones_like(grid_x) * 25.0

for key, val in sources.items():
    if time_h > val['start']:
        dt_sec    = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
        elapsed   = time_h - val['start']
        curr_T    = (T_source_max if elapsed <= burn_duration
                     else 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration)))
        dist_sq   = (grid_x - val['x']) ** 2 + (grid_z - source_z) ** 2
        temp_2d  += (curr_T - 25) * np.exp(-dist_sq / (pen_depth ** 2 + 15 ** 2))

# ==============================================================================
# --- 🔥 PDE HEAT SOLVER (FDM) ---
# ==============================================================================
def solve_heat_step(T: np.ndarray, Q: np.ndarray, alpha: float, dx: float, dt: float) -> np.ndarray:
    Tn = T.copy()
    Tn[1:-1, 1:-1] = (
        T[1:-1, 1:-1]
        + alpha * dt * (
            (T[2:,  1:-1] - 2 * T[1:-1, 1:-1] + T[:-2, 1:-1]) / (dx ** 2 + EPS)
            + (T[1:-1, 2:] - 2 * T[1:-1, 1:-1] + T[1:-1, :-2]) / (dx ** 2 + EPS)
        )
        + Q[1:-1, 1:-1] * dt
    )
    return Tn

Q_heat = np.zeros_like(temp_2d)
for val in sources.values():
    if time_h > val['start']:
        cx, cz   = val['x'], source_z
        elapsed  = time_h - val['start']
        curr_T   = (T_source_max if elapsed <= burn_duration
                    else 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration)))
        Q_heat  += (curr_T / 10.0) * np.exp(-((grid_x - cx) ** 2 + (grid_z - cz) ** 2) / (2 * 30 ** 2))

DX, DT, N_STEPS = 1.0, 0.1, 20
for _ in range(N_STEPS):
    temp_2d = solve_heat_step(temp_2d, Q_heat, alpha_rock, dx=DX, dt=DT)

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25.0

# ==============================================================================
# --- 🧱 TM TAHLIL: KUCHLANISH, DAMAGE, FAILURE (xavfsiz bo'lish qo'shilgan) ---
# ==============================================================================
temp_eff  = np.maximum(st.session_state.max_temp_map - 100, 0)
damage    = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
sigma_ci  = grid_ucs * (1 - damage)

E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)

sigma_thermal  = CONSTRAINT_FACTOR * (E_MODULUS * ALPHA_T_COEFF * delta_T) / (1 - nu_poisson + EPS)
sigma_thermal += 0.3 * thermal_gradient

grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act   = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act   = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb + EPS)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field     = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
thermal_boost     = 1 + 0.6 * (1 - np.exp(-delta_T / 200))
sigma_t_field_eff = sigma_t_field / (thermal_boost + EPS)

tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50) & (sigma1_act > sigma3_act)
sigma3_safe     = np.maximum(sigma3_act, 0.01)
sigma1_limit    = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + EPS) + grid_s_hb) ** grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > 400)
crushing  = shear_failure  & (temp_2d > 600)

depth_factor     = np.exp(-grid_z / (total_depth + EPS))
local_collapse_T = np.clip((st.session_state.max_temp_map - 600) / 300, 0, 1)
time_factor      = np.clip((time_h - 40) / 60, 0, 1)
collapse_final   = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw       = spalling | crushing | (st.session_state.max_temp_map > 900)
void_mask_smooth    = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth > 0.3) & (collapse_final > 0.05)

perm        = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent.astype(float))
void_volume = np.sum(void_mask_permanent) * (x_axis[1] - x_axis[0]) * (z_axis[1] - z_axis[0])

sigma1_act = np.where(void_mask_permanent, 0.0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0.0, sigma3_act)
sigma_ci   = np.where(void_mask_permanent, 0.01, sigma_ci)

# ==============================================================================
# --- 💨 GAS FLOW (DARCY QONUNI) ---
# ==============================================================================
pressure     = temp_2d * 10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx, vz       = -perm * dp_dx, -perm * dp_dz
gas_velocity = np.sqrt(vx**2 + vz**2)

# ==============================================================================
# --- 🧠 AI MODEL — Neural Network (PyTorch) ---
# ==============================================================================
@st.cache_resource(show_spinner=False)
def get_nn_model():
    """PyTorch modelini yaratish va o'qitish (faqat bir marta)"""
    if not PT_AVAILABLE:
        return None

    def generate_ucg_dataset(n=10000):
        data = []
        for _ in range(n):
            T = np.random.uniform(20, 1000)
            sigma1 = np.random.uniform(0, 50)
            sigma3 = np.random.uniform(0, 30)
            depth = np.random.uniform(0, 300)
            damage = 1 - np.exp(-0.002 * max(T - 100, 0))
            strength = 40 * (1 - damage)
            collapse = 1 if (sigma1 > strength or T > 700) else 0
            data.append([T, sigma1, sigma3, depth, collapse])
        return np.array(data)

    class CollapseNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(4, 32),
                nn.ReLU(),
                nn.Linear(32, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
                nn.Sigmoid()
            )
        def forward(self, x):
            return self.net(x)

    data = generate_ucg_dataset()
    X = torch.tensor(data[:, :-1], dtype=torch.float32)
    y = torch.tensor(data[:, -1], dtype=torch.float32).view(-1, 1)

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
        st.warning(f"PyTorch modelida xatolik: {e}. RandomForest ishlatiladi.")
        nn_model = None

if nn_model is None or not PT_AVAILABLE:
    from sklearn.ensemble import RandomForestClassifier
    X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_ai = void_mask_permanent.flatten().astype(int)
    if len(np.unique(y_ai)) > 1:
        rf_model = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
        rf_model.fit(X_ai, y_ai)
        collapse_pred = rf_model.predict_proba(X_ai)[:, 1].reshape(temp_2d.shape)
    else:
        collapse_pred = np.zeros_like(temp_2d)

# ==============================================================================
# --- ⚙️ SELEK OPTIMIZATSIYASI (xavfsiz bo'lish qo'shilgan) ---
# ==============================================================================
avg_t_p      = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam     = layers_data[-1]['ucs']
sv_seam      = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0
for _ in range(15):
    p_strength  = (ucs_seam * strength_red) * (w_sol / (H_seam + EPS)) ** 0.5
    y_zone_calc = (H_seam / 2) * (np.sqrt(sv_seam / (p_strength + EPS)) - 1)
    new_w       = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1:
        break
    w_sol = new_w

rec_width       = np.round(w_sol, 1)
pillar_strength = p_strength
y_zone          = max(y_zone_calc, 1.5)

fos_2d = np.clip(sigma1_limit / (sigma1_act + EPS), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0.0, fos_2d)

void_frac_base = float(np.mean(void_mask_permanent))

def objective(w_arr: np.ndarray) -> float:
    w = w_arr[0]
    strength = (ucs_seam * strength_red) * (w / (H_seam + EPS)) ** 0.5
    risk = void_frac_base * np.exp(-0.01 * (w - rec_width))
    return -(strength - 15.0 * risk)

opt_result       = minimize(objective, x0=[rec_width], bounds=[(5.0, 100.0)], method='SLSQP')
optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))

# ==============================================================================
# --- 📊 METRIKALAR ---
# ==============================================================================
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)",     f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi",         f"{void_volume:.1f} m²")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("AI Tavsiya (Selek)",   f"{optimal_width_ai:.1f} m",
          delta=f"Klassik: {rec_width} m", delta_color="off")

# ==============================================================================
# --- 📈 CHO'KISH VA HOEK-BROWN GRAFIKALARI ---
# ==============================================================================
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

s_max  = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p  = -s_max * np.exp(-(x_axis ** 2) / (2 * (total_depth / 2) ** 2))
uplift = (total_depth * 1e-4) * np.exp(-(x_axis ** 2) / (total_depth * 10)) * (time_h / 150) * 100

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
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20      = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + EPS) + s_s) ** a_s
    ucs_burn   = ucs_seam * np.exp(-0.0025 * (T_source_max - 20))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + EPS) + s_s) ** a_s
    s1_sov     = sigma3_ax + (ucs_seam * strength_red) * (
        mb_s * sigma3_ax / (ucs_seam * strength_red + EPS) + s_s) ** a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20,      name='20°C',        line=dict(color='red',    width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov,     name='Zararlangan', line=dict(color='cyan',   width=2, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish',      line=dict(color='orange', width=4)))
    st.plotly_chart(
        fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300,
                             legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")),
        use_container_width=True
    )

# ==============================================================================
# --- 🔥 TM MAYDONI (fig_tm) ---
# ==============================================================================
st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("📋 Ilmiy Tahlil")
    st.error("🔴 FOS < 1.0: Failure")
    st.warning("🟡 FOS 1.0–1.5: Unstable")
    st.success("🟢 FOS > 1.5: Stable")
    fig_s = go.Figure()
    for lyr in layers_data:
        fig_s.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'],
                               marker_color=lyr['color'], width=0.4))
    st.plotly_chart(
        fig_s.update_layout(barmode='stack', template="plotly_dark",
                            yaxis=dict(autorange='reversed'), height=450, showlegend=False),
        use_container_width=True
    )

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi")

    fig_tm = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
        subplot_titles=(
            "Harorat Maydoni (°C) + Gaz Oqimi",
            "FOS + AI Collapse Prediction (NN) + Yielded Zones"
        )
    )

    # Harorat heatmap
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis,
        colorscale='Hot', zmin=25, zmax=T_source_max,
        colorbar=dict(title="T (°C)", title_side="top", x=1.05, y=0.78, len=0.42, thickness=15),
        name="Harorat"
    ), row=1, col=1)

    # Gaz oqimi
    step = 12
    qx, qz = grid_x[::step, ::step].flatten(), grid_z[::step, ::step].flatten()
    qu, qw = vx[::step, ::step].flatten(), vz[::step, ::step].flatten()
    qmag = gas_velocity[::step, ::step].flatten()
    qmag_max = qmag.max() + EPS
    threshold = qmag_max * 0.05
    mask_q = qmag > threshold
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q] + EPS))
    fig_tm.add_trace(go.Scatter(
        x=qx[mask_q], y=qz[mask_q], mode='markers',
        marker=dict(symbol='arrow', size=10, color=qmag[mask_q], colorscale='ice',
                    cmin=0, cmax=qmag_max, angle=angles, opacity=0.85, showscale=False,
                    line=dict(width=0)),
        name="Gaz oqimi", hovertemplate="x=%{x:.0f}m  z=%{z:.0f}m<extra></extra>"
    ), row=1, col=1)

    # FOS Contour
    fig_tm.add_trace(go.Contour(
        z=fos_2d, x=x_axis, y=z_axis,
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']],
        zmin=0, zmax=3.0, contours_showlines=False,
        colorbar=dict(title="FOS", title_side="top", x=1.05, y=0.22, len=0.42, thickness=15),
        name="FOS"
    ), row=2, col=1)

    # Void (qora)
    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=void_visual, x=x_axis, y=z_axis,
        colorscale=[[0, 'black'], [1, 'black']], showscale=False, opacity=0.9, hoverinfo='skip'
    ), row=2, col=1)

    # Void kontur chegarasi
    fig_tm.add_trace(go.Contour(
        z=void_mask_permanent.astype(int), x=x_axis, y=z_axis,
        showscale=False, contours=dict(coloring='lines'), line=dict(color='white', width=2), hoverinfo='skip'
    ), row=2, col=1)

    # Failure nuqtalari
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

    # Selek to'rtburchagi
    for px in [(sources['1']['x'] + sources['2']['x']) / 2,
               (sources['2']['x'] + sources['3']['x']) / 2]:
        fig_tm.add_shape(
            type="rect", x0=px - rec_width/2, x1=px + rec_width/2,
            y0=source_z - H_seam/2, y1=source_z + H_seam/2,
            line=dict(color="lime", width=3), row=2, col=1
        )

    # AI Collapse Prediction
    fig_tm.add_trace(go.Heatmap(
        z=collapse_pred, x=x_axis, y=z_axis,
        colorscale='Viridis', opacity=0.4, showscale=False, name='AI Collapse (NN)'
    ), row=2, col=1)

    fig_tm.update_layout(
        template="plotly_dark", height=850, margin=dict(r=150, t=80, b=100),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# ==============================================================================
# --- 📊 KOMPLEKS MONITORING PANELI ---
# ==============================================================================
st.header(f"📊 {obj_name}: Kompleks Monitoring Paneli")

def calculate_live_metrics(h, layers, T_max):
    target    = layers[-1]
    ucs_0     = target['ucs']
    H_l       = target['t']
    curr_T    = (25 + (T_max - 25) * (min(h, 40) / 40) if h <= 40 else T_max * np.exp(-0.001 * (h - 40)))
    str_red   = np.exp(-0.0025 * (curr_T - 20))
    w_rec     = 15.0 + (h / 150) * 10
    p_str     = (ucs_0 * str_red) * (w_rec / (H_l + EPS)) ** 0.5
    max_sub   = (H_l * 0.05) * (min(h, 120) / 120)
    return p_str, w_rec, curr_T, max_sub

p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max)

mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric("Pillar Strength", f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric("Tavsiya: Selek Eni", f"{w_rec_live:.1f} m")
mk3.metric("Maks. Cho'kish", f"{s_max_3d * 100:.1f} cm")
mk4.metric("Jarayon bosqichi", "Faol" if time_h < 100 else "Sovish")

st.markdown("---")

def generate_realistic_3d_split(temp_field, x_coords, z_coords, total_depth, source_z, H_seam, time_h, T_max):
    """
    Realistik 3D model:
    - Blokli geologik muhit (strata va ko'mir alohida bloklar)
    - Haqiqiy harorat izosirtlari (isosurface) – 400°C va 800°C
    - Yonish kamerasi (silindr)
    - Model o'rtasidan kesilgan (y >= 0 qismi ko'rinadi)
    """
    import plotly.graph_objects as go
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator

    # 1. 3D harorat maydonini yaratish (temp_2d -> 3D, Y o'qi bo'ylab simmetrik)
    y_axis = np.linspace(-80, 80, 30)  # Y o'qi uchun tarmoq
    # Interpolator tayyorlash (x, z) -> T
    interp_T = RegularGridInterpolator((x_coords, z_coords), temp_field.T, bounds_error=False, fill_value=25)
    # 3D grid yaratish
    X3, Y3, Z3 = np.meshgrid(x_coords, y_axis, z_coords, indexing='ij')
    # Faqat y >= 0 nuqtalar uchun harorat hisoblaymiz (kesik effekti)
    T3 = np.zeros_like(X3)
    # Faqat y >= 0 uchun hisoblash (tezlik uchun)
    mask_y = Y3 >= 0
    points = np.stack([X3[mask_y], Z3[mask_y]], axis=-1)
    T3[mask_y] = interp_T(points).flatten()
    T3[~mask_y] = np.nan  # y < 0 qismi ko'rinmaydi

    fig = go.Figure()

    # 2. Harorat izosirtlari (400°C va 800°C)
    for temp_val, color, opacity in [(400, 'red', 0.6), (800, 'orange', 0.4)]:
        try:
            fig.add_trace(go.Isosurface(
                x=X3.flatten(), y=Y3.flatten(), z=Z3.flatten(),
                value=T3.flatten(), isomin=temp_val, isomax=temp_val,
                caps=dict(x_show=False, y_show=False, z_show=False),
                surface_count=1, colorscale=[[0, color], [1, color]],
                opacity=opacity, showscale=False, name=f"{temp_val}°C izosirt"
            ))
        except:
            pass  # agar izosirt topilmasa

    # 3. Blokli geologik muhit (to'rtburchak bloklar)
    # Yuqori qatlam bloki
    top_block = go.Mesh3d(
        x=[-120, 120, 120, -120, -120, 120, 120, -120],
        y=[0, 0, 80, 80, 0, 0, 80, 80],
        z=[0, 0, 0, 0, -40, -40, -40, -40],
        i=[0,0,0,1,1,2,2,3,4,4,4,5,5,6,6,7],
        j=[1,2,3,2,3,3,1,0,5,6,7,6,7,7,5,4],
        k=[2,3,1,3,1,1,0,1,6,7,5,7,5,5,4,5],
        color='#8B5A2B', opacity=0.7, name='Yuqori qatlam', showlegend=True
    )
    fig.add_trace(top_block)

    # Ko'mir bloki (markazda, qalinligi H_seam)
    coal_z_top = -total_depth + H_seam
    coal_z_bottom = -total_depth
    coal_block = go.Mesh3d(
        x=[-100, 100, 100, -100, -100, 100, 100, -100],
        y=[0, 0, 80, 80, 0, 0, 80, 80],
        z=[coal_z_top, coal_z_top, coal_z_top, coal_z_top, coal_z_bottom, coal_z_bottom, coal_z_bottom, coal_z_bottom],
        i=[0,0,0,1,1,2,2,3,4,4,4,5,5,6,6,7],
        j=[1,2,3,2,3,3,1,0,5,6,7,6,7,7,5,4],
        k=[2,3,1,3,1,1,0,1,6,7,5,7,5,5,4,5],
        color='darkorange', opacity=0.9, name='Ko\'mir qatlami', showlegend=True
    )
    fig.add_trace(coal_block)

    # 4. Yonish kamerasi (silindr, faqat y>=0 qismi)
    reactor_radius = min(H_seam * 0.4, 6.0)
    reactor_length = 60.0
    theta = np.linspace(0, 2*np.pi, 20)
    z_cyl = np.linspace(-reactor_length, reactor_length, 20)
    theta, z_cyl = np.meshgrid(theta, z_cyl)
    x_cyl = reactor_radius * np.cos(theta)
    y_cyl = reactor_radius * np.sin(theta)
    # Silindr markazi (0, 0, coal_z_center)
    coal_z_center = (coal_z_top + coal_z_bottom) / 2
    x_cyl += 0
    y_cyl += 0
    z_cyl_surf = z_cyl + coal_z_center
    # Faqat y>=0 qismini ko'rsatish
    mask_cyl = y_cyl >= 0
    fig.add_trace(go.Surface(
        x=x_cyl[mask_cyl], y=y_cyl[mask_cyl], z=z_cyl_surf[mask_cyl],
        colorscale='Hot', opacity=0.95, name="Yonish kamerasi", showscale=False,
        lighting=dict(ambient=0.3, diffuse=0.9)
    ))

    # 5. Gaz oqimi chiziqlari (bir necha yo'nalish)
    # Foydalanuvchi tomonidan hisoblangan gaz oqimi vx, vz dan foydalanish mumkin, lekin bu funksiyaga uzatish kerak.
    # Oddiy simulyatsiya uchun bir necha chiziq qo'shamiz:
    flow_lines = [
        [[0, 10, coal_z_center], [0, 30, coal_z_center-10], [0, 50, coal_z_center-20]],
        [[-20, 10, coal_z_center], [-30, 30, coal_z_center-5], [-40, 50, coal_z_center-15]],
        [[20, 10, coal_z_center], [30, 30, coal_z_center-5], [40, 50, coal_z_center-15]],
    ]
    for line in flow_lines:
        fig.add_trace(go.Scatter3d(
            x=[p[0] for p in line], y=[p[1] for p in line], z=[p[2] for p in line],
            mode='lines', line=dict(color='cyan', width=4), name='Gaz oqimi', showlegend=False
        ))

    # 6. Kesik chizig'i (y=0 tekisligida qizil kontur)
    # Y=0 da bir necha nuqta chizamiz
    y0_line_x = np.linspace(-120, 120, 20)
    y0_line_z = np.linspace(-total_depth-10, 20, 20)
    fig.add_trace(go.Scatter3d(
        x=y0_line_x, y=np.zeros_like(y0_line_x), z=np.full_like(y0_line_x, 0),
        mode='lines', line=dict(color='red', width=2), name='Kesik chizig\'i', showlegend=True
    ))

    # 7. Grafik sozlamalari
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='black', gridcolor='gray'),
            yaxis=dict(title='Y (m)', backgroundcolor='black', gridcolor='gray',
                       range=[0, 80]),  # faqat y>=0 ko'rinadi
            zaxis=dict(title='Z (m)', backgroundcolor='black', gridcolor='gray',
                       range=[-total_depth-20, 20]),
            aspectmode='manual', aspectratio=dict(x=1.2, y=0.6, z=0.8),
            camera=dict(eye=dict(x=1.5, y=0.5, z=1.2))
        ),
        height=700, margin=dict(l=0, r=0, b=0, t=0),
        template='plotly_dark',
        title=f"Realistik 3D Model (Kesik ko'rinish, vaqt={time_h} soat)"
    )
    return fig

# ==============================================================================
# --- 📑 CHUQURLASHTIRILGAN ILMIY HISOBOT ---
# ==============================================================================
st.markdown("---")
st.header("🔍 Chuqurlashtirilgan Dinamik Tahlil va Metodik Asoslash")

E_MODULUS_R, ALPHA_THERM, BETA_CONST = 5000.0, 1.0e-5, beta_thermal
target_l = layers_data[-1]
ucs_0_r, gsi_val, mi_val = target_l['ucs'], target_l['gsi'], target_l['mi']
gamma_kn = target_l['rho'] * 9.81 / 1000
H_depth_tot = sum(l['t'] for l in layers_data[:-1]) + target_l['t'] / 2

sigma_v_tot = (gamma_kn * H_depth_tot) / 1000
mb_dyn = mi_val * np.exp((gsi_val - 100) / (28 - 14 * D_factor))
s_dyn  = np.exp((gsi_val - 100) / (9 - 3 * D_factor))
ucs_t_dyn = ucs_0_r * np.exp(-BETA_CONST * (T_source_max - 20))
p_str_final = ucs_t_dyn * (rec_width / (H_seam + EPS)) ** 0.5
fos_final = p_str_final / (sigma_v_tot + EPS)

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
nisbatini ko'rsatadi. GSI={gsi_val} bo'lishi massivning mustahkamligi
laboratoriyaga nisbatan **{((1 - s_dyn) * 100):.1f}%** ga pastligini anglatadi.
""")

with t2:
    st.subheader("2. Termo-Mexanik Koeffitsiyentlar Tahlili")
    params_df = pd.DataFrame({
        "Parametr":         ["Elastiklik Moduli (E)", "Termal kengayish (α)", "Boshlang'ich T₀"],
        "Qiymat":           [f"{E_MODULUS_R} MPa",   f"{ALPHA_THERM} 1/°C", "20 °C"],
        "Tanlanish sababi": [
            "Ko'mir uchun xos o'rtacha deformatsiya koeffitsiyenti.",
            "Ko'mirning issiqlikdan chiziqli kengayish ko'rsatkichi (Yang, 2010).",
            "Kon qatlamining boshlang'ich tabiiy harorati.",
        ]
    })
    st.table(params_df)
    st.markdown("**A) Termal UCS pasayishi:**")
    st.latex(r"\sigma_{ci(T)} = \sigma_{ci(0)} \cdot e^{-\beta(T-T_0)} = " + f"{ucs_t_dyn:.2f}" + r" \text{ MPa}")
    st.write(f"**Interpretatsiya:** {T_source_max}°C haroratda jins mustahkamligi {((1 - ucs_t_dyn / ucs_0_r) * 100):.1f}% ga pasaydi.")
    st.markdown("**B) Termal kuchlanish ($\\sigma_{th}$):**")
    st.latex(r"\sigma_{th} \approx \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu} = " + f"{sigma_thermal.max():.2f}" + r" \text{ MPa}")

with t3:
    st.subheader("3. Selek Barqarorligi va Bibliografiya")
    st.latex(r"FOS = \frac{\sigma_p}{\sigma_v} = " + f"{fos_final:.2f}")
    st.write(f"**Wilson (1972) Yield Pillar nazariyasiga binoan:**")
    st.write(f"Selek o'lchami $w={rec_width}$ m bo'lganda, uning markaziy yadrosi "
             f"{sigma_v_tot:.2f} MPa lik geostatik yukni ko'tarishga qodir. Plastik zona: $y = {y_zone:.1f}$ m.")
    st.markdown("---")
    st.write("#### 📚 Asosiy Ilmiy Manbalar:")
    for ref in [
        "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*.",
        "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft.",
        "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*.",
        "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*.",
    ]:
        st.markdown(f"📖 {ref}")
    if fos_final < 1.3:
        st.error(f"🔴 **Ilmiy Xulosa:** FOS={fos_final:.2f}. Termal degradatsiya yuqori. Selek enini oshirish yoki gazlashtirish tezligini nazorat qilish tavsiya etiladi.")
    else:
        st.success(f"🟢 **Ilmiy Xulosa:** FOS={fos_final:.2f}. Tanlangan parametrlar massiv barqarorligini ta'minlaydi.")

st.markdown("---")
with st.expander("📚 Ilmiy Metodologiya va Manbalar (PhD Research References)"):
    st.markdown("#### Ushbu model quyidagi fundamental ilmiy ishlar asosida tuzilgan:")
    for r in [
        "1. **Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI.",
        "2. **Yang, D. (2010).** Stability of underground coal gasification. PhD Thesis.",
        "3. **Shao, S. et al. (2015).** A thermal damage constitutive model for rock.",
        "4. **Cui, X. et al. (2017).** Permeability evolution of coal under thermal-mechanical coupling.",
        "5. **Kratzsch, H. (2012).** Mining Subsidence Engineering.",
        "6. **Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics for Underground Mining.",
    ]:
        st.write(r)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
