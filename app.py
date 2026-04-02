import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Dinamik UCG Ssenariysi (Ilmiy va Vizual)")

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
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth
        })
        total_depth += thick

# --- ILMIY HISOB-KITOBLAR ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth
avg_mi = sum(l['mi'] * l['t'] for l in layers_data) / total_depth

# Hoek-Brown parametrlari (Boshlang'ich holat uchun)
mb = avg_mi * np.exp((avg_gsi - 100) / 28)
s_hb = np.exp((avg_gsi - 100) / 9)
a_hb = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

# Grid yaratish
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)

# 2D Termal model
source_z = total_depth - (layers_data[-1]['t'] / 2)
temp_2d = np.ones_like(grid_x) * 25 

sources = {'1': {'x': -total_depth/3, 'start': 0}, 
           '2': {'x': 0, 'start': 30}, 
           '3': {'x': total_depth/3, 'start': 60}}

for key, val in sources.items():
    if time_h > val['start']:
        dt = time_h - val['start']
        if dt <= burn_duration:
            radius = 15 + (dt * 0.5)
            curr_T = T_source_max
        else:
            radius = 15 + (burn_duration * 0.5)
            curr_T = 25 + (T_source_max - 25) * np.exp(-0.03 * (dt - burn_duration))
            
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (2 * radius**2))

# --- FAILURE MODEL (Siz bergan formula) ---
sigma_v = 0.027 * grid_z
strength = avg_ucs * np.exp(-0.002 * (temp_2d - 20))
failure_2d = sigma_v / (strength + 1e-6)
# ----------------------------------------------

# --- YANGI GRAFIK UCHUN MATEMATIKA: HOEK-BROWN ENVELOPES ---
# Sigma_3 (yon bosim) o'qi uchun diapazon
sigma3_axis = np.linspace(0, avg_ucs * 0.5, 100) # UCS ning yarmigacha yon bosim

# 1. Yonishdan oldin (20°C) - To'liq UCS
ucs_initial = avg_ucs
sigma1_initial = sigma3_axis + ucs_initial * (mb * sigma3_axis / ucs_initial + s_hb)**a_hb

# 2. Yonayotgan paytda (T_source_max) - Kuchli kuchsizlanish
# Termal kuchsizlanish koeffitsiyenti (sizning strength formulangizdan olingan mantiq)
reduction_hot = np.exp(-0.002 * (T_source_max - 20))
ucs_hot = avg_ucs * reduction_hot
sigma1_hot = sigma3_axis + ucs_hot * (mb * sigma3_axis / ucs_hot + s_hb)**a_hb

# 3. Sovugandan keyin (20°C, lekin zarar ko'rgan)
# Jins termal sikldan keyin qoldiq mustahkamlikka ega bo'ladi (taxminan 50% termal zarar saqlanib qoladi)
reduction_cooled = reduction_hot + (1 - reduction_hot) * 0.5 
ucs_cooled = avg_ucs * reduction_cooled
sigma1_cooled = sigma3_axis + ucs_cooled * (mb * sigma3_axis / ucs_cooled + s_hb)**a_hb
# -------------------------------------------------------------

# Subsidence (Gauss-Knothe profili)
angle_sub = 35
r_sub = total_depth / np.tan(np.radians(angle_sub))
sub_coeff = np.clip(0.1 - (avg_gsi/1000), 0.01, 0.05) 
s_max = (layers_data[-1]['t'] * sub_coeff) * (min(time_h, 100) / 100)
subsidence_profile = -s_max * np.exp(-(x_axis**2) / (2 * (r_sub/2.5)**2))

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2]) # Uchinchi ustun kengroq

with col_g1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_axis, y=subsidence_profile * 100, fill='tozeroy', line=dict(color='magenta', width=3)))
    fig1.update_layout(title="📉 Yer yuzasi cho'kishi (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    fig2 = go.Figure()
    uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*10)) * (time_h/150)
    fig2.add_trace(go.Scatter(x=x_axis, y=uplift * 100, fill='tozeroy', line=dict(color='cyan', width=3)))
    fig2.update_layout(title="🔥 Termal deformatsiya (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig2, use_container_width=True)

# --- YANGI GRAFIK: HOEK-BROWN ENVELOPE MONITORING ---
with col_g3:
    fig_hb = go.Figure()
    
    # 1. Yonishdan oldin (Qizil)
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_initial, name='Yonishdan oldin (20°C)', 
                                 line=dict(color='#FF4B4B', width=3)))
    
    # 2. Sovugandan keyin (Ko'k - termal zarar ko'rgan)
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_cooled, name='Sovugandan keyin (20°C, zarar)', 
                                 line=dict(color='#0068C9', width=3, dash='dash')))
    
    # 3. Yonayotgan paytda (Olovrang - eng kuchsiz)
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_hot, name=f'Yonayotgan paytda ({T_source_max}°C)', 
                                 line=dict(color='#FFA500', width=4)))
    
    # Grafik bezaklari
    fig_hb.update_layout(
        title="🛡️ Jins Mustahkamligi Chegarasi (Hoek-Brown Envelopes)",
        xaxis_title="Minor Principal Stress σ₃ (MPa)",
        yaxis_title="Major Principal Stress σ₁ (MPa)",
        template="plotly_dark",
        height=300,
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(0,0,0,0.5)")
    )
    # Tasvir kabi setka qo'shish
    fig_hb.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    fig_hb.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
    
    st.plotly_chart(fig_hb, use_container_width=True)
# --------------------------------------------------------

st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("🧱 Geologik Kesim")
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(title="Chuqurlik (m)", autorange='reversed'), height=750)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va Strukturaviy Holat")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                           subplot_titles=("Harorat Maydoni (°C)", "Buzilish koeffitsiyenti (Stress/Strength)"))
    
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="°C", x=1.02, y=0.78, len=0.45)), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(z=failure_2d, x=x_axis, y=z_axis, colorscale='Jet',
                                contours=dict(coloring='heatmap', showlines=True),
                                colorbar=dict(title="Index", x=1.02, y=0.22, len=0.45)), row=2, col=1)
    
    fig_tm.add_trace(go.Scatter(x=x_axis, y=subsidence_profile * 50, mode='lines', 
                                line=dict(color='white', width=3, dash='dash'), name="Deformatsiya"), row=2, col=1)

    for layer in layers_data:
        fig_tm.add_shape(type="line", x0=min(x_axis), y0=layer['z_start'], x1=max(x_axis), y1=layer['z_start'],
                         line=dict(color="rgba(255,255,255,0.2)", width=1, dash="dot"), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=850)
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.divider()
st.table({
    "Ko'rsatkich": ["Hoek-Brown mb", "Hoek-Brown s", "Maksimal Cho'kish (m)", "Ssenariya holati"],
    "Qiymat": [f"{mb:.3f}", f"{s_hb:.5f}", f"{abs(np.min(subsidence_profile)):.4f}", 
               f"{'Sovish' if time_h > burn_duration else 'Faol Yonish'}"]
})

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
