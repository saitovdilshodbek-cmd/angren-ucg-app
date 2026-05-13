import streamlit as st
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# --- 1. GEOMECHANICAL GROUND TRUTH (MOHR-COULOMB) ---
@st.cache_data
def generate_grounded_data(n_samples=10000):
    """Real geonexanik qonuniyatlar asosida sintetik ma'lumot generatsiyasi"""
    temp = np.random.uniform(20, 1000, n_samples)
    sigma_v = np.random.uniform(5, 50, n_samples)
    c = np.random.uniform(5, 15, n_samples)
    phi = np.deg2rad(np.random.uniform(25, 40, n_samples))
    pore_p = np.random.uniform(0, 20, n_samples)
    
    sigma_n = sigma_v - pore_p # Effektiv kuchlanish
    
    # Mohr-Coulomb Failure Criterion
    tau_limit = c + sigma_n * np.tan(phi)
    # Issiqlik ta'sirida shear stress ortishi (termik kuchlanish)
    tau_applied = (sigma_n * 0.7) * (1 + (temp/1100)**2) 
    
    # Target: Failure (Factor of Safety < 1.0 bo'lsa xavf yuqori)
    failure = (tau_limit / (tau_applied + 1e-6) < 1.1).astype(np.float32)
    
    X = np.column_stack([temp, sigma_v, c, phi, pore_p])
    return X, failure

# --- 2. BAYESIAN PINN ARCHITECTURE ---
class GeoPINN(nn.Module):
    def __init__(self, input_dim=5):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.LayerNorm(128), # BatchNorm o'rniga LayerNorm (Inference safe)
            nn.ReLU(),
            nn.Dropout(0.25)
        )
        # Output 1: Mean Risk (Failure Probability)
        self.risk_head = nn.Linear(128, 1)
        # Output 2: Log Variance (Aleatoric Uncertainty)
        self.log_var_head = nn.Linear(128, 1)

    def forward(self, x):
        features = self.encoder(x)
        risk = torch.sigmoid(self.risk_head(features))
        log_var = self.log_var_head(features)
        return risk, log_var

# --- 3. SCIENTIFIC LOSS (GAUSSIAN LIKELIHOOD + PHYSICS RESIDUAL) ---
def scientific_pinn_loss(pred_risk, log_var, target, inputs):
    # A. Data Loss (Aleatoric Uncertainty bilan)
    precision = torch.exp(-log_var)
    data_loss = torch.mean(precision * (target - pred_risk)**2 + log_var)

    # B. Physics Loss (Mohr-Coulomb Residual)
    temp, sigma_v, c, phi, pore_p = inputs[:, 0], inputs[:, 1], inputs[:, 2], inputs[:, 3], inputs[:, 4]
    sigma_n = sigma_v - pore_p
    tau_limit = c + sigma_n * torch.tan(phi)
    
    # Agar model fizikaga zid bashorat qilsa (masalan, chidamlilik yuqori lekin xavf yuqori desa)
    # Ushbu residual modelni fizik qonuniyatlar doirasida ushlab turadi
    physics_residual = torch.mean(torch.relu(pred_risk.flatten() * (tau_limit / 50) - (1 - target.flatten())))
    
    return data_loss + 0.1 * physics_residual

@st.cache_resource
def train_scientific_system():
    X, y = generate_grounded_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15)
    
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    
    model = GeoPINN()
    opt = torch.optim.Adam(model.parameters(), lr=0.001)
    
    X_t = torch.tensor(X_train_s, dtype=torch.float32)
    y_t = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)

    model.train()
    for epoch in range(300):
        opt.zero_grad()
        risk, log_var = model(X_t)
        loss = scientific_pinn_loss(risk, log_var, y_t, X_t)
        loss.backward()
        opt.step()
        
    return model, scaler

# Tizimni yuklash
pinn_model, global_scaler = train_scientific_system()

# --- 4. SAFE MULTI-USER MC INFERENCE ---
def mc_bayesian_inference(model, raw_data, n_samples=25):
    """Hybrid Mode: BatchNorm evalda, Dropout trainda qoladi"""
    model.eval() 
    # Faqat Dropoutni yoqamiz (MC Dropout uchun)
    for m in model.modules():
        if m.__class__.__name__.startswith('Dropout'):
            m.train()
            
    scaled = global_scaler.transform(raw_data)
    x_t = torch.tensor(scaled, dtype=torch.float32)
    
    risks, aleatorics = [], []
    with torch.no_grad():
        for _ in range(n_samples):
            r, lv = model(x_t)
            risks.append(r.numpy())
            aleatorics.append(torch.exp(lv).numpy())
    
    model.eval() # Hammasini evalga qaytarish
    return {
        "mean": np.mean(risks, axis=0),
        "epistemic": np.std(risks, axis=0), 
        "aleatoric": np.mean(aleatorics, axis=0) 
    }

# --- 5. STREAMLIT UI ---
st.set_page_config(page_title="Angren UCG Physics-AI", layout="wide")
st.title("🛡️ Geo-Decision Support System (Bayesian-PINN)")
st.markdown("""
Ushbu tizim **Mohr-Coulomb failure criterion** va **Deep Bayesian Inference** kombinatsiyasi asosida ishlaydi. 
U nafaqat xavfni, balki modelning o'ziga bo'lgan ishonchini ham tahlil qiladi.
""")

# Sidebar kiritish parametrlari
with st.sidebar:
    st.header("📥 Sensor Ma'lumotlari")
    t_in = st.slider("Harorat (°C)", 20, 1100, 500)
    s_v = st.slider("Vertikal Kuchlanish (MPa)", 5, 60, 30)
    c_in = st.slider("Jins Cohesion (MPa)", 5, 25, 12)
    phi_in = st.slider("Ishqalanish Burchagi (°)", 15, 50, 32)
    p_in = st.slider("G'ovak Bosimi (MPa)", 0, 30, 10)

# Analizni ishga tushirish
if st.button("🚀 Fizik-Intelektual Analizni Boshlash"):
    raw_input = np.array([[t_in, s_v, c_in, np.deg2rad(phi_in), p_in]])
    
    with st.spinner("Bayesian Inference hisoblanmoqda..."):
        res = mc_bayesian_inference(pinn_model, raw_input)
    
    m, e, a = res['mean'][0][0], res['epistemic'][0][0], res['aleatoric'][0][0]
    
    # Metrikalar
    c1, c2, c3 = st.columns(3)
    c1.metric("Xavf Ehtimoli", f"{m*100:.2f}%")
    c2.metric("Epistemic (Model Conf.)", f"±{e*100:.3f}%")
    c3.metric("Aleatoric (Data Noise)", f"{a:.4f}")
    
    # Grafik natija
    st.write("### 📊 Uncertainty Decomposition")
    st.info(f"""
    * **Risk**: {m*100:.1f}% - Umumiy buzilish ehtimoli.
    * **Epistemic Uncertainty**: {e*100:.2f}% - Modelning ushbu kiritilgan ma'lumotlar haqidagi bilim darajasi.
    * **Aleatoric Uncertainty**: {a:.4f} - Kiritilgan sensor ma'lumotlaridagi tabiiy shovqin va noaniqlik.
    """)
    
    if m > 0.75:
        st.error("🚨 DIQQAT: Geomexanik barqarorlik chegaradan chiqdi!")
    elif e > 0.15:
        st.warning("⚠️ OGOHLANTIRISH: Model bu hududda ishonchsiz bashorat bermoqda. Sensorlarni tekshiring.")
