from kubernetes import client, config
import json
import random
import time

def collect_telemetry():
    # 1. Load the local kubeconfig to give Python access to the kind cluster
    config.load_kube_config()
    
    # 2. Connect to the Apps API
    apps_v1 = client.AppsV1Api()
    
    # 3. Fetch the exact state of our Nginx castle
    deployment_name = "nginx-baseline"
    namespace = "default"
    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    
    # --- SENSORS ---
    # Sensor A: Replica Count
    desired_replicas = deployment.spec.replicas
    actual_replicas = deployment.status.ready_replicas or 0
    
    # Sensor B: Image Tag
    image_tag = deployment.spec.template.spec.containers[0].image
    
    # Sensor C: Simulated CPU Metrics
    cpu_load = round(random.uniform(10.0, 40.0), 2)
    
    # 4. Package the data into a JSON payload
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
    
    return json.dumps(payload, indent=2)

if __name__ == "__main__":
    print("Initializing Edge Sensors...")
    print(collect_telemetry())
