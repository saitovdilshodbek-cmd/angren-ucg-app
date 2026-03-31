import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go

# Sahifa sozlamalari
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Hoek-Brown mezonlari asosida")

# --- Sidebar: Umumiy Sozlamalar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Obyekt-001")
time = st.sidebar.slider("Jarayon vaqti (soat):", 0, 100, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

# Geologik kesim uchun standart ranglar palitrasi
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#000000', '#800080']

# --- Qatlamlar parametrlarini dinamik yaratish ---
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Qatlamlar xususiyatlari")

layers_data = []
total_depth = 0

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i == int(num_layers)-1)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi - {i+1}:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(f"Qalinlik (m) - {i+1}:", value=50.0, key=f"t_{i}")
            u = st.number_input(f"UCS (MPa) - {i+1}:", value=40.0, key=f"u_{i}")
        with col2:
            st.write("")
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI - {i+1}:", 0, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi - {i+1}:", value=10.0, key=f"m_{i}")
            
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color})
        total_depth += thick

# --- Matematik Model (Vaznli o'rtacha va TM degradatsiya) ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth

# Termal kuchsizlanish
temp_effect = 1 - np.exp(-0.05 * time)
thermal_deg = np.exp(-0.005 * time)
current_ucs = avg_ucs * thermal_deg
current_gsi = avg_gsi * thermal_deg

# Deformatsiya hisobi (1D)
x = np.linspace(-total_depth, total_depth, 300)
uplift = (total_depth * 1e-5 * 1000) * 0.1 * np.exp(-(x**2) / (total_depth*40)) * temp_effect
sub_coeff = np.clip(0.95 - (current_gsi / 200) - (current_ucs / 800), 0.05, 0.9)
r = total_depth / np.tan(np.radians(45))
s_max = layers_data[-1]['t'] * sub_coeff 
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x / r)) - s_max

# --- 2D Issiqlik Xaritasi Simulyatsiyasi ---
grid_x, grid_z = np.meshgrid(np.linspace(-total_depth, total_depth, 100), np.linspace(0, total_depth + 50, 100))
source_z = total_depth - (layers_data[-1]['t'] / 2)
temp_2d = np.ones_like(grid_x) * 25 
sources = [-total_depth/2, 0, total_depth/2]
for s_x in sources:
    radius = 15 + (time * 0.5)
    dist_sq = (grid_x - s_x)**2 + (grid_z - source_z)**2
    temp_2d += (1100 * temp_effect) * np.exp(-dist_sq / (2 * radius**2))

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x, y=uplift * 100, fill='tozeroy', line=dict(color='cyan', width=3)))
    fig1.update_layout(title="🔥 Termal ko'tarilish (cm)", template="plotly_dark", xaxis_title="Masofa (m)", yaxis_title="Balandlik (cm)")
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x, y=subsidence, fill='tozeroy', line=dict(color='magenta', width=3)))
    fig2.update_layout(title="📉 Mexanik cho'kish (m)", template="plotly_dark", xaxis_title="Masofa (m)", yaxis_title="Chuqurlik (m)")
    st.plotly_chart(fig2, use_container_width=True)

# --- Geologik Kesim, Legenda va Heatmap ---
st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 2])

with c1:
    st.subheader("📚 Legenda")
    legend_html = "<div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333;'>"
    for l in layers_data:
        legend_html += f"""
            <div style='display: flex; align-items: center; margin-bottom: 12px;'>
                <div style='width: 20px; height: 40px; background-color: {l['color']}; border: 1px solid white; border-radius: 3px; margin-right: 12px;'></div>
                <div style='color: white; line-height: 1.2;'>
                    <b>{l['name']}</b><br>
                    <span style='font-size: 0.85em; opacity: 0.8;'>{l['t']}m | UCS:{l['ucs']} | GSI:{l['gsi']}</span>
                </div>
            </div>"""
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

with c2:
    st.subheader("🧱 Struktura")
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Svit'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.5))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", showlegend=False, 
                             yaxis=dict(title="Chuqurlik (m)", autorange='reversed'), xaxis=dict(showticklabels=False),
                             height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_strata, use_container_width=True)

with c3:
    st.subheader("🔥 Issiqlik maydoni (2D)")
    fig_heat = go.Figure(data=go.Heatmap(z=temp_2d, x=np.linspace(-total_depth, total_depth, 100), 
                                        y=np.linspace(0, total_depth + 50, 100), colorscale='Hot', zmin=25, zmax=1100))
    fig_heat.update_layout(template="plotly_dark", yaxis=dict(autorange='reversed'), height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_heat, use_container_width=True)

# Natijalar jadvali
st.divider()
st.table({
    "Parametr": ["Umumiy chuqurlik (m)", "O'rtacha joriy UCS (MPa)", "O'rtacha joriy GSI", "Cho'kish koeffitsiyenti"],
    "Qiymat": [f"{total_depth:.1f}", f"{current_ucs:.2f}", f"{current_gsi:.1f}", f"{sub_coeff:.3f}"]
})

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
