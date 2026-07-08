from kubernetes import client, config
import random

def cause_chaos():
    print("Initiating Configuration Drift...")
    # Connect to the local cluster
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    
    deployment_name = "nginx-baseline"
    namespace = "default"
    
    # Fetch current deployment rules
    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    
    # Randomly choose an anomaly type to inject
    anomaly_type = random.choice(["scale_down", "unauthorized_image"])
    
    if anomaly_type == "scale_down":
        print("Anomaly Selected: Scaling replicas down to 1 (Under-provisioned risk!)")
        deployment.spec.replicas = 1
    elif anomaly_type == "unauthorized_image":
        print("Anomaly Selected: Injecting unauthorized container image (nginx:1.14.2 instead of latest!)")
        deployment.spec.template.spec.containers[0].image = "nginx:1.14.2"
        
    # Apply the malicious change to the cluster
    apps_v1.patch_namespaced_deployment(
        name=deployment_name, 
        namespace=namespace, 
        body=deployment
    )
    print("Drift successfully injected! The perfect castle has been altered.")

if __name__ == "__main__":
    cause_chaos()
