import streamlit as st
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# --- 1. GEOMECHANICAL GROUND TRUTH (MOHR-COULOMB) ---
def generate_grounded_data(n_samples=10000):
    # Kirish parametrlari: [T, Sigma_V, Cohesion, Phi, Pore_P]
    temp = np.random.uniform(20, 1000, n_samples)
    sigma_v = np.random.uniform(5, 50, n_samples)
    c = np.random.uniform(5, 15, n_samples)
    phi = np.deg2rad(np.random.uniform(25, 40, n_samples))
    pore_p = np.random.uniform(0, 20, n_samples)
    
    sigma_n = sigma_v - pore_p # Effektiv kuchlanish
    
    # Mohr-Coulomb Failure Criterion
    tau_limit = c + sigma_n * np.tan(phi)
    tau_applied = (sigma_n * 0.7) * (1 + (temp/1100)**2) # Issiqlik bilan kuchayuvchi shear stress
    
    # Target: Failure (FOS < 1.0)
    failure = (tau_limit / (tau_applied + 1e-6) < 1.0).astype(np.float32)
    
    X = np.column_stack([temp, sigma_v, c, phi, pore_p])
    return X, failure

# --- 2. BAYESIAN PINN ARCHITECTURE ---
class GeoPINN(nn.Module):
    def __init__(self, input_dim=5):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        # Bashorat: Mean (Risk) va Log_Variance (Aleatoric)
        self.risk_head = nn.Linear(128, 1)
        self.log_var_head = nn.Linear(128, 1)

    def forward(self, x):
        features = self.encoder(x)
        risk = torch.sigmoid(self.risk_head(features))
        log_var = self.log_var_head(features)
        return risk, log_var

# --- 3. SCIENTIFIC LOSS: DATA + PHYSICS + ALEATORIC ---
def scientific_pinn_loss(pred_risk, log_var, target, inputs):
    # A. Data Loss: Gaussian Likelihood approximation (Aleatoric)
    # Loss = exp(-s) * (y-pred)^2 + s
    precision = torch.exp(-log_var)
    mse = (target - pred_risk)**2
    data_loss = torch.mean(precision * mse + log_var)

    # B. Physics Residual (Mohr-Coulomb Constraint)
    # Neyron tarmoq Mohr-Coulomb qonunini buzsa, jazo beriladi
    temp, sigma_v, c, phi, pore_p = inputs[:, 0], inputs[:, 1], inputs[:, 2], inputs[:, 3], inputs[:, 4]
    sigma_n = sigma_v - pore_p
    tau_limit = c + sigma_n * torch.tan(phi)
    
    # Model bashorat qilgan xavf darajasi Mohr-Coulomb chegarasiga teskari bo'lsa (Penalty)
    # Ya'ni tau_limit katta bo'lsa-yu, model riskni 1.0 (failure) ko'rsatsa
    physics_residual = torch.mean(torch.relu(pred_risk.flatten() * (tau_limit / 50) - (1 - target.flatten())))
    
    return data_loss + 0.1 * physics_residual

@st.cache_resource
def train_scientific_system():
    X, y = generate_grounded_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15)
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GeoPINN().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    X_t = torch.tensor(X_train_s, dtype=torch.float32).to(device)
    y_t = torch.tensor(y_train, dtype=torch.float32).view(-1, 1).to(device)

    model.train()
    for _ in range(400):
        opt.zero_grad()
        risk, log_var = model(X_t)
        loss = scientific_pinn_loss(risk, log_var, y_t, X_t)
        loss.backward()
        opt.step()
        
    return model, scaler

pinn_model, global_scaler = train_scientific_system()

# --- 4. SAFE INFERENCE PIPELINE ---
def mc_bayesian_inference(model, raw_data, n_samples=30):
    model.train() # MC Dropout uchun train mode
    scaled = global_scaler.transform(raw_data)
    x_t = torch.tensor(scaled, dtype=torch.float32)
    
    risks, aleatorics = [], []
    with torch.no_grad():
        for _ in range(n_samples):
            r, lv = model(x_t)
            risks.append(r.numpy())
            aleatorics.append(torch.exp(lv).numpy())
    
    model.eval() # Xavfsiz holatga qaytish
    return {
        "mean": np.mean(risks, axis=0),
        "epistemic": np.std(risks, axis=0), # Model bilimidagi bo'shliq
        "aleatoric": np.mean(aleatorics, axis=0) # Ma'lumotdagi shovqin (Gaussian sigma)
    }

# --- 5. UI: SCIENTIFIC RESULTS ---
st.title("🛡️ Bayesian-PINN: Mohr-Coulomb Physics Engine")

# Sidebar: Sensor ma'lumotlari
st.sidebar.header("📥 Sensor Input")
t_in = st.sidebar.slider("Temperature (°C)", 20, 1000, 450)
s_v = st.sidebar.slider("Vertical Stress (MPa)", 5, 60, 30)
c_in = st.sidebar.slider("Cohesion (MPa)", 5, 20, 12)
phi_in = st.sidebar.slider("Friction Angle (°)", 20, 45, 32)
p_in = st.sidebar.slider("Pore Pressure (MPa)", 0, 25, 10)

if st.button("🚀 Run Physics-Informed Analysis"):
    raw_input = np.array([[t_in, s_v, c_in, np.deg2rad(phi_in), p_in]])
    res = mc_bayesian_inference(pinn_model, raw_input)
    
    m, e, a = res['mean'][0][0], res['epistemic'][0][0], res['aleatoric'][0][0]
    
    # Vizualizatsiya
    col1, col2, col3 = st.columns(3)
    col1.metric("Failure Probability", f"{m*100:.2f}%")
    col2.metric("Epistemic (Model Conf.)", f"±{e*100:.3f}%")
    col3.metric("Aleatoric (Data Noise)", f"{a:.4f}")
    
    if m > 0.7:
        st.error("🚨 KRITIK HOLAT: Mohr-Coulomb chegarasi buzildi!")
    elif e > 0.15:
        st.warning("⚠️ Model ushbu hududda yetarli tajribaga ega emas (Out-of-Distribution).")
