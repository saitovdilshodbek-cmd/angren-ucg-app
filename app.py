import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Engine", layout="wide")

# ==============================================================================
# --- 🌍 GEOTECHNICAL DATABASE (REAL CALIBRATION) ---
# ==============================================================================
geo_db = {
    "Angren (Uzbekistan)": {"E": 5500, "phi": 28, "c": 2.2, "alpha_T": 1.2e-5, "rho": 1350, "ucs": 15, "gsi": 55, "mi": 10},
    "Shivee Ovoo (Mongolia)": {"E": 3200, "phi": 24, "c": 1.8, "alpha_T": 1.5e-5, "rho": 1250, "ucs": 10, "gsi": 45, "mi": 8},
    "Powder River (USA)": {"E": 2800, "phi": 22, "c": 1.5, "alpha_T": 1.8e-5, "rho": 1200, "ucs": 8, "gsi": 40, "mi": 7},
    "Custom": {"E": 4000, "phi": 25, "c": 2.0, "alpha_T": 1.2e-5, "rho": 1500, "ucs": 20, "gsi": 50, "mi": 10}
}

st.title("🌐 Universal Geomechanical Engine (PhD Edition)")
st.markdown("### Termo-Mexanik (TM) Modellashtirish va Ko'p Modelli Plastiklik Tahlili")

# ==============================================================================
# --- ⚙️ SIDEBAR: PARAMETRLAR INTEGRATSIYASI ---
# ==============================================================================
st.sidebar.header("🌍 Global Konfiguratsiya")
selected_field = st.sidebar.selectbox("Kon ma'lumotlar bazasi:", list(geo_db.keys()))
params = geo_db[selected_field]

mode = st.sidebar.selectbox("Model Mode:", ["Field-specific (Metric)", "Universal (Dimensionless)"])
failure_model = st.sidebar.selectbox("Plastiklik Modeli (Failure):", ["Hoek-Brown", "Mohr-Coulomb", "Drucker-Prager"])

st.sidebar.header("⚙️ Geometriya va Vaqt")
obj_name = st.sidebar.text_input("Loyiha ID:", value=f"{selected_field.split()[0]}-TM-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 200, 48)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("💎 Jins va Termal")
D_factor = st.sidebar.slider("Disturbance Factor (D):", 0.0, 1.0, 0.5)
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1050)
burn_duration = st.sidebar.number_input("Kamera faol yonish muddati (soat):", value=40)

# Qatlamlarni generatsiya qilish
layers_data = []
total_depth = 0
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam: " + (f"Ko'mir (Main)" if i == int(num_layers)-1 else "Qatlam"), expanded=(i == int(num_layers)-1)):
        # Bazaviy qiymatlarni DB dan olish (oxirgi qatlam uchun)
        def_ucs = params['ucs'] if i == int(num_layers)-1 else 30.0
        def_gsi = params['gsi'] if i == int(num_layers)-1 else 65.0
        
        thick = st.number_input(f"Qalinlik (m):", value=40.0, key=f"t_{i}")
        u = st.number_input(f"UCS (MPa):", value=float(def_ucs), key=f"u_{i}")
        rho = st.number_input(f"Zichlik (kg/m³):", value=params['rho'] if i == int(num_layers)-1 else 2400, key=f"rho_{i}")
        g = st.slider(f"GSI:", 10, 100, int(def_gsi), key=f"g_{i}")
        
        layers_data.append({
            't': thick, 'ucs': u, 'rho': rho, 'gsi': g, 
            'mi': params['mi'], 'z_start': total_depth, 'color': strata_colors[i%5]
        })
        total_depth += thick

# ==============================================================================
# --- 🧮 HISOB-KITOB YADROSI (TM ENGINE) ---
# ==============================================================================
x_axis = np.linspace(-total_depth*1.2, total_depth*1.2, 120)
z_axis = np.linspace(0, total_depth + 40, 100)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)

# --- 1. Termal PDE (Fourier Law) Soddalashtirilgan Solver ---
alpha_rock = params['alpha_T'] * 1e5 
temp_2d = np.ones_like(grid_z) * 25

sources = [{'x': -40, 'start': 0}, {'x': 40, 'start': 30}] # Ko'p manbali tizim
for s in sources:
    if time_h > s['start']:
        dt_eff = (time_h - s['start'])
        # PDE yechimi mantiqida r_penetratsiya
        r_pen = np.sqrt(4 * alpha_rock * dt_eff) 
        curr_T = T_source_max if dt_eff <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.02*(dt_eff-burn_duration))
        dist_sq = (grid_x - s['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (r_pen**2 + 200))

# --- 2. Mexanik Kuchlanishlar ---
grid_sigma_v = np.zeros_like(grid_z)
grid_ucs = np.zeros_like(grid_z)
grid_mb = np.zeros_like(grid_z)
grid_s_hb = np.zeros_like(grid_z)
grid_a_hb = np.zeros_like(grid_z)

for i, layer in enumerate(layers_data):
    mask = (grid_z >= layer['z_start']) & (grid_z < (layer['z_start'] + layer['t']))
    if i == len(layers_data)-1: mask = grid_z >= layer['z_start']
    
    overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:i]) / 1e6
    grid_sigma_v[mask] = overburden + (layer['rho'] * 9.81 * (grid_z[mask] - layer['z_start'])) / 1e6
    grid_ucs[mask] = layer['ucs']
    grid_mb[mask] = layer['mi'] * np.exp((layer['gsi'] - 100) / (28 - 14 * D_factor))
    grid_s_hb[mask] = np.exp((layer['gsi'] - 100) / (9 - 3 * D_factor))
    grid_a_hb[mask] = 0.5 + (1/6)*(np.exp(-layer['gsi']/15) - np.exp(-20/3))

# Termo-mexanik bog'liqlik (Coupling)
sigma_thermal = 0.7 * (params['E'] * params['alpha_T'] * (temp_2d - 25)) / (1 - 0.25)
sigma1_act = grid_sigma_v + sigma_thermal * 0.5
sigma3_act = (grid_sigma_v * 0.5) - sigma_thermal * 0.2

# --- 3. Plastiklik Modellari (Elasto-plastic) ---
def check_failure(s1, s3, f_model, p_db):
    if f_model == "Hoek-Brown":
        limit = s3 + grid_ucs * (grid_mb * s3 / (grid_ucs + 1e-6) + grid_s_hb)**grid_a_hb
    elif f_model == "Mohr-Coulomb":
        phi_rad = np.radians(p_db['phi'])
        ka = (1 + np.sin(phi_rad)) / (1 - np.sin(phi_rad))
        limit = s3 * ka + 2 * (p_db['c']) * np.sqrt(ka)
    else: # Drucker-Prager
        limit = s3 * 1.4 + 2.0
    return limit / (s1 + 1e-6)

fos_2d = check_failure(sigma1_act, sigma3_act, failure_model, params)
yield_mask = fos_2d < 1.0

# ==============================================================================
# --- 📊 VIZUALIZATSIYA VA DIMENSIONLESS LOGIC ---
# ==============================================================================
if mode == "Universal (Dimensionless)":
    plot_x, plot_z = grid_x / total_depth, grid_z / total_depth
    plot_temp = (temp_2d - 25) / (T_source_max - 25)
    plot_fos = fos_2d
    z_label, t_label = "Normalized Depth (z/H)", "Theta (T-ratio)"
else:
    plot_x, plot_z = grid_x, grid_z
    plot_temp = temp_2d
    plot_fos = fos_2d
    z_label, t_label = "Depth (m)", "Temp (°C)"

# Grafiklar
st.subheader(f"📊 Ekspert Tahlili: {obj_name}")
m1, m2, m3 = st.columns(3)
m1.metric("Maks. Harorat", f"{np.max(temp_2d):.1f} °C")
m2.metric("O'rtacha FOS", f"{np.mean(fos_2d):.2f}")
m3.metric("Plastik Zona", f"{np.sum(yield_mask)/yield_mask.size*100:.1f} %")

fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=(f"Harorat Maydoni ({t_label})", "Barqarorlik (FOS) va Plastik Zonalar"))

# 1. Harorat Heatmap
fig_tm.add_trace(go.Heatmap(z=plot_temp, x=x_axis/total_depth if mode=="Universal (Dimensionless)" else x_axis, 
                             y=plot_z[:,0], colorscale='Hot', name="Temp"), row=1, col=1)

# 2. FOS va Yield Points
fig_tm.add_trace(go.Contour(z=plot_fos, x=x_axis/total_depth if mode=="Universal (Dimensionless)" else x_axis, 
                             y=plot_z[:,0], colorscale='RdYlGn', zmin=0, zmax=3, 
                             contours_showlines=False, name="FOS"), row=2, col=1)

# Plastik nuqtalarni Scatter bilan ustiga qo'yish
y_idx, x_idx = np.where(yield_mask == True)
fig_tm.add_trace(go.Scatter(x=x_axis[x_idx[::3]], y=z_axis[y_idx[::3]]/total_depth if mode=="Universal (Dimensionless)" else z_axis[y_idx[::3]], 
                             mode='markers', marker=dict(color='black', size=2, symbol='x'), name="Yielded"), row=2, col=1)

fig_tm.update_layout(height=800, template="plotly_dark", showlegend=False)
fig_tm.update_yaxes(autorange='reversed')
st.plotly_chart(fig_tm, use_container_width=True)

# Footer va Ilmiy ma'lumot
with st.expander("📚 Hisoblash metodologiyasi (PhD)"):
    st.write(f"**Tanlangan kon:** {selected_field}")
    st.latex(r"PDE: \frac{\partial T}{\partial t} = \alpha \nabla^2 T")
    st.latex(r"Failure: \text{" + failure_model + r" criterion applied}")
    st.info("Ushbu model real vaqtda termo-mexanik kuchlanishlar va jinsning plastik oqimini hisoblaydi.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Tuzuvchi: Saitov Dilshodbek | {selected_field} DB")
