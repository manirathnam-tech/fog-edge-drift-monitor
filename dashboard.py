import streamlit as st
import requests
import pandas as pd

# Set the page configuration
st.set_page_config(page_title="Edge-AI Monitor", layout="wide")

st.title("🌐 Cloud Command Center: Infrastructure Monitor")
st.markdown("Real-time telemetry and AI remediation from distributed Fog Nodes.")
st.markdown("---")

# Function to pull data from our local Cloud Backend
def fetch_alerts():
    try:
        response = requests.get("http://localhost:9000/cloud/alerts")
        if response.status_code == 200:
            return response.json().get("active_alerts", [])
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Cannot connect to Cloud Backend. Is it running?")
        return []
    return []

# Fetch the data
alerts = fetch_alerts()

# Dashboard Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🚨 Active Configuration Drift Alerts")
    
    if not alerts:
        st.success("✅ Infrastructure is completely healthy. No drift detected.")
    else:
        st.error(f"{len(alerts)} Anomalies Detected in the Cloud Queue!")
        
        # Loop through the alerts (reversed so the newest is at the top)
        for idx, alert in enumerate(reversed(alerts)):
            with st.expander(f"Drift Detected: {alert.get('target', 'Unknown')} (Click to expand)", expanded=True):
                
                st.write("**Anomalies Flagged by Edge Sensor:**")
                for reason in alert.get("reasons", []):
                    st.code(reason, language="bash")
                
                st.write("**🤖 Edge-AI Autonomous Remediation Plan:**")
                st.info(alert.get("remediation_plan", "No plan provided."))

with col2:
    st.subheader("System Status")
    st.metric(label="Fog Nodes Online", value="1 Active")
    st.metric(label="Cloud Queue Status", value="Healthy")
    
    # A simple refresh button to pull new data
    if st.button("🔄 Refresh Telemetry Data"):
        st.rerun()
