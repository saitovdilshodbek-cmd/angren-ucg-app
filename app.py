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

mb = avg_mi * np.exp((avg_gsi - 100) / 28)
s_hb = np.exp((avg_gsi - 100) / 9)
a_hb = 0.5 + (1/6)*(np.exp(-avg_gsi/15) - np.exp(-20/3))

x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 150)
z_axis = np.linspace(0, total_depth + 50, 120)
grid_x, grid_z = np.meshgrid(x_axis, z_axis)

source_z = total_depth - (layers_data[-1]['t'] / 2)
temp_2d = np.ones_like(grid_x) * 25 
plastic_zone_mask = np.zeros_like(grid_x) # RS2 dagi qizil X larni simulyatsiya qilish uchun

# Dinamik manbalar (RS2 rasmlaridagi kabi vaqtga bog'liq)
sources = {
    '1': {'x': -total_depth/3, 'start': 0}, 
    '2': {'x': 0, 'start': 40}, 
    '3': {'x': total_depth/3, 'start': 80}
}

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
        
        # RS2 dagi plastik zonani simulyatsiya qilish (kamera atrofida kuchliroq)
        if dt > 5:
            plastic_influence = np.exp(-dist_sq / (2 * (radius * 1.3)**2))
            plastic_zone_mask = np.maximum(plastic_zone_mask, plastic_influence)

# Failure Model
sigma_v = 0.027 * grid_z
strength = avg_ucs * np.exp(-0.002 * (temp_2d - 20))
failure_2d = sigma_v / (strength + 1e-6)

# --- HOEK-BROWN ENVELOPES ---
sigma3_axis = np.linspace(0, avg_ucs * 0.5, 100)
reduction_hot = np.exp(-0.002 * (T_source_max - 20))
sigma1_initial = sigma3_axis + avg_ucs * (mb * sigma3_axis / avg_ucs + s_hb)**a_hb
sigma1_hot = sigma3_axis + (avg_ucs * reduction_hot) * (mb * sigma3_axis / (avg_ucs * reduction_hot) + s_hb)**a_hb

# Subsidence
angle_sub = 35
r_sub = total_depth / np.tan(np.radians(angle_sub))
s_max = (layers_data[-1]['t'] * 0.04) * (min(time_h, 120) / 120)
subsidence_profile = -s_max * np.exp(-(x_axis**2) / (2 * (r_sub/2.5)**2))

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

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
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_initial, name='Normal (20°C)', line=dict(color='#FF4B4B', width=3)))
    fig_hb.add_trace(go.Scatter(x=sigma3_axis, y=sigma1_hot, name=f'Issiq ({T_source_max}°C)', line=dict(color='#FFA500', width=4)))
    fig_hb.update_layout(title="🛡️ Jins Mustahkamligi (Hoek-Brown)", template="plotly_dark", height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_hb, use_container_width=True)

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
    st.subheader("🔥 TM Maydoni va Strukturaviy Holat (RS2 Simulyatsiyasi)")
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                           subplot_titles=("Harorat Maydoni (°C)", "Buzilish va Plastik zonalar (Shear Failure)"))
    
    # Harorat Heatmap
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="°C", x=1.02, y=0.78, len=0.45)), row=1, col=1)
    
    # Stress/Strength Contour
    fig_tm.add_trace(go.Contour(z=failure_2d, x=x_axis, y=z_axis, colorscale='Jet',
                                contours=dict(coloring='heatmap', showlines=False),
                                colorbar=dict(title="Index", x=1.02, y=0.22, len=0.45)), row=2, col=1)
    
    # --- RS2 uslubidagi "Shear Failure" (Qizil X nuqtalar) qo'shish ---
    # Plastik zona yetarli darajaga yetganda nuqtalarni ko'rsatamiz
    px = grid_x[plastic_zone_mask > 0.7]
    pz = grid_z[plastic_zone_mask > 0.7]
    if len(px) > 0:
        fig_tm.add_trace(go.Scatter(x=px, y=pz, mode='markers', 
                                    marker=dict(symbol='x', color='red', size=4, opacity=0.4),
                                    name="Shear Failure"), row=2, col=1)

    # Deformatsiya chizig'i
    fig_tm.add_trace(go.Scatter(x=x_axis, y=subsidence_profile * 50, mode='lines', 
                                line=dict(color='white', width=2, dash='dash'), name="Egrilik"), row=2, col=1)

    fig_tm.update_layout(template="plotly_dark", height=850, showlegend=False)
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

st.divider()
st.table({
    "Ko'rsatkich": ["Hoek-Brown mb", "Hoek-Brown s", "Maksimal Cho'kish (m)", "Faol kameralar"],
    "Qiymat": [f"{mb:.3f}", f"{s_hb:.5f}", f"{abs(np.min(subsidence_profile)):.4f}", 
               f"{sum(1 for v in sources.values() if time_h > v['start'])} ta"]
})

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
