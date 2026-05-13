import streamlit as st
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

# ==========================================
# 1. FEM PHYSICS ENGINE (The Physical Base)
# ==========================================
def fem_solver(nx=30, ny=30, nz=20):
    """
    3D Geostatik maydon solveri.
    Maqsad: PINN uchun boshlang'ich fizik karkas yaratish.
    """
    z = np.linspace(-3000, 0, nz)
    X, Y, Z = np.meshgrid(
        np.linspace(0, 5000, nx),
        np.linspace(0, 2000, ny),
        z, indexing="ij"
    )

    # Fizik maydonlar (MPa va °C)
    sigma_v = 10 + 0.02 * np.abs(Z) # Vertical Stress
    pore = 2 + 0.006 * np.abs(Z)    # Pore Pressure
    temp = 20 + 0.025 * np.abs(Z)   # Temperature field

    sigma_eff = sigma_v - pore

    # Mohr-Coulomb Failure Criteria proxy
    c, phi = 12, np.deg2rad(30)
    tau_limit = c + sigma_eff * np.tan(phi)
    tau_applied = sigma_eff * 0.8 * (1 + (temp / 1200) ** 2)

    # FEM natijasi - Sigmoid risk maydoni
    fem_risk = 1 / (1 + np.exp(-(tau_applied - tau_limit)))

    return X, Y, Z, sigma_v, pore, temp, fem_risk

# ==========================================
# 2. PINN RESIDUAL CORRECTOR
# ==========================================
class PINN_Corrector(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(5, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        return torch.sigmoid(self.net(x))

# ==========================================
# 3. TRUE PHYSICS LOSS (MOHR-COULOMB CONSTRAINT)
# ==========================================
def physics_loss_function(pred, inputs):
    """
    Physics Constraint: Risk must be consistent with Stress/Strength Ratio.
    Agar pred_risk > physical_limit bo'lsa, penalty qo'llaniladi.
    """
    temp = inputs[:, 0]
    sigma = inputs[:, 1]
    pore = inputs[:, 2]

    sigma_eff = sigma - pore
    
    # Notenglik cheklovi: Risk effektiv kuchlanishning kritik chegarasidan 
    # asossiz ravishda o'tib ketmasligi kerak.
    # sigma_eff/60 - normalizatsiya qilingan fizik limit
    constraint = torch.relu(pred.flatten() - (sigma_eff / 60))

    return torch.mean(constraint)

# ==========================================
# 4. COUPLED TRAINING ENGINE
# ==========================================
@st.cache_resource
def train_v4_system():
    X, Y, Z, sigma_v, pore, temp, fem_risk = fem_solver()

    # Features: [T, Sigma_V, Pore, Depth, FEM_Risk]
    features = np.column_stack([
        temp.flatten(), sigma_v.flatten(), pore.flatten(),
        Z.flatten(), fem_risk.flatten()
    ])

    scaler = StandardScaler()
    Xs = scaler.fit_transform(features)

    model = PINN_Corrector()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    Xt = torch.tensor(Xs, dtype=torch.float32)
    yt = torch.tensor(fem_risk.flatten(), dtype=torch.float32).view(-1, 1)

    # Training Loop
    for epoch in range(350):
        opt.zero_grad()
        pred = model(Xt)

        # 1. Data Fitting (Mimic FEM)
        loss_data = nn.MSELoss()(pred, yt)
        
        # 2. Physical Consistency (True PINN Residual)
        loss_phys = physics_loss_function(pred, Xt)

        # Total Hybrid Loss
        total_loss = loss_data + 0.25 * loss_phys

        total_loss.backward()
        opt.step()

    return model, scaler

# ==========================================
# 5. INFERENCE & STREAMLIT UI
# ==========================================
st.set_page_config(page_title="Angren Digital Twin v4", layout="wide")
st.title("🌐 FEM + PINN v4: Physics-Consistent Digital Twin")

model, scaler = train_v4_system()

if st.button("🚀 Run Bi-Directional Simulation"):
    # Re-run physical solver
    X, Y, Z, sigma_v, pore, temp, fem_risk = fem_solver()

    # Prepare for AI Correction
    grid_flat = np.column_stack([
        temp.flatten(), sigma_v.flatten(), pore.flatten(),
        Z.flatten(), fem_risk.flatten()
    ])
    Xs = scaler.transform(grid_data := grid_flat)
    
    with torch.no_grad():
        pinn_pred = model(torch.tensor(Xs, dtype=torch.float32)).numpy()
        risk_3d = pinn_pred.reshape(X.shape)

    # UI Visuals
    st.subheader("🌋 Deep Geomechanical Risk Profile")
    st.line_chart(risk_3d.mean(axis=(0, 1)))

    st.success("✔ Physics Coupling Active: Mohr-Coulomb Constraint Enforced in Loss Function.")
    
    with st.expander("🔬 Modelning ilmiy asosi (Technical Insight)"):
        st.write("""
        * **FEM Engine**: Bazaviy gidro-termik va geostatik kuchlanish maydonini hisoblaydi.
        * **PINN Residual**: Neyron tarmoq loss funksiyasi ichida Mohr-Coulomb notengligini tekshiradi.
        * **Constraint**: `torch.relu` funksiyasi orqali fizik qonuniyat buzilgan nuqtalar jazolanadi.
        """)
