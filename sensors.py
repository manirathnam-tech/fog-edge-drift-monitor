import os
import time
import requests
import urllib3
from kubernetes import client, config

# suppress the k8s self-signed cert warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def monitor_cluster():
    print("[SENSOR] Booting up edge telemetry sensor...")
    
    # connect to aws cluster
    try:
        config.load_kube_config(config_file=os.path.expanduser("~/.kube/aws-cloud-config"))
        k8s_api = client.AppsV1Api()
        print("[SENSOR] Connected to AWS Control Plane. Starting continuous monitoring...")
    except Exception as e:
        print(f"[SENSOR FATAL] Could not connect to AWS: {str(e)}")
        return
    
    # continuous polling loop
    while True:
        try:
            # read current state from aws
            deployment = k8s_api.read_namespaced_deployment(name="nginx-baseline", namespace="default")
            
            # the absolute gitops truth
            expected = 3 
            
            # CHANGE: reading raw replicas instead of ready_replicas to bypass probe lag
            actual = deployment.status.replicas or 0
            
            # construct the exact payload
            payload = {
                "target": "nginx-baseline",
                "expected_replicas": expected,
                "actual_replicas": actual
            }
            
            # fire the telemetry to the local fog node api gateway
            try:
                requests.post("http://127.0.0.1:8000/api/v1/telemetry", json=payload, timeout=2)
                print(f"[SENSOR] Telemetry dispatched -> Expected: {expected} | Actual: {actual}")
            except Exception:
                print("[SENSOR WARNING] Fog Node API is unreachable. Is it running?")
                
        except Exception as e:
            print(f"[SENSOR ERROR] Failed to read AWS cluster state: {str(e)}")
            
        # wait 5 seconds before checking again
        time.sleep(5)

if __name__ == "__main__":
    monitor_cluster()
