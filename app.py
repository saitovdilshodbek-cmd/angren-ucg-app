import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
import pydeck as pdk
import torch
import torch.nn as nn

# ==============================================================================
# Sahifa sozlamalari
# ==============================================================================
st.set_page_config(page_title="Universal Geomechanical Monitor", layout="wide")
st.title("🌐 Universal Yer yuzasi Deformatsiyasi Monitoringi")
st.markdown("### Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi")

# ==============================================================================
# GPU qo'llab-quvvatlash
# ==============================================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if device.type == "cuda":
    st.sidebar.success(f"✅ GPU ishlatilmoqda: {torch.cuda.get_device_name(0)}")
else:
    st.sidebar.info("⚠️ CPU ishlatilmoqda (GPU yo'q)")

# ==============================================================================
# Matematik metodologiya (o'zgarishsiz)
# ==============================================================================
st.sidebar.header("🧮 Matematik Metodologiya")
formula_option = st.sidebar.selectbox(
    "Formulalarni ko'rish:",
    ["Yopish", "1. Hoek-Brown Failure (2018)",
     "2. Thermal Damage & Permeability",
     "3. Thermal Stress & Tension",
     "4. Pillar & Subsidence"]
)
# ... (qolgan metodologiya kodi o'zgarmaydi, qisqartirildi)
# Eslatma: To'liq kodda metodologiya qismi avvalgidek qoladi.
# Uzunlikni saqlash uchun bu yerda qisqartirilgan holda keltirilmoqda.

# ==============================================================================
# ⚙️ SIDEBAR: PARAMETRLAR (qo'shimcha elementlar bilan)
# ==============================================================================
st.sidebar.header("⚙️ Umumiy parametrlar")
obj_name      = st.sidebar.text_input("Loyiha nomi:", value="Angren-UCG-001")
time_h        = st.sidebar.slider("Jarayon vaqti (soat):", 1, 150, 24)
num_layers    = st.sidebar.number_input("Qatlamlar soni:", min_value=1, max_value=5, value=3)
tensile_mode  = st.sidebar.selectbox("Tensile modeli:", ["Empirical (UCS)", "HB-based (auto)", "Manual"])

# ===== YANGI: Real-time simulyatsiya =====
run_sim = st.sidebar.checkbox("▶️ Real-time ishga tushirish")
if run_sim:
    # Simulyatsiya vaqtini saqlash
    if "sim_time" not in st.session_state:
        st.session_state.sim_time = 1
    if st.session_state.sim_time <= time_h:
        time_h = st.session_state.sim_time  # joriy vaqtni o'rnatish
        # Vaqtni oshirish va rerun
        st.session_state.sim_time += 1
        st.experimental_rerun()
    else:
        st.session_state.sim_time = 1
        st.success("Simulyatsiya tugadi!")
else:
    st.session_state.sim_time = 1

# ===== YANGI: Fayl yuklash =====
uploaded_file = st.sidebar.file_uploader("📂 Real dataset yuklash (CSV)", type=["csv"])

# ==============================================================================
# Qatlam ma'lumotlari (avvalgidek)
# ==============================================================================
strata_colors = ['#87CEEB', '#F4A460', '#D3D3D3', '#F5DEB3', '#555555']
layers_data   = []
total_depth   = 0.0
# ... (qatlam yig'ish kodi avvalgidek)

# ==============================================================================
# GRID va MANBA (avvalgidek)
# ==============================================================================
# ... (x_axis, z_axis, grid_x, grid_z, source_z, H_seam, sigma_v, Hoek-Brown...)

# ==============================================================================
# Issiqlik maydoni va FDM (avvalgidek)
# ==============================================================================
# ... (temp_2d, delta_T, damage, sigma_ci, etc.)

# ==============================================================================
# 🧠 AI MODEL — Neural Network (GPU bilan)
# ==============================================================================
@st.cache_resource(show_spinner=False)
def get_nn_model():
    """PyTorch modelini yaratish va o'qitish (GPU da)"""
    # Dataset generator
    def generate_ucg_dataset(n=10000):
        data = []
        for _ in range(n):
            T = np.random.uniform(20, 1000)
            sigma1 = np.random.uniform(0, 50)
            sigma3 = np.random.uniform(0, 30)
            depth = np.random.uniform(0, 300)
            damage = 1 - np.exp(-0.002 * max(T - 100, 0))
            strength = 40 * (1 - damage)
            collapse = 1 if (sigma1 > strength or T > 700) else 0
            data.append([T, sigma1, sigma3, depth, collapse])
        return np.array(data)

    class CollapseNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(4, 32),
                nn.ReLU(),
                nn.Linear(32, 64),
                nn.ReLU(),
                nn.Linear(64, 1),
                nn.Sigmoid()
            )
        def forward(self, x):
            return self.net(x)

    data = generate_ucg_dataset()
    X = torch.tensor(data[:, :-1], dtype=torch.float32).to(device)
    y = torch.tensor(data[:, -1], dtype=torch.float32).view(-1, 1).to(device)

    model = CollapseNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.BCELoss()

    for epoch in range(50):
        pred = model(X)
        loss = loss_fn(pred, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    model.eval()
    return model

def predict_nn(model, temp, s1, s3, depth):
    X = np.column_stack([temp.flatten(), s1.flatten(), s3.flatten(), depth.flatten()])
    X_t = torch.tensor(X, dtype=torch.float32).to(device)
    with torch.no_grad():
        pred = model(X_t).cpu().numpy()
    return pred.reshape(temp.shape)

# Modelni olish
nn_model = get_nn_model()

# Agar real dataset yuklangan bo'lsa, modelni qayta o'qitish
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if all(col in df.columns for col in ["T", "sigma1", "sigma3", "depth", "collapse"]):
        X_real = torch.tensor(df[["T", "sigma1", "sigma3", "depth"]].values, dtype=torch.float32).to(device)
        y_real = torch.tensor(df["collapse"].values, dtype=torch.float32).view(-1, 1).to(device)
        # Qisqa qayta o'qitish
        optimizer = torch.optim.Adam(nn_model.parameters(), lr=0.001)
        loss_fn = nn.BCELoss()
        for epoch in range(20):
            pred = nn_model(X_real)
            loss = loss_fn(pred, y_real)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        st.success("✅ Model real data bilan qayta o‘qitildi!")

# AI bashorat
collapse_pred = predict_nn(nn_model, temp_2d, sigma1_act, sigma3_act, grid_z)

# ==============================================================================
# Selek optimizatsiyasi (avvalgidek)
# ==============================================================================
# ... (rec_width, pillar_strength, y_zone, fos_2d, optimal_width_ai)

# ==============================================================================
# Metrikalar (avvalgidek)
# ==============================================================================
st.subheader(f"📊 {obj_name}: Monitoring va Ekspert Xulosasi")
# ... (5 ta metric)

# ==============================================================================
# Grafiklar (avvalgidek)
# ==============================================================================
# ... (cho'kish, Hoek-Brown)

# ==============================================================================
# 🔥 TM MAYDONI (avvalgidek, AI nomi o'zgartirildi)
# ==============================================================================
# ... (fig_tm)

# ==============================================================================
# 🌍 Geolokatsiya xaritasi (YANGI)
# ==============================================================================
st.markdown("---")
st.subheader("🌍 Geolokatsiya xaritasi")
view_state = pdk.ViewState(
    latitude=41.2995,   # Angren taxminiy koordinatasi
    longitude=69.2401,
    zoom=10
)
layer = pdk.Layer(
    "ScatterplotLayer",
    data=pd.DataFrame({
        "lat": [41.2995],
        "lon": [69.2401],
        "name": [obj_name]
    }),
    get_position='[lon, lat]',
    get_radius=500,
    get_color=[255, 0, 0],
    pickable=True,
    tooltip=True
)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}"}))

# ==============================================================================
# 📄 Hisobot yuklab olish (YANGI)
# ==============================================================================
if st.button("📄 Hisobot yuklab olish"):
    report = f"""
    ========================================
    LOYIHA: {obj_name}
    Vaqt: {time_h} soat
    ========================================
    
    📊 Asosiy natijalar:
    - Pillar Strength (σp): {pillar_strength:.2f} MPa
    - Plastik zona (y): {y_zone:.1f} m
    - Kamera hajmi: {void_volume:.1f} m²
    - Maks. o'tkazuvchanlik: {np.max(perm):.1e} m²
    - AI Collapse ehtimoli (o'rtacha): {np.mean(collapse_pred):.3f}
    
    🔥 Termal parametrlar:
    - Maksimal harorat: {T_source_max} °C
    - Termal kuchlanish: {sigma_thermal.max():.2f} MPa
    - Termal degradatsiya: {damage.max():.2%}
    
    ⚙️ Selek tavsiyasi:
    - Klassik usul: {rec_width} m
    - AI optimizatsiya: {optimal_width_ai:.1f} m
    - Xavfsizlik koeffitsiyenti (FOS): {fos_2d[~void_mask_permanent].mean() if np.any(~void_mask_permanent) else 0:.2f}
    
    📌 Xulosa: 
    - Xavf darajasi: {"YUQORI" if pillar_strength < 15 else "O'RTA" if pillar_strength < 25 else "PAST"}
    - Tavsiya etilgan selek eni: {optimal_width_ai:.1f} m
    """
    st.download_button("⬇️ Hisobotni yuklab olish", report, file_name=f"{obj_name}_report.txt", mime="text/plain")

# ==============================================================================
# Kompleks monitoring paneli va 3D (avvalgidek)
# ==============================================================================
# ... (generate_integrated_3d, trendlar, interpretatsiya)

# ==============================================================================
# Chuqurlashtirilgan ilmiy hisobot (avvalgidek)
# ==============================================================================
# ... (tabs)

# ==============================================================================
# Footer
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.write(f"Tuzuvchi: {obj_name.split('-')[0]} / Saitov Dilshodbek")
