import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# ================= SENSOR =================
def get_sensor_data():
    return {
        "temperature": np.random.uniform(400, 1000),
        "gas_pressure": np.random.uniform(1, 8),
        "stress": np.random.uniform(5, 15)
    }

# ================= DIGITAL TWIN =================
def compute_effective(sensor):
    temp = sensor["temperature"]
    gas = sensor["gas_pressure"]
    stress = sensor["stress"]

    thermo = stress + 0.01 * temp
    effective = thermo - gas

    return effective

# ================= ANOMALY =================
def detect_anomaly(history, value):
    if len(history) < 10:
        return False

    mean = np.mean(history)
    std = np.std(history)

    if std == 0:
        return False

    return abs(value - mean) > 2 * std

# ================= STREAMLIT =================
def run_ai_monitor():
    st.set_page_config(layout="wide")
    st.title("🧠 UCG AI Predictive Monitoring")

    placeholder = st.empty()

    history = []
    anomalies = []

    for _ in range(200):

        sensor = get_sensor_data()
        effective = compute_effective(sensor)

        is_anomaly = detect_anomaly(history, effective)

        history.append(effective)
        anomalies.append(effective if is_anomaly else None)

        with placeholder.container():

            col1, col2, col3 = st.columns(3)

            col1.metric("🌡 Temp", f"{sensor['temperature']:.1f} °C")
            col2.metric("💨 Gas", f"{sensor['gas_pressure']:.2f} MPa")
            col3.metric("🧱 Stress", f"{effective:.2f} MPa")

            # GRAPH
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                y=history,
                mode='lines',
                name='Stress'
            ))

            fig.add_trace(go.Scatter(
                y=anomalies,
                mode='markers',
                name='Anomaly',
                marker=dict(color='red', size=8)
            ))

            st.plotly_chart(fig, use_container_width=True)

            # ALERT SYSTEM
            if is_anomaly:
                st.error("🚨 ANOMALY DETECTED! Collapse ehtimoli!")
            elif effective > 10:
                st.warning("⚠️ Xavf ortmoqda")
            else:
                st.success("✅ Normal holat")

        time.sleep(1)

if __name__ == "__main__":
    run_ai_monitor()
