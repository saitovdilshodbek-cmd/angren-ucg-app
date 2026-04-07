import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
import time
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

# ========================== KONSTANTALAR ==========================
EPS = 1e-12
APP_URL = "https://angren-ucg-app-a7rxktm6usxqixabhaq576.streamlit.app"

# ========================== TARJIMALAR (faqat asosiy) ==========================
TRANSLATIONS = {
    'uz': {
        'app_title': "Universal Yer yuzasi Deformatsiyasi Monitoringi",
        'app_subtitle': "Termo-Mexanik (TM) tahlil va Selek O'lchami Optimizatsiyasi",
        'sidebar_header_params': "⚙️ Umumiy parametrlar",
        'project_name': "Loyiha nomi:",
        'process_time': "Jarayon vaqti (soat):",
        'num_layers': "Qatlamlar soni:",
        'tensile_model': "Tensile modeli:",
        'rock_props': "💎 Jins Xususiyatlari",
        'disturbance': "Disturbance Factor (D):",
        'poisson': "Poisson koeffitsiyenti (ν):",
        'stress_ratio': "Stress Ratio (k = σh/σv):",
        'tensile_params': "📐 Cho'zilish va Selek",
        'tensile_ratio': "Tensile Ratio (σt0/UCS):",
        'thermal_decay': "Thermal Decay (β):",
        'combustion': "🔥 Yonish va Termal",
        'burn_duration': "Kamera yonish muddati (soat):",
        'max_temp': "Maksimal harorat (°C)",
        'timeline': "📅 Loyiha bosqichlari",
        'layer_params': "{num}-qatlam parametrlari",
        'layer_name': "Nomi:",
        'thickness': "Qalinlik (m):",
        'ucs': "UCS (MPa):",
        'density': "Zichlik (kg/m³):",
        'color': "Rangi:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (MPa):",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastik zona (y)",
        'cavity_volume': "Kamera Hajmi",
        'max_permeability': "Maks. O'tkazuvchanlik",
        'ai_recommendation': "AI Tavsiya (Selek)",
        'monitoring_header': "📊 {obj_name}: Monitoring va Ekspert Xulosasi",
        'subsidence_title': "📉 Yer yuzasi cho'kishi (cm)",
        'thermal_deform_title': "🔥 Termal deformatsiya (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Ilmiy Tahlil",
        'fos_red': "🔴 FOS < 1.0: Failure",
        'fos_yellow': "🟡 FOS 1.0–1.5: Unstable",
        'fos_green': "🟢 FOS > 1.5: Stable",
        'tm_field_title': "🔥 TM Maydoni va Selek Interferensiyasi",
        'temp_subplot': "Harorat Maydoni (°C) + Gaz Oqimi",
        'fos_subplot': "FOS + AI Collapse Prediction + Yielded Zones",
        'gas_flow': "Gaz oqimi",
        'ai_collapse': "AI Collapse (NN)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'timeline_table': "| Bosqich | Vaqti | Tavsif |\n|---------|-------|--------|\n| **Rejalashtirish** | 2026-04-01 | Validatsiya |\n| **Optimallashtirish** | 2026-05-15 | NN/RF test |\n| **Integratsiya** | 2026-06-30 | Deploy |",
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Monitoring ma'lumotlarini yuklab olish (CSV)",
        'advanced_analysis': "🔍 Chuqurlashtirilgan Dinamik Tahlil"
    },
    'en': {
        'app_title': "Universal Surface Deformation Monitoring",
        'app_subtitle': "Thermo-Mechanical (TM) Analysis and Pillar Size Optimization",
        'sidebar_header_params': "⚙️ General Parameters",
        'project_name': "Project name:",
        'process_time': "Process time (hours):",
        'num_layers': "Number of layers:",
        'tensile_model': "Tensile model:",
        'rock_props': "💎 Rock Properties",
        'disturbance': "Disturbance Factor (D):",
        'poisson': "Poisson's ratio (ν):",
        'stress_ratio': "Stress Ratio (k = σh/σv):",
        'tensile_params': "📐 Tension and Pillar",
        'tensile_ratio': "Tensile Ratio (σt0/UCS):",
        'thermal_decay': "Thermal Decay (β):",
        'combustion': "🔥 Combustion and Thermal",
        'burn_duration': "Burn duration (hours):",
        'max_temp': "Maximum temperature (°C)",
        'timeline': "📅 Project Timeline",
        'layer_params': "Layer {num} parameters",
        'layer_name': "Name:",
        'thickness': "Thickness (m):",
        'ucs': "UCS (MPa):",
        'density': "Density (kg/m³):",
        'color': "Color:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (MPa):",
        'pillar_strength': "Pillar Strength (σp)",
        'plastic_zone': "Plastic zone (y)",
        'cavity_volume': "Cavity Volume",
        'max_permeability': "Max Permeability",
        'ai_recommendation': "AI Recommendation (Pillar)",
        'monitoring_header': "📊 {obj_name}: Monitoring and Expert Summary",
        'subsidence_title': "📉 Surface subsidence (cm)",
        'thermal_deform_title': "🔥 Thermal deformation (cm)",
        'hb_envelopes_title': "🛡️ Hoek-Brown Envelopes",
        'scientific_analysis': "📋 Scientific Analysis",
        'fos_red': "🔴 FOS < 1.0: Failure",
        'fos_yellow': "🟡 FOS 1.0–1.5: Unstable",
        'fos_green': "🟢 FOS > 1.5: Stable",
        'tm_field_title': "🔥 TM Field and Pillar Interference",
        'temp_subplot': "Temperature Field (°C) + Gas Flow",
        'fos_subplot': "FOS + AI Collapse Prediction + Yielded Zones",
        'gas_flow': "Gas flow",
        'ai_collapse': "AI Collapse (NN)",
        'tensile_empirical': "Empirical (UCS)",
        'tensile_hb': "HB-based (auto)",
        'tensile_manual': "Manual",
        'timeline_table': "| Stage | Time | Description |\n|-------|------|-------------|\n| **Planning** | 2026-04-01 | Validation |\n| **Optimization** | 2026-05-15 | NN/RF test |\n| **Integration** | 2026-06-30 | Deploy |",
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Download monitoring data (CSV)",
        'advanced_analysis': "🔍 In-depth Dynamic Analysis"
    },
    'ru': {
        'app_title': "Универсальный мониторинг деформации земной поверхности",
        'app_subtitle': "Термо-механический (ТМ) анализ и оптимизация размера целика",
        'sidebar_header_params': "⚙️ Общие параметры",
        'project_name': "Название проекта:",
        'process_time': "Время процесса (часы):",
        'num_layers': "Количество слоёв:",
        'tensile_model': "Модель растяжения:",
        'rock_props': "💎 Свойства породы",
        'disturbance': "Фактор нарушения (D):",
        'poisson': "Коэффициент Пуассона (ν):",
        'stress_ratio': "Коэффициент напряжений (k = σh/σv):",
        'tensile_params': "📐 Растяжение и целик",
        'tensile_ratio': "Отношение растяжения (σt0/UCS):",
        'thermal_decay': "Термическое затухание (β):",
        'combustion': "🔥 Горение и термика",
        'burn_duration': "Длительность горения (часы):",
        'max_temp': "Максимальная температура (°C)",
        'timeline': "📅 Этапы проекта",
        'layer_params': "Параметры слоя {num}",
        'layer_name': "Название:",
        'thickness': "Мощность (м):",
        'ucs': "UCS (МПа):",
        'density': "Плотность (кг/м³):",
        'color': "Цвет:",
        'gsi': "GSI:",
        'mi': "mi:",
        'manual_st0': "σt0 (МПа):",
        'pillar_strength': "Прочность целика (σp)",
        'plastic_zone': "Пластическая зона (y)",
        'cavity_volume': "Объём полости",
        'max_permeability': "Макс. проницаемость",
        'ai_recommendation': "Рекомендация ИИ (Целик)",
        'monitoring_header': "📊 {obj_name}: Мониторинг и экспертное заключение",
        'subsidence_title': "📉 Оседание поверхности (см)",
        'thermal_deform_title': "🔥 Термическая деформация (см)",
        'hb_envelopes_title': "🛡️ Огибающие Хука-Брауна",
        'scientific_analysis': "📋 Научный анализ",
        'fos_red': "🔴 FOS < 1.0: Разрушение",
        'fos_yellow': "🟡 FOS 1.0–1.5: Неустойчиво",
        'fos_green': "🟢 FOS > 1.5: Устойчиво",
        'tm_field_title': "🔥 ТМ поле и интерференция целика",
        'temp_subplot': "Температурное поле (°C) + поток газа",
        'fos_subplot': "FOS + прогноз обрушения ИИ + зоны текучести",
        'gas_flow': "Поток газа",
        'ai_collapse': "Обрушение по ИИ (НС)",
        'tensile_empirical': "Эмпирическая (UCS)",
        'tensile_hb': "На основе HB (auto)",
        'tensile_manual': "Ручной ввод",
        'timeline_table': "| Этап | Время | Описание |\n|------|-------|----------|\n| **Планирование** | 2026-04-01 | Валидация |\n| **Оптимизация** | 2026-05-15 | Тестирование NN/RF |\n| **Интеграция** | 2026-06-30 | Деплой |",
        'live_monitoring_tab': "🔄 Live 3D Monitoring",
        'download_data': "📥 Скачать данные мониторинга (CSV)",
        'advanced_analysis': "🔍 Углубленный динамический анализ"
    }
}

def t(key, **kwargs):
    lang = st.session_state.get('language', 'uz')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz']).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ========================== FIZIKA FUNKSIYALARI ==========================
def thermal_damage(T):
    if T < 100: return 0.0
    elif T < 400: return 0.1 * (T - 100) / 300
    elif T < 800: return 0.1 + 0.4 * (T - 400) / 400
    else: return min(0.95, 0.5 + 0.45 * (T - 800) / 400)

def calc_vertical_stress(depth, density=2500):
    return density * 9.81 / 1e6 * depth

def hoek_brown_strength(ucs, gsi, mi, D, sigma3=0):
    mb = mi * np.exp((gsi - 100) / (28 - 14 * D))
    s = np.exp((gsi - 100) / (9 - 3 * D))
    a = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
    return sigma3 + ucs * (mb * sigma3 / ucs + s)**a

def improved_fos(ucs, gsi, mi, D, nu, T, depth, H_seam):
    damage = thermal_damage(T)
    ucs_eff = ucs * (1 - damage)
    sigma_strength = hoek_brown_strength(ucs_eff, gsi, mi, D, sigma3=0)
    sigma_v = calc_vertical_stress(depth)
    pillar_effect = (20 / (H_seam + EPS))**0.5
    return np.clip((sigma_strength * pillar_effect) / (sigma_v + EPS), 0, 5)

@st.cache_data(show_spinner=False)
def compute_temperature_field(time_h, T_max, burn_duration, total_depth, source_z, grid_shape):
    x = np.linspace(-total_depth*1.5, total_depth*1.5, grid_shape[1])
    z = np.linspace(0, total_depth+50, grid_shape[0])
    X, Z = np.meshgrid(x, z)
    T_field = np.ones_like(X) * 25.0
    alpha = 1e-6
    for src_x in [-total_depth/3, 0, total_depth/3]:
        if time_h > 40:
            dt = (time_h - 40)*3600
            r = np.sqrt((X - src_x)**2 + (Z - source_z)**2)
            T_field += (T_max-25) * np.exp(-r**2 / (4*alpha*dt + 100))
    return T_field, x, z, X, Z

@st.cache_data(show_spinner=False)
def compute_geomechanics(layers, Z, X, T_field, D, nu, k, tensile_mode, tensile_ratio, beta, total_depth, time_h):
    # Simplified but functional
    sigma_v = np.zeros_like(Z)
    ucs_grid = np.zeros_like(Z)
    for i, layer in enumerate(layers):
        mask = (Z >= layer['z_start']) & (Z < layer['z_start']+layer['t'])
        if i == len(layers)-1:
            mask = Z >= layer['z_start']
        over = sum(l['rho']*9.81*l['t'] for l in layers[:i])/1e6
        sigma_v[mask] = over + layer['rho']*9.81*(Z[mask]-layer['z_start'])/1e6
        ucs_grid[mask] = layer['ucs']
    damage = np.clip(1 - np.exp(-0.002*np.maximum(T_field-100,0)), 0, 0.95)
    ucs_eff = ucs_grid * (1 - damage)
    sigma_h = k * sigma_v
    sigma1 = np.maximum(sigma_v, sigma_h)
    sigma3 = np.minimum(sigma_v, sigma_h)
    fos = ucs_eff / (sigma1 + EPS)
    fos = np.clip(fos, 0, 3)
    void = (T_field > 900) | (fos < 0.5)
    perm = 1e-12 * (void.astype(float)**3)
    gas_vel = np.sqrt(perm) * T_field * 1e-3
    void_volume = np.sum(void) * (X[0,1]-X[0,0]) * (Z[1,0]-Z[0,0])
    return {'fos': fos, 'void': void, 'perm': perm, 'gas_velocity': gas_vel, 'void_volume': void_volume, 'damage': damage}

# ========================== PILLAR OPTIMIZATSIYASI ==========================
def optimize_pillar(ucs_seam, H_seam, sv_seam, strength_red, void_frac, init_w):
    def obj(w):
        strength = (ucs_seam*strength_red)*(w/(H_seam+EPS))**0.5
        risk = void_frac * np.exp(-0.01*(w-init_w))
        return -(strength - 15*risk)
    res = minimize(obj, x0=[init_w], bounds=[(5,100)], method='SLSQP')
    return float(np.clip(res.x[0],5,100))

# ========================== ASOSIY ILOVA ==========================
st.set_page_config(page_title=t('app_title'), layout="wide")
st.title(t('app_title'))
st.markdown(f"### {t('app_subtitle')}")

if 'language' not in st.session_state:
    st.session_state.language = 'uz'
lang = st.sidebar.selectbox("Til", ['uz','en','ru'], format_func=lambda x: {'uz':'Oʻzbek','en':'English','ru':'Русский'}[x])
st.session_state.language = lang

st.sidebar.header(t('sidebar_header_params'))
obj_name = st.sidebar.text_input(t('project_name'), 'Angren-UCG-001')
time_h = st.sidebar.slider(t('process_time'), 1, 150, 24)
num_layers = st.sidebar.number_input(t('num_layers'), 1, 5, 3)
tensile_mode = st.sidebar.selectbox(t('tensile_model'), [t('tensile_empirical'), t('tensile_hb'), t('tensile_manual')])

st.sidebar.subheader(t('rock_props'))
D_factor = st.sidebar.slider(t('disturbance'), 0.0, 1.0, 0.7)
nu_poisson = st.sidebar.slider(t('poisson'), 0.1, 0.4, 0.25)
k_ratio = st.sidebar.slider(t('stress_ratio'), 0.1, 2.0, 0.5)

st.sidebar.subheader(t('tensile_params'))
tensile_ratio = st.sidebar.slider(t('tensile_ratio'), 0.03, 0.15, 0.08)
beta_thermal = st.sidebar.number_input(t('thermal_decay'), 0.001, 0.01, 0.0035, format="%.4f")

st.sidebar.subheader(t('combustion'))
burn_duration = st.sidebar.number_input(t('burn_duration'), 10, 200, 40)
T_source_max = st.sidebar.slider(t('max_temp'), 600, 1200, 1075)

with st.sidebar.expander(t('timeline')):
    st.markdown(t('timeline_table'))

layers_data = []
total_depth = 0.0
colors = ['#87CEEB','#F4A460','#D3D3D3']
for i in range(num_layers):
    with st.sidebar.expander(t('layer_params', num=i+1)):
        name = st.text_input(t('layer_name'), f"Qatlam-{i+1}", key=f"n_{i}")
        thick = st.number_input(t('thickness'), 0.1, 200.0, 50.0, key=f"t_{i}")
        ucs_val = st.number_input(t('ucs'), 0.1, 200.0, 40.0, key=f"u_{i}")
        rho_val = st.number_input(t('density'), 100, 5000, 2500, key=f"r_{i}")
        gsi_val = st.slider(t('gsi'), 10, 100, 60, key=f"g_{i}")
        mi_val = st.number_input(t('mi'), 0.1, 50.0, 10.0, key=f"m_{i}")
        st0_val = st.number_input(t('manual_st0'), 0.0, 20.0, 3.0, key=f"s_{i}") if tensile_mode == t('tensile_manual') else 0.0
    layers_data.append({
        'name': name, 't': thick, 'ucs': ucs_val, 'rho': rho_val,
        'gsi': gsi_val, 'mi': mi_val, 'z_start': total_depth, 'sigma_t0_manual': st0_val
    })
    total_depth += thick

# Validatsiya
valid = True
for i, l in enumerate(layers_data):
    if l['t']<=0 or l['ucs']<=0 or l['rho']<=0 or l['mi']<=0 or not (10<=l['gsi']<=100):
        st.error(f"Qatlam {i+1} da xato parametrlar")
        valid = False
if not valid:
    st.stop()

# Hisoblash
progress = st.progress(0, text="Hisoblanmoqda...")
grid_shape = (60, 100)
source_z = total_depth - layers_data[-1]['t']/2
H_seam = layers_data[-1]['t']
T_field, x_axis, z_axis, grid_x, grid_z = compute_temperature_field(time_h, T_source_max, burn_duration, total_depth, source_z, grid_shape)
progress.progress(0.4)
geo = compute_geomechanics(layers_data, grid_z, grid_x, T_field, D_factor, nu_poisson, k_ratio,
                           tensile_mode, tensile_ratio, beta_thermal, total_depth, time_h)
progress.progress(0.8)
fos_2d = geo['fos']
void_mask = geo['void']
perm = geo['perm']
gas_vel = geo['gas_velocity']
void_volume = geo['void_volume']
damage = geo['damage']

# Pillar optimizatsiyasi
avg_T_seam = np.mean(T_field[np.abs(z_axis - source_z).argmin(), :])
strength_red = np.exp(-0.0025*(avg_T_seam-20))
ucs_seam = layers_data[-1]['ucs']
sv_seam = np.max(geo['fos'] * 10)  # rough
rec_width_init = 20.0
p_strength = (ucs_seam*strength_red)*(rec_width_init/(H_seam+EPS))**0.5
y_zone = max((H_seam/2)*(np.sqrt(sv_seam/(p_strength+EPS))-1), 1.5)
pillar_strength = p_strength
void_frac = float(np.mean(void_mask))
optimal_width = optimize_pillar(ucs_seam, H_seam, sv_seam, strength_red, void_frac, rec_width_init)

# Metrikalar
st.subheader(t('monitoring_header', obj_name=obj_name))
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
c2.metric(t('plastic_zone'), f"{y_zone:.1f} m")
c3.metric(t('cavity_volume'), f"{void_volume:.1f} m²")
c4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
c5.metric(t('ai_recommendation'), f"{optimal_width:.1f} m")

# Grafiklar
st.markdown("---")
col1, col2, col3 = st.columns(3)
s_max = (H_seam*0.04)*(min(time_h,120)/120)
subsidence = -s_max * np.exp(-(x_axis**2)/(2*(total_depth/2)**2))
with col1:
    fig_sub = go.Figure(go.Scatter(x=x_axis, y=subsidence*100, fill='tozeroy'))
    fig_sub.update_layout(title=t('subsidence_title'), height=300)
    st.plotly_chart(fig_sub, use_container_width=True)
with col2:
    thermal_uplift = (total_depth*1e-4)*np.exp(-(x_axis**2)/(total_depth*10))*(time_h/150)*100
    fig_th = go.Figure(go.Scatter(x=x_axis, y=thermal_uplift, fill='tozeroy'))
    fig_th.update_layout(title=t('thermal_deform_title'), height=300)
    st.plotly_chart(fig_th, use_container_width=True)
with col3:
    sigma3_ax = np.linspace(0, ucs_seam*0.5, 100)
    mb = layers_data[-1]['mi'] * np.exp((layers_data[-1]['gsi']-100)/(28-14*D_factor))
    s_hb = np.exp((layers_data[-1]['gsi']-100)/(9-3*D_factor))
    a = 0.5 + (1/6)*(np.exp(-layers_data[-1]['gsi']/15)-np.exp(-20/3))
    s1 = sigma3_ax + ucs_seam*(mb*sigma3_ax/(ucs_seam+EPS)+s_hb)**a
    fig_hb = go.Figure(go.Scatter(x=sigma3_ax, y=s1))
    fig_hb.update_layout(title=t('hb_envelopes_title'), height=300)
    st.plotly_chart(fig_hb, use_container_width=True)

# TM maydoni
st.markdown("---")
left, right = st.columns([1,2])
with left:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red'))
    st.warning(t('fos_yellow'))
    st.success(t('fos_green'))
with right:
    st.subheader(t('tm_field_title'))
    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           subplot_titles=(t('temp_subplot'), t('fos_subplot')))
    fig_tm.add_trace(go.Heatmap(z=T_field, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_2d, x=x_axis, y=z_axis, colorscale='RdYlGn', zmin=0, zmax=3), row=2, col=1)
    fig_tm.update_layout(height=700)
    fig_tm.update_yaxes(autorange='reversed', row=1)
    fig_tm.update_yaxes(autorange='reversed', row=2)
    st.plotly_chart(fig_tm, use_container_width=True)

# Live monitoring tab (sodda)
st.header("🔄 Live Monitoring")
tab1, tab2 = st.tabs([t('live_monitoring_tab'), t('advanced_analysis')])
with tab1:
    if st.button("Run Live Simulation"):
        with st.spinner("Simulating..."):
            time.sleep(1)
            st.success("Done")
with tab2:
    st.header(t('advanced_analysis'))
    st.info("Monte Carlo and sensitivity analysis can be added here.")

st.sidebar.markdown("---")
st.sidebar.write("Tuzuvchi: Saitov Dilshodbek | Streamlit Cloud")
