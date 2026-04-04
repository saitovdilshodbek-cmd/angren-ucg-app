import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# --- 🧮 TO'LIQ MATEMATIK METODOLOGIYA (PHD LEVEL) ---
# ==============================================================================
st.sidebar.header("🧮 Matematik Metodologiya")
formula_option = st.sidebar.selectbox(
    "Formulalarni ko'rish:",
    ["Yopish", "1. Hoek-Brown Failure (2018)", "2. Thermal Damage & Permeability", "3. Thermal Stress & Tension", "4. Pillar & Subsidence"]
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

# --- Sidebar: Parametrlar (Asl holatda saqlandi) ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

tensile_mode = st.sidebar.selectbox(
    "Tensile modeli:",
    ["Empirical (UCS)", "HB-based (auto)", "Manual"]
)

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

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

layers_data = []
total_depth = 0
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
            u = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
            rho = st.number_input(f"Zichlik (kg/m³):", value=2500, key=f"rho_{i}")
        with col2:
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
            
        s_t0_val = st.number_input(f"σt0 (MPa):", value=3.0, key=f"st_{i}") if tensile_mode == "Manual" else 0.0
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'rho': rho, 
            'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth,
            'sigma_t0_manual': s_t0_val
        })
        total_depth += thick

# --- HISOB-KITOBLAR (ALGORITM BUZILMAGAN) ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

grid_sigma_v, grid_ucs, grid_mb, grid_s_hb, grid_a_hb, grid_sigma_t0_manual = [np.zeros_like(grid_z) for _ in range(6)]

if 'max_temp_map' not in st.session_state or st.session_state.max_temp_map.shape != grid_z.shape:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
if 'last_obj_name' not in st.session_state or st.session_state.last_obj_name != obj_name:
    st.session_state.max_temp_map = np.ones_like(grid_z) * 25
    st.session_state.last_obj_name = obj_name

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1: mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))
    grid_sigma_t0_manual[mask] = layer['sigma_t0_manual']

alpha_rock = 1.0e-6 
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt_sec = (time_h - val['start']) * 3600
        pen_depth = np.sqrt(4 * alpha_rock * dt_sec) 
        curr_T = T_source_max if (time_h - val['start']) <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*((time_h-val['start'])-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (pen_depth**2 + 15**2))

st.session_state.max_temp_map = np.maximum(st.session_state.max_temp_map, temp_2d)
delta_T = temp_2d - 25

# --- TM ANALIZ: Stress va Damage ---
temp_eff = np.maximum(st.session_state.max_temp_map - 100, 0)
damage = 1 - np.exp(-0.002 * temp_eff)
damage = np.clip(damage, 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

E = 5000 
alpha_T_coeff = 1e-5
constraint_factor = 0.7 

dT_dx = np.gradient(temp_2d, axis=1)
dT_dz = np.gradient(temp_2d, axis=0)
thermal_gradient = np.sqrt(dT_dx**2 + dT_dz**2)

sigma_thermal = constraint_factor * (E * alpha_T_coeff * delta_T) / (1 - nu_poisson)
sigma_thermal += 0.3 * thermal_gradient

grid_sigma_h = (k_ratio * grid_sigma_v) - sigma_thermal
sigma1_act = np.maximum(grid_sigma_v, grid_sigma_h)
sigma3_act = np.minimum(grid_sigma_v, grid_sigma_h)

if tensile_mode == "Empirical (UCS)":
    grid_sigma_t0_base = tensile_ratio * sigma_ci
elif tensile_mode == "HB-based (auto)":
    grid_sigma_t0_base = (sigma_ci * grid_s_hb) / (1 + grid_mb)
else:
    grid_sigma_t0_base = grid_sigma_t0_manual

sigma_t_field = grid_sigma_t0_base * np.exp(-beta_thermal * (temp_2d - 20))
thermal_tension_boost = 1 + 0.6 * (1 - np.exp(-delta_T / 200))
sigma_t_field_eff = sigma_t_field / thermal_tension_boost

# --- FAILURE DETECTION & VOID ---
tensile_failure = (sigma3_act <= -sigma_t_field_eff) & (delta_T > 50) & (sigma1_act > sigma3_act)
sigma3_safe = np.maximum(sigma3_act, 0.01)
sigma1_limit = sigma3_safe + sigma_ci * (grid_mb * sigma3_safe / (sigma_ci + 1e-6) + grid_s_hb)**grid_a_hb
shear_failure = sigma1_act >= sigma1_limit

spalling = tensile_failure & (temp_2d > 400)
crushing = shear_failure & (temp_2d > 600)

depth_factor = np.exp(-grid_z / total_depth)
local_collapse_T = np.clip((st.session_state.max_temp_map - 600) / 300, 0, 1)
time_factor = np.clip((time_h - 40) / 60, 0, 1)
collapse_final = local_collapse_T * time_factor * (1 - depth_factor)

void_mask_raw = (spalling | crushing | (st.session_state.max_temp_map > 900))
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.5)
void_mask_permanent = (void_mask_permanent > 0.3) & (collapse_final > 0.05)

# --- Permeability va Void Volume ---
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])

sigma1_act = np.where(void_mask_permanent, 0, sigma1_act)
sigma3_act = np.where(void_mask_permanent, 0, sigma3_act)
sigma_ci = np.where(void_mask_permanent, 0.01, sigma_ci)

# --- Selek Optimizatsiyasi ---
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = grid_sigma_v[np.abs(z_axis - source_z).argmin(), :].max()

w_sol = 20.0
for _ in range(15):
    p_strength = (ucs_seam * strength_red) * (w_sol / H_seam)**0.5
    y_zone_calc = (H_seam / 2) * (np.sqrt(sv_seam / (p_strength + 1e-6)) - 1)
    new_w = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1: break
    w_sol = new_w

rec_width, pillar_strength, y_zone = np.round(w_sol, 1), p_strength, max(y_zone_calc, 1.5)
fos_2d = np.clip(sigma1_limit / (sigma1_act + 1e-6), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0, fos_2d)

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength (σp)", f"{pillar_strength:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Kamera Hajmi", f"{void_volume:.1f} m³")
m4.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m5.metric("TAVSIYA: Selek Eni", f"{rec_width} m")

st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])
s_max = (H_seam * 0.04) * (min(time_h, 120) / 120)
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*10)) * (time_h/150) * 100

with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p*100, fill='tozeroy', line=dict(color='magenta', width=3))).update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy', line=dict(color='cyan', width=3))).update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300), use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + 1e-6) + s_s)**a_s
    strength_red_burning = np.exp(-0.0025 * (T_source_max - 20))
    ucs_burning = ucs_seam * strength_red_burning
    s1_burning = sigma3_ax + ucs_burning * (mb_s * sigma3_ax / (ucs_burning + 1e-6) + s_s)**a_s
    s1_sov = sigma3_ax + (ucs_seam * strength_red) * (mb_s * sigma3_ax / (ucs_seam * strength_red + 1e-6) + s_s)**a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name='Zararlangan', line=dict(color='cyan', dash='dash', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name='Yonish payti', line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300, 
                                        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")), use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])
with c1:
    st.subheader("📋 Ilmiy Tahlil")
    st.error("🔴 FOS < 1.0: Failure")
    st.warning("🟡 FOS 1.0 - 1.5: Unstable")
    st.success("🟢 FOS > 1.5: Stable")
    fig_s = go.Figure()
    for l in layers_data: fig_s.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    st.plotly_chart(fig_s.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, showlegend=False), use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi (RS2)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, subplot_titles=("Harorat Maydoni (°C)", "Xavfsizlik Koeffitsiyenti (FOS) & Yielded Zones"))
    
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, 
        colorbar=dict(title="T (°C)", title_side="top", x=1.05, y=0.78, len=0.42, thickness=15)
    ), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=fos_2d, x=x_axis, y=z_axis, 
        colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']], 
        zmin=0, zmax=3.0, contours_showlines=False, 
        colorbar=dict(title="FOS", title_side="top", x=1.05, y=0.22, len=0.42, thickness=15)
    ), row=2, col=1)

    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(
        z=void_visual, x=x_axis, y=z_axis,
        colorscale=[[0, 'black'], [1, 'black']], 
        showscale=False, opacity=0.9, hoverinfo='skip'
    ), row=2, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=void_mask_permanent.astype(int),
        x=x_axis, y=z_axis,
        showscale=False,
        contours=dict(coloring='lines'),
        line=dict(color='white', width=2),
        hoverinfo='skip'
    ), row=2, col=1)
    
    shear_disp = np.copy(shear_failure)
    shear_disp[void_mask_permanent] = False
    tens_disp = np.copy(tensile_failure)
    tens_disp[void_mask_permanent] = False

    fig_tm.add_trace(go.Scatter(x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2], mode='markers', marker=dict(color='red', size=3, symbol='x'), name='Shear'), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2], mode='markers', marker=dict(color='blue', size=3, symbol='cross'), name='Tensile'), row=2, col=1)
    
    for px in [(sources['1']['x']+sources['2']['x'])/2, (sources['2']['x']+sources['3']['x'])/2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H_seam/2, y1=source_z+H_seam/2, line=dict(color="lime", width=3), row=2, col=1)
    
    fig_tm.update_layout(
        template="plotly_dark", height=850, margin=dict(r=150, t=80, b=100),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
    )
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1); fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)


# ==============================================================================
# --- 🌀 UCG: SOATBAY (time_h) VA QATLAMLAR INTEGRATSIYASI ---
# ==============================================================================
st.header("🌀 UCG: Termo-Mexanik Dinamik 3D Model")

def generate_integrated_3d(h, layers, s_max):
    grid_res = 30 # Bloklar hisoblanganda unumdorlik uchun resni biroz kamaytirdik
    x = np.linspace(-100, 100, grid_res)
    y = np.linspace(-60, 60, grid_res)
    gx, gy = np.meshgrid(x, y)
    
    # Cho'kish krateri (Gaussian model)
    subs_map = -s_max * np.exp(-(gx**2 + gy**2) / 800)
    
    fig = go.Figure()
    
    curr_z = 0
    for i, layer in enumerate(layers):
        z_top_base = curr_z
        z_bottom_base = curr_z + layer['t']
        
        # Deformatsiya koeffitsiyentlari
        deform_top = subs_map * (0.85 ** i)
        deform_bottom = subs_map * (0.85 ** (i + 1))
        
        z_top = -z_top_base + deform_top
        z_bottom = -z_bottom_base + deform_bottom
        
        # 1. Qatlamning ustki sirti
        fig.add_trace(go.Surface(
            x=gx, y=gy, z=z_top,
            colorscale=[[0, layer['color']], [1, layer['color']]],
            opacity=0.9, showscale=False, name=f"{layer['name']} (Top)",
            hoverinfo='skip'
        ))
        
        # 2. Qatlamning pastki sirti
        fig.add_trace(go.Surface(
            x=gx, y=gy, z=z_bottom,
            colorscale=[[0, layer['color']], [1, layer['color']]],
            opacity=0.9, showscale=False, name=f"{layer['name']} (Bottom)",
            hoverinfo='skip'
        ))

        # 3. Qatlamning yon devorlari (Blok ko'rinishini berish uchun)
        # To'rning chetki chiziqlari bo'ylab vertikal yuzalar chizamiz
        for side in range(4):
            if side == 0: # X-min devori
                sx, sy = gx[:, 0], gy[:, 0]
                sz_t, sz_b = z_top[:, 0], z_bottom[:, 0]
            elif side == 1: # X-max devori
                sx, sy = gx[:, -1], gy[:, -1]
                sz_t, sz_b = z_top[:, -1], z_bottom[:, -1]
            elif side == 2: # Y-min devori
                sx, sy = gx[0, :], gy[0, :]
                sz_t, sz_b = z_top[0, :], z_bottom[0, :]
            else: # Y-max devori
                sx, sy = gx[-1, :], gy[-1, :]
                sz_t, sz_b = z_top[-1, :], z_bottom[-1, :]

            fig.add_trace(go.Surface(
                x=np.array([sx, sx]),
                y=np.array([sy, sy]),
                z=np.array([sz_t, sz_b]),
                colorscale=[[0, layer['color']], [1, layer['color']]],
                opacity=1.0, showscale=False, hoverinfo='skip'
            ))
            
        curr_z = z_bottom_base

    # UCG Kamerasi (Issiqlik zonasi)
    coal_z = -(sum(l['t'] for l in layers[:-1]) + layers[-1]['t']/2)
    u, v = np.mgrid[0:2*np.pi:15j, 0:np.pi:15j]
    r = min(h / 10, 12)
    
    if r > 1:
        cx, cy, cz = r*np.cos(u)*np.sin(v), (r*0.7)*np.sin(u)*np.sin(v), (r*0.5)*np.cos(v) + coal_z
        fig.add_trace(go.Surface(
            x=cx, y=cy, z=cz, 
            colorscale='Hot', opacity=1.0, showscale=False,
            lighting=dict(ambient=0.6, diffuse=0.8)
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(backgroundcolor="rgb(20, 20, 20)", gridcolor="gray", showbackground=True),
            yaxis=dict(backgroundcolor="rgb(20, 20, 20)", gridcolor="gray", showbackground=True),
            zaxis=dict(backgroundcolor="rgb(20, 20, 20)", gridcolor="gray", showbackground=True, range=[-sum(l['t'] for l in layers)-10, 20]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=0.6, z=0.5)
        ),
        height=700, margin=dict(l=0, r=0, b=0, t=0),
        template="plotly_dark"
    )
    return fig

# ==============================================================================
# --- 📑 CHUQURLASHTIRILGAN ILMIY HISOBOT VA BIBLIOGRAFIYA (PHD EDITION) ---
# ==============================================================================
st.markdown("---")
st.header("🔍 Chuqurlashtirilgan Dinamik Tahlil va Metodik Asoslash")

# --- 1. O'ZGARMAS KOEFFITSIYENTLAR (PHYSICAL CONSTANTS) ---
# Bu koeffitsiyentlar Angren koni qo'ng'ir ko'miri uchun laboratoriya tadqiqotlari
# va Yang (2010) metodikasiga asosan olingan tayanch nuqtalardir.
E_MODULUS = 5000         # MPa (Young's Modulus)
ALPHA_THERMAL = 1.0e-5   # 1/°C (Linear Thermal Expansion)
BETA_CONST = beta_thermal # Sidebar'dan olingan degradatsiya koeffitsiyenti

# Hisob-kitoblar (NameError oldini olish uchun barchasi bir blokda)
target = layers_data[-1]
ucs_0 = target['ucs']
gsi_val = target['gsi']
mi_val = target['mi']
gamma_kn = target['rho'] * 9.81 / 1000 
H_depth_total = sum(l['t'] for l in layers_data[:-1]) + target['t']/2 

sigma_v_total = (gamma_kn * H_depth_total) / 1000 
mb_dyn = mi_val * np.exp((gsi_val - 100) / (28 - 14 * D_factor))
s_dyn = np.exp((gsi_val - 100) / (9 - 3 * D_factor))
a_dyn = 0.5 + (1/6) * (np.exp(-gsi_val/15) - np.exp(-20/3))
ucs_t_dyn = ucs_0 * np.exp(-BETA_CONST * (T_source_max - 20))
p_strength_final = ucs_t_dyn * (rec_width / H_seam)**0.5
fos_final = p_strength_final / (sigma_v_total + 1e-6)

# --- 2. VIZUALIZATSIYA (TABS) ---
t1, t2, t3 = st.tabs(["🏗️ Massiv Parametrlari", "🔥 Termal Degradatsiya", "⚖️ Barqarorlik & Manbalar"])

with t1:
    st.subheader("1. Hoek-Brown (2018) Klassifikatsiyasi")
    st.write("**Jins massivi sifat ko'rsatkichlari:**")
    
    c1, c2 = st.columns(2)
    with c1:
        st.latex(r"m_b = " + f"{mb_dyn:.3f}")
        st.caption(f"Massiv ishqalanish burchagi funksiyasi ($m_i={mi_val}$ asosida)")
        
        st.latex(r"s = " + f"{s_dyn:.4f}")
        st.caption(f"Yoriqlilik darajasi (GSI={gsi_val} da)")
    
    with c2:
        st.markdown(f"""
        **Ilmiy izoh:**
        **Hoek & Brown (2018)** mezoniga ko'ra, $m_b$ va $s$ koeffitsiyentlari laboratoriya namunasining butunligini massivdagi yoriqlarga nisbatini ko'rsatadi. 
        Angren konida GSI ning {gsi_val} bo'lishi massivning o'rta darajadagi blokli tuzilishga ega ekanligini va uning mustahkamligi laboratoriyaga nisbatan {((1-s_dyn)*100):.1f}% ga pastligini anglatadi.
        """)

with t2:
    st.subheader("2. Termo-Mexanik Koeffitsiyentlar Tahlili")
    
    st.write("**Hisobda qo'llanilgan o'zgarmas fizik parametrlar:**")
    st.table({
        "Parametr": ["Elastiklik Moduli (E)", "Termal kengayish (α)", "Atrof-muhit harorati (T₀)"],
        "Qiymat": [f"{E_MODULUS} MPa", f"{ALPHA_THERMAL} 1/°C", "20 °C"],
        "Tanlanish sababi": [
            "Ko'miri uchun xos bo'lgan o'rtacha deformatsiya koeffitsiyenti.",
            "Ko'mirning issiqlikdan chiziqli kengayish ko'rsatkichi (Yang, 2010).",
            "Kon qatlamining boshlang'ich tabiiy harorati."
        ]
    })

    st.markdown("**A) Termal UCS pasayishi:**")
    st.latex(r"\sigma_{ci(T)} = \sigma_{ci(0)} \cdot e^{-\beta(T-T_0)} = " + f"{ucs_t_dyn:.2f}" + r" \text{ MPa}")
    st.write(f"**Interpretatsiya:** {T_source_max}°C haroratda jins mustahkamligi {((1 - ucs_t_dyn/ucs_0)*100):.1f}% ga pasaydi. Bu **Shao (2015)** damage-modeli bo'yicha mikro-yoriqlar zichligining ortishi bilan tushuntiriladi.")

    st.markdown("**B) Termal kuchlanish ($\sigma_{th}$):**")
    st.latex(r"\sigma_{th} \approx \frac{E \cdot \alpha \cdot \Delta T}{1 - \nu} = " + f"{sigma_thermal.max():.2f}" + r" \text{ MPa}")
    st.write("Ushbu kuchlanish kamera atrofidagi jinsning erkin kengayishiga to'sqinlik (constraint) mavjudligi sababli yuzaga keladi.")

with t3:
    st.subheader("3. Selek Barqarorligi va Bibliografiya")
    
    st.latex(r"FOS = \frac{\sigma_p}{\sigma_v} = " + f"{fos_final:.2f}")
    
    st.write(f"**Wilson (1972) Yield Pillar nazariyasiga binoan:**")
    st.write(f"Selek o'lchami $w={rec_width}$ m bo'lganda, uning markaziy yadrosi (core) {sigma_v_total:.2f} MPa lik geostatik yukni ko'tarishga qodir. Plastik zona kengligi $y = {y_zone:.1f}$ m ekanligi aniqlandi.")

    st.markdown("---")
    st.write("#### 📚 Asosiy Ilmiy Manbalar (Citations):")
    
    # Maqolalarga havola va qisqacha izoh
    refs = [
        "**Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI – 2018 edition. *JRMGE*. (Massiv mustahkamligini baholash uchun).",
        "**Yang, D. (2010).** *Stability of Underground Coal Gasification*. PhD Thesis, TU Delft. (UCG termal koeffitsiyentlari uchun tayanch manba).",
        "**Shao, S., et al. (2015).** A thermal damage constitutive model for rock. *IJRMMS*. (UCS va harorat bog'liqligi uchun).",
        "**Wilson, A. H. (1972).** Research into the determination of pillar size. *Mining Engineer*. (Selek o'lchamlarini hisoblash metodikasi)."
    ]
    for ref in refs:
        st.markdown(f"📖 {ref}")

    # Yakuniy PhD xulosasi
    if fos_final < 1.3:
        st.error(f"🔴 **Ilmiy Xulosa:** FOS={fos_final:.2f}. Ko'mirning termal degradatsiyasi yuqori. Selek enini oshirish yoki gazlashtirish tezligini nazorat qilish tavsiya etiladi.")
    else:
        st.success(f"🟢 **Ilmiy Xulosa:** FOS={fos_final:.2f}. Tanlangan parametrlar massiv barqarorligini ta'minlaydi.")

# --- ILMIY METODOLOGIYA VA MANBALAR ---
st.markdown("---")
with st.expander("📚 Ilmiy Metodologiya va Manbalar (PhD Research References)"):
    st.markdown("#### Ushbu model quyidagi fundamental va zamonaviy ilmiy ishlar asosida tuzilgan:")
    refs = [
        "1. **Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI - 2018 edition.",
        "2. **Yang, D. (2010).** Stability of underground coal gasification.",
        "3. **Shao, S. et al. (2015).** A thermal damage constitutive model for rock.",
        "4. **Cui, X. et al. (2017).** Permeability evolution of coal under thermal-mechanical coupling.",
        "5. **Kratzsch, H. (2012).** Mining Subsidence Engineering.",
        "6. **Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics: For Underground Mining."
    ]
    for r in refs:
        st.write(r)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
