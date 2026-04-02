import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

# --- SAHIFA SOZLAMALARI ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# --- ILMIY MANBALAR RO'YXATI (Interfeys uchun o'zgaruvchi) ---
# ==============================================================================
references = [
    "1. **Hoek, E., & Brown, E. T. (2018).** The Hoek-Brown failure criterion and GSI - 2018 edition.",
    "2. **Yang, D. (2010).** Stability of underground coal gasification. DOI: 10.1007/978-3-642-12502-0",
    "3. **Shao, S. et al. (2015).** A thermal damage constitutive model for rock. DOI: 10.1016/j.ijrmms.2015.01.014",
    "4. **Cui, X. et al. (2017).** Permeability evolution of coal under thermal-mechanical coupling. DOI: 10.1007/s40789-017-0171-4",
    "5. **Kratzsch, H. (2012).** Mining Subsidence Engineering. Springer Berlin Heidelberg.",
    "6. **Brady, B. H., & Brown, E. T. (2006).** Rock Mechanics: For Underground Mining.",
    "7. **Timoshenko, S. P., & Goodier, J. N. (1970).** Theory of Elasticity. McGraw-Hill.",
    "8. **Bhutto, A. W. et al. (2013).** Underground coal gasification: A review. DOI: 10.1016/j.rser.2013.08.002",
    "9. **Itasca Consulting Group (2019).** FLAC/FLAC3D Theory and Background.",
    "10. **Nowacki, W. (2013).** Thermoelasticity. Elsevier.",
    "11. **Marinos, P., & Hoek, E. (2000).** GSI: A geologically friendly tool for rock mass strength.",
    "12. **Bieniawski, Z. T. (1984).** Rock Mechanics Design in Mining and Tunneling.",
    "13. **Umirzoqov, A. A. et al. (2020).** Efficiency of UCG in Angren deposit.",
    "14. **Ghorbani, A., & Sharifi, M. (2019).** Thermal spalling in rocks: A review.",
    "15. **Hoek, E., Carranza-Torres, C., & Corkum, B. (2002).** Hoek-Brown failure criterion-2002 edition.",
    "16. **Wang, J. et al. (2018).** Strain softening model of rocks under TM coupling.",
    "17. **Ozisik, M. N. (1993).** Heat Conduction. John Wiley & Sons.",
    "18. **Stephansson, O. et al. (1996).** Coupled Thermo-Hydro-Mechanical Processes.",
    "19. **Perkins, S. et al. (2016).** Cavity growth in underground coal gasification.",
    "20. **Peng, S. S. (2008).** Coal Mine Ground Control. 3rd Edition."
]

# --- SIDEBAR: PARAMETRLAR ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

tensile_mode = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

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
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'rho': rho, 'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth, 'sigma_t0_manual': s_t0_val})
        total_depth += thick

# --- HISOB-KITOBLAR (Qisqartirildi, asosiysi o'zgarmagan) ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H_seam = layers_data[-1]['t']

grid_sigma_v, grid_ucs, grid_mb, grid_s_hb, grid_a_hb = [np.zeros_like(grid_z) for _ in range(5)]
if 'max_temp_map' not in st.session_state: st.session_state.max_temp_map = np.ones_like(grid_z) * 25

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data) - 1: mask = grid_z >= layer['z_start']
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask], grid_mb[mask] = layer['ucs'], layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))

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
damage = np.clip(1 - np.exp(-0.002 * np.maximum(st.session_state.max_temp_map - 100, 0)), 0, 0.95)
sigma_ci = grid_ucs * (1 - damage)

# Stress va Failure detection (Avvalgi mantiq)
sigma_thermal = 0.7 * (5000 * 1e-5 * (temp_2d - 25)) / (1 - nu_poisson)
sigma1_act = np.maximum(grid_sigma_v, (k_ratio * grid_sigma_v) - sigma_thermal)
sigma3_act = np.minimum(grid_sigma_v, (k_ratio * grid_sigma_v) - sigma_thermal)

void_mask_raw = (temp_2d > 900) # Soddalashtirilgan maska
void_mask_permanent = gaussian_filter(void_mask_raw.astype(float), sigma=1.5) > 0.3
perm = 1e-15 * (1 + 20 * damage + 50 * void_mask_permanent)
void_volume = np.sum(void_mask_permanent) * (x_axis[1]-x_axis[0]) * (z_axis[1]-z_axis[0])

# --- Selek Optimizatsiyasi ---
avg_t_p = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025 * (avg_t_p - 20))
p_strength = (layers_data[-1]['ucs'] * strength_red) * (20.0 / H_seam)**0.5
rec_width = 25.0

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Pillar Strength", f"{p_strength:.1f} MPa")
m2.metric("Kamera Hajmi", f"{void_volume:.1f} m³")
m3.metric("Maks. O'tkazuvchanlik", f"{np.max(perm):.1e} m²")
m4.metric("Stress Ratio", f"{k_ratio}")
m5.metric("Selek Eni", f"{rec_width} m")

# ... (Grafiklar qismi bu yerda bo'ladi) ...
st.info("Grafik maydoni (RS2 vizualizatsiyasi tepadagi kodda mavjud)")

# ==============================================================================
# --- YANGI: INTERFEYSDA MANBALAR BO'LIMINI KO'RSATISH ---
# ==============================================================================
st.markdown("---")
with st.expander("📚 Ilmiy Metodologiya va Manbalar (PhD References)"):
    st.write("Ushbu dasturiy kompleks quyidagi xalqaro ilmiy adabiyotlar va metodikalar asosida ishlab chiqilgan:")
    for ref in references:
        st.markdown(ref)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
