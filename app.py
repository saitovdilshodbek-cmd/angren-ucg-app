import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
import json
import os
import pydeck as pdk

# =========================== PYTORCH (GPU) ===========================
try:
    import torch
    import torch.nn as nn
    PT_AVAILABLE = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
except ImportError:
    PT_AVAILABLE = False
    device = "cpu"
    st.warning("⚠️ PyTorch o'rnatilmagan. RandomForestClassifier ishlatiladi.")
    from sklearn.ensemble import RandomForestClassifier

# =========================== MULTI-LANGUAGE ===========================
lang = st.sidebar.selectbox("🌐 Til / Language", ["O'zbek", "Русский", "English"])
texts = {
    "O'zbek": {
        "title": "Universal Yer yuzasi Deformatsiyasi Monitoringi",
        "subtitle": "Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi",
        "warning_pt": "⚠️ PyTorch o'rnatilmagan. RandomForestClassifier ishlatiladi.",
        # qisqacha, asosiy matnlar uchun
    },
    "English": {
        "title": "Universal Surface Deformation Monitoring",
        "subtitle": "Thermo-Mechanical (TM) Analysis and Pillar Size Optimization",
    },
    "Русский": {
        "title": "Универсальный мониторинг деформации земной поверхности",
        "subtitle": "Термо-механический анализ и оптимизация размера целика",
    }
}
T = texts[lang]

st.set_page_config(page_title=T["title"], layout="wide")
st.title(f"🌐 {T['title']}")
st.markdown(f"### {T['subtitle']}")

# =========================== SIDEBAR: PARAMETRLAR ===========================
st.sidebar.header("⚙️ Umumiy parametrlar")

# Vaqt slayderi + avto-play
col_time1, col_time2 = st.sidebar.columns([3, 1])
with col_time1:
    time_h = st.slider("Jarayon vaqti (soat):", 1, 150, 24, key="time_slider")
with col_time2:
    auto_play = st.button("▶️ Play", help="Vaqtni avtomatik oshirish")
if auto_play:
    if 'play_idx' not in st.session_state:
        st.session_state.play_idx = time_h
    if st.session_state.play_idx < 150:
        st.session_state.play_idx += 1
        time_h = st.session_state.play_idx
        st.experimental_rerun()
    else:
        st.session_state.play_idx = 1

# Konfiguratsiyani saqlash / yuklash
config_file = "ucg_config.json"
if st.sidebar.button("💾 Konfiguratsiyani saqlash"):
    config = {
        "obj_name": st.session_state.get("obj_name", "Angren-UCG-001"),
        "time_h": time_h,
        "num_layers": st.session_state.get("num_layers", 3),
        "D_factor": st.session_state.get("D_factor", 0.7),
        "nu_poisson": st.session_state.get("nu_poisson", 0.25),
        "k_ratio": st.session_state.get("k_ratio", 0.5),
        "tensile_ratio": st.session_state.get("tensile_ratio", 0.08),
        "beta_thermal": st.session_state.get("beta_thermal", 0.0035),
        "burn_duration": st.session_state.get("burn_duration", 40),
        "T_source_max": st.session_state.get("T_source_max", 1075),
        "layers": layers_data if 'layers_data' in locals() else []
    }
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    st.sidebar.success("Saqlandi!")
if st.sidebar.button("📂 Konfiguratsiyani yuklash"):
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            cfg = json.load(f)
        st.session_state.obj_name = cfg.get("obj_name", "Angren-UCG-001")
        st.session_state.time_h = cfg.get("time_h", 24)
        st.session_state.num_layers = cfg.get("num_layers", 3)
        st.session_state.D_factor = cfg.get("D_factor", 0.7)
        st.session_state.nu_poisson = cfg.get("nu_poisson", 0.25)
        st.session_state.k_ratio = cfg.get("k_ratio", 0.5)
        st.session_state.tensile_ratio = cfg.get("tensile_ratio", 0.08)
        st.session_state.beta_thermal = cfg.get("beta_thermal", 0.0035)
        st.session_state.burn_duration = cfg.get("burn_duration", 40)
        st.session_state.T_source_max = cfg.get("T_source_max", 1075)
        st.experimental_rerun()
    else:
        st.sidebar.error("Fayl topilmadi!")

obj_name = st.sidebar.text_input("Loyiha nomi:", value=st.session_state.get("obj_name", "Angren-UCG-001"), key="obj_name")
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=st.session_state.get("num_layers", 3), key="num_layers")
tensile_mode = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, st.session_state.get("D_factor", 0.7), key="D_factor")
nu_poisson = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, st.session_state.get("nu_poisson", 0.25), key="nu_poisson")
k_ratio = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, st.session_state.get("k_ratio", 0.5), key="k_ratio")

st.sidebar.subheader("📐 Cho'zilish va Selek")
tensile_ratio = st.sidebar.slider("Tensile Ratio (σt0/UCS):", 0.03, 0.15, st.session_state.get("tensile_ratio", 0.08), key="tensile_ratio")
beta_thermal = st.sidebar.number_input("Thermal Decay (β):", value=st.session_state.get("beta_thermal", 0.0035), format="%.4f", key="beta_thermal")

st.sidebar.subheader("🔥 Yonish va Termal")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=st.session_state.get("burn_duration", 40), key="burn_duration")
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, st.session_state.get("T_source_max", 1075), key="T_source_max")

# AI o'qitish parametrlari
with st.sidebar.expander("🤖 AI sozlamalari"):
    ai_epochs = st.number_input("O'qitish davrlari:", 10, 200, 50)
    ai_lr = st.number_input("Learning rate:", 0.0001, 0.01, 0.001, format="%.4f")

# Geografik tanlov
geo_options = {"Angren": (41.2995, 69.2401), "Shargun": (38.4667, 67.9333), "Olmaliq": (40.8511, 69.5983)}
selected_mine = st.sidebar.selectbox("🏭 Kon tanlang:", list(geo_options.keys()))
lat, lon = geo_options[selected_mine]

# =========================== QATLAMLAR ===========================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2,1])
        with col1:
            name = st.text_input("Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input("Qalinlik (m):", value=50.0, key=f"t_{i}")
            u = st.number_input("UCS (MPa):", value=40.0, key=f"u_{i}")
            rho = st.number_input("Zichlik (kg/m³):", value=2500.0, key=f"rho_{i}")
        with col2:
            color = st.color_picker("Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider("GSI:", 10, 100, 60, key=f"g_{i}")
            m = st.number_input("mi:", value=10.0, key=f"m_{i}")
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

# =========================== GRID VA MANBA ===========================
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth+50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - layers_data[-1]['t']/2
H_seam = layers_data[-1]['t']

grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)
grid_sigma_t0_manual = np.zeros_like(grid_z)

if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
    st.session_state.max_temp_map = np.ones_like(grid_z)*25
for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start']+layer['t']))
    if i == len(layers_data)-1:
        mask = grid_z >= layer['z_start']
    overburden = sum(l['rho']*9.81*l['t'] for l in layers_data[:i])/1e6
    grid_sigma_v[mask] = overburden + (layer['rho']*9.81*(grid_z[mask]-layer['z_start']))/1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi']-100)/(28-14*D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi']-100)/(9-3*D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15)-np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

# Issiqlik manbalari
alpha_rock = 1e-6
sources = {
    '1': {'x': -total_depth/3, 'start': 0},
    '2': {'x': 0, 'start': 40},
    '3': {'x': total_depth/3, 'start': 80},
}
temp_2d = np.ones_like(grid_x)*25.0
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec = (time_h - val['start'])*3600
        pen_depth = np.sqrt(4*alpha_rock*dt_sec)
        elapsed = time_h - val['start']
        curr_T = T_source_max if elapsed <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T-25)*np.exp(-dist_sq/(pen_depth**2+15**2))

# FDM issiqlik diffuziyasi
def solve_heat_step(T, Q, alpha, dx, dt):
    Tn = T.copy()
    Tn[1:-1,1:-1] = (T[1:-1,1:-1] + alpha*dt*((T[2:,1:-1]-2*T[1:-1,1:-1]+T[:-2,1:-1])/dx**2 +
                     (T[1:-1,2:]-2*T[1:-1,1:-1]+T[1:-1,:-2])/dx**2) + Q[1:-1,1:-1]*dt)
    return Tn

Q_heat = np.zeros_like(temp_2d)
for val in sources.values():
    if time_h > val['start']:
        cx, cz = val['x'], source_z
        elapsed = time_h - val['start']
        curr_T = T_source_max if elapsed <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(elapsed-burn_duration))
        Q_heat += (curr_T/10.0)*np.exp(-((grid_x-cx)**2+(grid_z-cz)**2)/(2*30**2))

DX, DT, N_STEPS = 1.0, 0.1, 20
for _ in range(N_STEPS):
    temp_2d = solve_heat_step(temp_2d, Q_heat, alpha_rock, DX, DT)

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25.0

# =========================== TM TAHLIL ===========================
temp_eff = np.maximum(st.session_state.max_temp_map-100, 0)
damage = np.clip(1-np.exp(-0.002*temp_eff), 0, 0.95)
sigma_ci = grid_ucs*(1-damage)

E_MODULUS, ALPHA_T_COEFF, CONSTRAINT_FACTOR = 5000.0, 1e-5, 0.7
dT_dx, dT_dz = np.gradient(temp_2d, axis=1), np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2+dT_dz**2)
sigma_thermal = CONSTRAINT_FACTOR*(E_MODULUS*ALPHA_T_COEFF*delta_T)/(1-nu_poisson) + 0.3*thermal_gradient

grid_sigma_h = k_ratio*grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb)/(1+grid_mb)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal*(temp_2d-20))
thermal_boost = 1 + 0.6*(1-np.exp(-delta_T/200))
sigma_t_field_eff = sigma_t_field/thermal_boost

tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T>50) & (sigma1_act>sigma3_act)
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci*(grid_mb*sigma3_safe/(sigma_ci+1e-6)+grid_s_hb)**grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d>400)
crushing = shear_failure & (temp_2d>600)

depth_factor = np.exp(-grid_z/total_depth)
local_collapse_T = np.clip((st.session_state.max_temp_map-600)/300,0,1)
time_factor = np.clip((time_h-40)/60,0,1)
collapse_final = local_collapse_T * time_factor * (1-depth_factor)

void_mask_raw = spalling | crushing | (st.session_state.max_temp_map>900)
void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_smooth>0.3) & (collapse_final>0.05)

perm = 1e-15*(1+20*damage+50*void_mask_permanent.astype(float))
void_volume = np.sum(void_mask_permanent)*(x_axis[1]-x_axis[0])*(z_axis[1]-z_axis[0])

sigma1_act = np.where(void_mask_permanent, 0.0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0.0, sigma3_act)
sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)

# Gaz oqimi
pressure = temp_2d*10.0
dp_dx, dp_dz = np.gradient(pressure, axis=1), np.gradient(pressure, axis=0)
vx, vz = -perm*dp_dx, -perm*dp_dz
gas_velocity = np.sqrt(vx**2+vz**2)

# =========================== AI MODEL (PyTorch) ===========================
@st.cache_resource(show_spinner=False)
def get_nn_model(epochs, lr):
    if not PT_AVAILABLE:
        return None
    def generate_data(n=10000):
        data = []
        for _ in range(n):
            T = np.random.uniform(20,1000)
            s1 = np.random.uniform(0,50)
            s3 = np.random.uniform(0,30)
            d = np.random.uniform(0,300)
            dam = 1-np.exp(-0.002*max(T-100,0))
            strength = 40*(1-dam)
            collapse = 1 if (s1>strength or T>700) else 0
            data.append([T,s1,s3,d,collapse])
        return np.array(data)
    class CollapseNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(4,32), nn.ReLU(), nn.Linear(32,64), nn.ReLU(), nn.Linear(64,1), nn.Sigmoid())
        def forward(self, x): return self.net(x)
    data = generate_data()
    X = torch.tensor(data[:,:-1], dtype=torch.float32).to(device)
    y = torch.tensor(data[:,-1], dtype=torch.float32).view(-1,1).to(device)
    model = CollapseNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCELoss()
    for epoch in range(epochs):
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

nn_model = get_nn_model(ai_epochs, ai_lr) if PT_AVAILABLE else None

# Real dataset yuklash
uploaded_file = st.sidebar.file_uploader("📂 Real dataset yuklash (CSV)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if all(col in df.columns for col in ["T","sigma1","sigma3","depth","collapse"]):
        X_real = torch.tensor(df[["T","sigma1","sigma3","depth"]].values, dtype=torch.float32).to(device)
        y_real = torch.tensor(df["collapse"].values, dtype=torch.float32).view(-1,1).to(device)
        if nn_model is not None:
            optimizer = torch.optim.Adam(nn_model.parameters(), lr=ai_lr)
            loss_fn = nn.BCELoss()
            for epoch in range(20):
                pred = nn_model(X_real)
                loss = loss_fn(pred, y_real)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            from sklearn.metrics import accuracy_score, roc_auc_score
            y_pred = (nn_model(X_real).cpu().detach().numpy() > 0.5).astype(int)
            acc = accuracy_score(y_real.cpu(), y_pred)
            st.sidebar.success(f"✅ Qayta o‘qitildi. Aniqlik: {acc:.2%}")
        else:
            # RandomForest
            from sklearn.ensemble import RandomForestClassifier
            rf = RandomForestClassifier(n_estimators=30, random_state=42)
            rf.fit(df[["T","sigma1","sigma3","depth"]], df["collapse"])
            st.sidebar.success("✅ RandomForest qayta o‘qitildi.")
            nn_model = rf  # not torch but we handle later

# AI bashorat
if nn_model is not None:
    if PT_AVAILABLE and isinstance(nn_model, torch.nn.Module):
        collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)
    else:
        # RandomForest branch
        X_ai = np.column_stack([temp_2d.flatten(), sigma1_act.flatten(), sigma3_act.flatten(), grid_z.flatten()])
        collapse_pred = nn_model.predict_proba(X_ai)[:,1].reshape(temp_2d.shape)
else:
    collapse_pred = np.zeros_like(temp_2d)

# =========================== SELEK OPTIMIZATSIYASI ===========================
avg_t_p = np.mean(temp_2d[np.abs(z_axis-source_z).argmin(),:])
strength_red = np.exp(-0.0025*(avg_t_p-20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis-source_z).argmin(),:].max()

w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam*strength_red)*(w_sol/H_seam)**0.5
    y_zone_calc = (H_seam/2)*(np.sqrt(sv_seam/(p_strength+1e-6))-1)
    new_w = 2*max(y_zone_calc,1.5)+0.5*H_seam
    if abs(new_w-w_sol)<0.1: break
    w_sol = new_w
rec_width = np.round(w_sol,1)
pillar_strength = p_strength
y_zone = max(y_zone_calc,1.5)

fos_2d = np.clip(sigma1_limit/(sigma1_act+1e-6),0,3.0)
fos_2d = np.where(void_mask_permanent,0.0,fos_2d)

void_frac_base = float(np.mean(void_mask_permanent))
def objective(w_arr):
    w = w_arr[0]
    strength = (ucs_seam*strength_red)*(w/H_seam)**0.5
    risk = void_frac_base*np.exp(-0.01*(w-rec_width))
    return -(strength-15.0*risk)
opt_result = minimize(objective, x0=[rec_width], bounds=[(5.0,100.0)], method='SLSQP')
optimal_width_ai = float(np.clip(opt_result.x[0],5.0,100.0))

# =========================== EROZIYA MODELI ===========================
erosion_factor = 1 + 0.001 * time_h * (T_source_max/500)
s_max_eroded = (H_seam*0.04)*(min(time_h,120)/120) * erosion_factor

# =========================== METRIKALAR VA OGOHLANTIRISH ===========================
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi", f"{void_volume:.1f} m²")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m")

# Avtomatik ogohlantirish
avg_fos = fos_2d[~void_mask_permanent].mean() if np.any(~void_mask_permanent) else 0
if avg_fos < 1.3:
    st.error("🚨 XAVF: O'rtacha FOS 1.3 dan past! Selek enini oshiring.")
if np.mean(collapse_pred) > 0.7:
    st.warning("⚠️ AI model yuqori collapse ehtimolini bashorat qilmoqda.")

# =========================== GRAFIKLAR ===========================
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5,1.5,2])
s_max_eroded = (H_seam*0.04)*(min(time_h,120)/120)*erosion_factor
sub_p = -s_max_eroded*np.exp(-(x_axis**2)/(2*(total_depth/2)**2))
uplift = (total_depth*1e-4)*np.exp(-(x_axis**2)/(total_depth*10))*(time_h/150)*100
with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy')).update_layout(title="📉 Cho'kish (cm, eroziya bilan)", template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy')).update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam*0.5,100)
    mb_s,s_s,a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam*(mb_s*sigma3_ax/(ucs_seam+1e-6)+s_s)**a_s
    ucs_burn = ucs_seam*np.exp(-0.0025*(T_source_max-20))
    s1_burning = sigma3_ax + ucs_burn*(mb_s*sigma3_ax/(ucs_burn+1e-6)+s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam*strength_red)*(mb_s*sigma3_ax/(ucs_seam*strength_red+1e-6)+s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name='Zararlangan', line=dict(color='cyan', dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish', line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title="Hoek-Brown", template="plotly_dark", height=300), use_container_width=True)

# =========================== TM MAYDONI (2D) ===========================
st.markdown("---")
c1, c2 = st.columns([1,2.5])
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
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, name="Harorat"), row=1, col=1)
    step=12
    qx,qz = grid_x[::step,::step].flatten(), grid_z[::step,::step].flatten()
    qu,qw = vx[::step,::step].flatten(), vz[::step,::step].flatten()
    qmag = gas_velocity[::step,::step].flatten()
    mask_q = qmag > 0.05*qmag.max()
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q]))
    fig_tm.add_trace(go.Scatter(x=qx[mask_q], y=qz[mask_q], mode='markers', marker=dict(symbol='arrow', size=8, angle=angles, color='cyan'), name="Gaz oqimi"), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale='RdYlGn', zmin=0, zmax=3.0, name="FOS"), row=2, col=1)
    void_visual = np.where(void_mask_permanent, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis, colorscale='Greys', opacity=0.7, name="Void"), row=2, col=1)
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis', opacity=0.4, showscale=False, name="AI Collapse"), row=2, col=1)
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=2), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=800)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# =========================== VAQT SERIYASI ANIMATSIYASI ===========================
st.markdown("---")
st.subheader("📈 Vaqt bo‘yicha cho‘kish animatsiyasi")
time_frames = np.arange(1, time_h+1, max(1, time_h//20))
subsidence_over_time = []
for t in time_frames:
    s_t = (H_seam*0.04)*(min(t,120)/120)*erosion_factor
    sub_t = -s_t*np.exp(-(x_axis**2)/(2*(total_depth/2)**2))
    subsidence_over_time.append(sub_t*100)
fig_anim = go.Figure(
    data=[go.Scatter(x=x_axis, y=subsidence_over_time[0], mode='lines', line=dict(color='magenta'))],
    layout=go.Layout(
        title="Cho'kish evolyutsiyasi",
        xaxis=dict(range=[x_axis.min(), x_axis.max()]),
        yaxis=dict(range=[-max([s.min() for s in subsidence_over_time])*1.1, 0]),
        updatemenus=[dict(type="buttons", buttons=[dict(label="Play", method="animate", args=[None])])]
    ),
    frames=[go.Frame(data=[go.Scatter(x=x_axis, y=y)]) for y in subsidence_over_time]
)
st.plotly_chart(fig_anim, use_container_width=True)

# =========================== 3D MODEL ===========================
def generate_integrated_3d(h, layers, s_max):
    grid_res = 30
    x_i = np.linspace(-100,100,grid_res)
    y_i = np.linspace(-60,60,grid_res)
    gx,gy = np.meshgrid(x_i,y_i)
    subs_map = -s_max*np.exp(-(gx**2+gy**2)/800)
    fig = go.Figure()
    curr_z = 0.0
    for i,layer in enumerate(layers):
        z_top = -curr_z + subs_map*(0.85**i)
        z_bottom = -(curr_z+layer['t']) + subs_map*(0.85**(i+1))
        cs = [[0,layer['color']],[1,layer['color']]]
        fig.add_trace(go.Surface(x=gx,y=gy,z=z_top,colorscale=cs,opacity=0.9,showscale=False,name=layer['name'],hoverinfo='skip'))
        fig.add_trace(go.Surface(x=gx,y=gy,z=z_bottom,colorscale=cs,opacity=0.9,showscale=False,hoverinfo='skip'))
        for sx,sy,szt,szb in [(gx[:,0],gy[:,0],z_top[:,0],z_bottom[:,0]),
                              (gx[:,-1],gy[:,-1],z_top[:,-1],z_bottom[:,-1]),
                              (gx[0,:],gy[0,:],z_top[0,:],z_bottom[0,:]),
                              (gx[-1,:],gy[-1,:],z_top[-1,:],z_bottom[-1,:])]:
            fig.add_trace(go.Surface(x=np.array([sx,sx]), y=np.array([sy,sy]), z=np.array([szt,szb]), colorscale=cs, opacity=1.0, showscale=False, hoverinfo='skip'))
        curr_z += layer['t']
    coal_z = -(sum(l['t'] for l in layers[:-1]) + layers[-1]['t']/2)
    r_c = min(h/10,12)
    if r_c>1:
        u_c,v_c = np.mgrid[0:2*np.pi:15j, 0:np.pi:15j]
        fig.add_trace(go.Surface(x=r_c*np.cos(u_c)*np.sin(v_c), y=(r_c*0.7)*np.sin(u_c)*np.sin(v_c), z=(r_c*0.5)*np.cos(v_c)+coal_z, colorscale='Hot', opacity=1.0, lighting=dict(ambient=0.6,diffuse=0.8)))
    fig.update_layout(scene=dict(xaxis=dict(backgroundcolor="rgb(20,20,20)",gridcolor="gray"), yaxis=dict(backgroundcolor="rgb(20,20,20)",gridcolor="gray"), zaxis=dict(backgroundcolor="rgb(20,20,20)",gridcolor="gray", range=[-sum(l['t'] for l in layers)-10,20]), aspectmode='manual', aspectratio=dict(x=1,y=0.6,z=0.5)), height=700, margin=dict(l=0,r=0,b=0,t=0), template="plotly_dark")
    return fig

st.markdown("---")
st.subheader("🌐 3D Geomexanik Massiv")
st.plotly_chart(generate_integrated_3d(time_h, layers_data, s_max_eroded), use_container_width=True)

# =========================== GEOXARITA ===========================
st.markdown("---")
st.subheader("🌍 Geolokatsiya xaritasi")
# Xaritada harorat intensivligi
heat_data = pd.DataFrame({"lat":[lat], "lon":[lon], "intensity":[np.mean(temp_2d)]})
layer = pdk.Layer("HeatmapLayer", data=heat_data, get_position='[lon, lat]', get_weight='intensity', radius=1000)
view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=10)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# =========================== HISOBOT YUKLASH ===========================
if st.button("📄 Hisobot yuklab olish"):
    report = f"""
    LOYIHA: {obj_name}
    Vaqt: {time_h} soat
    Pillar Strength: {pillar_strength:.2f} MPa
    Plastik zona: {y_zone:.1f} m
    O'rtacha collapse ehtimoli: {np.mean(collapse_pred):.3f}
    Tavsiya etilgan selek eni: {optimal_width_ai:.1f} m
    """
    st.download_button("⬇️ Yuklab olish", report, file_name=f"{obj_name}_report.txt")

# =========================== QOLGAN QISMLAR (Trendlar, ilmiy hisobot) ===========================
st.markdown("---")
st.header("📊 Kompleks Monitoring Paneli")
def calculate_live_metrics(h, layers, T_max):
    target = layers[-1]
    ucs_0 = target['ucs']; H_l = target['t']
    curr_T = 25+(T_max-25)*(min(h,40)/40) if h<=40 else T_max*np.exp(-0.001*(h-40))
    str_red = np.exp(-0.0025*(curr_T-20))
    w_rec = 15.0+(h/150)*10
    p_str = (ucs_0*str_red)*(w_rec/H_l)**0.5
    max_sub = (H_l*0.05)*(min(h,120)/120)
    return p_str, w_rec, curr_T, max_sub
p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max)
mk1,mk2,mk3,mk4 = st.columns(4)
mk1.metric("Pillar Strength", f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C")
mk2.metric("Tavsiya: Selek Eni", f"{w_rec_live:.1f} m")
mk3.metric("Maks. Cho'kish", f"{s_max_3d*100:.1f} cm")
mk4.metric("Jarayon bosqichi", "Faol" if time_h<100 else "Sovish")

st.markdown("---")
col_left, col_right = st.columns([2,1])
with col_left:
    st.subheader("📈 Dinamik Trendlar")
    h_axis = np.linspace(0,150,50)
    st_trend = [calculate_live_metrics(v, layers_data, T_source_max)[0] for v in h_axis]
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=h_axis, y=st_trend, name="Mustahkamlik", line=dict(color='orange', width=3)))
    fig_trend.add_vline(x=time_h, line_dash="dash", line_color="red")
    fig_trend.update_layout(template="plotly_dark", height=250, title="Mustahkamlik pasayishi (MPa/h)")
    st.plotly_chart(fig_trend, use_container_width=True)
with col_right:
    st.write("**Qatlamlar tuzilishi:**")
    for lyr in layers_data:
        st.caption(f"• {lyr['name']}: {lyr['t']} m (UCS: {lyr['ucs']} MPa)")

# Ilmiy interpretatsiya (qisqa)
with st.expander("📝 Avtomatik Ilmiy Interpretatsiya", expanded=True):
    risk_level = "YUQORI" if p_str<15 else "O'RTA" if p_str<25 else "PAST"
    reduction_pct = (1-p_str/(layers_data[-1]['ucs']+1e-6))*100
    st.write(f"""
**Tahlil natijasi ({time_h} soat):**
1. **Termal degradatsiya:** Harorat {t_now:.1f}°C → mustahkamlik {reduction_pct:.1f}% kamaygan.
2. **Yer yuzasi:** {s_max_3d*100:.1f} cm cho'kish.
3. **Xavf darajasi:** **{risk_level}**.
4. **Tavsiya:** Selek eni **{optimal_width_ai:.1f} m**.
""")

st.markdown("---")
st.header("🔍 Chuqurlashtirilgan Ilmiy Hisobot")
# Qisqacha Hoek-Brown va termal tahlil (oldingi kodda mavjud)
# ... (uzoq bo'lib ketmasligi uchun bu qismni avvalgi kodingizdan olib qo'ying)
st.info("Batafsil Hoek-Brown va termal tahlil uchun oldingi versiyadagi `t1, t2, t3` tablarni qo'shing.")

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
