import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Ilmiy UCG Ssenariysi (Angren Case)")

# --- Sidebar: Parametrlar ---
st.sidebar.header("⚙️ Model Parametrlari")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)

# 1. GEOLOGIYA
st.sidebar.subheader("🧱 Geologik Qatlamlar")
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

layers_data = []
total_depth = 0
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"Nomi:", value=f"Qatlam-{i+1}", key=f"n_{i}")
            thick = st.number_input(f"Qalinlik (m):", value=50.0, key=f"t_{i}")
            ucs = st.number_input(f"UCS (MPa):", value=40.0, key=f"u_{i}")
        with col2:
            gsi = st.slider(f"GSI:", 10, 100, 60, key=f"g_{i}")
            mi = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
            color = st.color_picker(f"Rang:", strata_colors[i % len(strata_colors)], key=f"c_{i}")
        
        layers_data.append({'name': name, 't': thick, 'ucs': ucs, 'gsi': gsi, 'mi': mi, 'color': color, 'z_start': total_depth})
        total_depth += thick

# 2. TERMAL VA MEXANIK
st.sidebar.subheader("🔥 Termo-Mexanik Sozlamalar")
T_source = st.sidebar.slider("Yonish harorati (°C)", 600, 1200, 1000)
thermal_alpha = 1e-6 # Diffuziya koeffitsiyenti
phi = st.sidebar.slider("Ishqalanish burchagi (Phi °)", 20, 45, 30)
cohesion = st.sidebar.slider("Bog'lanish (C, MPa)", 0.1, 20.0, 5.0)
gamma = 0.027 # O'rtacha zichlik (MN/m3)

# --- ILMIY HISOB-KITOBLAR ---
# 1. Hoek-Brown parametrlarini hisoblash (O'rtacha qiymatlar bo'yicha)
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth
avg_mi = sum(l['mi'] * l['t'] for l in layers_data) / total_depth

mb = avg_mi * np.exp((avg_gsi - 100) / 28)
s_hb = np.exp((avg_gsi - 100) / 9)
a_hb = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

# 2. Grid (To'r) yaratish
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
X, Z = np.meshgrid(x_axis, z_axis)

# 3. Harorat maydoni (Thermal Field)
# Issiqlik manbai ko'mir qatlamining o'rtasida deb hisoblaymiz
source_z = total_depth - (layers_data[-1]['t'] / 2)
dist_sq = (X)**2 + (Z - source_z)**2
T_field = 25 + T_source * np.exp(-dist_sq / (4 * thermal_alpha * (time_h * 3600)))

# 4. Kuchlanish va Buzilish (Stress & Failure)
sigma_v = gamma * Z # Vertikal kuchlanish
shear_strength = sigma_v * np.tan(np.radians(phi)) + cohesion
# Harorat ta'sirida mustahkamlikning kamayishi
failure_index = (shear_strength / (cohesion + 1e-6)) * np.exp(-0.002 * (T_field - 25))

# 5. Cho'kish (Subsidence - Gauss-Knothe)
angle_sub = 35 # Cho'kish burchagi
r_sub = total_depth / np.tan(np.radians(angle_sub))
S_max = (layers_data[-1]['t'] * 0.02) * (min(time_h, 100) / 100)
subsidence = -S_max * np.exp(-(x_axis**2) / (2 * (r_sub/2.5)**2))

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Kompleks Monitoring")

# Yuqori grafiklar: Cho'kish va Deformatsiya
col_g1, col_g2 = st.columns(2)
with col_g1:
    fig_sub = go.Figure()
    fig_sub.add_trace(go.Scatter(x=x_axis, y=subsidence * 100, fill='tozeroy', line=dict(color='#FF00FF', width=3)))
    fig_sub.update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig_sub, use_container_width=True)

with col_g2:
    fig_fail = go.Figure()
    max_fail = np.max(failure_index, axis=0)
    fig_fail.add_trace(go.Scatter(x=x_axis, y=max_fail, line=dict(color='orange', width=2)))
    fig_fail.update_layout(title="💥 Buzilish ko'rsatkichi (Failure Index)", template="plotly_dark", height=300)
    st.plotly_chart(fig_fail, use_container_width=True)

st.divider()

# Asosiy 2D Kesim
c1, c2 = st.columns([1, 3])

with c1:
    st.write("### 🧱 Geologiya")
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color']))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(title="Chuqurlik (m)", autorange='reversed'), height=600)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.write("### 🔥 TM Maydoni va Mexanik Holat")
    fig_main = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                             subplot_titles=("Harorat Tarqalishi (°C)", "Geomexanik Barqarorlik (Buzilish Zonasi)"))
    
    # Harorat Heatmap
    fig_main.add_trace(go.Heatmap(z=T_field, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source), row=1, col=1)
    
    # Failure Heatmap
    fig_main.add_trace(go.Heatmap(z=failure_index, x=x_axis, y=z_axis, colorscale='Portland', zmin=0, zmax=2), row=2, col=1)
    
    # Qatlam chegaralarini chizish
    for layer in layers_data:
        fig_main.add_shape(type="line", x0=min(x_axis), y0=layer['z_start'], x1=max(x_axis), y1=layer['z_start'],
                           line=dict(color="white", width=1, dash="dot"), row=2, col=1)

    fig_main.update_layout(template="plotly_dark", height=700)
    fig_main.update_yaxes(autorange='reversed', title="Chuqurlik (m)")
    st.plotly_chart(fig_main, use_container_width=True)

# --- HISOBOT JADVALI ---
st.divider()
st.subheader("📄 Ilmiy Hisobot")
col_res1, col_res2 = st.columns(2)

with col_res1:
    st.table({
        "Hoek-Brown Parametrlari": ["mb (disturbed)", "s (constant)", "a (exponent)"],
        "Qiymat": [f"{mb:.3f}", f"{s_hb:.5f}", f"{a_hb:.4f}"]
    })

with col_res2:
    st.table({
        "Natijaviy Ko'rsatkichlar": ["Maksimal Harorat", "Max Subsidence (cm)", "Holat"],
        "Qiymat": [f"{np.max(T_field):.1f} °C", f"{abs(np.min(subsidence)*100):.2f}", 
                   "Kritik" if np.max(failure_index) > 1.5 else "Barqaror"]
    })

st.sidebar.markdown("---")
st.sidebar.info(f"Tuzuvchi: Saitov Dilshodbek\nLoyiha: {obj_name}")
