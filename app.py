import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize

# --- ML kutubxonasini tekshirish ---
try:
    from sklearn.ensemble import RandomForestRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor AI", layout="wide")

if not SKLEARN_AVAILABLE:
    st.warning("⚠️ 'scikit-learn' kutubxonasi topilmadi. AI funksiyalari cheklangan rejimda ishlaydi. 'pip install scikit-learn' buyrug'ini bering.")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi (AI & PDE)")
st.markdown("### Termo-Mexanik (TM) tahlil, Gaz Dinamikasi va AI Optimizatsiyasi")

# ==============================================================================
# --- 🧮 PDE FUNKSIYALARI ---
# ==============================================================================
def solve_heat_step(T, Q, alpha, dx, dt):
    Tn = T.copy()
    Tn[1:-1,1:-1] = T[1:-1,1:-1] + alpha * dt * (
        (T[2:,1:-1] - 2*T[1:-1,1:-1] + T[:-2,1:-1]) / dx**2 +
        (T[1:-1,2:] - 2*T[1:-1,1:-1] + T[1:-1,:-2]) / dx**2
    ) + Q[1:-1,1:-1]*dt
    return Tn

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 48)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, 0.5)

st.sidebar.subheader("🔥 Yonish va Termal")
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)
beta_thermal = st.sidebar.number_input("Thermal Decay (β):", value=0.0035, format="%.4f")

# Qatlamlar ma'lumotlari
layers_data = []
total_depth = 0
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari"):
        name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"n_{i}")
        thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
        u = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
        g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
        m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'rho': 2500, 'gsi': g, 'mi': m, 'color': strata_colors[i%5], 'z_start': total_depth})
        total_depth += thick

# --- HISOB-KITOBLAR ---
x_axis = np.linspace(-total_depth*1.2, total_depth*1.2, 100)
z_axis = np.linspace(0, total_depth + 20, 80)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']
ucs_seam = layers_data[-1]['ucs']

grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1: mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))

# --- PDE HEAT SOLVER ---
alpha_rock = 1.0e-6
temp_2d = np.ones_like(grid_x) * 25
Q_source = np.zeros_like(temp_2d)
for sx in [-total_depth/3, 0, total_depth/3]:
    dist_sq = (grid_x - sx)**2 + (grid_z - source_z)**2
    Q_source += 600 * np.exp(-dist_sq / 300)

for _ in range(min(int(time_h), 25)):
    temp_2d = solve_heat_step(temp_2d, Q_source, alpha_rock, dx=2.5, dt=0.2)

# --- TM ANALIZ ---
damage = 1 - np.exp(-0.002 * (temp_2d - 100).clip(0))
sigma_ci = grid_ucs * (1 - damage)
sigma_thermal = 0.7 * (5000 * 1e-5 * (temp_2d - 25)) / (1 - nu_poisson)
sigma1_act = np.maximum(grid_sigma_v, (k_ratio * grid_sigma_v) - sigma_thermal)
sigma3_act = np.minimum(grid_sigma_v, (k_ratio * grid_sigma_v) - sigma_thermal)

void_mask = (temp_2d > 900) | (sigma1_act > (sigma3_act.clip(0.1) + sigma_ci * (grid_mb * sigma3_act.clip(0.1) / sigma_ci + grid_s_hb)**grid_a_hb))
void_mask_permanent = gaussian_filter(void_mask.astype(float), sigma=1.2) > 0.4

# --- 💨 GAS FLOW (DARCY) ---
perm = 1e-15 * (1 + 30 * damage + 100 * void_mask_permanent)
pressure = temp_2d * 10 
dp_dx, dp_dz = np.gradient(pressure)
vx = -perm * dp_dx
vz = -perm * dp_dz

# --- 🧠 AI MODEL ---
if SKLEARN_AVAILABLE:
    try:
        X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
        y_ai = void_mask_permanent.flatten().astype(int)
        rf_model = RandomForestRegressor(n_estimators=15, max_depth=6)
        rf_model.fit(X_ai[::15], y_ai[::15])
        collapse_pred = rf_model.predict(X_ai).reshape(temp_2d.shape)
    except:
        collapse_pred = void_mask_permanent.astype(float)
else:
    collapse_pred = void_mask_permanent.astype(float)

# --- ⚙️ OPTIMIZATION ---
def objective_w(w):
    strength = (ucs_seam * np.exp(-0.0025 * (T_source_max-25))) * (w / H_seam)**0.5
    return -(strength - 25 * np.mean(void_mask_permanent))

opt_res = minimize(objective_w, x0=25, bounds=[(10, 80)])
optimal_width_ai = opt_res.x[0]

# --- VIZUALIZATSIYA ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Max Temp", f"{temp_2d.max():.0f} °C")
col2.metric("O'tkazuvchanlik", f"{perm.max():.1e} m²")
col3.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m")
col4.metric("O'pirilish xavfi", f"{np.mean(collapse_pred)*100:.1f} %")

st.markdown("---")
fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=("Harorat va Gaz Oqimi", "O'pirilish Xavfi (AI)"))

# 1-Grafik: Harorat + Gas Flow
fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', colorbar=dict(title="Temp", x=1.02, y=0.75, len=0.4)), row=1, col=1)

s = 6 # Skip points for vectors
fig_tm.add_trace(go.Cone(
    x=grid_x[::s, ::s].flatten(),
    y=np.zeros_like(grid_x[::s, ::s].flatten()), # Y doimo 0 (2D tekislik uchun)
    z=grid_z[::s, ::s].flatten(),
    u=vx[::s, ::s].flatten(),
    v=np.zeros_like(vx[::s, ::s].flatten()), # V doimo 0
    w=vz[::s, ::s].flatten(),
    sizemode="scaled", sizeref=3, showscale=False, colorscale='Blues'
), row=1, col=1)

# 2-Grafik: AI Risk
fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', colorbar=dict(title="Risk", x=1.02, y=0.25, len=0.4)), row=2, col=1)

# Selek chizmasi (Optimal eni ko'rsatish)
fig_tm.add_shape(type="rect", x0=-optimal_width_ai/2, x1=optimal_width_ai/2, 
                 y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)

fig_tm.update_yaxes(autorange='reversed')
fig_tm.update_layout(height=850, template="plotly_dark", showlegend=False)
st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
