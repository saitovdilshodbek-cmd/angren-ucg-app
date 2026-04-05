import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
import pydeck as pdk
import torch
import torch.nn as nn

# ==============================================================================
# Sahifa sozlamalari
# ==============================================================================
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")
st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# GPU qo'llab-quvvatlash
# ==============================================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if device.type == "cuda":
    st.sidebar.success(f"✅ GPU ishlatilmoqda: {torch.cuda.get_device_name(0)}")
else:
    st.sidebar.info("⚠️ CPU ishlatilmoqda (GPU yo'q)")

# ==============================================================================
# Matematik metodologiya (qisqa holda, to'liq kodingizda saqlang)
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
        # ... (matematik formulalar, avvalgidek qoldiring)
        st.info("Ilmiy asos qismi to'liq kodingizda mavjud")

# ==============================================================================
# ⚙️ SIDEBAR: PARAMETRLAR
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name      = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h        = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers    = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)
tensile_mode  = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

# Real-time simulyatsiya
run_sim = st.sidebar.checkbox("▶️ Real-time ishga tushirish")
if run_sim:
    if "sim_time" not in st.session_state:
        st.session_state.sim_time = 1
    if st.session_state.sim_time <= time_h:
        time_h = st.session_state.sim_time
        st.session_state.sim_time += 1
        # Streamlit versiyasiga qarab rerun
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()
    else:
        st.session_state.sim_time = 1
        st.success("Simulyatsiya tugadi!")

# Fayl yuklash
uploaded_file = st.sidebar.file_uploader("📂 Real dataset yuklash (CSV)", type=["csv"])

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

# ==============================================================================
# Qatlam ma'lumotlarini yig'ish
# ==============================================================================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data   = []
total_depth   = 0.0

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
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

if not layers_data:
    st.error("❌ Kamida 1 ta qatlam kiriting!")
    st.stop()

# ==============================================================================
# GRID va MANBA
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

# Session state
if ('max_temp_map' not in st.session_state or
    st.session_state.max_temp_map.shape != grid_z.shape):
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name
elif st.session_state.get('last_obj_name') != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name

# Hoek-Brown qatlam bo'yicha
for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1:
        mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask]     = layer['ucs']
    grid_mb[mask]      = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask]    = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask]    = 0.5 + (1/6) * (np.exp(-layer['gsi']/15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

# ==============================================================================
# Issiqlik maydoni (Gaussian + FDM)
# ==============================================================================
alpha_rock = 1.0e-6
sources = {
    '1': {'x': -total_depth/3, 'start': 0},
    '2': {'x': 0,              'start': 40},
    '3': {'x':  total_depth/3, 'start': 80},
}
temp_2d = np.ones_like(grid_x) * 25.0

for key, val in sources.items():
    if time_h > val['start']:
        dt_sec    = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
        elapsed   = time_h - val['start']
        if elapsed <= burn_duration:
            curr_T = T_source_max
        else:
            curr_T = 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

# FDM (issiqlik diffuziyasi)
def solve_heat_step(T, Q, alpha, dx, dt):
    Tn = T.copy()
    Tn[1:-1, 1:-1] = (T[1:-1, 1:-1] +
                      alpha * dt * ((T[2:, 1:-1] - 2*T[1:-1, 1:-1] + T[:-2, 1:-1]) / dx**2 +
                                    (T[1:-1, 2:] - 2*T[1:-1, 1:-1] + T[1:-1, :-2]) / dx**2) +
                      Q[1:-1, 1:-1] * dt)
    return Tn

Q_heat = np.zeros_like(temp_2d)
for val in sources.values():
    if time_h > val['start']:
        cx, cz = val['x'], source_z
        elapsed = time_h - val['start']
        if elapsed <= burn_duration:
            curr_T = T_source_max
        else:
            curr_T = 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration))
        Q_heat += (curr_T / 10.0) * np.exp(-((grid_x - cx)**2 + (grid_z - cz)**2) / (2 * 30**2))

DX, DT, N_STEPS = 1.0, 0.1, 20
for _ in range(N_STEPS):
    temp_2d = solve_heat_step(temp_2d, Q_heat, alpha_rock, DX, DT)

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25.0

# ==============================================================================
# TM TAHLIL: KUCHLANISH, DAMAGE, FAILURE
# ==============================================================================
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage   = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1.0e-5, 0.7
dT_dx = np.gradient(temp_2d, axis=1)
dT_dz = np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)

sigma_thermal = CONSTRAINT_FACTOR * (E_MODULUS * ALPHA_T_COEFF * delta_T) / (1 - nu_poisson)
sigma_thermal += 0.3 * thermal_gradient

grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
thermal_boost = 1 + 0.6 * (1 - np.exp(-delta_T / 200))
sigma_t_field_eff = sigma_t_field / thermal_boost

tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50) & (sigma1_act > sigma3_act)
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + 1e-6) + grid_s_hb) ** grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > 400)
crushing = shear_failure & (temp_2d > 600)

depth_factor = np.exp(-grid_z / total_depth)
local_collapse_T = np.clip((st.session_state.max_temp_map - 600) / 300, 0, 1)
time_factor = np.clip((time_h - 40) / 60, 0, 1)
collapse_final = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw = spalling | crushing | (st.session_state.max_temp_map > 900)
void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth > 0.3) & (collapse_final > 0.05)

perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent.astype(float))
void_volume = np.sum(void_mask_permanent) * (x_axis[1] - x_axis[0]) * (z_axis[1] - z_axis[0])

sigma1_act = np.where(void_mask_permanent, 0.0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0.0, sigma3_act)
sigma_ci   = np.where(void_mask_permanent, 0.01, sigma_ci)

# Gaz oqimi
pressure = temp_2d * 10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx = -perm * dp_dx
vz = -perm * dp_dz
gas_velocity = np.sqrt(vx**2 + vz**2)

# ==============================================================================
# 🧠 AI MODEL (PyTorch) — ENDI TO'G'RI JOYLASHTIRILDI
# ==============================================================================
@st.cache_resource(show_spinner=False)
def get_nn_model():
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
                nn.Linear(4, 32), nn.ReLU(),
                nn.Linear(32, 64), nn.ReLU(),
                nn.Linear(64, 1), nn.Sigmoid()
            )
        def forward(self, x): return self.net(x)

    data = generate_ucg_dataset()
    X = torch.tensor(data[:, :-1], dtype=torch.float32).to(device)
    y = torch.tensor(data[:, -1], dtype=torch.float32).view(-1, 1).to(device)

    model = CollapseNet().to(device)
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
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.reshape(temp.shape)

nn_model = get_nn_model()

# Agar real dataset yuklangan bo'lsa, qayta o'qitish
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if all(col in df.columns for col in ["T", "sigma1", "sigma3", "depth", "collapse"]):
        X_real = torch.tensor(df[["T", "sigma1", "sigma3", "depth"]].values, dtype=torch.float32).to(device)
        y_real = torch.tensor(df["collapse"].values, dtype=torch.float32).view(-1, 1).to(device)
        optimizer = torch.optim.Adam(nn_model.parameters(), lr=0.001)
        loss_fn = nn.BCELoss()
        for epoch in range(20):
            pred = nn_model(X_real)
            loss = loss_fn(pred, y_real)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        st.success("✅ Model real data bilan qayta o‘qitildi!")

# AI bashorat (endi barcha o'zgaruvchilar mavjud)
collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)

# ==============================================================================
# SELEK OPTIMIZATSIYASI
# ==============================================================================
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam * strength_red) * (w_sol / H_seam) ** 0.5
    y_zone_calc = (H_seam / 2) * (np.sqrt(sv_seam / (p_strength + 1e-6)) - 1)
    new_w = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1:
        break
    w_sol = new_w

rec_width = np.round(w_sol, 1)
pillar_strength = p_strength
y_zone = max(y_zone_calc, 1.5)

fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0.0, fos_2d)

void_frac_base = float(np.mean(void_mask_permanent))

def objective(w_arr):
    w = w_arr[0]
    strength = (ucs_seam * strength_red) * (w / H_seam) ** 0.5
    risk = void_frac_base * np.exp(-0.01 * (w - rec_width))
    return -(strength - 15.0 * risk)

opt_result = minimize(objective, x0=[rec_width], bounds=[(5.0, 100.0)], method='SLSQP')
optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))

# ==============================================================================
# METRIKALAR VA GRAFIKLAR (qisqa holda, asosiy ko'rinish)
# ==============================================================================
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi", f"{void_volume:.1f} m²")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m")

# Cho'kish grafiklari (qisqa)
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])
s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*10)) * (time_h/150) * 100
with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy')).update_layout(title="📉 Cho'kish (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy')).update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax/(ucs_seam+1e-6) + s_s)**a_s
    ucs_burn = ucs_seam * np.exp(-0.0025*(T_source_max-20))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax/(ucs_burn+1e-6) + s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam*strength_red) * (mb_s * sigma3_ax/(ucs_seam*strength_red+1e-6) + s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name='Zararlangan', line=dict(color='cyan', dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish', line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title="Hoek-Brown", template="plotly_dark", height=300), use_container_width=True)

# ==============================================================================
# 🔥 TM MAYDONI (2D heatmap + FOS + AI)
# ==============================================================================
st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader("📋 Qatlamlar kesimi")
    fig_s = go.Figure()
    for lyr in layers_data:
        fig_s.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'], marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)
with c2:
    st.subheader("🔥 TM Maydoni")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                           subplot_titles=("Harorat + Gaz oqimi", "FOS + AI Collapse"))
    # Harorat
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, name="Harorat"), row=1, col=1)
    # Gaz oqimi (vektorlar)
    step = 12
    qx, qz = grid_x[::step, ::step].flatten(), grid_z[::step, ::step].flatten()
    qu, qw = vx[::step, ::step].flatten(), vz[::step, ::step].flatten()
    qmag = gas_velocity[::step, ::step].flatten()
    mask_q = qmag > 0.05 * qmag.max()
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q]))
    fig_tm.add_trace(go.Scatter(x=qx[mask_q], y=qz[mask_q], mode='markers', marker=dict(symbol='arrow', size=8, angle=angles, color='cyan'), name="Gaz oqimi"), row=1, col=1)
    # FOS konturi
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale='RdYlGn', zmin=0, zmax=3.0, name="FOS"), row=2, col=1)
    # Void zonasi
    void_visual = np.where(void_mask_permanent, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis, colorscale='Greys', opacity=0.7, name="Void"), row=2, col=1)
    # AI Collapse
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name="AI Collapse"), row=2, col=1)
    # Selek to'rtburchagi
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=2), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=800)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# ==============================================================================
# Xarita va hisobot (YANGI)
# ==============================================================================
st.markdown("---")
st.subheader("🌍 Geolokatsiya xaritasi")
view_state = pdk.ViewState(latitude=41.2995, longitude=69.2401, zoom=10)
layer = pdk.Layer("ScatterplotLayer", data=pd.DataFrame({"lat":[41.2995], "lon":[69.2401], "name":[obj_name]}),
                  get_position='[lon, lat]', get_radius=500, get_color=[255,0,0], pickable=True)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text":"{name}"}))

if st.button("📄 Hisobot yuklab olish"):
    report = f"""
    LOYIHA: {obj_name}
    Vaqt: {time_h} soat
    Pillar Strength: {pillar_strength:.2f} MPa
    Plastik zona: {y_zone:.1f} m
    Kamera hajmi: {void_volume:.1f} m²
    O'rtacha collapse ehtimoli: {np.mean(collapse_pred):.3f}
    Tavsiya etilgan selek eni: {optimal_width_ai:.1f} m
    """
    st.download_button("⬇️ Yuklab olish", report, file_name=f"{obj_name}_report.txt")

# ==============================================================================
# Qolgan qismlar (3D, trendlar, ilmiy hisobot) — sizning asl kodingizga qo'shing
# ==============================================================================
st.markdown("---")
st.info("📌 3D model, trendlar va chuqur ilmiy hisobot asl kodingizda mavjud. Ushbu qisqa versiyada ular chiqarib tashlandi. To'liq versiya uchun yuqoridagi qismlarni o'z kodingizga qo'shing.")
