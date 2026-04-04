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
st.markdown("### 🔬 PhD Research: PDE Heat, Darcy Flow & AI Integration")

# ==============================================================================
# --- ⚙️ SIDEBAR PARAMETRLAR ---
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 48)
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
        thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
        u = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
        g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
        layers_data.append({'t': thick, 'ucs': u, 'gsi': g, 'color': strata_colors[i%5], 'z_start': total_depth})
        total_depth += thick

# ==============================================================================
# --- 🧮 HISOB-KITOBLAR (INTEGRATSIYA) ---
# ==============================================================================

# 1. Grid yaratish
x_axis = np.linspace(-total_depth*1.2, total_depth*1.2, 100)
z_axis = np.linspace(0, total_depth + 30, 80)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']
ucs_seam = layers_data[-1]['ucs']

# 2. 🔥 PDE HEAT SOLVER (UPGRADE)
def solve_heat_step(T, Q, alpha, dx, dt):
    Tn = T.copy()
    # Laplas operatori (2D issiqlik o'tkazuvchanlik)
    Tn[1:-1,1:-1] = T[1:-1,1:-1] + alpha * dt * (
        (T[2:,1:-1] - 2*T[1:-1,1:-1] + T[:-2,1:-1]) / dx**2 +
        (T[1:-1,2:] - 2*T[1:-1,1:-1] + T[1:-1,:-2]) / dx**2
    ) + Q[1:-1,1:-1]*dt
    return Tn

temp_2d = np.ones_like(grid_x) * 25.0
alpha_rock = 1.0e-6 
Q = np.zeros_like(temp_2d)
sources_x = [-total_depth/3, 0, total_depth/3]

for sx in sources_x:
    dist_sq = (grid_x - sx)**2 + (grid_z - source_z)**2
    Q += 500 * np.exp(-dist_sq / 200)

# Iterativ yechim
for _ in range(10):
    temp_2d = solve_heat_step(temp_2d, Q * (time_h/150), alpha_rock, dx=2.0, dt=0.2)
temp_2d = np.clip(temp_2d, 25, T_source_max)

# 3. 🪨 GEOMEXANIKA (Failure Fields)
grid_sigma_v = (2500 * 9.81 * grid_z) / 1e6
damage = 1 - np.exp(-beta_thermal * (temp_2d - 25))
sigma_ci = ucs_seam * (1 - damage)
sigma1_act = grid_sigma_v * 1.2
sigma3_act = grid_sigma_v * 0.5

void_mask_raw = (temp_2d > 850) | (sigma_ci < 5.0)
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.2) > 0.4

# 4. 💨 GAS FLOW (DARCY)
perm = 1e-15 * (1 + 100 * void_mask_permanent)
pressure = temp_2d * 10 
dp_dx = np.gradient(pressure, axis=1)
dp_dz = np.gradient(pressure, axis=0)
vx = -perm * dp_dx
vz = -perm * dp_dz

# 5. 🧠 AI MODEL (Collapse Prediction)
try:
    X_train = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
    y_train = void_mask_permanent.flatten().astype(int)
    rf_model = RandomForestRegressor(n_estimators=30, max_depth=10)
    rf_model.fit(X_train, y_train)
    collapse_pred = rf_model.predict(X_train).reshape(temp_2d.shape)
except:
    collapse_pred = void_mask_permanent.astype(float)

# 6. ⚙️ AUTO OPTIMIZATION (SELEK)
def objective(w):
    strength = (ucs_seam) * (w / H_seam)**0.5
    risk = np.mean(void_mask_permanent)
    return -(strength - 15 * risk)

opt = minimize(objective, x0=20.0, bounds=[(5, 100)])
optimal_width_ai = opt.x[0]

# ==============================================================================
# --- 📊 VIZUALIZATSIYA ---
# ==============================================================================
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Maks. Harorat", f"{temp_2d.max():.1f} °C")
m2.metric("O'pirilish xavfi", f"{np.mean(collapse_pred)*100:.1f} %")
m3.metric("Kamera Hajmi", f"{np.sum(void_mask_permanent):.1f} m²")
m4.metric("O'tkazuvchanlik", f"{np.max(perm):.1e}")
m5.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m")

fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                       subplot_titles=("PDE Harorat Maydoni va Gaz Oqimi", "AI Collapse Heatmap va Selek"))

# Top: Heatmap + Gas Flow (Quiver)
fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', colorbar=dict(title="T °C", x=1.02, y=0.78, len=0.4)), row=1, col=1)

skip = 7
x_v, z_v = grid_x[::skip, ::skip].flatten(), grid_z[::skip, ::skip].flatten()
u_v, w_v = vx[::skip, ::skip].flatten(), vz[::skip, ::skip].flatten()
mask = np.isfinite(u_v) & np.isfinite(w_v)
if np.any(mask):
    fig_tm.add_trace(go.Quiver(x=x_v[mask], y=z_v[mask], u=u_v[mask], v=w_v[mask], scale=0.1, line=dict(color='white', width=1)), row=1, col=1)

# Bottom: AI Prediction
fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', colorbar=dict(title="Risk", x=1.02, y=0.22, len=0.4)), row=2, col=1)

# Selek chizmasi
for px in [-total_depth/4, total_depth/4]:
    fig_tm.add_shape(type="rect", x0=px-optimal_width_ai/2, x1=px+optimal_width_ai/2, 
                     y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)

fig_tm.update_layout(height=800, template="plotly_dark", showlegend=False)
fig_tm.update_yaxes(autorange='reversed')
st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
