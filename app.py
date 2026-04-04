import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
try:
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    st.error("Scikit-learn kutubxonasi topilmadi. Terminalda 'pip install scikit-learn' buyrug'ini bering.")

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor Pro", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Pro Edition: PDE Heat, Darcy Flow & AI Optimization")

# ==============================================================================
# --- ⚙️ SIDEBAR PARAMETRLAR ---
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("💎 Jins va Termal")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.7)
beta_thermal = st.sidebar.number_input("Thermal Decay (β):", value=0.0035, format="%.4f")
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

layers_data = []
total_depth = 0
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == num_layers-1)):
        name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"n_{i}")
        thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
        u = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
        rho = st.number_input(f"Zichlik (kg/m³):", value=2500, key=f"rho_{i}")
        g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
        m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'rho': rho, 'gsi': g, 'mi': m, 'color': strata_colors[i%5], 'z_start': total_depth})
        total_depth += thick

# ==============================================================================
# --- 🧮 PDE VA GEOMEXANIK HISOB-KITOBLAR ---
# ==============================================================================
# Grid yaratish
x_axis = np.linspace(-total_depth, total_depth, 100)
z_axis = np.linspace(0, total_depth + 20, 80)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']
ucs_seam = layers_data[-1]['ucs']

# 1. 🔥 PDE HEAT SOLVER
def solve_heat_step(T, Q, alpha, dx, dt):
    Tn = T.copy()
    Tn[1:-1,1:-1] = T[1:-1,1:-1] + alpha * dt * (
        (T[2:,1:-1] - 2*T[1:-1,1:-1] + T[:-2,1:-1]) / dx**2 +
        (T[1:-1,2:] - 2*T[1:-1,1:-1] + T[1:-1,:-2]) / dx**2
    ) + Q[1:-1,1:-1]*dt
    return Tn

temp_2d = np.ones_like(grid_x) * 25.0
alpha_rock = 1.0e-6 
Q_source = np.zeros_like(temp_2d)
sources = {'1': -total_depth/3, '2': 0, '3': total_depth/3}
for sx in sources.values():
    dist_sq = (grid_x - sx)**2 + (grid_z - source_z)**2
    Q_source += 500 * np.exp(-dist_sq / 200)

# Simulyatsiya iteratsiyasi
for _ in range(15):
    temp_2d = solve_heat_step(temp_2d, Q_source * (time_h/150), alpha_rock, dx=2.0, dt=0.2)
temp_2d = np.clip(temp_2d, 25, T_source_max)

# 2. 🪨 STRESS VA FAILURE FIELD
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
grid_sigma_v = np.zeros_like(grid_z)

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data)-1: mask = grid_z >= layer['z_start']
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6

# Termal zarar va mustahkamlik pasayishi
damage = 1 - np.exp(-beta_thermal * (temp_2d - 25))
sigma_ci = grid_ucs * (1 - damage)
sigma1_act = grid_sigma_v * 1.2 # Soddalashtirilgan
sigma3_act = grid_sigma_v * 0.5

# Failure detection
void_mask_raw = (temp_2d > 800) | (sigma_ci < 5.0)
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.2) > 0.4
perm = 1e-15 * (1 + 100 * void_mask_permanent)

# 3. 💨 GAS FLOW (DARCY)
pressure = temp_2d * 10 
dp_dx = np.gradient(pressure, axis=1)
dp_dz = np.gradient(pressure, axis=0)
vx = -perm * dp_dx
vz = -perm * dp_dz

# 4. 🧠 AI MODEL (COLLAPSE PREDICTION)
try:
    X_train = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_train = void_mask_permanent.flatten().astype(int)
    rf_model = RandomForestRegressor(n_estimators=20, max_depth=8)
    rf_model.fit(X_train, y_train)
    collapse_pred = rf_model.predict(X_train).reshape(temp_2d.shape)
except:
    collapse_pred = void_mask_permanent.astype(float)

# 5. ⚙️ AUTO OPTIMIZATION (SELEK)
def objective(w):
    strength = (ucs_seam) * (w / H_seam)**0.5
    risk = np.mean(void_mask_permanent)
    return -(strength - 15 * risk)

opt_res = minimize(objective, x0=20.0, bounds=[(5, 100)])
optimal_width_ai = opt_res.x[0]

# ==============================================================================
# --- 📊 VIZUALIZATSIYA ---
# ==============================================================================
m1, m2, m3, m4 = st.columns(4)
m1.metric("Maks. Harorat", f"{temp_2d.max():.1f} °C")
m2.metric("O'rtacha Bosim", f"{pressure.mean():.1f} kPa")
m3.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m")
m4.metric("Risk Koeffitsiyenti", f"{np.mean(collapse_pred):.2f}")

fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                       subplot_titles=("PDE Harorat Maydoni va Gaz Oqimi", "AI Collapse Bashorati va FOS"))

# Row 1: Heatmap + Streamlines (Gas Flow)
fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', colorbar=dict(title="T °C", x=1.02, y=0.75, len=0.4)), row=1, col=1)

# Gas Flow Vectors (Cone)
skip = 7
fig_tm.add_trace(go.Cone(
    x=grid_x[::skip, ::skip].flatten(),
    y=np.zeros_like(grid_x[::skip, ::skip]).flatten(),
    z=grid_z[::skip, ::skip].flatten(),
    u=vx[::skip, ::skip].flatten(),
    v=np.zeros_like(vx[::skip, ::skip]).flatten(),
    w=vz[::skip, ::skip].flatten(),
    sizemode="scaled", sizeref=1.5, showscale=False, colorscale='Blues'
), row=1, col=1)

# Row 2: AI Collapse Prediction
fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.7, colorbar=dict(title="Risk", x=1.02, y=0.25, len=0.4)), row=2, col=1)

# Selek chizmasi
for px in [-total_depth/6, total_depth/6]:
    fig_tm.add_shape(type="rect", x0=px-optimal_width_ai/2, x1=px+optimal_width_ai/2, 
                     y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)

fig_tm.update_layout(height=800, template="plotly_dark", showlegend=False)
fig_tm.update_yaxes(autorange='reversed')
st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
