import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# Sahifa sozlamalari
# ==============================================================================
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")
st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# Kesh funksiyalari (performance uchun)
# ==============================================================================
@st.cache_data(ttl=3600)
def compute_hoek_brown_params(gsi, mi, D_factor):
    """Hoek-Brown parametrlarini hisoblash"""
    mb = mi * np.exp((gsi - 100) / (28 - 14 * D_factor))
    s = np.exp((gsi - 100) / (9 - 3 * D_factor))
    a = 0.5 + (1/6) * (np.exp(-gsi/15) - np.exp(-20/3))
    return mb, s, a

@st.cache_data(ttl=300)
def solve_heat_field(grid_x, grid_z, sources, source_z, time_h, burn_duration, T_source_max, alpha_rock):
    """Issiqlik maydonini hisoblash (optimallashtirilgan)"""
    temp_2d = np.ones_like(grid_x) * 25.0
    
    for key, val in sources.items():
        if time_h > val['start']:
            dt_sec = (time_h - val['start']) * 3600
            pen_depth = np.sqrt(4 * alpha_rock * dt_sec)
            elapsed = time_h - val['start']
            if elapsed <= burn_duration:
                curr_T = T_source_max
            else:
                curr_T = 25 + (T_source_max - 25) * np.exp(-0.03 * (elapsed - burn_duration))
            dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
            temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))
    
    return temp_2d

# ==============================================================================
# Matematik metodologiya
# ==============================================================================
st.sidebar.header("🧮 Matematik Metodologiya")
formula_option = st.sidebar.selectbox(
    "Formulalarni ko'rish:",
    ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability",
     "3. Thermal Stress & Tension", "4. Pillar & Subsidence"]
)

if formula_option != "Yopish":
    with st.expander(f"📚 Ilmiy asos: {formula_option}", expanded=True):
        if formula_option == "1. Hoek-Brown Failure (2018)":
            st.latex(r"\sigma_1 = \sigma_3 + \sigma_{ci} \left( m_b \frac{\sigma_3}{\sigma_{ci}} + s \right)^a")
            st.latex(r"m_b = m_i \exp\left(\frac{GSI-100}{28-14D}\right); \quad s = \exp\left(\frac{GSI-100}{9-3D}\right)")
            st.info("**Hoek-Brown:** GSI va Disturbance (D) faktorlari asosida massiv mustahkamligini hisoblash.")
        elif formula_option == "2. Thermal Damage & Permeability":
            st.latex(r"D(T) = 1 - \exp\left(-\beta (T - T_0)\right)")
            st.latex(r"k = k_0 \left[ 1 + 20 \cdot D(T) + 50 \cdot V_{void} \right]")
            st.info("**Termal degradatsiya:** Harorat ta'sirida jins strukturasining emirilishi va o'tkazuvchanlik ortishi.")
        elif formula_option == "3. Thermal Stress & Tension":
            st.latex(r"\sigma_{th} = \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu}")
            st.latex(r"\sigma_{t(T)} = \sigma_{t0} \cdot \exp\left(-\beta_{th} (T - 20)\right)")
            st.info("**Termo-mexanika:** Termal kengayish kuchlanishi va cho'zilish mustahkamligining kamayishi.")
        elif formula_option == "4. Pillar & Subsidence":
            st.latex(r"\sigma_{p} = (UCS \cdot \eta) \cdot \left( \frac{w}{H} \right)^{0.5}")
            st.latex(r"y = \frac{H}{2} \left( \sqrt{\frac{\sigma_v}{\sigma_p}} - 1 \right)")
            st.info("**Geomexanika:** Selek barqarorligi, plastik zona va yer yuzasining deformatsiyasi.")

# ==============================================================================
# Sidebar: Parametrlar
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("💎 Jins Xususiyatlari")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider("Poisson koeffitsiyenti (ν):", 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider("Stress Ratio (k = σh/σv):", 0.1, 2.0, 0.5)

st.sidebar.subheader("📐 Cho'zilish va Selek")
tensile_ratio = st.sidebar.slider("Tensile Ratio (σt0/UCS):", 0.03, 0.15, 0.08)
beta_thermal = st.sidebar.number_input("Thermal Decay (β):", value=0.0035, format="%.4f")

st.sidebar.subheader("🔥 Yonish va Termal")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

# ==============================================================================
# Qatlam ma'lumotlarini yig'ish
# ==============================================================================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data = []
total_depth = 0.0

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input("Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input("Qalinlik (m):", value=50.0, key=f"t_{i}")
            ucs_val = st.number_input("UCS (MPa):", value=40.0, key=f"u_{i}")
            rho = st.number_input("Zichlik (kg/m³):", value=2500.0, key=f"rho_{i}")
        with col2:
            color = st.color_picker("Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            gsi = st.slider("GSI:", 10, 100, 60, key=f"g_{i}")
            mi = st.number_input("mi:", value=10.0, key=f"m_{i}")
    
    layers_data.append({
        'name': name, 't': thick, 'ucs': ucs_val, 'rho': rho,
        'gsi': gsi, 'mi': mi, 'color': color, 'z_start': total_depth,
        'z_end': total_depth + thick
    })
    total_depth += thick

if not layers_data:
    st.error("❌ Kamida 1 ta qatlam kiriting!")
    st.stop()

# ==============================================================================
# Grid va manba hisob-kitoblari
# ==============================================================================
x_axis = np.linspace(-total_depth * 1.5, total_depth * 1.5, 120)  # optimallashtirildi
z_axis = np.linspace(0, total_depth + 50, 100)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = layers_data[-1]['z_start'] + layers_data[-1]['t'] / 2
H_seam = layers_data[-1]['t']

# Matritsalarni tayyorlash
grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)

# Qatlamlar bo'yicha hisoblash
for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < layer['z_end'])
    if i == len(layers_data) - 1:
        mask = grid_z >= layer['z_start']
    
    # Vertikal kuchlanish
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    
    # Jins parametrlari
    grid_ucs[mask] = layer['ucs']
    mb, s, a = compute_hoek_brown_params(layer['gsi'], layer['mi'], D_factor)
    grid_mb[mask] = mb
    grid_s_hb[mask] = s
    grid_a_hb[mask] = a

# ==============================================================================
# Issiqlik maydoni
# ==============================================================================
sources = {
    '1': {'x': -total_depth / 3, 'start': 0},
    '2': {'x': 0, 'start': 40},
    '3': {'x': total_depth / 3, 'start': 80},
}

alpha_rock = 1.0e-6
temp_2d = solve_heat_field(grid_x, grid_z, sources, source_z, time_h, burn_duration, T_source_max, alpha_rock)

# Session state uchun maksimal harorat
if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)

# ==============================================================================
# Termo-mexanik tahlil
# ==============================================================================
delta_T = temp_2d - 25.0
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage = np.clip(1 - np.exp(-0.002 * temp_eff), 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

# Termal kuchlanish
E_MODULUS = 5000.0
ALPHA_T_COEFF = 1.0e-5
sigma_thermal = 0.7 * (E_MODULUS * ALPHA_T_COEFF * delta_T) / (1 - nu_poisson)

grid_sigma_h = k_ratio * grid_sigma_v - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

# Cho'zilish mustahkamligi
if tensile_ratio > 0:
    grid_sigma_t0_base = tensile_ratio * sigma_ci
else:
    grid_sigma_t0_base = np.ones_like(sigma_ci) * 3.0

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * np.maximum(delta_T, 0))
sigma_t_field = np.clip(sigma_t_field, 0.01, None)

# Failure zonalari
tensile_failure = (sigma3_act <= -sigma_t_field) & (delta_T > 50)
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + 1e-6) + grid_s_hb) ** grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

# Void (bo'shliq) zonasini aniqlash
spalling = tensile_failure & (temp_2d > 400)
crushing = shear_failure & (temp_2d > 600)

depth_factor = np.exp(-grid_z / total_depth)
local_collapse_T = np.clip((st.session_state.max_temp_map - 600) / 300, 0, 1)
time_factor = np.clip((time_h - 40) / 60, 0, 1)
collapse_final = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw = spalling | crushing | (st.session_state.max_temp_map > 900)
void_mask_smooth = gaussian_filter(void_mask_raw.astype(float), sigma=1.0)
void_mask_permanent = (void_mask_smooth > 0.3) & (collapse_final > 0.05)

# ==============================================================================
# AI model (RandomForestClassifier)
# ==============================================================================
X_ai = np.column_stack([
    temp_2d.flatten(),
    sigma1_act.flatten(),
    sigma3_act.flatten(),
    grid_z.flatten(),
    damage.flatten()
])

y_ai = void_mask_permanent.flatten().astype(int)

if len(np.unique(y_ai)) > 1:
    rf_model = RandomForestClassifier(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_ai, y_ai)
    collapse_pred = rf_model.predict_proba(X_ai)[:, 1].reshape(temp_2d.shape)
else:
    collapse_pred = np.zeros_like(temp_2d)

# ==============================================================================
# Selek optimizatsiyasi
# ==============================================================================
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * np.maximum(avg_t_p - 20, 0))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

# Klassik iterativ yechim
w_sol = max(20.0, H_seam * 0.8)
for _ in range(20):
    p_strength = (ucs_seam * strength_red) * (w_sol / H_seam) ** 0.5
    y_zone_calc = (H_seam / 2) * (max(np.sqrt(sv_seam / (p_strength + 1e-6)) - 1, 0))
    new_w = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1:
        break
    w_sol = new_w

rec_width = max(np.round(w_sol, 1), 5.0)
pillar_strength = p_strength
y_zone = max(y_zone_calc, 1.5)

# FOS (Xavfsizlik koeffitsiyenti)
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0.0, fos_2d)

# AI optimizatsiya
void_frac_base = float(np.mean(void_mask_permanent))

def objective(w_arr):
    w = w_arr[0]
    strength = (ucs_seam * strength_red) * (w / H_seam) ** 0.5
    risk = void_frac_base * np.exp(-0.01 * (w - rec_width))
    return -(strength - 15.0 * risk)

try:
    opt_result = minimize(objective, x0=[rec_width], bounds=[(5.0, 100.0)], method='SLSQP')
    optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except:
    optimal_width_ai = rec_width

# ==============================================================================
# Metrikalar va cho'kish hisobi
# ==============================================================================
void_volume = np.sum(void_mask_permanent) * (x_axis[1] - x_axis[0]) * (z_axis[1] - z_axis[0])
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent.astype(float))

st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi", f"{void_volume:.1f} m²")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("AI Tavsiya (Selek)", f"{optimal_width_ai:.1f} m", delta=f"Klassik: {rec_width} m")

# ==============================================================================
# Cho'kish va Hoek-Brown grafiklari
# ==============================================================================
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis ** 2) / (2 * (total_depth / 2) ** 2))
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
    s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + 1e-6) + s_s) ** a_s
    ucs_burn = ucs_seam * np.exp(-0.0025 * (T_source_max - 20))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + 1e-6) + s_s) ** a_s
    s1_sov = sigma3_ax + (ucs_seam * strength_red) * (mb_s * sigma3_ax / (ucs_seam * strength_red + 1e-6) + s_s) ** a_s
    
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name='Zararlangan', line=dict(color='cyan', width=2, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish', line=dict(color='orange', width=4)))
    st.plotly_chart(
        fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300),
        use_container_width=True
    )

# ==============================================================================
# TM maydoni (asosiy vizualizatsiya)
# ==============================================================================
st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("📋 Qatlamlar Kesimi")
    fig_s = go.Figure()
    cum_depth = 0
    for lyr in layers_data:
        fig_s.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'],
                               marker_color=lyr['color'], width=0.4))
        cum_depth += lyr['t']
    st.plotly_chart(
        fig_s.update_layout(barmode='stack', template="plotly_dark",
                            yaxis=dict(autorange='reversed'), height=450),
        use_container_width=True
    )
    
    st.info("🔴 FOS < 1.0: Failure\n🟡 FOS 1.0–1.5: Unstable\n🟢 FOS > 1.5: Stable")

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi")
    
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                           subplot_titles=("Harorat Maydoni (°C) + Gaz Oqimi", "FOS + AI Collapse Prediction"))
    
    # Harorat heatmap
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot',
                                 zmin=25, zmax=T_source_max, name="Harorat"), row=1, col=1)
    
    # Gaz oqimi vektorlari
    step = 15
    qx, qz = grid_x[::step, ::step], grid_z[::step, ::step]
    vx = -perm * np.gradient(temp_2d, axis=1)
    vz = -perm * np.gradient(temp_2d, axis=0)
    qu, qw = vx[::step, ::step], vz[::step, ::step]
    qmag = np.sqrt(qu**2 + qw**2)
    
    mask_q = qmag > 0.01 * qmag.max()
    fig_tm.add_trace(go.Scatter(x=qx[mask_q].flatten(), y=qz[mask_q].flatten(),
                                 mode='markers', marker=dict(size=6, color='cyan', symbol='arrow',
                                                             angle=np.degrees(np.arctan2(qw[mask_q], qu[mask_q]))),
                                 name="Gaz oqimi"), row=1, col=1)
    
    # FOS konturi
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis,
                                 colorscale='RdYlGn', zmin=0, zmax=3.0, name="FOS"), row=2, col=1)
    
    # Void zonasi
    void_visual = np.where(void_mask_permanent, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis,
                                 colorscale='Greys', opacity=0.7, name="Void"), row=2, col=1)
    
    # AI Collapse prediction
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis,
                                 colorscale='Viridis', opacity=0.4, showscale=False, name="AI Collapse"), row=2, col=1)
    
    # Selek chegaralari
    for px in [sources['1']['x'], sources['2']['x'], sources['3']['x']]:
        fig_tm.add_shape(type="rect",
                         x0=px - rec_width/2, x1=px + rec_width/2,
                         y0=source_z - H_seam/2, y1=source_z + H_seam/2,
                         line=dict(color="lime", width=2), row=2, col=1)
    
    fig_tm.update_layout(template="plotly_dark", height=800, showlegend=True)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

# ==============================================================================
# Kompleks monitoring paneli
# ==============================================================================
st.header(f"📊 {obj_name}: Kompleks Monitoring Paneli")

def calculate_live_metrics(h, layers, T_max):
    target = layers[-1]
    ucs_0 = target['ucs']
    H_l = target['t']
    curr_T = 25 + (T_max - 25) * (min(h, 40) / 40) if h <= 40 else T_max * np.exp(-0.001 * (h - 40))
    str_red = np.exp(-0.0025 * (curr_T - 20))
    w_rec = 15.0 + (h / 150) * 10
    p_str = (ucs_0 * str_red) * (w_rec / H_l) ** 0.5
    max_sub = (H_l * 0.05) * (min(h, 120) / 120)
    return p_str, w_rec, curr_T, max_sub

p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max)

mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric("Pillar Strength", f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C")
mk2.metric("Tavsiya: Selek Eni", f"{w_rec_live:.1f} m")
mk3.metric("Maks. Cho'kish", f"{s_max_3d * 100:.1f} cm")
mk4.metric("Jarayon bosqichi", "Faol" if time_h < 100 else "Sovish")

# ==============================================================================
# 3D vizualizatsiya
# ==============================================================================
st.markdown("---")
st.subheader("🌐 3D Geomexanik Massiv")

def generate_3d_model(layers, subsidence):
    grid_res = 40
    x_i = np.linspace(-80, 80, grid_res)
    y_i = np.linspace(-60, 60, grid_res)
    gx, gy = np.meshgrid(x_i, y_i)
    subs_map = -subsidence * np.exp(-(gx**2 + gy**2) / 600)
    
    fig = go.Figure()
    curr_z = 0
    
    for i, layer in enumerate(layers):
        z_top = -curr_z + subs_map * (0.9 ** i)
        z_bottom = -(curr_z + layer['t']) + subs_map * (0.9 ** (i+1))
        
        fig.add_trace(go.Surface(x=gx, y=gy, z=z_top, colorscale=[[0, layer['color']], [1, layer['color']]],
                                 opacity=0.9, showscale=False, name=layer['name']))
        curr_z += layer['t']
    
    # Kamera (yonish zonasi)
    coal_z = -(sum(l['t'] for l in layers[:-1]) + layers[-1]['t']/2)
    r_c = 8
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:20j]
    fig.add_trace(go.Surface(x=r_c*np.cos(u)*np.sin(v), y=r_c*0.7*np.sin(u)*np.sin(v),
                              z=r_c*0.5*np.cos(v) + coal_z, colorscale='Hot', opacity=0.8))
    
    fig.update_layout(scene=dict(aspectmode='manual', aspectratio=dict(x=1, y=0.6, z=0.5),
                                  zaxis=dict(range=[-curr_z-10, 20])),
                      height=600, template="plotly_dark")
    return fig

st.plotly_chart(generate_3d_model(layers_data, s_max_3d), use_container_width=True)

# ==============================================================================
# Xulosa va interpretatsiya
# ==============================================================================
st.markdown("---")
with st.expander("📝 Avtomatik Ilmiy Interpretatsiya", expanded=True):
    risk_level = "YUQORI" if pillar_strength < 15 else "O'RTA" if pillar_strength < 25 else "PAST"
    reduction_pct = (1 - pillar_strength / (layers_data[-1]['ucs'] + 1e-6)) * 100
    
    st.write(f"""
**Tahlil natijasi ({time_h} soat):**
1. **Termal degradatsiya:** Harorat {t_now:.1f}°C ga yetishi natijasida ko'mir mustahkamligi {reduction_pct:.1f}% ga kamaygan.
2. **Yer yuzasi:** {s_max_3d * 100:.1f} cm vertikal cho'kish kutilmoqda.
3. **Xavf darajasi:** **{risk_level}**.
4. **Tavsiya:** Selek eni **{optimal_width_ai:.1f} m** (AI optimallashtirilgan).
""")
    
    if pillar_strength / sv_seam < 1.3:
        st.error("⚠️ Xavfsizlik koeffitsiyenti 1.3 dan past! Selek o'lchamini oshirish tavsiya etiladi.")
    else:
        st.success("✅ Xavfsizlik koeffitsiyenti talabga javob beradi.")

# ==============================================================================
# Footer
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.write(f"**Loyiha:** {obj_name}")
st.sidebar.write("**Tuzuvchi:** Geomexanika Monitoring Tizimi")
