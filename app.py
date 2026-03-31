import streamlit as st
import numpy as np
from scipy.special import erf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Matematik Model va Ma'lumotlarni Tayyorlash ---
# (Avvalgi kod qismlari o'zgarishsiz qoladi, faqat vizualizatsiya qismi yangilanadi)

# ... (layers_data, total_depth, temp_2d, cracks_2d hisoblash qismlari) ...

with c2:
    st.subheader("🏗️ Geotexnik Kuchlanish va Deformatsiya Tahlili")
    
    # 2D model uchun subplotlar
    fig_tm = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("🌡️ Termal Maydon Tarqalishi (°C)", "🧱 Jinslarning Yoriqlanishi va Er yuzasi Cho'kishi")
    )

    # 1. Termal Maydon (Heatmap)
    fig_tm.add_trace(go.Heatmap(
        z=temp_2d, x=grid_x[0], y=grid_z[:,0], 
        colorscale='Hot', zmin=25, zmax=1100,
        colorbar=dict(title="Harorat (°C)", x=1.05, y=0.78, len=0.4)
    ), row=1, col=1)

    # 2. Yoriqlanish Zichligi (RS2 Style Contour)
    # Kontur darajalarini aniq belgilaymiz (0.1 dan 1.0 gacha)
    fig_tm.add_trace(go.Contour(
        z=cracks_2d, x=grid_x[0], y=grid_z[:,0],
        colorscale='Jet',
        contours=dict(
            start=0, end=1, size=0.1,
            showlines=True,
            coloring='heatmap'
        ),
        line_width=0.5,
        colorbar=dict(title="Yoriqlanish<br>Koeffitsiyenti", x=1.05, y=0.22, len=0.4),
        name="Yoriqlanish"
    ), row=2, col=1)

    # 3. Yer yuzasi deformatsiyasi (Oq chiziq)
    # Bu chiziqni vizual ravishda yuqorida (minus qiymatda) ko'rsatish uchun:
    fig_tm.add_trace(go.Scatter(
        x=x_axis, 
        y=subsidence * 50 - 50,  # Masshtabni va joylashuvni to'g'irlash
        mode='lines',
        line=dict(color='white', width=4, dash='dash'),
        name="Yer yuzasi cho'kishi (Profil)"
    ), row=2, col=1)

    # Qatlamlar chegarasini chizish (RS2 kabi aniq chiziqlar)
    for layer in layers_data:
        fig_tm.add_shape(type="line",
            x0=min(x_axis), y0=layer['z_start'], x1=max(x_axis), y1=layer['z_start'],
            line=dict(color="rgba(255,255,255,0.4)", width=1.5, dash="solid"),
            row=2, col=1
        )

    # Grafik sozlamalari
    fig_tm.update_layout(
        template="plotly_dark", 
        height=900, 
        margin=dict(l=50, r=120, t=50, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Y o'qini teskari qilish (Chuqurlik pastga qarab ortadi)
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(title_text="Chuqurlik (m)", autorange='reversed', row=2, col=1)
    fig_tm.update_xaxes(title_text="Masofa (m)", row=2, col=1)

    st.plotly_chart(fig_tm, use_container_width=True)
