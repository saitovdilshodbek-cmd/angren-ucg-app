import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Sahifa sozlamalari
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")

st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Dinamik UCG Ssenariysi (RS2 Style)")

# --- Sidebar: Umumiy Sozlamalar ---
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time = st.sidebar.slider("Jarayon vaqti (soat):", 0, 150, 24)
num_layers = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)

st.sidebar.subheader("🔥 Yonish muddati")
burn_duration = st.sidebar.number_input("Kamera yonish muddati (soat):", value=40)

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
        
        layers_data.append({
            'name': name, 't': thick, 'ucs': u, 'gsi': g, 'mi': m, 'color': color, 'z_start': total_depth
        })
        total_depth += thick

# --- 🎓 ILMIY METODIKA VA FORMULALAR (LINKLAR BILAN) ---
with st.expander("🎓 ILMIY METODIKA VA MATEMATIK MODELLAR (MA'LUMOTNOMA)"):
    st.markdown("Ushbu monitoring tizimi xalqaro miqyosda tan olingan geomexanik metodlar asosida ishlaydi:")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.markdown(r"""
        #### 1. Termal Degradatsiya (Strength Reduction)
        Jins mustahkamligining harorat ta'sirida pasayishi:
        $$Strength_{t} = Strength_{initial} \cdot e^{-0.005 \cdot t}$$
        🔗 [Ilmiy asos: Thermo-mechanical modeling of UCG](https://www.sciencedirect.com/science/article/pii/S016651621400155X)
        
        #### 2. Cho'kish Koeffitsiyenti (Sub-coeff)
        GSI va UCS qiymatlari asosidagi bog'liqlik:
        $$a = 0.95 - \frac{GSI}{200} - \frac{UCS}{800}$$
        🔗 [Metodika: Hoek-Brown Failure Criterion](https://www.rocscience.com/help/rs2/theory_guides/theory_guide/Hoek-Brown_Failure_Criterion.htm)
        """)
    with f_col2:
        st.markdown(r"""
        #### 3. Gauss-Knothe Profili
        Yer yuzasidagi cho'kishning dinamik taqsimoti:
        $$S(x) = -S_{max} \cdot \exp\left(-\frac{x^2}{2\sigma^2}\right)$$
        🔗 [Nazariya: Principles of Subsidence Engineering](https://www.researchgate.net/publication/285061614_Principles_of_subsidence_engineering)
        
        #### 4. Kamera Dinamikasi
        Kamera radiusi kengayishi va sovish jarayoni:
        $R(t) = 15 + 0.6 \cdot \Delta t$
        🔗 [Dasturiy vosita: Streamlit Documentation](https://docs.streamlit.io/)
        """)

# --- Matematik Model (Hisob-kitoblar) ---
avg_ucs = sum(l['ucs'] * l['t'] for l in layers_data) / total_depth
avg_gsi = sum(l['gsi'] * l['t'] for l in layers_data) / total_depth
thermal_deg = np.exp(-0.005 * time)

current_ucs = avg_ucs * thermal_deg
current_gsi = avg_gsi * thermal_deg 

sub_coeff = np.clip(0.95 - (current_gsi / 200) - (current_ucs / 800), 0.05, 0.9)

# --- VAQTGA BOG'LIQ DINAMIK DEFORMATSIYA ---
x_axis = np.linspace(-total_depth*1.5, total_depth*1.5, 300)
r_dynamic = (total_depth / np.tan(np.radians(35))) * (0.8 + 0.2 * min(time, 100) / 100)
s_max_dynamic = (layers_data[-1]['t'] * sub_coeff) * (min(time, 100) / 100)
subsidence_dynamic = -s_max_dynamic * np.exp(-(x_axis**2) / (2 * (r_dynamic/2.5)**2))

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
        active_time = time - val['start']
        if active_time <= burn_duration:
            radius = 15 + (active_time * 0.6)
            current_temp = 1075
        else:
            radius = 15 + (burn_duration * 0.6)
            cooling_time = active_time - burn_duration
            current_temp = 1075 * np.exp(-0.03 * cooling_time)
            
        dist_sq = (grid_x - val['x'])**2 + (grid_z - source_z)**2
        temp_2d += current_temp * np.exp(-dist_sq / (2 * radius**2))
        cracks_2d += np.exp(-dist_sq / (2 * (radius * 1.4)**2))

# --- VIZUALIZATSIYA ---
st.subheader(f"📊 {obj_name}: Monitoring Natijalari")
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_axis, y=uplift * 100, fill='tozeroy', line=dict(color='cyan', width=3)))
    fig1.update_layout(title="🔥 Termal ko'tarilish (cm)", template="plotly_dark", height=250, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_axis, y=subsidence_dynamic, fill='tozeroy', line=dict(color='magenta', width=3)))
    fig2.update_layout(title="📉 Mexanik cho'kish (m)", template="plotly_dark", height=250, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader("🧱 Geologik Kesim")
    fig_strata = go.Figure()
    for l in layers_data:
        fig_strata.add_trace(go.Bar(x=['Kesim'], y=[l['t']], name=l['name'], marker_color=l['color'], width=0.4))
    fig_strata.update_layout(barmode='stack', template="plotly_dark", yaxis=dict(title="Chuqurlik (m)", autorange='reversed'), height=700, showlegend=True)
    st.plotly_chart(fig_strata, use_container_width=True)

with c2:
    st.subheader("🔥 TM Maydoni va 🧱 Strukturaviy Deformatsiya")
    fig_tm = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Harorat Maydoni (°C)", "Yoriqlanish va Yer yuzasi Deformatsiyasi (RS2 Style)")
    )
    
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=grid_x[0], y=grid_z[:,0], 
        colorscale='Hot', zmin=25, zmax=1100,
        colorbar=dict(title="°C", x=1.02, y=0.78, len=0.45)
    ), row=1, col=1)
    
    fig_tm.add_trace(go.Contour(
        z=cracks_2d, x=grid_x[0], y=grid_z[:,0],
        colorscale='Jet', 
        line_width=0.5,
        contours=dict(coloring='heatmap', showlines=True, start=0, end=1.0, size=0.1),
        colorbar=dict(
            title=dict(text="Zichlik", side="top"), 
            x=1.02, y=0.22, len=0.45,
            tickvals=[0, 0.25, 0.5, 0.75, 1.0],
            ticktext=["Barqaror", "Past", "O'rta", "Yuqori", "Kritik"]
        ),
        zmin=0, zmax=1.1, name="Yoriqlanish"
    ), row=2, col=1)

    # --- TO'G'IRLANGAN DEFORMATSIYA CHIZIG'I ---
    # Koeffitsiyentni o'zgartirib, chiziqni pastga (0 dan chuqurlik tomonga) yo'naltirdik
    fig_tm.add_trace(go.Scatter(
        x=x_axis, y=subsidence_dynamic * -30, # -30 vizualizatsiya uchun masshtab
        mode='lines', line=dict(color='white', width=4, dash='dash'),
        name="Dinamik Profil"
    ), row=2, col=1)

    for layer in layers_data:
        fig_tm.add_shape(type="line", x0=min(x_axis), y0=layer['z_start'], x1=max(x_axis), y1=layer['z_start'],
                         line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"), row=2, col=1)
    
    fig_tm.update_layout(template="plotly_dark", height=850, margin=dict(l=20, r=80, t=40, b=20))
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=1, col=1)
    # Range ni -50 dan boshladik, shunda profil yer yuzasidan (0 dan) pastga tushadi
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', range=[total_depth + 50, -50], row=2, col=1)
    
    st.plotly_chart(fig_tm, use_container_width=True)

# Natijalar jadvali
st.divider()
st.table({
    "Parametr": ["Umumiy chuqurlik (m)", "Maksimal cho'kish (m)", "Yonish muddati", "Ssenariya holati"],
    "Qiymat": [f"{total_depth:.1f}", f"{abs(s_max_dynamic):.3f}", f"{burn_duration} soat", 
               f"{'Sovish jarayoni' if time > burn_duration else 'Faol yonish'}"]
})

st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek")
