import os
import requests
import streamlit as st
from kubernetes import client, config
from dotenv import load_dotenv

# load env vars
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

# page config
st.set_page_config(page_title="Edge-AI Drift Monitor", layout="wide")

st.title("Edge-AI Infrastructure Configuration Drift Monitor")
st.subheader("Fog and Edge Computing Project | Live Telemetry & Remediation")
st.markdown("---")

# project overview
with st.expander("Executive Summary & Architecture", expanded=False):
    st.markdown("""
    **Executive Summary**
    This project demonstrates an end-to-end cloud-native telemetry pipeline designed to automatically detect configuration drift within containerized environments (Kubernetes) and leverage a localized Large Language Model (LLM) to evaluate anomalies and generate precise, deterministic remediation scripts.

    **Core System Objectives**
    * **Continuous Monitoring:** Custom Python-based edge sensors monitor the operational state of container infrastructure against a declarative GitOps source of truth.
    * **Edge-AI Decision Engine:** A FastAPI gateway intercepts telemetry anomalies, formats structural context, and prompts an edge LLM (Phi-3) to analyze infrastructure drift.
    * **Reliability Evaluation:** The system acts as a live evaluation framework for assessing whether a generative AI model can output flawless, syntax-accurate CLI commands (kubectl) under tight resource constraints.
    * **Cloud Visualization:** Enriched payloads containing metrics, drift reasoning, and AI-generated remediation playbooks are shipped to a scalable backend queue and visualized live on an enterprise monitoring dashboard.
    """)
st.markdown("---")

# k8s client setup
@st.cache_resource(ttl=10)
def get_k8s_client():
    try:
        config.load_kube_config(config_file=os.path.expanduser("~/.kube/aws-cloud-config"))
        return client.AppsV1Api()
    except Exception:
        return None

# retrieve recent issues
@st.cache_data(ttl=10)
def get_recent_interventions():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return []
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=all&labels=drift-alert"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()[:5]
    except Exception:
        pass
    return []

col1, col2 = st.columns([1, 1])

# cluster status section
with col1:
    st.header("AWS Cluster Status")
    k8s_api = get_k8s_client()
    
    if k8s_api:
        try:
            deployment = k8s_api.read_namespaced_deployment(name="nginx-baseline", namespace="default")
            
            # evaluate against GitOps declarative baseline, not the tampered state
            expected = 3 
            actual = deployment.status.ready_replicas or 0
            
            if expected == actual:
                st.success("Infrastructure Healthy: No Configuration Drift")
                st.metric(label="Nginx Replicas", value=actual, delta="0 Drift")
            else:
                st.error("ACTIVE DRIFT DETECTED")
                st.metric(label="Nginx Replicas", value=actual, delta=f"{actual - expected} Pods (Drift)", delta_color="inverse")
                
            st.info(f"Target Image: {deployment.spec.template.spec.containers[0].image}")
            
        except Exception:
            st.warning("Awaiting deployment target 'nginx-baseline' initialization.")
    else:
        st.error("Connection failed. Verify kubeconfig.")

# remediation log section
with col2:
    st.header("Remediation Log")
    issues = get_recent_interventions()
    
    if issues:
        for issue in issues:
            status_color = "[CLOSED]" if issue['state'] == "closed" else "[OPEN]"
            with st.expander(f"{status_color} {issue['title']} (Issue #{issue['number']})", expanded=(issue['state'] == "open")):
                st.markdown(issue['body'])
                st.markdown(f"[View Execution in GitHub]({issue['html_url']})")
    else:
        st.info("No recent interventions logged.")

st.markdown("---")
if st.button("Poll Latest Telemetry"):
    st.rerun()
