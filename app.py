import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
import matplotlib.colors as mcolors

# Sahifa sozlamalari
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Hoek-Brown mezonlari asosida")

# --- Sidebar: Umumiy Sozlamalar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Obyekt-001")
time = st.sidebar.slider("Jarayon vaqti (soat):", 0, 100, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

# --- Qatlamlar parametrlarini dinamik yaratish ---
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Qatlamlar xususiyatlari")

# Geologik kesim uchun ranglar palitrasi
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#000000', '#800080'] # Siz yuborgan rasmga o'xshash
layers_data = []
total_depth = 0

for i in range(int(num_layers)):
    with st.sidebar.expander(f"{i+1}-qatlam parametrlari", expanded=(i==0)):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input(f"Nomi - {i+1}:", value=f"Qatlam-{i+1}", key=f"name_{i}")
            thick = st.number_input(f"Qalinlik (m) - {i+1}:", value=50.0, key=f"t_{i}")
            u = st.number_input(f"UCS (MPa) - {i+1}:", value=40.0, key=f"u_{i}")
        with col2:
            st.write("") # Bo'sh joy
            st.write("")
            st.write("")
            color = st.color_picker(f"Rangi:", strata_colors[i % len(strata_colors)], key=f"color_{i}")
            g = st.slider(f"GSI - {i+1}:", 0, 100, 60, key=f"g_{i}")
            m = st.number_input(f"mi - {i+1}:", value=10.0, key=f"m_{i}")
            
        layers_data.append({'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color})
        total_depth += thick

# --- Matematik Model (Vaznli o'rtacha va TM degradatsiya) ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth

# Termal kuchsizlanish (TM Link)
thermal_deg = np.exp(-0.005 * time)
current_ucs = avg_ucs * thermal_deg
current_gsi = avg_gsi * thermal_deg

# Deformatsiya hisobi
x = np.linspace(-total_depth, total_depth, 300)

# 1. Termal ko'tarilish
temp_effect = 1 - np.exp(-0.05 * time)
uplift = (total_depth * 1e-5 * 1000) * 0.1 * np.exp(-(x**2) / (total_depth*40)) * temp_effect

# 2. Mexanik cho'kish
sub_coeff = 0.95 - (current_gsi / 200) - (current_ucs / 800)
sub_coeff = np.clip(sub_coeff, 0.05, 0.9)

r = total_depth / np.tan(np.radians(45))
# Eng pastki qatlam qalinligini asosiy bo'shliq sifatida olamiz
s_max = layers_data[-1]['t'] * sub_coeff 
subsidence = s_max * 0.5 * (1 + erf(np.sqrt(np.pi) * x / r)) - s_max

# --- Grafiklarni chiqarish ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col1, col2 = st.columns(2)

with col1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x, y=uplift * 100, fill='tozeroy', line=dict(color='cyan')))
    fig1.update_layout(title="🔥 Termal ko'tarilish (cm)", template="plotly_dark", xaxis_title="Masofa (m)", yaxis_title="Balandlik (cm)")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x, y=subsidence, fill='tozeroy', line=dict(color='magenta')))
    fig2.update_layout(title="📉 Mexanik cho'kish (m)", template="plotly_dark", xaxis_title="Masofa (m)", yaxis_title="Chuqurlik (m)")
    st.plotly_chart(fig2, use_container_width=True)

# --- Geologik Kesim va Legenda (New Section) ---
st.markdown("---")
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("📚 Legenda")
    legend_html = "<div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px;'>"
    for l in layers_data:
        legend_html += f"""
            <div style='display: flex; align-items: center; margin-bottom: 10px;'>
                <div style='width: 30px; height: 30px; background-color: {l['color']}; border-radius: 5px; margin-right: 15px;'></div>
                <div style='color: white;'>
                    <b>{l['name']}</b><br>
                    <span style='font-size: 0.9em; opacity: 0.8;'>{l['t']} m | UCS: {l['ucs']} | GSI: {l['gsi']}</span>
                </div>
            </div>
        """
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

with c2:
    st.subheader("🧱 Geologik qatlamlar struktursi")
    
    # Stratigrafik kesimni hisoblash
    current_depth = 0
    bar_data = []
    
    for l in layers_data:
        bar_data.append(go.Bar(
            y=[l['t']],
            x=['Kesim'],
            name=l['name'],
            marker_color=l['color'],
            hovertemplate=f"<b>{l['name']}</b><br>Qalinlik: %{{y}} m<br>Chuqurlik: {current_depth:.1f} - {current_depth + l['t']:.1f} m<extra></extra>"
        ))
        current_depth += l['t']

    fig_strata = go.Figure(data=bar_data)
    
    # Stacking (qatlamlarni bir-birining ustiga qo'yish)
    fig_strata.update_layout(
        barmode='stack',
        template="plotly_dark",
        yaxis=dict(title="Chuqurlik (m)", autorange='reversed'), # Chuqurlik pastga yo'naltirilgan
        xaxis=dict(title="", showticklabels=False),
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False # Legenda chap tomonda alohida ko'rsatilgan
    )
    st.plotly_chart(fig_strata, use_container_width=True)

# --- Natijalar jadvali ---
st.divider()
st.subheader("📋 O'rtacha hisoblangan ko'rsatkichlar")
st.table({
    "Parametr": ["Umumiy chuqurlik (m)", "O'rtacha joriy UCS (MPa)", "O'rtacha joriy GSI", "Cho'kish koeffitsiyenti"],
    "Qiymat": [f"{total_depth:.1f}", f"{current_ucs:.2f}", f"{current_gsi:.1f}", f"{sub_coeff:.3f}"]
})

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
