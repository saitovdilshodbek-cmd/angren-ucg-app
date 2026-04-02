import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Sahifa sozlamalari ---
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil: Seleklar Barqarorligi va O'zaro Ta'sir")

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

mb = avg_mi * np.exp((avg_gsi - 100) / 28)
s_hb = np.exp((avg_gsi - 100) / 9)
a_hb = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)
source_z = total_depth - (layers_data[-1]['t'] / 2)

# Seleklar (Pillars) mantiqi uchun manbalar
sources = {'1': {'x': -total_depth/2.5, 'start': 0}, 
           '2': {'x': 0, 'start': 40}, 
           '3': {'x': total_depth/2.5, 'start': 80}}

temp_2d = np.ones_like(grid_x) * 25 
plastic_zone_mask = np.zeros_like(grid_x)

for key, val in sources.items():
    if time_h > val['start']:
        dt = time_h - val['start']
        radius = 15 + (min(dt, burn_duration) * 0.5)
        curr_T = T_source_max if dt <= burn_duration else 25 + (T_source_max - 25) * np.exp(-0.03 * (dt - burn_duration))
            
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        # Termal ta'sir qo'shilishi (Superpozitsiya prinsipi)
        temp_2d += (curr_T - 25) * np.exp(-dist_sq / (2 * radius**2))
        
        # RS2 simulyatsiyasi uchun plastik zona (Interferensiya bilan)
        plastic_influence = np.exp(-dist_sq / (2 * (radius * 1.3)**2))
        plastic_zone_mask = np.maximum(plastic_zone_mask, plastic_influence)

# Stress va Strength
sigma_v = 0.027 * grid_z
strength = avg_ucs * np.exp(-0.002 * (temp_2d - 20)) # Harorat ortishi bilan strength kamayadi
failure_2d = sigma_v / (strength + 1e-6)

# Hoek-Brown Envelopes
sigma3_axis = np.linspace(0, avg_ucs * 0.5, 100)
reduction_hot = np.exp(-0.002 * (T_source_max - 20))
sigma1_initial = sigma3_axis + avg_ucs * (mb * sigma3_axis / avg_ucs + s_hb)**a_hb
sigma1_hot = sigma3_axis + (avg_ucs * reduction_hot) * (mb * sigma3_axis / (avg_ucs * reduction_hot) + s_hb)**a_hb
reduction_cooled = reduction_hot + (1 - reduction_hot) * 0.5 
sigma1_cooled = sigma3_axis + (avg_ucs * reduction_cooled) * (mb * sigma3_axis / (avg_ucs * reduction_cooled) + s_hb)**a_hb

# --- SELEK MONITORINGI (Pillar Analysis) ---
pillar_x_coords = [(sources['1']['x'] + sources['2']['x'])/2, (sources['2']['x'] + sources['3']['x'])/2]
pillar_status = []
for px in pillar_x_coords:
    # Selek o'rtasidagi haroratni grid'dan topish
    idx_x = np.abs(x_axis - px).argmin()
    idx_z = np.abs(z_axis - source_z).argmin()
    t_pillar = temp_2d[idx_z, idx_x]
    strength_reduct = np.exp(-0.002 * (t_pillar - 20))
    pillar_status.append({'x': px, 'temp': t_pillar, 'safety': strength_reduct})

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

s_max = (layers_data[-1]['t'] * 0.04) * (min(time_h, 120) / 120)
subsidence_profile = -s_max * np.exp(-(x_axis**2) / (2 * (total_depth/2)**2))

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

with col_g3:
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_initial, name='Boshlang\'ich', line=dict(color='#FF4B4B', width=3)))
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_cooled, name='Sovigan (zarar)', line=dict(color='#0068C9', width=3, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_hot, name='Issiq (Kameralar)', line=dict(color='#FFA500', width=4)))
    fig_hb.update_layout(title="🛡️ Hoek-Brown Envelopes", template="plotly_dark", height=300, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_hb, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("🧱 Seleklar Holati")
    for i, ps in enumerate(pillar_status):
        st.metric(f"{i+1}-Selek Harorati", f"{ps['temp']:.1f} °C")
        st.write(f"Mustahkamlik: {ps['safety']*100:.1f}%")
        if ps['safety'] < 0.7:
            st.error(f"⚠️ {i+1}-selekda kritik kuchsizlanish!")
        else:
            st.success(f"✅ {i+1}-selek barqaror.")
    
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(autorange='reversed'), height=450)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va Selek Interferensiyasi (RS2)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                           subplot_titles=("Termal Interferensiya (°C)", "Plastik Zonalar va Seleklar Buzilishi"))
    
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=failure_2d, x=x_axis, y=z_axis, colorscale='Jet', contours=dict(showlines=False)), row=2, col=1)
    
    # Seleklar o'rtasida buzilish nuqtalari (Red X)
    mask = plastic_zone_mask > 0.65
    fig_tm.add_trace(go.Scatter(x=grid_x[mask], y=grid_z[mask], mode='markers', 
                                marker=dict(symbol='x', color='red', size=3, opacity=0.3)), row=2, col=1)

    # Selek markazlarini belgilash
    for ps in pillar_status:
        fig_tm.add_vline(x=ps['x'], line_width=2, line_dash="dash", line_color="rgba(255,255,255,0.5)", row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=850, showlegend=False)
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
