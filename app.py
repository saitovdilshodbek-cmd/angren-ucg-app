# =========================== 2-QISM (davomi) ===========================

# ---------- Quduqlar konfiguratsiyasi (yagona slayder) ----------
st.sidebar.markdown("---")
st.sidebar.subheader("Quduqlar konfiguratsiyasi")
well_distance = st.sidebar.slider(
    "Quduqlar orasidagi masofa (m):",
    50.0, 500.0, 200.0, 10.0,
    key="well_dist_slider"
)

# =========================== SELEK OPTIMIZATSIYASI ===========================
# Seam bo‘yicha o‘rtacha kuchlanish va harorat
seam_top = layers_data[-1]['z_start']
seam_bot = seam_top + layers_data[-1]['t']
seam_mask = (z_axis >= seam_top) & (z_axis <= seam_bot)
sv_seam = float(np.mean(grid_sigma_v[seam_mask, :]))      # MPa
avg_t_p = float(np.mean(temp_2d[seam_mask, :]))           # °C

strength_red = np.exp(-beta_strength * (avg_t_p - 20))
ucs_seam = layers_data[-1]['ucs']
# Plastik zona (Wilson 1972, yon bosim hisobga olingan)
phi_friction = np.radians(30.0)                               # ko'mir uchun ichki ishqalanish burchagi
kp = (1 + np.sin(phi_friction)) / (1 - np.sin(phi_friction))  # Rankine koeffitsiyenti
p0 = 0.1                                                      # yon bosim (MPa)
sigma_c = ucs_seam * strength_red
arg = max((sv_seam + p0) / (sigma_c * kp + EPS), 1.0001)
y_zone = (H_seam / (2 * kp)) * np.log(arg)                    # Manba: Wilson (1972) tuzatilgan formula

# Pillar enini optimal hisoblash (iteratsiya)
w_sol = 20.0
for _ in range(15):
    p_strength = sigma_c * (w_sol / (H_seam + EPS)) ** 0.5     # Wilson empirik mustahkamlik
    y_zone_calc = (H_seam / (2 * kp)) * np.log((sv_seam + p0) / (p_strength * kp + EPS) + 1e-6)
    new_w = 2 * max(y_zone_calc, 1.5) + 0.5 * H_seam
    if abs(new_w - w_sol) < 0.1:
        break
    w_sol = new_w
rec_width = np.round(w_sol, 1)
pillar_strength = p_strength

fos_2d = np.clip(sigma1_limit / (sigma1_act + EPS), 0, 3.0)
fos_2d = np.where(void_mask_permanent, 0.0, fos_2d)
void_frac_base = float(np.mean(void_mask_permanent))

def objective(w_arr):
    w = w_arr[0]
    strength = (ucs_seam * strength_red) * (w / (H_seam + EPS)) ** 0.5
    risk = void_frac_base * np.exp(-0.01 * (w - rec_width))
    return -(strength - 15.0 * risk)

try:
    opt_result = minimize(objective, x0=[rec_width], bounds=[(5.0, 100.0)], method='SLSQP')
    optimal_width_ai = float(np.clip(opt_result.x[0], 5.0, 100.0))
except (ValueError, RuntimeError) as e:
    st.warning(f"Optimizatsiya xatosi: {e}. Klassik tavsiya ishlatiladi.")
    optimal_width_ai = rec_width

# =========================== METRIKALAR ===========================
st.subheader(t('monitoring_header', obj_name=obj_name))
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric(t('pillar_strength'), f"{pillar_strength:.1f} MPa")
m2.metric(t('plastic_zone'), f"{y_zone:.1f} m")

cavity_length_y = well_distance
void_volume_3d = void_volume * cavity_length_y
m3.metric(t('cavity_volume'), f"{void_volume_3d:.1f} m³")
m4.metric(t('max_permeability'), f"{np.max(perm):.1e} m²")
m5.metric(t('ai_recommendation'), f"{optimal_width_ai:.1f} m",
          delta=f"Klassik: {rec_width} m", delta_color="off")

# =========================== CHO‘KISH VA HOEK-BROWN ===========================
st.markdown("---")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.5, 2])

# Cho‘kish – Knothe nazariyasi asosida tuzatilgan
extraction_ratio = np.clip(time_h / 200, 0, 1)                # vaqt bo‘yicha qazib olish darajasi
a_subs = 0.85                                                 # NCB 1975 sublevel caving koeffitsiyenti
s_max = layers_data[-1]['t'] * a_subs * extraction_ratio       # maksimal cho‘kish (m)

# Influence radius (tortish burchagi ko‘mir uchun ~35°)
R_influence = total_depth / np.tan(np.radians(35))
sub_p = -s_max * np.exp(-(x_axis**2) / (2 * R_influence**2))  # cho‘kish profili

# Gorizontal cho‘zilish εh (NCB 1975 bo‘yicha)
dx = x_axis[1] - x_axis[0]
slope = np.gradient(sub_p, dx)                                # qiyalik (i)
strain_h = np.gradient(slope, dx)                             # gorizontal cho‘zilish (1/m)
strain_h_mm_per_m = strain_h * 1000                           # mm/m

# Thermal deformation (avvalgidek)
uplift = (total_depth * 1e-4) * np.exp(-(x_axis**2) / (total_depth * 10)) * (time_h / 150) * 100

with col_g1:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=sub_p * 100, fill='tozeroy',
                                         line=dict(color='magenta', width=3)))
                    .update_layout(title=t('subsidence_title'), template="plotly_dark", height=300),
                    use_container_width=True)
with col_g2:
    st.plotly_chart(go.Figure(go.Scatter(x=x_axis, y=uplift, fill='tozeroy',
                                         line=dict(color='cyan', width=3)))
                    .update_layout(title=t('thermal_deform_title'), template="plotly_dark", height=300),
                    use_container_width=True)
with col_g3:
    sigma3_ax = np.linspace(0, ucs_seam * 0.5, 100)
    mb_s, s_s, a_s = grid_mb.max(), grid_s_hb.max(), grid_a_hb.max()
    s1_20 = sigma3_ax + ucs_seam * (mb_s * sigma3_ax / (ucs_seam + EPS) + s_s) ** a_s
    ucs_burn = ucs_seam * np.exp(-beta_damage * (T_source_max - 20))
    s1_burning = sigma3_ax + ucs_burn * (mb_s * sigma3_ax / (ucs_burn + EPS) + s_s) ** a_s
    s1_sov = sigma3_ax + (ucs_seam * strength_red) * (mb_s * sigma3_ax / (ucs_seam * strength_red + EPS) + s_s) ** a_s
    fig_hb = go.Figure()
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_20, name='20°C', line=dict(color='red', width=2)))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_sov, name=t('tensile_hb'), line=dict(color='cyan', width=2, dash='dash')))
    fig_hb.add_trace(go.Scatter(x=sigma3_ax, y=s1_burning, name=t('combustion'), line=dict(color='orange', width=4)))
    st.plotly_chart(fig_hb.update_layout(title=t('hb_envelopes_title'), template="plotly_dark", height=300,
                                         legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")),
                    use_container_width=True)

# =========================== TM MAYDONI (1→3→2 sxemasi) ===========================
st.markdown("---")
c1, c2 = st.columns([1, 2.5])

with c1:
    st.subheader(t('scientific_analysis'))
    st.error(t('fos_red'))
    st.warning(t('fos_yellow'))
    st.success(t('fos_green'))

    fig_layers = go.Figure()
    for lyr in layers_data:
        fig_layers.add_trace(go.Bar(x=['Kesim'], y=[lyr['t']], name=lyr['name'],
                                    marker_color=lyr['color'], width=0.4))
    st.plotly_chart(fig_layers.update_layout(barmode='stack', template="plotly_dark",
                                             yaxis=dict(autorange='reversed'), height=450,
                                             showlegend=False), use_container_width=True)

with c2:
    st.subheader("UCG Yonish Bosqichlari (1 → 3 → 2 sxemasi) – Yangi Ilmiy Model")

    coal_layer = layers_data[-1]
    h_seam = coal_layer['t']
    ucs_coal_pa = coal_layer['ucs'] * 1e6
    rho_coal = coal_layer['rho']
    well_x = [-well_distance, 0, well_distance]
    cavity_width = well_distance - rec_width
    cavity_width = max(cavity_width, 10)

    E_MOD = E_ROCKMASS_GPA * 1e9           # Pa (Hoek–Diederichs)
    ALPHA = 1.0e-5
    NU = nu_poisson
    K0 = NU / (1 - NU)

    sigma_v_overburden = sum(l['rho'] * 9.81 * l['t'] for l in layers_data[:-1]) / 1e6
    sigma_v_total = sigma_v_overburden + (rho_coal * 9.81 * (h_seam / 2)) / 1e6
    Hc = h_seam * np.sqrt(sigma_v_total / (coal_layer['ucs'] + 1e-5))
    Hc = np.clip(Hc, h_seam, h_seam * 4)

    states_132 = {1: [0], 2: [0, 2], 3: [0, 1, 2]}
    stage = st.select_slider("Bosqichni tanlang:", options=[1, 2, 3], value=1, key="ucg_stage_132")
    active_wells = states_132[stage]

    def compute_advanced_fos(grid_x, grid_z, active_wells, well_x, source_z, h_seam, cavity_width,
                             temp_field, sigma_v_field, layers_data, layer_bounds,
                             E, alpha, nu, K0, Hc, sigma_v_coal_MPa, ucs_coal_pa, stage, well_distance):
        fos = np.full_like(grid_x, 3.0)
        for px_idx in active_wells:
            px = well_x[px_idx]
            dist = np.sqrt((grid_x - px) ** 2 + (grid_z - source_z) ** 2)
            dz = source_z - grid_z
            T = temp_field
            delta_T = np.maximum(T - 20, 0)
            thermal_zone = dist < (h_seam * 3)
            for (top, bot, layer) in layer_bounds:
                mask = (grid_z >= top) & (grid_z < bot)
                if not np.any(mask):
                    continue
                ucs_pa = layer['ucs'] * 1e6
                gsi = layer['gsi']
                mi = layer['mi']
                mb = mi * np.exp((gsi - 100) / (28 - 14 * D_factor))
                s_hb = np.exp((gsi - 100) / (9 - 3 * D_factor))
                a_hb = 0.5 + (1 / 6) * (np.exp(-gsi / 15) - np.exp(-20 / 3))
                sigma_v = sigma_v_field[mask]
                delta_T_m = delta_T[mask]
                D_T = 1 - np.exp(-beta_damage * delta_T_m)
                sigma_ci_T = ucs_pa * (1 - D_T)
                sigma_3 = K0 * sigma_v * (0.6 + 0.4 * (1 - D_T))
                sigma_th = np.zeros_like(sigma_v)
                local_thermal = thermal_zone[mask]
                if np.any(local_thermal):
                    th_vals = (E * alpha * delta_T_m[local_thermal]) / (1 - nu)
                    sigma_th[local_thermal] = np.clip(th_vals, 0, sigma_ci_T[local_thermal] * 0.25)
                sigma_1 = sigma_v + sigma_th
                term = mb * sigma_3 / (sigma_ci_T + EPS_PA) + s_hb
                sigma_limit = sigma_3 + sigma_ci_T * (term) ** a_hb
                fos_val = np.clip(sigma_limit / (sigma_1 + EPS_PA), 0, 3)
                yield_mask = sigma_1 > (sigma_limit * 0.85)
                fos_val[yield_mask] = np.minimum(fos_val[yield_mask], 0.8)
                fos_sub = fos[mask]
                fos_sub = np.minimum(fos_sub, fos_val)
                fos[mask] = fos_sub
                if layer == layers_data[-1]:
                    dome_width = (cavity_width / 2) * np.clip(1 - dz[mask] / (Hc + 1e-5), 0, 1)
                    failure_zone = fos_val < 1.2
                    dome_condition = (dz[mask] > 0) & (dz[mask] < Hc) & (np.abs(grid_x[mask] - px) < dome_width) & failure_zone
                    if np.any(dome_condition):
                        decay = np.clip(1 - (dz[mask][dome_condition] / (Hc + 1e-5)), 0.3, 1.0)
                        fos_sub[dome_condition] = np.minimum(fos_sub[dome_condition], decay)
                        fos[mask] = fos_sub
        for px_idx in active_wells:
            px = well_x[px_idx]
            a = cavity_width / 2
            b = h_seam / 2
            cavity_ellipse = ((grid_x - px) ** 2 / (a ** 2 + EPS) + (grid_z - source_z) ** 2 / (b ** 2 + EPS)) < 1
            fos[cavity_ellipse] = 0.05
        bottom_layer = layers_data[-1]
        bottom_boundary = bottom_layer['z_start'] + bottom_layer['t']
        fos[grid_z > bottom_boundary] = 2.5
        all_wells = [0, 1, 2]
        for i in all_wells:
            if i not in active_wells:
                px = well_x[i]
                pillar_mask = (np.abs(grid_x - px) < h_seam * 1.5) & (np.abs(grid_z - source_z) < h_seam * 1.2)
                fos[pillar_mask] = 2.5
        if stage == 2:
            selek_eni = well_distance - cavity_width
            pillar_zone = (np.abs(grid_x - well_x[1]) < (selek_eni / 2)) & \
                          (grid_z > (source_z - h_seam)) & (grid_z < (source_z + h_seam))
            fos[pillar_zone] = 2.2
        fos = np.nan_to_num(fos, nan=3.0, posinf=3.0, neginf=0.0)
        return fos

    fos_stage = compute_advanced_fos(
        grid_x, grid_z, active_wells, well_x, source_z, h_seam, cavity_width,
        temp_2d, grid_sigma_v, layers_data, layer_bounds,
        E_MOD, ALPHA, NU, K0, Hc, sigma_v_total, ucs_coal_pa, stage, well_distance
    )

    fig_tm = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                           subplot_titles=(t('temp_subplot'), "Geomexanik Holat (Yangi Ilmiy Model)"))
    fig_tm.add_trace(go.Heatmap(z=temp_2d, x=x_axis, y=z_axis, colorscale='Hot', zmin=25, zmax=T_source_max,
                                colorbar=dict(title="T (°C)", x=1.05, y=0.78, len=0.42, thickness=15),
                                name=t('temp_subplot')), row=1, col=1)
    step = 12
    qx, qz = grid_x[::step, ::step].flatten(), grid_z[::step, ::step].flatten()
    qu, qw = vx[::step, ::step].flatten(), vz[::step, ::step].flatten()
    qmag = gas_velocity[::step, ::step].flatten()
    qmag_max = qmag.max() + EPS
    mask_q = qmag > qmag_max * 0.05
    angles = np.degrees(np.arctan2(qw[mask_q], qu[mask_q] + EPS))
    fig_tm.add_trace(go.Scatter(x=qx[mask_q], y=qz[mask_q], mode='markers',
                                marker=dict(symbol='arrow', size=10, color=qmag[mask_q], colorscale='ice',
                                            cmin=0, cmax=qmag_max, angle=angles, opacity=0.85,
                                            showscale=False, line=dict(width=0)),
                                name=t('gas_flow')), row=1, col=1)
    fig_tm.add_trace(go.Contour(z=fos_stage, x=x_axis, y=z_axis,
                                colorscale=[[0, 'black'], [0.1, 'red'], [0.4, 'orange'],
                                            [0.7, 'yellow'], [0.85, 'lime'], [1, 'darkgreen']],
                                zmin=0, zmax=3, contours_showlines=False,
                                colorbar=dict(title="FOS", x=1.05, y=0.22, len=0.42, thickness=15),
                                name="FOS"), row=2, col=1)
    fracture_mask = np.where(fos_stage < 1.2, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=fracture_mask, x=x_axis, y=z_axis,
                                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(255,0,0,0.5)']],
                                showscale=False, opacity=0.6, hoverinfo='skip',
                                name="Yielded Zones"), row=2, col=1)
    r_burn_vis = h_seam * 1.5
    for idx in active_wells:
        px = well_x[idx]
        fig_tm.add_shape(type="circle", x0=px - r_burn_vis, x1=px + r_burn_vis,
                         y0=source_z - r_burn_vis, y1=source_z + r_burn_vis,
                         line=dict(color="orange", width=2),
                         fillcolor='rgba(255,165,0,0.15)', row=2, col=1)
    for px in well_x:
        fig_tm.add_shape(type="rect", x0=px - rec_width / 2, x1=px + rec_width / 2,
                         y0=source_z - h_seam / 2, y1=source_z + h_seam / 2,
                         line=dict(color="lime", width=3),
                         fillcolor="rgba(0,255,0,0.1)", row=2, col=1)
    if stage == 2:
        fig_tm.add_shape(type="rect", x0=well_x[1] - 80, x1=well_x[1] + 80,
                         y0=source_z - 30, y1=source_z + 30,
                         line=dict(color="cyan", width=4, dash="dash"),
                         fillcolor='rgba(0,255,255,0.1)', row=2, col=1)
        fig_tm.add_annotation(x=well_x[1], y=source_z + 100, text="HIMOYA SELEGI (PILLAR)",
                              showarrow=True, arrowhead=2, font=dict(color="cyan", size=12),
                              row=2, col=1)
    fig_tm.add_trace(go.Heatmap(z=collapse_pred, x=x_axis, y=z_axis, colorscale='Viridis',
                                opacity=0.4, showscale=False, name="AI Collapse"), row=2, col=1)
    shear_disp = np.copy(shear_failure)
    shear_disp[void_mask_permanent] = False
    tens_disp = np.copy(tensile_failure)
    tens_disp[void_mask_permanent] = False
    fig_tm.add_trace(go.Scatter(x=grid_x[shear_disp][::2], y=grid_z[shear_disp][::2],
                                mode='markers', marker=dict(color='red', size=3, symbol='x'),
                                name='Shear'), row=2, col=1)
    fig_tm.add_trace(go.Scatter(x=grid_x[tens_disp][::2], y=grid_z[tens_disp][::2],
                                mode='markers', marker=dict(color='blue', size=3, symbol='cross'),
                                name='Tensile'), row=2, col=1)
    void_visual = np.where(void_mask_permanent > 0.1, 1.0, np.nan)
    fig_tm.add_trace(go.Heatmap(z=void_visual, x=x_axis, y=z_axis,
                                colorscale=[[0, 'black'], [1, 'black']],
                                showscale=False, opacity=0.8, hoverinfo='skip'), row=2, col=1)
    fig_tm.add_shape(type="line", x0=x_axis.min(), x1=x_axis.max(),
                     y0=source_z - h_seam / 2, y1=source_z - h_seam / 2,
                     line=dict(color="white", width=2, dash="dash"), row=2, col=1)
    fig_tm.add_shape(type="line", x0=x_axis.min(), x1=x_axis.max(),
                     y0=source_z + h_seam / 2, y1=source_z + h_seam / 2,
                     line=dict(color="white", width=2, dash="dash"), row=2, col=1)
    zoom_margin = h_seam * 12
    fig_tm.update_layout(template="plotly_dark", height=900, margin=dict(r=150, t=80, b=100),
                         showlegend=True, legend=dict(orientation="h", yanchor="bottom",
                                                    y=-0.12, xanchor="center", x=0.5))
    fig_tm.update_yaxes(autorange='reversed', row=1, col=1)
    fig_tm.update_yaxes(autorange='reversed', row=2, col=1)
    fig_tm.update_yaxes(range=[source_z + zoom_margin / 2, source_z - zoom_margin], row=2, col=1)
    st.plotly_chart(fig_tm, use_container_width=True)

    if st.checkbox("Avtomatik animatsiya (1→2→3 bosqichlar)"):
        anim_placeholder = st.empty()
        for s in [1, 2, 3]:
            wells_s = states_132[s]
            fos_s = compute_advanced_fos(
                grid_x, grid_z, wells_s, well_x, source_z, h_seam, cavity_width,
                temp_2d, grid_sigma_v, layers_data, layer_bounds,
                E_MOD, ALPHA, NU, K0, Hc, sigma_v_total, ucs_coal_pa, s, well_distance
            )
            fig_s = go.Figure(go.Contour(z=fos_s, x=x_axis, y=z_axis,
                                         colorscale=[[0, 'black'], [0.1, 'red'], [0.4, 'orange'],
                                                     [0.7, 'yellow'], [0.85, 'lime'], [1, 'darkgreen']],
                                         zmin=0, zmax=3, contours_showlines=False,
                                         colorbar=dict(title="FOS")))
            fig_s.update_yaxes(range=[source_z + zoom_margin / 2, source_z - zoom_margin], autorange=False)
            fig_s.update_layout(template="plotly_dark", height=500,
                                title=f"Bosqich {s} (1-3-2 sxemasi)")
            anim_placeholder.plotly_chart(fig_s, use_container_width=True)
            time.sleep(1.2)
        st.success("Animatsiya yakunlandi.")

    selek_eni = well_distance - cavity_width
    msgs = {
        1: f"**1-Bosqich:** Chap quduq yoqilgan. Qalinlik = {h_seam:.1f} m, Quduqlar masofasi = {well_distance:.0f} m, Selek eni = {selek_eni:.1f} m.",
        2: f"**2-Bosqich (Muhim):** O‘ng quduq yoqilgan. O‘rtadagi selek tomni ushlab turadi. Selek eni = {selek_eni:.1f} m.",
        3: f"**3-Bosqich:** Markaziy selek gazlashtirilmoqda. Barqaror cho‘kish."
    }
    st.info(msgs[stage])
    if selek_eni < 18.5:
        st.error(f"⚠️ KRITIK: Selek o'lchami ({selek_eni:.1f} m) xavfsiz chegaradan past!")
    else:
        st.success(f"✅ BARQAROR: Selek o'lchami ({selek_eni:.1f} m) me'yorda.")

# =========================== KOMPLEKS MONITORING PANELI ===========================
st.header(t('monitoring_panel', obj_name=obj_name))

def calculate_live_metrics(h, layers, T_max, sigma_v_MPa, beta_str=beta_strength):
    target = layers[-1]
    ucs_0, H_l = target['ucs'], target['t']
    curr_T = (25 + (T_max - 25)*(min(h,40)/40) if h <= 40
              else T_max * np.exp(-0.001*(h-40)))
    str_red = np.exp(-beta_str * (curr_T - 20))
    ucs_eff = ucs_0 * str_red
    # Wilson formula asosida FOS=1.5 ga teskari hisob
    fos_target = 1.5
    w_rec = H_l * (sigma_v_MPa * fos_target / (ucs_eff + EPS)) ** 2          # Manba: Wilson (1972) teskari formula
    w_rec = float(np.clip(w_rec, 5.0, 80.0))
    p_str = ucs_eff * (w_rec / (H_l + EPS)) ** 0.5
    max_sub = (H_l * 0.05) * (min(h,120)/120)
    return p_str, w_rec, curr_T, max_sub

# O‘rtacha litostatik kuchlanish
H_total = sum(l['t'] for l in layers_data)
rho_avg = np.mean([l['rho'] for l in layers_data])
sigma_v_live = rho_avg * 9.81 * H_total / 1e6   # MPa

p_str, w_rec_live, t_now, s_max_3d = calculate_live_metrics(time_h, layers_data, T_source_max, sigma_v_live)
mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric(t('pillar_live'), f"{p_str:.1f} MPa", delta=f"{t_now:.0f} °C", delta_color="inverse")
mk2.metric(t('rec_width_live'), f"{w_rec_live:.1f} m")
mk3.metric(t('max_subsidence_live'), f"{s_max_3d * 100:.1f} cm")
mk4.metric(t('process_stage'), t('stage_active') if time_h < 100 else t('stage_cooling'))

# ---------- Gorizontal deformatsiya metrikasi (NCB 1975) ----------
m6 = st.columns(1)[0]
m6.metric("Maks. ε_h (NCB)", f"{np.max(np.abs(strain_h_mm_per_m)):.2f} mm/m",
          delta="KRITIK" if np.max(np.abs(strain_h_mm_per_m)) > 6.0 else "Norma")

st.markdown("---")

# ====================== AI RISK PREDICTION (Sensor CSV) ======================
with st.expander("🤖 AI Risk Prediction (Sensor CSV)", expanded=False):
    st.markdown("Yuklangan sensor ma'lumotlari asosida **fizik model** yordamida xavf indeksini bashorat qilish.")
    sensor_file = st.file_uploader("Sensor CSV faylini yuklang (kerakli ustunlar: 'temp', 'stress', 'ucs_lab')",
                                   type=['csv'], key="sensor_ai")
    if sensor_file:
        df_sensor = pd.read_csv(sensor_file)
        required_cols = ['temp', 'stress', 'ucs_lab']
        missing = [c for c in required_cols if c not in df_sensor.columns]
        if missing:
            st.error(f"Faylda quyidagi ustunlar yo‘q: {missing}. Iltimos, to‘g‘ri formatda yuklang.")
        else:
            risk_vals = predict_risk_from_sensor(None,                # model ishlatilmaydi
                                                 df_sensor['temp'].values,
                                                 df_sensor['stress'].values,
                                                 df_sensor['ucs_lab'].values)
            df_sensor['risk'] = risk_vals
            st.subheader("Bashorat natijalari")
            st.dataframe(df_sensor, use_container_width=True)
            fig_risk_line = go.Figure()
            fig_risk_line.add_trace(go.Scatter(y=risk_vals, mode='lines+markers',
                                               name='Risk (0-1)', line=dict(color='red')))
            fig_risk_line.add_hline(y=0.5, line_dash='dash', line_color='orange',
                                    annotation_text="O'rta chegara")
            fig_risk_line.add_hline(y=0.7, line_dash='dash', line_color='red',
                                    annotation_text="Yuqori chegara")
            fig_risk_line.update_layout(title="AI Risk Prediction", xaxis_title="Qator indeksi",
                                        yaxis_title="Risk", template='plotly_dark')
            st.plotly_chart(fig_risk_line, use_container_width=True)
            avg_risk = np.mean(risk_vals)
            st.metric("O'rtacha risk", f"{avg_risk:.3f}",
                      delta="Yuqori" if avg_risk > 0.7 else ("O'rta" if avg_risk > 0.5 else "Past"))
            if avg_risk > 0.7:
                st.error("⚠️ Yuqori xavf! Tez choralar ko‘rish kerak.")
            elif avg_risk > 0.5:
                st.warning("⚠️ O‘rtacha xavf. Monitoringni kuchaytirish tavsiya etiladi.")
            else:
                st.success("✅ Xavf past. Hozircha xavfsiz.")

# ====================== Risk Map ======================
@st.cache_data(show_spinner=False)
def compute_risk_map(fos_arr, damage_arr, void_arr, temp_arr, T_max):
    fos_risk = np.clip(1.0 - fos_arr / 2.0, 0, 1)
    thermal_risk = damage_arr
    void_risk = void_arr.astype(float)
    temp_risk = np.clip(temp_arr / T_max, 0, 1)
    risk = 0.40 * fos_risk + 0.30 * thermal_risk + 0.20 * void_risk + 0.10 * temp_risk
    return np.clip(risk, 0, 1)

risk_map = compute_risk_map(fos_2d, damage, void_mask_permanent, temp_2d, T_source_max)

with st.expander("🗺️ Kompozit Xavf Indeksi Xaritasi"):
    risk_col1, risk_col2 = st.columns([2, 1])
    with risk_col1:
        fig_risk = go.Figure()
        fig_risk.add_trace(go.Heatmap(z=risk_map, x=x_axis, y=z_axis,
            colorscale=[[0.0, '#1a472a'], [0.33, '#27ae60'], [0.50, '#f39c12'],
                        [0.75, '#e74c3c'], [1.0, '#7b241c']],
            zmin=0, zmax=1, colorbar=dict(title="Risk (0–1)", tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                                          ticktext=["Xavfsiz", "Past", "O'rta", "Yuqori", "Kritik"])))
        fig_risk.add_trace(go.Contour(z=void_mask_permanent.astype(int), x=x_axis, y=z_axis,
                                      showscale=False, contours=dict(coloring='lines'),
                                      line=dict(color='white', width=2, dash='dot'),
                                      hoverinfo='skip', name='Void chegarasi'))
        fig_risk.update_layout(title="Kompozit Xavf Indeksi (FOS·40% + Damage·30% + Void·20% + T·10%)",
                              template='plotly_dark', height=450,
                              yaxis=dict(autorange='reversed', title='Chuqurlik (m)'),
                              xaxis=dict(title='Gorizontal masofa (m)'))
        st.plotly_chart(fig_risk, use_container_width=True)
    with risk_col2:
        total_cells = risk_map.size
        r_safe = np.sum(risk_map < 0.25) / total_cells * 100
        r_low = np.sum((risk_map >= 0.25) & (risk_map < 0.5)) / total_cells * 100
        r_medium = np.sum((risk_map >= 0.5) & (risk_map < 0.75)) / total_cells * 100
        r_high = np.sum(risk_map >= 0.75) / total_cells * 100
        fig_pie = go.Figure(go.Pie(labels=["Xavfsiz (<0.25)", "Past (0.25–0.5)",
                                           "O'rta (0.5–0.75)", "Kritik (>0.75)"],
                                   values=[r_safe, r_low, r_medium, r_high],
                                   marker_colors=['#27ae60', '#f39c12', '#e67e22', '#e74c3c'],
                                   hole=0.4, textinfo='label+percent'))
        fig_pie.update_layout(template='plotly_dark', height=300, title="Zona taqsimoti",
                             showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.metric("O'rtacha xavf indeksi", f"{np.mean(risk_map):.3f}")
        st.metric("Maksimal xavf indeksi", f"{np.max(risk_map):.3f}")
        if np.max(risk_map) > 0.75:
            st.error("🔴 Kritik zona mavjud!")
        elif np.max(risk_map) > 0.5:
            st.warning("🟡 O'rta xavf zonasi bor")
        else:
            st.success("🟢 Umumiy holat qoniqarli")

# ------------------------------- FOS Vaqt Bashorati -------------------------------
def fos_at_time(th, ucs0, beta_d, beta_str, T_max, burn_dur, w, H, sv_const):
    if th <= burn_dur:
        T_t = 25 + (T_max - 25) * (th / burn_dur)
    else:
        T_t = 25 + (T_max - 25) * np.exp(-0.03 * (th - burn_dur))
    damage = np.clip(1 - np.exp(-beta_d * max(T_t - 100, 0)), 0, 0.95)
    str_red = np.exp(-beta_str * max(T_t - 20, 0))
    ucs_eff = ucs0 * (1 - damage) * str_red
    p_str = ucs_eff * (w / (H + 1e-9)) ** 0.5
    return np.clip(p_str / (sv_const + 1e-9), 0, 5)

with st.expander("📈 FOS Vaqt Bashorati (Trend)"):
    time_points = np.arange(1, time_h + 1, max(1, time_h // 20))
    fos_timeline = [fos_at_time(th, ucs_seam, beta_damage, beta_strength,
                                T_source_max, burn_duration, rec_width, H_seam, sv_seam)
                    for th in time_points]
    slope, intercept, r_value, _, _ = linregress(time_points, fos_timeline)
    future_times = np.arange(time_h, min(time_h * 2, 300), max(1, time_h // 10))
    fos_forecast = intercept + slope * future_times
    fos_forecast = np.clip(fos_forecast, 0, 3)
    if slope < 0 and intercept + slope * time_h > 1.0:
        t_critical = (1.0 - intercept) / slope
        critical_info = f"⚠️ FOS=1.0 ga taxminan **{t_critical:.0f}** soatda yetishi mumkin"
    else:
        critical_info = "✅ Hozirgi trend bo'yicha FOS=1.0 ga yetish xavfi yo'q"
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=time_points, y=fos_timeline, mode='lines+markers',
                                   name='Hisoblangan FOS', line=dict(color='cyan', width=2),
                                   marker=dict(size=6)))
    trend_line = intercept + slope * time_points
    fig_trend.add_trace(go.Scatter(x=time_points, y=trend_line, mode='lines',
                                   name=f'Trend (R²={r_value**2:.3f})',
                                   line=dict(color='yellow', width=1, dash='dot')))
    fig_trend.add_trace(go.Scatter(x=future_times, y=fos_forecast, mode='lines',
                                   name='Bashorat', line=dict(color='orange', width=2, dash='dash'),
                                   fill='tozeroy', fillcolor='rgba(255,165,0,0.1)'))
    fig_trend.add_hline(y=1.5, line_color='green', line_dash='dash', annotation_text='Barqaror chegarasi (1.5)')
    fig_trend.add_hline(y=1.0, line_color='red', line_dash='dash', annotation_text='Kritik chegara (1.0)')
    fig_trend.add_vline(x=time_h, line_color='white', line_dash='dot', annotation_text=f'Hozir ({time_h}h)')
    fig_trend.update_layout(template='plotly_dark', height=400,
                            title=f"FOS vaqt bashorati | Trend: {slope:+.4f} FOS/soat",
                            xaxis_title='Vaqt (soat)', yaxis_title='FOS',
                            legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig_trend, use_container_width=True)
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Trend ko'rsatkichi", f"{slope:+.5f} FOS/soat",
               delta="Kamaymoqda" if slope < 0 else "O'smoqda",
               delta_color="inverse" if slope < 0 else "normal")
    tc2.metric("R² (trend aniqligi)", f"{r_value**2:.4f}")
    tc3.metric("Hozirgi FOS", f"{fos_timeline[-1]:.3f}")
    st.info(critical_info)

# =========================== 3D LITOLOGIK KESIM ===========================
with st.expander("🌍 3D Litologik Kesim"):
    fig_3d = go.Figure()
    y_3d = np.linspace(-total_depth * 0.5, total_depth * 0.5, 30)
    for i, layer in enumerate(layers_data):
        z_top = layer['z_start']
        z_bot = layer['z_start'] + layer['t']
        x_3d = np.linspace(x_axis.min(), x_axis.max(), 30)
        X3, Y3 = np.meshgrid(x_3d, y_3d)
        Z_top = np.full_like(X3, z_top)
        hex_color = layer['color'].lstrip('#')
        r, g, b = tuple(int(hex_color[j:j+2], 16) for j in (0, 2, 4))
        rgb_str = f"rgb({r},{g},{b})"
        fig_3d.add_trace(go.Surface(x=X3, y=Y3, z=Z_top, colorscale=[[0, rgb_str], [1, rgb_str]],
                                    showscale=False, opacity=0.7, name=layer['name'],
                                    hovertemplate=f"{layer['name']}<br>UCS: {layer['ucs']} MPa<br>GSI: {layer['gsi']}<extra></extra>"))
    for src_x in [-total_depth/3, 0, total_depth/3]:
        theta = np.linspace(0, 2*np.pi, 30)
        phi = np.linspace(0, np.pi, 20)
        THETA, PHI = np.meshgrid(theta, phi)
        R = H_seam * 0.4
        cx = src_x + R * np.sin(PHI) * np.cos(THETA)
        cy = R * np.sin(PHI) * np.sin(THETA)
        cz = source_z + R * np.cos(PHI)
        fig_3d.add_trace(go.Surface(x=cx, y=cy, z=cz, colorscale=[[0, 'orange'], [1, 'red']],
                                    showscale=False, opacity=0.85, name='Yonish kamerasi'))
    fig_3d.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Chuqurlik (m)',
                                    zaxis=dict(autorange='reversed'),
                                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))),
                         template='plotly_dark', height=600,
                         title="3D Litologik Model + Yonish Kameralari", showlegend=True)
    st.plotly_chart(fig_3d, use_container_width=True)
    st.caption("Sariq/qizil sferalar — yonish kameralari joylashuvi")

# =========================== MONTE CARLO NOANIQLIK TAHLILI (to‘liq overburden) ===========================
@st.cache_data(show_spinner=False)
def monte_carlo_fos(ucs_mean, ucs_std, gsi_mean, gsi_std, d_mean, temp_mean,
                    H_seam, H_total, rho_avg, beta_d, beta_str, n_sim=2000):
    rng = np.random.default_rng(SEED_GLOBAL)
    ucs_s = rng.normal(ucs_mean, ucs_std, n_sim).clip(1, 300)
    gsi_s = rng.normal(gsi_mean, gsi_std, n_sim).clip(10, 100)
    T_s   = rng.normal(temp_mean, temp_mean*0.1, n_sim).clip(20, 1200)
    H_s   = rng.normal(H_total, H_total*0.05, n_sim).clip(10, 2000)
    rho_s = rng.normal(rho_avg, rho_avg*0.05, n_sim).clip(1500, 3500)
    dmg_s = np.clip(1 - np.exp(-beta_d * np.maximum(T_s - 100, 0)), 0, 0.95)
    sci_s = ucs_s * (1 - dmg_s)
    str_r = np.exp(-beta_str * (T_s - 20))
    p_str = (sci_s * str_r) * (20.0 / (H_seam + 1e-12)) ** 0.5
    sv_s  = rho_s * 9.81 * H_s / 1e6                # to‘g‘ri litostatik bosim (MPa)
    fos_s = np.clip(p_str / (sv_s + 1e-12), 0, 5)
    pf = float(np.mean(fos_s < 1.0))
    return fos_s, pf

with st.expander("🎲 Monte Carlo Noaniqlik Tahlili"):
    mc_col1, mc_col2 = st.columns([1, 2])
    with mc_col1:
        ucs_std = st.number_input("UCS standart og'ish (MPa)", value=5.0, min_value=0.1)
        gsi_std = st.number_input("GSI standart og'ish", value=5.0, min_value=0.1)
        n_mc = st.selectbox("Simulyatsiya soni", [500, 1000, 2000, 5000], index=1)
    with mc_col2:
        fos_mc, pf = monte_carlo_fos(layers_data[-1]['ucs'], ucs_std, layers_data[-1]['gsi'], gsi_std,
                                     D_factor, avg_t_p, H_seam, H_total, rho_avg,
                                     beta_damage, beta_strength, n_sim=n_mc)
        fig_mc = go.Figure()
        fig_mc.add_histogram(x=fos_mc, nbinsx=40, marker_color=np.where(fos_mc < 1.0, '#E74C3C', '#27AE60'),
                             name='FOS taqsimoti')
        fig_mc.add_vline(x=1.0, line_color='red', line_dash='dash', annotation_text='FOS=1.0')
        fig_mc.add_vline(x=1.5, line_color='yellow', line_dash='dash', annotation_text='FOS=1.5')
        fig_mc.add_vline(x=np.mean(fos_mc), line_color='cyan', line_dash='dot',
                         annotation_text=f"O'rtacha={np.mean(fos_mc):.2f}")
        fig_mc.update_layout(template='plotly_dark', height=350,
                             title=f"FOS taqsimoti | Failure ehtimoli: {pf*100:.1f}%",
                             xaxis_title='FOS', yaxis_title='Chastota')
        st.plotly_chart(fig_mc, use_container_width=True)
    mc_stats = pd.DataFrame({
        'Ko\'rsatkich': ['O\'rtacha FOS', 'Mediana', 'Std og\'ish', '5-percentil', '95-percentil', 'Failure ehtimoli'],
        'Qiymat': [f"{np.mean(fos_mc):.3f}", f"{np.median(fos_mc):.3f}", f"{np.std(fos_mc):.3f}",
                   f"{np.percentile(fos_mc, 5):.3f}", f"{np.percentile(fos_mc, 95):.3f}", f"{pf*100:.2f}%"]
    })
    st.dataframe(mc_stats, hide_index=True, use_container_width=True)

# =========================== SSENARIY TAQQOSLASH (A vs B) ===========================
with st.expander("⚖️ Ssenariy Taqqoslash (A vs B)"):
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("**Ssenariy A**")
        a_ucs  = st.number_input("UCS_A (MPa)", value=float(layers_data[-1]['ucs']), key="a_ucs")
        a_gsi  = st.slider("GSI_A", 10, 100, layers_data[-1]['gsi'], key="a_gsi")
        a_temp = st.number_input("T_A (°C)", value=float(T_source_max), key="a_t")
    with sc2:
        st.markdown("**Ssenariy B**")
        b_ucs  = st.number_input("UCS_B (MPa)", value=float(layers_data[-1]['ucs'])*0.8, key="b_ucs")
        b_gsi  = st.slider("GSI_B", 10, 100, max(10, layers_data[-1]['gsi']-10), key="b_gsi")
        b_temp = st.number_input("T_B (°C)", value=float(T_source_max)*1.1, key="b_t")

    sigma_v_total_scenario = sum(l['rho']*9.81*l['t'] for l in layers_data[:-1])/1e6 + \
                             layers_data[-1]['rho']*9.81*(H_seam/2)/1e6
    fos_a = (a_ucs * np.exp(-0.0025 * (a_temp - 20))) / (sigma_v_total_scenario + 1e-12)
    fos_b = (b_ucs * np.exp(-0.0025 * (b_temp - 20))) / (sigma_v_total_scenario + 1e-12)

    def norm_safe(val, mn, mx):
        return float(np.clip((val - mn) / (mx - mn + 1e-12), 0, 1))

    ucs_max = max(a_ucs, b_ucs, 100)
    gsi_max = 100
    vals_a = [norm_safe(a_ucs, 0, ucs_max), norm_safe(a_gsi, 10, gsi_max),
              norm_safe(fos_a, 0, 3), 1 - norm_safe(a_temp, 20, 1200)]
    vals_b = [norm_safe(b_ucs, 0, ucs_max), norm_safe(b_gsi, 10, gsi_max),
              norm_safe(fos_b, 0, 3), 1 - norm_safe(b_temp, 20, 1200)]

    categories = ['UCS', 'GSI', 'FOS (taxmin)', 'Termal risk']
    fig_radar = go.Figure()
    for name, vals, color in [("A", vals_a, '#3498DB'), ("B", vals_b, '#E74C3C')]:
        fig_radar.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=categories + [categories[0]],
                                            fill='toself', name=f"Ssenariy {name}",
                                            line=dict(color=color, width=2), fillcolor=color, opacity=0.3))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                            template='plotly_dark', height=400, title="Ssenariylar radar taqqoslama")
    st.plotly_chart(fig_radar, use_container_width=True)
    comp_df = pd.DataFrame({
        'Ko\'rsatkich': ['UCS (MPa)', 'GSI', 'FOS (taxmin)', 'Harorat (°C)'],
        'Ssenariy A': [f"{a_ucs:.1f}", f"{a_gsi}", f"{fos_a:.2f}", f"{a_temp:.0f}"],
        'Ssenariy B': [f"{b_ucs:.1f}", f"{b_gsi}", f"{fos_b:.2f}", f"{b_temp:.0f}"],
        'Farq': [f"{b_ucs - a_ucs:+.1f}", f"{b_gsi - a_gsi:+d}", f"{fos_b - fos_a:+.2f}", f"{b_temp - a_temp:+.0f}"]
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

# =========================== SEZGIRLIK TAHLILI (TORNADO) – to‘liq chuqurlik ===========================
def hoek_brown_params(gsi, mi, d):
    mb = mi * np.exp((gsi - 100) / (28 - 14 * d))
    s  = np.exp((gsi - 100) / (9 - 3 * d))
    a  = 0.5 + (1/6)*(np.exp(-gsi/15) - np.exp(-20/3))
    return mb, s, a

def thermal_damage_func(T):
    return np.clip(1 - np.exp(-0.002 * np.maximum(T - 100, 0)), 0, 0.95)

def thermal_reduction_func(T):
    return np.exp(-0.0025 * (T - 20))

def in_situ_stress(rho, H, nu):
    sigma_v = rho * 9.81 * H / 1e6
    k = nu / (1 - nu)
    sigma_h = k * sigma_v
    return sigma_v, sigma_h

def pillar_strength_func(ucs, gsi, mi, d, T, width, H):
    dmg = thermal_damage_func(T)
    ucs_eff = ucs * (1 - dmg)
    str_red = thermal_reduction_func(T)
    return (ucs_eff * str_red) * (width / (H + 1e-12)) ** 0.5

def compute_fos_func(ucs, gsi, mi, d, nu, T, width, H, rho, sigma_v_override=None):
    if sigma_v_override is not None:
        sigma_v = sigma_v_override
    else:
        sigma_v, _ = in_situ_stress(rho, H, nu)
    p_str = pillar_strength_func(ucs, gsi, mi, d, T, width, H)
    return np.clip(p_str / (sigma_v + 1e-12), 0, 5)

def sensitivity_analysis(base_params, H, rho, range_pct=0.2, sigma_v_override=None):
    base_fos = compute_fos_func(**base_params, H=H, rho=rho, sigma_v_override=sigma_v_override)
    results = []
    for key in base_params.keys():
        low_params = base_params.copy()
        high_params = base_params.copy()
        if key == 'nu':
            low_params[key] = max(0.1, base_params[key] - 0.05)
            high_params[key] = min(0.4, base_params[key] + 0.05)
        elif key == 'd':
            low_params[key] = max(0, base_params[key] - 0.2)
            high_params[key] = min(1, base_params[key] + 0.2)
        else:
            low_params[key] = base_params[key] * (1 - range_pct)
            high_params[key] = base_params[key] * (1 + range_pct)
        fos_low = compute_fos_func(**low_params, H=H, rho=rho, sigma_v_override=sigma_v_override)
        fos_high = compute_fos_func(**high_params, H=H, rho=rho, sigma_v_override=sigma_v_override)
        results.append({'param': key, 'low': fos_low - base_fos, 'high': fos_high - base_fos})
    df = pd.DataFrame(results)
    df['impact'] = np.maximum(np.abs(df['low']), np.abs(df['high']))
    return df.sort_values('impact', ascending=True), base_fos

with st.expander("🌪️ Sezgirlik Tahlili (Tornado Plot) - Yangi Ilmiy Model"):
    st.markdown("Quyidagi tahlilda **Hoek-Brown**, **termal degradatsiya** va **Wilson pillar** nazariyalari asosida FOS sezgirligi baholanadi.")
    H_total_sens = sum(l['t'] for l in layers_data)
    rho_avg_sens = np.mean([l['rho'] for l in layers_data])
    sigma_v_full = rho_avg_sens * 9.81 * H_total_sens / 1e6      # MPa
    df_sens, fos_base = sensitivity_analysis(
        base_params={'ucs': layers_data[-1]['ucs'], 'gsi': layers_data[-1]['gsi'], 'mi': layers_data[-1]['mi'],
                     'd': D_factor, 'nu': nu_poisson, 'T': avg_t_p, 'width': rec_width},
        H=H_seam, rho=layers_data[-1]['rho'], range_pct=0.2, sigma_v_override=sigma_v_full)
    fig_tornado = go.Figure()
    fig_tornado.add_bar(y=df_sens['param'], x=df_sens['low'], orientation='h',
                        name='−20% (yoki pasaytirilgan)', marker_color='#E74C3C')
    fig_tornado.add_bar(y=df_sens['param'], x=df_sens['high'], orientation='h',
                        name='+20% (yoki oshirilgan)', marker_color='#27AE60')
    fig_tornado.add_vline(x=0, line_color='white', line_width=2)
    fig_tornado.update_layout(title=f"FOS Sezgirligi (asosiy FOS = {fos_base:.2f})",
                              barmode='relative', template='plotly_dark', height=450,
                              xaxis_title='ΔFOS', yaxis_title='Parametr',
                              legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    st.plotly_chart(fig_tornado, use_container_width=True)
    st.caption("Parametrlar: ucs – bir oʻqli mustahkamlik, gsi – geologik kuch indeksi, mi – Hoek-Brown doimiysi, d – buzilish koeffitsiyenti, nu – Puasson koeffitsiyenti, T – harorat, width – selek eni.")
    st.info(f"**Xulosa:** Asosiy FOS = {fos_base:.2f}. Eng ta'sirchan parametr: **{df_sens.iloc[-1]['param']}** (ΔFOS = {df_sens.iloc[-1]['high']:.3f}).")

# =========================== SIRDESAI DASHBOARD ===========================
st.header("🕹️ Ultimate Interactive Dashboard (Real-time Animation)")
st.markdown("Ushbu panelda Sirdesai va boshqalar (2017) modeli asosida termal buzilish, kuchlanish va sirt deformatsiyalari interaktiv tarzda kuzatiladi.")

@st.cache_data
def calculate_comprehensive_metrics_sird(x, z, E, nu, alpha, beta_th, angle_draw, t_max, width, depth, shift):
    X, Z = np.meshgrid(x, z, indexing='ij')
    reaktor_x = shift
    dist = np.sqrt((X - reaktor_x)**2 + (Z - depth)**2)
    temp = 25 + (t_max - 25) * np.exp(-dist / (width / 2))
    dT = np.maximum(temp - 25, 0)
    dmg = np.clip(1 - np.exp(-beta_th * dT), 0, 1)
    sth = (E * alpha * dT) / (1 - nu)
    i = depth * np.tan(np.radians(angle_draw))
    s_max = (0.001 * (width**2)) / (1 + depth / 450)
    sv = s_max * np.exp(-((x - reaktor_x)**2) / (2 * i**2))
    sh = ((x - reaktor_x) / i) * sv * 0.55
    return dmg, sth, sv.reshape(-1), sh.reshape(-1)

with st.sidebar.expander("📊 Sirdesai Dashboard sozlamalari", expanded=False):
    method_sird = st.radio("UCG Usuli", ["LVW", "CRIP"], key="sird_method")
    reaktor_shift_sird = st.slider("Reaktor siljishi (m)", -100, 100, 0, key="sird_shift") if method_sird == "CRIP" else 0
    c_width_sird = st.slider("Reaktor kengligi (W) [m]", 20, 200, 100, key="sird_width")
    c_depth_sird = st.selectbox("Chuqurlik (h) [m]", [100, 500, 1000], index=1, key="sird_depth")
    t_core_sird = st.slider("Reaktor Harorati (°C)", 25, 1100, 950, key="sird_temp")

p_sird = {'E': 25.45e9, 'nu': 0.24, 'alpha': 11e-6, 'beta_th': 0.0025, 'angle_draw': 35}
x_axis_sird = np.linspace(-350, 350, 150)
z_axis_sird = np.linspace(0, c_depth_sird + 150, 80)

dmg_sird, sth_sird, sv_sird, sh_sird = calculate_comprehensive_metrics_sird(
    x_axis_sird, z_axis_sird,
    p_sird['E'], p_sird['nu'], p_sird['alpha'], p_sird['beta_th'], p_sird['angle_draw'],
    t_core_sird, c_width_sird, c_depth_sird, reaktor_shift_sird
)

main_col_sird, theory_col_sird = st.columns([2.5, 1])
with main_col_sird:
    fig_sird = make_subplots(rows=2, cols=2, subplot_titles=("A) Vertikal Cho'kish (sv)", "B) Gorizontal Siljish (sh)", "C) Termal Buzilish D(T)", "D) Termal Kuchlanish (MPa)"), vertical_spacing=0.25, horizontal_spacing=0.12)
    fig_sird.add_trace(go.Scatter(x=x_axis_sird, y=-sv_sird, fill='tozeroy', name="sv", line=dict(color='#00f2ff', width=3), hovertemplate='X: %{x} m<br>Cho\'kish: %{y} mm'), row=1, col=1)
    fig_sird.add_trace(go.Scatter(x=[x_axis_sird[np.argmax(sv_sird)]], y=[-np.max(sv_sird)], mode='markers+text', text=f'Max: {np.max(sv_sird):.2f}mm', textposition='top center', marker=dict(color='red', size=12, symbol='x')), row=1, col=1)
    fig_sird.add_trace(go.Scatter(x=x_axis_sird, y=sh_sird, name="sh", line=dict(color='orange'), hovertemplate='X: %{x} m<br>Siljish: %{y} mm'), row=1, col=2)
    fig_sird.add_trace(go.Heatmap(z=dmg_sird.T, x=x_axis_sird, y=z_axis_sird, colorscale='Viridis', zmin=0, zmax=1, colorbar=dict(title="D(T)", x=0.43, len=0.35, y=0.2, thickness=15)), row=2, col=1)
    fig_sird.add_trace(go.Heatmap(z=(sth_sird.T / 1e6), x=x_axis_sird, y=z_axis_sird, colorscale='Cividis', colorbar=dict(title="MPa", x=1.05, len=0.35, y=0.2, thickness=15)), row=2, col=2)
    fig_sird.update_yaxes(title_text="Chuqurlik (m)", autorange="reversed", row=2, col=1)
    fig_sird.update_yaxes(autorange="reversed", row=2, col=2)
    fig_sird.update_layout(height=850, template='plotly_dark', showlegend=False, margin=dict(t=80, l=60, r=80))
    st.plotly_chart(fig_sird, use_container_width=True)
with theory_col_sird:
    st.markdown("### 📚 Ilmiy Mexanizm")
    st.markdown("**Sirdesai modeli asosidagi cho'kish mexanizmi:**")
    st.code("""
    Yer yuzasi
─────────────────────────
     ^
     | S (maks. cho'kish)
     |
─────┼─────   γ (tortish burchagi)
     |    ╱
M ───┼───╱  (qatlam qalinligi)
     |  ╱
─────┼─╱───
     |╱
[=====W=====]  Reaktor kengligi
    """, language="text")
    st.info("**Grafik ko'rsatkichlari:**\n- **M**: Qatlam qalinligi (m)\n- **W**: Reaktor kengligi (m)\n- **S**: Maksimal vertikal cho'kish (mm)\n- **γ (gamma)**: Tortish burchagi (daraja)")
    st.success("**Tahlil (PhD Xulosasi):**\nReaktor yer yuzasiga qanchalik yaqin bo'lsa (h kam bo'lsa), sirt deformatsiyasi shunchalik keskinlashadi. Kenglik (W) 100 metrdan oshganda yuqori cho'kish kutiladi.")

# =========================== LIVE 3D MONITORING ===========================
st.header("🔄 Live 3D Monitoring (Real-time)")
tab_live, tab_ai_orig, tab_advanced = st.tabs([t('live_monitoring_tab'), t('ai_monitor_title'), t('advanced_analysis')])

# ---------- Pillar modelini o‘rgatish (live monitoring uchun) ----------
@st.cache_resource
def train_live_pillar_model():
    rng = np.random.default_rng(SEED_GLOBAL)
    n = 5000
    burn  = rng.uniform(10, 200, n)
    T_max = rng.uniform(400, 1200, n)
    ucs   = rng.uniform(15, 80, n)
    H     = rng.uniform(2, 30, n)
    str_red = np.exp(-0.0025 * (T_max - 20))
    sv_est  = 2500 * 9.81 * 200 / 1e6        # 200 m tipik chuqurlik
    w_target = H * (sv_est * 1.5 / (ucs * str_red + 1e-6)) ** 2   # FOS=1.5 teskari Wilson
    X = np.column_stack([burn, T_max, ucs])
    rf = RandomForestRegressor(n_estimators=50, random_state=SEED_GLOBAL)
    rf.fit(X, np.clip(w_target, 5, 60))
    return rf

rf_live = train_live_pillar_model()

with tab_live:
    st.markdown("### Real-time subsidence, temperature, anomalies and alerts")
    TIME_STEPS = st.slider("Simulation steps", 10, 200, 50, key="live_steps")
    run_live = st.button("▶️ Run Live Monitoring", key="run_live")
    stop_live = st.button("⏹ Stop Monitoring", key="stop_live")
    if 'stop_flag_live' not in st.session_state: st.session_state.stop_flag_live = False
    if stop_live: st.session_state.stop_flag_live = True
    col_live1, col_live2 = st.columns(2)
    subs_plot_live = col_live1.empty()
    temp_plot_live = col_live2.empty()
    col_live3, col_live4 = st.columns(2)
    pillar_plot_live = col_live3.empty()
    trend_plot_live = col_live4.empty()
    surface_3d_plot_live = st.empty()
    alert_box_live = st.empty()
    if 'live_history_df' not in st.session_state:
        st.session_state.live_history_df = pd.DataFrame(columns=['step', 'mean_subsidence_cm', 'max_temp_c', 'FOS', 'pillar_width_m'])
    if run_live:
        st.session_state.stop_flag_live = False
        X_live = np.linspace(-20, 20, 50); Y_live = np.linspace(-20, 20, 50)
        X_grid_live, Y_grid_live = np.meshgrid(X_live, Y_live)
        subs_history_live = []; fos_history_live = []; width_history_live = []; temp_history_live = []; steps_done = 0
        for t_step in range(TIME_STEPS):
            if st.session_state.stop_flag_live: break
            Z_subs = np.exp(-(X_grid_live**2 + Y_grid_live**2) / (2 * (5 + t_step * 0.1)**2)) * 5 * t_step / TIME_STEPS
            Z_temp = np.exp(-(X_grid_live**2 + Y_grid_live**2) / (2 * 8**2)) * T_source_max * t_step / TIME_STEPS
            Z_filtered = gaussian_filter(Z_subs, sigma=1)
            anomalies = Z_subs - Z_filtered
            anomaly_points = np.where(np.abs(anomalies) > 0.2)
            avg_ucs = np.mean([l['ucs'] for l in layers_data])
            X_feat = np.array([[burn_duration, T_source_max, avg_ucs]]).reshape(1, -1)
            pillar_width_pred = rf_live.predict(X_feat)[0]          # o‘qitilgan model
            FOS_live = np.clip(2.5 - t_step * 0.03, 0.8, 2.5)
            mean_subs = np.mean(Z_subs)
            subs_history_live.append(mean_subs); fos_history_live.append(FOS_live); width_history_live.append(pillar_width_pred); temp_history_live.append(np.mean(Z_temp))
            new_row = pd.DataFrame({'step': [t_step + 1], 'mean_subsidence_cm': [mean_subs * 100], 'max_temp_c': [np.max(Z_temp)], 'FOS': [FOS_live], 'pillar_width_m': [pillar_width_pred]})
            st.session_state.live_history_df = pd.concat([st.session_state.live_history_df, new_row], ignore_index=True).tail(1000)
            fig_subs = go.Figure(go.Heatmap(z=Z_subs * 100, x=X_live, y=Y_live, colorscale='Viridis')).update_layout(title='Surface Subsidence (cm)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            subs_plot_live.plotly_chart(fig_subs, use_container_width=True, key=f"subs_{t_step}")
            fig_temp = go.Figure(go.Heatmap(z=Z_temp, x=X_live, y=Y_live, colorscale='Hot')).update_layout(title='Temperature Field (°C)', xaxis_title='X (m)', yaxis_title='Y (m)', height=350)
            temp_plot_live.plotly_chart(fig_temp, use_container_width=True, key=f"temp_{t_step}")
            pillar_plot_live.metric(label="Recommended Pillar Width (m)", value=f"{pillar_width_pred:.2f}", delta=f"FOS = {FOS_live:.2f}")
            trend_fig = go.Figure(go.Scatter(y=subs_history_live, mode='lines+markers', name='Subsidence (cm)')).update_layout(title='Subsidence Trend', xaxis_title='Time step', yaxis_title='Mean subsidence (cm)', height=350)
            trend_plot_live.plotly_chart(trend_fig, use_container_width=True, key=f"trend_{t_step}")
            surface_fig = go.Figure(data=[go.Surface(z=Z_subs * 100, x=X_live, y=Y_live, colorscale='Viridis', opacity=0.9)])
            if anomaly_points[0].size > 0:
                surface_fig.add_trace(go.Scatter3d(x=X_grid_live[anomaly_points], y=Y_grid_live[anomaly_points], z=Z_subs[anomaly_points] * 100, mode='markers', marker=dict(color='red', size=5), name='Anomaly'))
            surface_fig.update_layout(title='3D Surface & Anomalies', scene=dict(zaxis_title='Subsidence (cm)'), height=500)
            surface_3d_plot_live.plotly_chart(surface_fig, use_container_width=True, key=f"surf_{t_step}")
            alerts = []
            if FOS_live < 1.2: alerts.append("⚠️ FOS Critical!")
            if mean_subs * 100 > 3: alerts.append("⚠️ High Subsidence!")
            if np.max(Z_temp) > 1100: alerts.append("🔥 Overheating Alert!")
            if alerts: alert_box_live.markdown("### 🔴 ALERTS\n" + "\n".join(alerts))
            else: alert_box_live.markdown("### 🟢 All systems normal")
            time.sleep(0.1); steps_done += 1
        st.success(f"✅ Live monitoring completed after {steps_done} steps.")
    if not st.session_state.live_history_df.empty:
        st.markdown("---"); st.subheader("📥 Download Monitoring Results (CSV)")
        csv_data = st.session_state.live_history_df.to_csv(index=False).encode('utf-8')
        st.download_button(label=t('download_data'), data=csv_data, file_name="ucg_live_monitoring.csv", mime="text/csv")

# ---------- AI Monitoring (anomaliya va FOS bashorat) ----------
with tab_ai_orig:
    st.markdown(f"*{t('ai_monitor_desc')}*")
    def get_sensor_data_sim(step, total_steps, base_temp):
        trend = step / total_steps
        temp = base_temp * (0.5 + 0.7 * trend) + np.random.normal(0, 10)
        pressure = 2 + 5 * trend + np.random.normal(0, 0.5)
        stress = 5 + 10 * trend + np.random.normal(0, 0.5)
        return {"temperature": temp, "gas_pressure": pressure, "stress": stress}

    def compute_effective_stress(sensor, biot_alpha=0.85, K_bulk_GPa=10.0,
                                  alpha_thermal=1e-5, T_ref=20.0):
        """Termo-poro-mexanik effektiv kuchlanish (Coussy, 2004; Biot-Terzaghi)."""
        sigma   = sensor["stress"]
        p_pore  = sensor["gas_pressure"]
        T       = sensor["temperature"]
        K_MPa   = K_bulk_GPa * 1000.0
        delta_T = T - T_ref
        sigma_eff = sigma - biot_alpha * p_pore + 3.0 * K_MPa * alpha_thermal * delta_T / 1e3
        return sigma_eff

    def detect_anomaly_z(history, value, threshold=2.0, window=20):
        if len(history) < window: return False
        recent = history[-window:]; mean = np.mean(recent); std = np.std(recent) + 1e-6
        return abs(value - mean) > threshold * std

    def simulate_sensors_fos(n_steps):
        T = np.linspace(20, min(1100, T_source_max), n_steps) + np.random.normal(0, 10, n_steps)
        sigma_v = np.linspace(5, min(15, sv_seam * 10), n_steps) + np.random.normal(0, 0.5, n_steps)
        return pd.DataFrame({'Temperature': T, 'VerticalStress': sigma_v})

    if PT_AVAILABLE:
        class SimpleNN(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(2, 16); self.fc2 = nn.Linear(16, 16); self.fc3 = nn.Linear(16, 1)
            def forward(self, x): x = torch.relu(self.fc1(x)); x = torch.relu(self.fc2(x)); return self.fc3(x)
        fos_nn_model = SimpleNN().to(device); fos_criterion = nn.MSELoss(); fos_optimizer = torch.optim.Adam(fos_nn_model.parameters(), lr=0.01)
    else:
        fos_rf_model = RandomForestRegressor(n_estimators=50, random_state=42)

    ai_tab1, ai_tab2 = st.tabs(["📡 Anomaliya Aniqlash (Digital Twin)", "📊 FOS Prediction (SimpleNN / RF)"])
    with ai_tab1:
        st.markdown("#### Sensor ma'lumotlari asosida real-vaqt anomaliya aniqlash")
        t1_col1, t1_col2, t1_col3 = st.columns([1, 1, 2])
        with t1_col1: ai_steps_1 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=60, step=10, key="ai_steps_1")
        with t1_col2: anomaly_threshold = st.slider("Anomaliya chegarasi (σ)", 1.0, 4.0, 2.0, 0.5, key="thresh_1")
        with t1_col3: run_ai_1 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_1")
        if run_ai_1:
            placeholder_1 = st.empty()
            history_eff = []; anomalies_eff = []; temp_history = []; gas_history = []; stress_history = []
            for step in range(int(ai_steps_1)):
                sensor = get_sensor_data_sim(step, int(ai_steps_1), T_source_max * 0.6)
                effective = compute_effective_stress(sensor)
                is_anomaly = detect_anomaly_z(history_eff, effective, threshold=anomaly_threshold)
                history_eff.append(effective); anomalies_eff.append(effective if is_anomaly else None)
                temp_history.append(sensor["temperature"]); gas_history.append(sensor["gas_pressure"]); stress_history.append(sensor["stress"])
                with placeholder_1.container():
                    acol1, acol2, acol3, acol4 = st.columns(4)
                    acol1.metric("🌡 Harorat", f"{sensor['temperature']:.1f} °C", delta=f"{sensor['temperature'] - np.mean(temp_history):.1f}" if len(temp_history) > 1 else None)
                    acol2.metric("💨 Gaz bosimi", f"{sensor['gas_pressure']:.2f} MPa")
                    acol3.metric("🧱 Effektiv σ", f"{effective:.2f} MPa", delta_color="inverse", delta="⚠️ Anomaliya!" if is_anomaly else "Normal")
                    acol4.metric("📈 Qadam", f"{step+1}/{int(ai_steps_1)}")
                    fig_a = make_subplots(rows=2, cols=2, subplot_titles=("Effektiv Kuchlanish & Anomaliyalar", "Harorat Tarixi (°C)", "Gaz Bosimi (MPa)", "Stress Tarixi (MPa)"), vertical_spacing=0.15, horizontal_spacing=0.1)
                    fig_a.add_trace(go.Scatter(y=history_eff, mode='lines', name='Effektiv σ', line=dict(color='cyan', width=2)), row=1, col=1)
                    fig_a.add_trace(go.Scatter(y=anomalies_eff, mode='markers', name='Anomaliya', marker=dict(color='red', size=10, symbol='x')), row=1, col=1)
                    fig_a.add_trace(go.Scatter(y=temp_history, mode='lines', name='Harorat', line=dict(color='orange', width=2)), row=1, col=2)
                    fig_a.add_trace(go.Scatter(y=gas_history, mode='lines+markers', name='Gaz bosimi', line=dict(color='lime', width=1), marker=dict(size=4)), row=2, col=1)
                    fig_a.add_trace(go.Scatter(y=stress_history, mode='lines', name='Stress', line=dict(color='magenta', width=2)), row=2, col=2)
                    fig_a.update_layout(template="plotly_dark", height=500, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(t=60, b=60))
                    st.plotly_chart(fig_a, use_container_width=True, key=f"anom_{step}")
                    anomaly_count = sum(1 for a in anomalies_eff if a is not None)
                    if is_anomaly: st.error(f"🚨 ANOMALIYA ANIQLANDI! (Jami: {anomaly_count}) — Collapse ehtimoli yuqori!")
                    elif effective > pillar_strength * 0.8: st.warning(f"⚠️ Kuchlanish Pillar Strength ({pillar_strength:.1f} MPa) ning 80% dan oshdi!")
                    else: st.success(f"✅ Normal holat — Effektiv σ: {effective:.2f} MPa")
                    st.progress((step+1)/int(ai_steps_1))
                time.sleep(0.15)
            st.balloons(); st.success(f"✅ Monitoring yakunlandi! Jami anomaliyalar: {sum(1 for a in anomalies_eff if a is not None)}")
    with ai_tab2:
        st.markdown("#### SimpleNN yoki RandomForest yordamida FOS (Factor of Safety) bashorati")
        t2_col1, t2_col2 = st.columns([1, 3])
        with t2_col1: ai_steps_2 = st.number_input(t('ai_steps'), min_value=10, max_value=500, value=50, step=10, key="ai_steps_2"); fos_target = st.number_input("Maqsad FOS qiymati", min_value=5.0, max_value=30.0, value=12.0, step=0.5)
        with t2_col2: run_ai_2 = st.button(t('ai_run_btn'), type="primary", use_container_width=True, key="run_ai_2")
        if run_ai_2:
            placeholder_2 = st.empty()
            sensor_data_fos = simulate_sensors_fos(int(ai_steps_2))
            pillar_strength_pred = []
            fos_rf_trained = False
            for i in range(int(ai_steps_2)):
                row = sensor_data_fos.iloc[i]
                X = np.array([[row.Temperature, row.VerticalStress]])
                if PT_AVAILABLE:
                    X_t = torch.tensor(X, dtype=torch.float32).to(device)
                    y_pred = fos_nn_model(X_t).detach().cpu().numpy()[0][0]
                    target = torch.tensor([[fos_target]], dtype=torch.float32).to(device)
                    fos_optimizer.zero_grad(); loss = fos_criterion(fos_nn_model(X_t), target); loss.backward(); fos_optimizer.step()
                else:
                    if not fos_rf_trained: fos_rf_model.fit(X, [fos_target]); fos_rf_trained = True
                    y_pred = fos_rf_model.predict(X)[0]
                pillar_strength_pred.append(float(y_pred))
                if y_pred < 10: fos_color = t('fos_red')
                elif y_pred <= 15: fos_color = t('fos_yellow')
                else: fos_color = t('fos_green')
                with placeholder_2.container():
                    p2c1, p2c2, p2c3 = st.columns(3)
                    p2c1.metric("🌡 Harorat", f"{row.Temperature:.1f} °C")
                    p2c2.metric("🧱 Vertikal Stress", f"{row.VerticalStress:.2f} MPa")
                    p2c3.metric("📊 Bashorat FOS", f"{y_pred:.2f}", delta=fos_color)
                    fig_fos = make_subplots(rows=1, cols=2, subplot_titles=("FOS Bashorati (Tarixiy)", "Sensor: Harorat vs Stress"))
                    fig_fos.add_trace(go.Scatter(y=pillar_strength_pred, mode='lines+markers', name=t('pillar_live'), line=dict(color='lime', width=2), marker=dict(size=5)), row=1, col=1)
                    fig_fos.add_hline(y=fos_target, line_dash="dash", line_color="yellow", annotation_text=f"Maqsad: {fos_target}", row=1, col=1)
                    fig_fos.add_trace(go.Scatter(x=sensor_data_fos['Temperature'].iloc[:i+1].tolist(), y=sensor_data_fos['VerticalStress'].iloc[:i+1].tolist(), mode='markers', name='Sensor yo\'li', marker=dict(color=list(range(i+1)), colorscale='Viridis', size=6, showscale=False)), row=1, col=2)
                    fig_fos.update_layout(template="plotly_dark", height=420, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), margin=dict(t=60, b=60))
                    fig_fos.update_xaxes(title_text="Qadam", row=1, col=1); fig_fos.update_yaxes(title_text="FOS / Strength", row=1, col=1)
                    fig_fos.update_xaxes(title_text="Harorat (°C)", row=1, col=2); fig_fos.update_yaxes(title_text="Vertikal Stress (MPa)", row=1, col=2)
                    st.plotly_chart(fig_fos, use_container_width=True, key=f"fospred_{i}")
                    st.info(f"Qadam {i+1}/{int(ai_steps_2)} | Model: {'PyTorch SimpleNN' if PT_AVAILABLE else 'RandomForest'} | {fos_color}")
                    st.progress((i+1)/int(ai_steps_2))
                time.sleep(0.05)
            st.balloons()
            final_fos = pillar_strength_pred[-1] if pillar_strength_pred else 0
            if final_fos < 10: st.error(f"🔴 Yakuniy FOS: {final_fos:.2f} — Xavfli zona!")
            elif final_fos <= 15: st.warning(f"🟡 Yakuniy FOS: {final_fos:.2f} — Noaniq holat")
            else: st.success(f"🟢 Yakuniy FOS: {final_fos:.2f} — Barqaror!")

# ---------- Chuqurlashtirilgan tahlil (oldingidek) ----------
with tab_advanced:
    st.header(t('advanced_analysis'))
    E_MODULUS_R, ALPHA_THERM, BETA_CONST = E_MODULUS, ALPHA_T_COEFF, beta_damage
    target_l = layers_data[-1]
    ucs_0_r, gsi_val, mi_val = target_l['ucs'], target_l['gsi'], target_l['mi']
    gamma_kn = target_l['rho'] * 9.81 / 1000
    H_depth_tot = sum(l['t'] for l in layers_data[:-1]) + target_l['t']/2
    sigma_v_tot = (gamma_kn * H_depth_tot) / 1000
    mb_dyn = mi_val * np.exp((gsi_val-100)/(28-14*D_factor))
    s_dyn = np.exp((gsi_val-100)/(9-3*D_factor))
    ucs_t_dyn = ucs_0_r * np.exp(-beta_damage*(T_source_max-20))
    p_str_final = ucs_t_dyn * (rec_width/(H_seam+EPS))**0.5
    fos_final = p_str_final/(sigma_v_tot+EPS)
    t1,t2,t3 = st.tabs([t('tab_mass'), t('tab_thermal'), t('tab_stability')])
    with t1:
        st.subheader(t('hb_class'))
        c1r,c2r = st.columns(2)
        with c1r:
            st.latex(t('hb_mb', mb=mb_dyn))
            st.caption(t('hb_caption_mb', mi=mi_val))
            st.latex(t('hb_s', s=s_dyn))
            st.caption(t('hb_caption_s', gsi=gsi_val))
        with c2r:
            st.markdown(t('hb_interpret', gsi=gsi_val, perc=((1 - s_dyn)*100)))
    with t2:
        st.subheader(t('thermal_params'))
        params_df = pd.DataFrame({t('param_table_param'): [t('modulus'), t('alpha'), t('temp0')],
                                  t('param_table_value'): [f"{E_MODULUS_R} MPa", f"{ALPHA_THERM} 1/°C", "20 °C"],
                                  t('param_table_reason'): [t('modulus_reason'), t('alpha_reason'), t('temp0_reason')]})
        st.table(params_df)
        st.markdown(t('ucs_decay'))
        st.latex(t('ucs_decay_eq', ucs=ucs_t_dyn))
        st.write(t('ucs_interpret', temp=T_source_max, perc=((1 - ucs_t_dyn/ucs_0_r)*100)))
        st.markdown(t('thermal_stress'))
        st.latex(t('thermal_stress_eq', sigma=sigma_thermal.max()))
    with t3:
        st.subheader(t('pillar_stability'))
        st.latex(t('fos_eq', fos=fos_final))
        st.write(t('pillar_wilson', w=rec_width, sv=sigma_v_tot, y=y_zone))
        st.markdown("---")
        st.write(t('references'))
        for ref in [t('ref1'), t('ref2'), t('ref3'), t('ref4'), t('ref5'), t('ref6'), t('ref7'), t('ref8'), t('ref9'), t('ref10'), t('ref11')]:
            st.markdown(f"📖 {ref}")
        if fos_final < 1.3: st.error(t('conclusion_danger', fos=fos_final))
        else: st.success(t('conclusion_safe', fos=fos_final))

# ====================== TEST, XATOLIKLAR VA LINTER/DEBUGGER ======================
st.markdown("---")
st.header("🧪 Dasturlash bo‘yicha qo‘shimcha: test, xatolik tahlillari va vositalar")
tab_test, tab_errors, tab_tools = st.tabs(["✅ Test (test_math)", "🐞 Xatoliklar namunalari", "🛠️ Linter / Formatter / Debugger"])
with tab_test:
    st.subheader("file: test_math.py – test funksiyasi")
    code_test = '''def add(x, y):
    return x + y

def test_add():
    assert add(1, 2) == 3
    assert add(-1, -2) == -3
'''
    st.code(code_test, language="python")
    if st.button("▶️ test_add() ni ishga tushirish"):
        try:
            def add(x, y): return x + y
            assert add(1, 2) == 3
            assert add(-1, -2) == -3
            st.success("✅ Barcha testlar muvaffaqiyatli o‘tdi!")
        except AssertionError as e:
            st.error(f"❌ Test xatosi: {e}")
with tab_errors:
    st.subheader("Turli dasturlash tillarida sintaksis, mantiqiy va resurs xatolari (tuzatilgan)")
    lang_choice = st.selectbox("Tilni tanlang", ["Python", "JavaScript", "Java", "C++ (misol yo'q, lekin jadvalda ko'rsatilgan)"], key="err_lang")
    if lang_choice == "Python":
        st.markdown("**Sintaksis xatosi (to'g'rilangan)**")
        st.code('''# Noto'g'ri: if operatorida ':' yo'q
# x = 5
# if x == 5 print(x)

# Tuzatilgan:
if x == 5:
    print(x)''', language="python")
        st.markdown("**Mantiqiy xato (o'rtacha hisoblash)**")
        st.code('''# Noto'g'ri: // butun bo'linish, kasr qismini tashlaydi
def average(nums):
    total = sum(nums)
    return total // len(nums)

# Tuzatilgan:
def average(nums):
    total = sum(nums)
    return total / len(nums)''', language="python")
        st.markdown("**Resurs oqishi (fayl yopilmasligi)**")
        st.code('''# Noto'g'ri: fayl yopilmagan
def read_file(path):
    f = open(path, 'r')
    data = f.read()
    # f.close() unutib qolingan

# Tuzatilgan (context manager):
def read_file(path):
    with open(path, 'r') as f:
        data = f.read()
    return data''', language="python")
    elif lang_choice == "JavaScript":
        st.markdown("**Sintaksis xatosi**")
        st.code('''// Noto'g'ri: if sharti noto'g'ri
// if (x === 10) console.log("Ten");

// Tuzatilgan:
if (x === 10) {
    console.log("Ten");
}''', language="javascript")
        st.markdown("**Mantiqiy xato (sort)**")
        st.code('''// Noto'g'ri: lexikografik tartib
function sortNumbers(arr) {
    return arr.sort();
}

// Tuzatilgan:
function sortNumbers(arr) {
    return arr.sort((a, b) => a - b);
}''', language="javascript")
        st.markdown("**Resurs oqishi (fayl oqishning yo'q)**")
        st.code('''// Noto'g'ri: fayl ochilgan, lekin yopilmaydi
const fs = require('fs');
function readFile(path) {
    const data = fs.readFileSync(path, 'utf-8');
    return data;
}

// Tuzatilgan (finally bilan yopish):
const fs = require('fs');
function readFile(path) {
    try {
        const data = fs.readFileSync(path, 'utf-8');
        return data;
    } finally {
        fs.closeSync(fs.openSync(path, 'r'));
    }
}''', language="javascript")
    elif lang_choice == "Java":
        st.markdown("**Sintaksis xatosi (nuqta-vergul)**")
        st.code('''// Noto'g'ri: nuqta-vergul yo'q
// int x = 7;
// if (x == 7) System.out.println("Seven")

// Tuzatilgan:
if (x == 7) {
    System.out.println("Seven");
}''', language="java")
        st.markdown("**Mantiqiy xato (butun bo'linma)**")
        st.code('''// Noto'g'ri: int / int -> int
public double divide(int a, int b) {
    return a / b;   // butun qismi
}

// Tuzatilgan:
public double divide(int a, int b) {
    return (double) a / b;
}''', language="java")
        st.markdown("**Resurs oqishi (FileInputStream ochilgan, yopilmagan)**")
        st.code('''// Noto'g'ri: in, out yopilmagan
public void copyFile(String src, String dest) throws IOException {
    FileInputStream in = new FileInputStream(src);
    FileOutputStream out = new FileOutputStream(dest);
    byte[] buf = new byte[1024];
    int len;
    while ((len = in.read(buf)) > 0) {
        out.write(buf, 0, len);
    }
    // in.close(), out.close() chaqirilmagan
}

// Tuzatilgan: try-with-resources
public void copyFile(String src, String dest) throws IOException {
    try (FileInputStream in = new FileInputStream(src);
         FileOutputStream out = new FileOutputStream(dest)) {
        byte[] buf = new byte[1024];
        int len;
        while ((len = in.read(buf)) > 0) {
            out.write(buf, 0, len);
        }
    }
}''', language="java")
with tab_tools:
    st.subheader("Tillar bo‘yicha linter / formatter va debugger vositalari")
    tools_data = [
        {"Til": "Python", "Linter / Formatter": "Pylint, Flake8, Black", "Buyruq": "pylint mycode.py\nflake8 path/to/code.py\nblack mycode.py", "Debugger / Profiler": "PDB (python -m pdb mycode.py), ipdb"},
        {"Til": "JavaScript/Node.js", "Linter / Formatter": "ESLint, Prettier", "Buyruq": "npx eslint file.js\nnpx prettier --write .", "Debugger / Profiler": "node --inspect file.js, Chrome DevTools"},
        {"Til": "Java", "Linter / Formatter": "Checkstyle, SpotBugs", "Buyruq": "mvn checkstyle:checkstyle\nmvn spotbugs:spotbugs", "Debugger / Profiler": "jdb, IDE debugger (IntelliJ, Eclipse)"},
        {"Til": "C#", "Linter / Formatter": "dotnet-format, StyleCop", "Buyruq": "dotnet format\n(Visual Studio integratsiyasi)", "Debugger / Profiler": "Visual Studio debugger, dbgclr"},
        {"Til": "C/C++", "Linter / Formatter": "clang-format, cppcheck", "Buyruq": "clang-format -i file.cpp\ncppcheck .", "Debugger / Profiler": "gdb, Valgrind (valgrind --leak-check=full ./program)"},
        {"Til": "Go", "Linter / Formatter": "go fmt, go vet", "Buyruq": "go fmt ./...\ngo vet ./...", "Debugger / Profiler": "Delve (dlv debug)"},
        {"Til": "Rust", "Linter / Formatter": "rustfmt, Clippy", "Buyruq": "cargo fmt -- --check\ncargo clippy", "Debugger / Profiler": "gdb target/debug/myprog, rust-lldb"},
        {"Til": "PHP", "Linter / Formatter": "phpcs (PHP_CodeSniffer)", "Buyruq": "./vendor/bin/phpcs src/", "Debugger / Profiler": "Xdebug, php -a"}
    ]
    df_tools = pd.DataFrame(tools_data)
    st.dataframe(df_tools, use_container_width=True)

# ====================== YAKUNIY LOG VA SIDEBAR IZOH ======================
logger.info(f"Run start | obj={obj_name} | layers={num_layers} | T_max={T_source_max}")
logger.info(f"FOS computed = {pillar_strength/(sv_seam+1e-12):.4f} | rec_width = {rec_width:.2f} m")

st.sidebar.markdown("---")
st.sidebar.info("""
**Eslatma:**  
Ikkinchi koddagi FastAPI va Docker konfiguratsiyalari Streamlit ilovasiga mos emas. Ular alohida fayllar (`api.py`, `Dockerfile`, `docker-compose.yml`) sifatida saqlanishi mumkin.  
""")
st.sidebar.write(f"Tuzuvchi: Saitov Dilshodbek | Device: {device}")
