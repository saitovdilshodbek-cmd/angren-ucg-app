import plotly.graph_objects as go
import numpy as np

# 1. Asosiy figuraning statik qismlarini yaratamiz (Z-kesma va Stress maydoni)
# Z bo'yicha markaziy kesma (Center slice)
z_slice = temp_vol.shape[2] // 2

fig_complex = go.Figure()

# Statik Trace 1: Harorat kesmasi
fig_complex.add_trace(go.Surface(
    x=x_v[:, :, z_slice],
    y=y_v[:, :, z_slice],
    z=z_v[:, :, z_slice],
    surfacecolor=temp_vol[0, :, :, z_slice], # Dastlabki vaqtdagi kesma
    colorscale='Hot',
    cmin=25, cmax=1200,
    showscale=True,
    opacity=0.5,
    name="Temp Slice"
))

# Statik Trace 2: sigma1 - sigma3 differensial stress
stress_field = sigma1_3d - sigma3_3d
fig_complex.add_trace(go.Volume(
    x=x_v.flatten(),
    y=y_v.flatten(),
    z=z_v.flatten(),
    value=stress_field.flatten(),
    opacity=0.08,
    surface_count=20,
    colorscale='Jet',
    name="Stress Field"
))

# 2. Animatsiya kadrlari (Frames) ni yaratamiz
frames = []
for t in range(nt):
    frames.append(go.Frame(
        data=[
            # Isosurface - bu animatsiya qilinadigan qism
            go.Isosurface(
                x=x_v.flatten(),
                y=y_v.flatten(),
                z=z_v.flatten(),
                value=temp_vol[t].flatten(),
                isomin=600,
                isomax=1200,
                colorscale='Hot',
                showscale=False
            ),
            # Agar slice ham vaqtga qarab o'zgarishi kerak bo'lsa, 
            # bu yerga Surface trace-ni ham qo'shish mumkin
        ],
        name=f"t={t}"
    ))

# 3. Figuraga kadrlarni yuklash va tugmalarni sozlash
fig_complex.frames = frames

fig_complex.update_layout(
    title="Geofizik Jarayon: Harorat va Stress Maydoni",
    scene=dict(
        xaxis_title='X',
        yaxis_title='Y',
        zaxis_title='Z'
    ),
    updatemenus=[dict(
        type="buttons",
        buttons=[
            dict(
                label="Play",
                method="animate",
                args=[None, {"frame": {"duration": 100, "redraw": True}, "fromcurrent": True}]
            ),
            dict(
                label="Pause",
                method="animate",
                args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]
            )
        ],
        direction="left",
        pad={"r": 10, "t": 87},
        showactive=False,
        x=0.1,
        xanchor="right",
        y=0,
        yanchor="top"
    )]
)

fig_complex.show()
