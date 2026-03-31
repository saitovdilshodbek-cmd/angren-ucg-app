import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Sahifa sozlamalari
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Dinamik UCG Ssenariysi")

# --- Sidebar: Umumiy Sozlamalar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Obyekt-001")
time = st.sidebar.slider("Jarayon vaqti (soat):", 0, 100, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#000000', '#800080']

# --- Qatlamlar parametrlarini kiritish ---
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
            g = st.slider(f"GSI:", 0, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi:", value=10.0, key=f"m_{i}")
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color})
        total_depth += thick

# --- Matematik Model (Xatolar tuzatilgan qismi) ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth
thermal_deg = np.exp(-0.005 * time)

# Xato tuzatilgan qatorlar:
current_ucs = avg_ucs * thermal_deg
current_gsi = avg_gsi * thermal_deg 

sub_coeff = np.clip(0.95 - (current_gsi / 200) - (current_ucs / 800), 0.05, 0.9)

# Deformatsiya grafiklari uchun X o'qi
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 300)
r = total_depth / np.tan(np.radians(45))
s_max = layers_data[-1]['t'] * sub_coeff 
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x_axis / r)) - s_max
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth*20)) * (1 - np.exp(-0.05 * time))

# --- 2D DINAMIK ISSIQLIK VA YORIQLAR MODELI ---
grid_x, grid_z = np.meshgrid(np.linspace(-total_depth*1.2, total_depth*1.2, 120), np.linspace(0, total_depth + 50, 100))
source_z = total_depth - (layers_data[-1]['t'] / 2)

temp_2d = np.ones_like(grid_x) * 25 
cracks_2d = np.zeros_like(grid_x)

sources = {
    '1': {'x': -total_depth/2, 'start': 0},
    '3': {'x': total_depth/2, 'start': 30},
    '2': {'x': 0, 'start': 60}
}

for key, val in sources.items():
    if time > val['start']:
        dt = time - val['start']
        radius = 15 + (dt * 0.6)
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += 1075 * np.exp(-dist_sq / (2 * radius**2))
        crack_radius = radius * 1.4
        cracks_2d += np.exp(-dist_sq / (2 * crack_radius**2))

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_axis, y=uplift * 100, fill='tozeroy', line=dict(color='cyan', width=3)))
    fig1.update_layout(title="🔥 Termal ko'tarilish (cm)", template="plotly_dark", height=300)
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_axis, y=subsidence, fill='tozeroy', line=dict(color='magenta', width=3)))
    fig2.update_layout(title="📉 Mexanik cho'kish (m)", template="plotly_dark", height=300)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("🧱 Struktura")
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(title="Chuqurlik (m)", autorange='reversed'), height=500, showlegend=False)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🔥 Issiqlik va 🧱 Yoriqlanish Maydoni")
    fig_tm = make_subplots(rows=2, cols=1, subplot_titles=("Harorat Maydoni (°C)", "Jinslarning Yoriqlanish Zichligi"))
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=grid_x[0], y=grid_z[:,0], colorscale='Hot', zmin=25, zmax=1100), row=1, col=1)
    fig_tm.add_trace(go.Heatmap(z=cracks_2d, x=grid_x[0], y=grid_z[:,0], colorscale='Greys', zmin=0, zmax=1.2), row=2, col=1)
    fig_tm.update_layout(template="plotly_dark", height=700)
    fig_tm.update_yaxes(autorange='reversed')
    st.plotly_chart(fig_tm, use_container_width=True)

# Natijalar jadvali
st.divider()
st.table({
    "Parametr": ["Umumiy chuqurlik (m)", "O'rtacha joriy UCS (MPa)", "Cho'kish koeffitsiyenti", "Ssenariya holati"],
    "Qiymat": [f"{total_depth:.1f}", f"{current_ucs:.2f}", f"{sub_coeff:.3f}", 
               f"{'Faqat 1-nuqta' if time<=30 else '1 va 3-nuqtalar' if time<=60 else 'Hamma nuqtalar faol'}"]
})

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
