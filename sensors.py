from kubernetes import client, config
import requests
import json
import random
import time

def collect_telemetry():
    # 1. Connect to the local cluster
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    
    # 2. Fetch the state of the Nginx deployment
    deployment_name = "nginx-baseline"
    namespace = "default"
    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    
    # 3. Extract metrics
    desired_replicas = deployment.spec.replicas
    actual_replicas = deployment.status.ready_replicas or 0
    image_tag = deployment.spec.template.spec.containers[0].image
    cpu_load = round(random.uniform(10.0, 40.0), 2)
    
    # 4. Package payload
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target": deployment_name,
        "metrics": {
            "desired_replicas": desired_replicas,
            "actual_replicas": actual_replicas,
            "current_image": image_tag,
            "cpu_utilization_percent": cpu_load
        }
    }
    return payload

def send_to_fog_node(payload):
    # This is the local address where your FastAPI server is listening
    url = "http://localhost:8000/api/v1/telemetry"
    
    print(f"Transmitting telemetry to Fog Node at {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"[SUCCESS] Fog Node Processed Data. Status: {response.json().get('status')}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to Fog Node. Is it running?")

if __name__ == "__main__":
    print("Initializing Edge Sensors...")
    data = collect_telemetry()
    send_to_fog_node(data)
