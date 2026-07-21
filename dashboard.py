#!/usr/bin/env python3
# Author: Manirathnam
# Course: Fog and Edge Computing
# Desc: Streamlit UI to show edge telemetry and active gitops issues

import streamlit as st
import urllib.request
import json
import pandas as pd
import time

GH_USER = "manirathnam-tech"
GH_REPO = "fog-edge-drift-monitor"

st.set_page_config(page_title="Edge Telemetry Panel", layout="wide")
st.title("🛡️ Edge Node Telemetry & Cloud Backend Dashboard")
st.write("Aggregated physical metrics from edge node sensors alongside GitOps processing records.")

# --- edge sensors ---
st.subheader("📡 Live Fog Node Sensors")

try:
    with open("live_telemetry.json", "r") as local_source:
        metrics = json.load(local_source)
except FileNotFoundError:
    metrics = {"cpu_usage": 0.0, "memory_usage": 0.0, "network_traffic": 0.0, "drift_flag": 0}

block1, block2, block3, block4 = st.columns(4)

block1.metric("CPU Utilization", f"{metrics.get('cpu_usage')} %")
block2.metric("Memory Footprint", f"{metrics.get('memory_usage')} MB")
block3.metric("Network Interface Throughput", f"{metrics.get('network_traffic')} Mbps")

drift_state = metrics.get('drift_flag')
block4.metric(
    "Cluster State Drift", 
    "MUTATED" if drift_state == 1 else "CLEAN", 
    delta="- CRITICAL ALARM" if drift_state == 1 else "NORMAL STATUS", 
    delta_color="inverse"
)

st.markdown("---")

# --- gitops alerts ---
@st.cache_data(ttl=5)
def fetch_github_records():
    api_endpoint = f"https://api.github.com/repos/{GH_USER}/{GH_REPO}/issues?labels=drift-alert&state=open"
    try:
        conn = urllib.request.Request(api_endpoint)
        conn.add_header("Accept", "application/vnd.github.v3+json")
        with urllib.request.urlopen(conn) as network_res:
            return json.loads(network_res.read().decode())
    except Exception:
        return []

st.subheader("☁️ Cloud Backend: Active GitOps Remediation Alerts")
open_incidents = fetch_github_records()

if not open_incidents:
    st.success("✅ System state consistent. Cloud tracking queue is currently empty.")
else:
    st.warning(f"⚠️ Notice: FaaS pipeline has isolated {len(open_incidents)} unresolved cluster changes.")
    
    parsed_logs = []
    for item in open_incidents:
        parsed_logs.append({
            "Incident ID": f"#{item['number']}",
            "Logged Warning": item['title'],
            "Timestamp": item['created_at'].replace("T", " ").replace("Z", ""),
            "Tracking Link": item['html_url']
        })
        
    log_frame = pd.DataFrame(parsed_logs)
    st.dataframe(log_frame, use_container_width=True, hide_index=True)

time.sleep(3)
st.rerun()
