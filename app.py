
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")
-3
+31
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']
alpha_rock = 1.0e-6 
alpha_rock = 1.0e-6
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
temp_2d = np.ones_like(grid_x) * 25
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec) 
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
        curr_T = T_source_max if (time_h - val['start']) <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*((time_h-val['start'])-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))
# ==============================================================================
# --- 🔥 PDE HEAT SOLVER (UPGRADE) ---
# Gaussdan keyin iterativ aniqlashtirish: issiqlik tarqalishi tenglamasi (2D FDM)
# ==============================================================================
def solve_heat_step(T, Q, alpha, dx, dt):
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
# Issiqlik manbai (UCG kamera joylashuvi)
Q_heat = np.zeros_like(temp_2d)
for val in sources.values():
    cx_src = val['x']
    Q_heat += 500 * np.exp(-((grid_x - cx_src)**2 + (grid_z - source_z)**2) / 200)
# 10 ta iteratsiya bilan PDE yechimi (temp_2d ni aniqlashtiramiz)
for _ in range(10):
    temp_2d = solve_heat_step(temp_2d, Q_heat, alpha_rock, dx=1.0, dt=0.1)
# ==============================================================================
st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25
-2
+2
damage = np.clip(damage, 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)
E = 5000 
E = 5000
alpha_T_coeff = 1e-5
constraint_factor = 0.7 
constraint_factor = 0.7
dT_dx = np.gradient(temp_2d, axis=1)
dT_dz = np.gradient(temp_2d, axis=0)
-1
+37
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])
# ==============================================================================
# --- 💨 GAS FLOW (DARCY QONUNI) ---
# Bosim gradient asosida gaz oqim vektorlari
# ==============================================================================
pressure = temp_2d * 10  # Soddalashtirilgan: P ~ T*10 (Pa/MPa proporsionallik)
dp_dx_gas = np.gradient(pressure, axis=1)
dp_dz_gas = np.gradient(pressure, axis=0)
vx_gas = -perm * dp_dx_gas
vz_gas = -perm * dp_dz_gas
gas_velocity = np.sqrt(vx_gas**2 + vz_gas**2)
# ==============================================================================
sigma1_act = np.where(void_mask_permanent, 0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0, sigma3_act)
sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)
# --- Selek Optimizatsiyasi ---
# ==============================================================================
# --- 🧠 AI MODEL (RandomForest — Collapse Prediction) ---
# temp_2d, sigma1, sigma3, chuqurlik → void/collapse ehtimoli
# ==============================================================================
try:
    from sklearn.ensemble import RandomForestRegressor
    X_ai = np.column_stack([
        temp_2d.flatten(),
        sigma1_act.flatten(),
        sigma3_act.flatten(),
        grid_z.flatten()
    ])
    y_ai = void_mask_permanent.flatten().astype(int)
    rf_model = RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42)
    rf_model.fit(X_ai, y_ai)
    collapse_pred = rf_model.predict(X_ai).reshape(temp_2d.shape)
except Exception:
    collapse_pred = np.zeros_like(temp_2d)
# ==============================================================================
# --- Selek Optimizatsiyasi (klassik iteratsiya) ---
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
-0
+13
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0, fos_2d)
# ==============================================================================
# --- ⚙️ AUTO OPTIMIZATION (Scipy Minimize) ---
# Mustahkamlik va void xavfini muvozanatlash orqali optimal selek enini topish
# ==============================================================================
def objective(w):
    strength = ucs_seam * (w[0] / H_seam)**0.5
    risk = np.mean(void_mask_permanent)
    return -(strength - 15 * risk)
opt_result = minimize(objective, x0=[rec_width], bounds=[(5, 100)])
optimal_width_ai = float(np.clip(opt_result.x[0], 5, 100))
# ==============================================================================
# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
-1
+2
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi", f"{void_volume:.1f} m³")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("TAVSIYA: Selek Eni", f"{rec_width} m")
m5.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m",
          delta=f"Klassik: {rec_width} m", delta_color="off")
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])
-1
+1
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name='Zararlangan', line=dict(color='cyan', dash='dash', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish payti', line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300, 
    st.plotly_chart(fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300,
                                        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")), use_container_width=True)
st.markdown("---")
-9
+10
with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi (RS2)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=("Harorat Maydoni (°C)", "Xavfsizlik Koeffitsiyenti (FOS) & Yielded Zones"))
    
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                           subplot_titles=("Harorat Maydoni (°C)", "FOS, AI Collapse & Gaz Oqimi"))
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, 
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
        colorbar=dict(title="T (°C)", title_side="top", x=1.05, y=0.78, len=0.42, thickness=15)
    ), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=fos_2d, x=x_axis, y=z_axis, 
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']], 
        zmin=0, zmax=3.0, contours_showlines=False, 
        z=fos_2d, x=x_axis, y=z_axis,
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']],
        zmin=0, zmax=3.0, contours_showlines=False,
        colorbar=dict(title="FOS", title_side="top", x=1.05, y=0.22, len=0.42, thickness=15)
    ), row=2, col=1)
    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=void_visual, x=x_axis, y=z_axis,
        colorscale=[[0, 'black'], [1, 'black']], 
        colorscale=[[0, 'black'], [1, 'black']],
        showscale=False, opacity=0.9, hoverinfo='skip'
    ), row=2, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=void_mask_permanent.astype(int),
        x=x_axis, y=z_axis,
-1
+1
        line=dict(color='white', width=2),
        hoverinfo='skip'
    ), row=2, col=1)
    
    shear_disp = np.copy(shear_failure)
    shear_disp[void_mask_permanent] = False
    tens_disp = np.copy(tensile_failure)
-3
+72
    fig_tm.add_trace(go.Scatter(x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2], mode='markers', marker=dict(color='red', size=3, symbol='x'), name='Shear'), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2], mode='markers', marker=dict(color='blue', size=3, symbol='cross'), name='Tensile'), row=2, col=1)
    
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)
    
    # ------------------------------------------------------------------
    # 🧠 AI Collapse Prediction — Viridis heatmap (row=2)
    # ------------------------------------------------------------------
    fig_tm.add_trace(go.Heatmap(
        z=collapse_pred,
        x=x_axis, y=z_axis,
        colorscale='Viridis',
        opacity=0.4,
        showscale=False,
        name='AI Collapse'
    ), row=2, col=1)
    # ------------------------------------------------------------------
    # 💨 Gas Flow Vectors — Cone (row=1, harorat maydonida ko'rsatiladi)
    # Siyrak nuqtalarda (skip) vektorlar
    # ------------------------------------------------------------------
    skip = 8
    gx_skip = grid_x[::skip, ::skip].flatten()
    gz_skip = grid_z[::skip, ::skip].flatten()
    vx_skip = vx_gas[::skip, ::skip].flatten()
    vz_skip = vz_gas[::skip, ::skip].flatten()
    gy_zero = np.zeros_like(gx_skip)
    vy_zero = np.zeros_like(vx_skip)
    fig_tm.add_trace(go.Cone(
        x=gx_skip, y=gy_zero, z=gz_skip,
        u=vx_skip, v=vy_zero, w=vz_skip,
        sizemode="scaled", sizeref=2,
        showscale=False,
        colorscale='Blues',
        name='Gaz Oqimi'
    ), row=1, col=1)
    # ------------------------------------------------------------------
    fig_tm.update_layout(
        template="plotly_dark", height=850, margin=dict(r=150, t=80, b=100),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1); fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)
# ==============================================================================
# --- 🌀 UCG: SOATBAY (time_h) VA QATLAMLAR INTEGRATSIYASI ---
# ==============================================================================
st.header("🌀 UCG: Termo-Mexanik Dinamik 3D Model")
def generate_hourly_3d_model(h, layers):
    grid_res = 45
    x = np.linspace(-100, 100, grid_res)
    y = np.linspace(-60, 60, grid_res)
    grid_x_3d, grid_y_3d = np.meshgrid(x, y)
    centers_x = [-60, 0, 60]
    radii = []
    temp_states = []
    for i, cx in enumerate(centers_x):
        start_h = i * 40
        if h <= start_h:
            radii.append(0); temp_states.append("Sovuq")
        elif start_h < h <= start_h + 40:
            growth = (h - start_h) / 40
            radii.append(2 + growth * 10); temp_states.append("Faol")
        else:
            radii.append(12); temp_states.append("Soviyotgan")
    total_subs = np.zeros_like(grid_x_3d)
    for i in range(3):
        if radii[i] > 0:
            hour_factor = min(h / 150, 1.0)
            amplitude = (radii[i] / 12) * 5.0 * hour_factor
        ...
[truncated]
