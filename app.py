import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("🔥 Yonish va Termal")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)
T_source_max = st.sidebar.slider("Maksimal harorat (°C)", 600, 1200, 1075)

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

# --- Qatlamlar ma'lumotlarini yig'ish ---
layers_data = []
total_depth = 0
for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
            u = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
        with col2:
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
        
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth})
        total_depth += thick

# --- ILMIY HISOB-KITOBLAR ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth
avg_mi = sum(l['mi'] * l['t'] for l in layers_data) / total_depth

x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)
H = layers_data[-1]['t'] # Ko'mir qatlami qalinligi

# Issiqlik maydoni
sources = {'1': {'x': -total_depth/3, 'start': 0}, '2': {'x': 0, 'start': 40}, '3': {'x': total_depth/3, 'start': 80}}
temp_2d = np.ones_like(grid_x) * 25 
for key, val in sources.items():
    if time_h > val['start']:
        dt = time_h - val['start']
        radius = 15 + (min(dt, burn_duration) * 0.5)
        curr_T = T_source_max if dt <= burn_duration else 25 + (T_source_max-25)*np.exp(-0.03*(dt-burn_duration))
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (2 * radius**2))

# --- TAKOMILLASHTIRILGAN WILSON VA FOS MODELI ---

# 1. Stress holati (Lateral confinement K0=0.5 deb olindi)
sigma_v = 0.027 * source_z 
sigma_h = 0.5 * sigma_v 

# 2. Termal ta'sir ostidagi mustahkamlik (Pillar Core Strength)
avg_t_at_pillar = np.mean(temp_2d[np.abs(z_axis - source_z).argmin(), :])
strength_red_factor = np.exp(-0.0025 * (avg_t_at_pillar - 20))
pillar_strength_insitu = 0.6 * (avg_ucs * strength_red_factor)

# 3. Wilson y-zone (Plastik zona kengligi)
# Lateral confinement hisobga olingan holda
y_zone = (H / 2) * (np.sqrt(sigma_v / (pillar_strength_insitu + 1e-6)) - 1)
y_zone = max(y_zone, 1.5)

# 4. Stable Core (Empirik: 0.5 * H)
stable_core = 0.5 * H
rec_width = np.round(2 * y_zone + stable_core, 1)

# 5. FOS Interpretatsiyasi (Strength / Stress)
current_strength = (avg_ucs * np.exp(-0.0025 * (temp_2d - 20))) * 0.6
current_stress = 0.027 * grid_z
fos_2d = current_strength / (current_stress + 1e-6)

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Wilson Modeli va Selek Barqarorligi")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Pillar Strength (σp)", f"{pillar_strength_insitu:.1f} MPa")
m2.metric("Plastik zona (y)", f"{y_zone:.1f} m")
m3.metric("Stable Core (0.5H)", f"{stable_core:.1f} m")
m4.metric("Tavsiya etilgan W", f"{rec_width} m")

st.markdown("---")

c1, c2 = st.columns([1, 2.5])

with c1:
    st.info("**FOS Interpretatsiyasi:**")
    st.error("🔴 FOS < 1.0: Buzilish (Failure)")
    st.warning("🟡 FOS 1.0 - 1.5: Xavfli (Unstable)")
    st.success("🟢 FOS > 1.5: Xavfsiz (Stable)")
    
    # Selek holati xulosasi
    current_fos_avg = np.mean(fos_2d[np.abs(z_axis - source_z).argmin(), :])
    if current_fos_avg < 1:
        st.error(f"Holat: BUZILISH (FOS: {current_fos_avg:.2f})")
    elif current_fos_avg < 1.5:
        st.warning(f"Holat: XAVFLI (FOS: {current_fos_avg:.2f})")
    else:
        st.success(f"Holat: XAVFSIZ (FOS: {current_fos_avg:.2f})")

with c2:
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, 
                           subplot_titles=("Harorat Maydoni (°C)", "Xavfsizlik Koeffitsiyenti (FOS)"))
    
    # Heatmap Harorat
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max, 
                                colorbar=dict(title="°C", x=1.02, y=0.78, len=0.45)), row=1, col=1)
    
    # FOS Kontur (Siz aytgan rangli klassifikatsiya bilan)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, 
                                colorscale=[[0, 'red'], [0.33, 'yellow'], [0.5, 'green'], [1, 'darkgreen']],
                                zmin=0, zmax=3.0, 
                                colorbar=dict(title="FOS", x=1.02, y=0.22, len=0.45),
                                contours=dict(start=0, end=3, size=0.5, showlines=False)), row=2, col=1)
    
    # Selek chizmasi
    p_x1 = (sources['1']['x'] + sources['2']['x']) / 2
    p_x2 = (sources['2']['x'] + sources['3']['x']) / 2
    for px in [p_x1, p_x2]:
        fig_tm.add_shape(type="rect", x0=px-rec_width/2, x1=px+rec_width/2, y0=source_z-H/2, y1=source_z+H/2, 
                         line=dict(color="lime", width=3), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=800, showlegend=False)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
