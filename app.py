import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def run_ucg_model():
    st.title("UCG: Strip Pillar Bosim Taqsimoti Modeli")
    
    # Sidebar orqali parametrlarni kiritish
    st.sidebar.header("Geomexanik Parametrlar")
    H = st.sidebar.slider("H - Qatlam chuqurligi (m)", 50, 500, 200)
    m = st.sidebar.slider("m - Ko'mir qatlami qalinligi (m)", 1, 20, 5)
    We = st.sidebar.slider("We - UCG paneli kengligi (m)", 10, 100, 50)
    Wp = st.sidebar.slider("Wp - Pillar (ustun) kengligi (m)", 10, 100, 40)
    gamma = 25  # Jinsning o'rtacha zichligi (kN/m3)
    
    # Hisoblash: Statik yuk
    sigma_v = gamma * H / 1000  # MPa da
    
    # Grafik chizish
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Pillar va Panellarni chizish
    # Panel 1 (Chap)
    ax.add_patch(plt.Rectangle((-We - Wp/2, 0), We, m, color='orange', label='UCG Panel (Yonish zonasi)'))
    # Strip Pillar (O'rta)
    ax.add_patch(plt.Rectangle((-Wp/2, 0), Wp, m, color='gray', label='Strip Pillar (Butun qolgan qism)'))
    # Panel 2 (O'ng)
    ax.add_patch(plt.Rectangle((Wp/2, 0), We, m, color='orange'))
    
    # Yuklanish chiziqlari (Vertical Stress sigma_zl)
    x_pillar = np.linspace(-Wp/2, Wp/2, 100)
    # Oddiy taqsimot modeli: chekkalarda bosim yuqori
    stress_dist = sigma_v * (1 + np.exp(-abs(x_pillar)/(Wp/4))) 
    
    ax.plot(x_pillar, stress_dist + m + 2, color='red', linewidth=2, label='$\sigma_{zl}$ Taqsimoti')
    ax.fill_between(x_pillar, m + 2, stress_dist + m + 2, color='red', alpha=0.2)

    # Bezatish
    ax.set_xlim(-We - Wp, We + Wp)
    ax.set_ylim(-2, max(stress_dist) + m + 10)
    ax.set_xlabel("Kenglik (m)")
    ax.set_ylabel("Balandlik / Kuchlanish")
    ax.set_title(f"Chuqurlik H={H}m dagi kuchlanish holati")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    st.pyplot(fig)
    
    st.write(f"**Ma'lumot:** Hozirgi chuqurlikda tog' jinsining statik bosimi taxminan **{sigma_v:.2f} MPa** ni tashkil etadi.")
    st.info("Ushbu model strip-pillar markazidagi bosim konsentratsiyasini ko'rsatadi.")

if __name__ == "__main__":
    run_ucg_model()
