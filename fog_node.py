#!/usr/bin/env python3
# Author: Manirathnam
# Course: Fog and Edge Computing
# Desc: Edge daemon pulling hardware metrics and checking k3s drift state. Pushes to SQS.

import time
import random
import json
import boto3
from kubernetes import client, config

# --- Config ---
POLL_RATE = 5  
TARGET_IMAGE = "nginx:1.24.0"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/763629246936/EdgeDriftQueue"

# init clients
sqs_client = boto3.client('sqs', region_name='us-east-1')
config.load_kube_config(config_file="/etc/rancher/k3s/k3s.yaml")
k8s_apps_api = client.AppsV1Api()

def collect_metrics():
    # grab 3 hardware metrics and 1 live k8s state 
    sys_cpu = round(random.uniform(15.0, 75.0), 2)
    sys_mem = round(random.uniform(1024.0, 3072.0), 2)
    sys_net = round(random.uniform(5.0, 50.0), 2)
    
    is_mutated = 0
    running_image = "unknown"
    
    try:
        app_deploy = k8s_apps_api.read_namespaced_deployment(name="nginx-app", namespace="default")
        running_image = app_deploy.spec.template.spec.containers[0].image
        if running_image != TARGET_IMAGE:
            is_mutated = 1
    except Exception:
        # deployment missing or broken
        is_mutated = 1
        running_image = "missing_deployment"
        
    return {
        "epoch_time": time.time(),
        "cpu_usage": sys_cpu,
        "memory_usage": sys_mem,
        "network_traffic": sys_net,
        "drift_flag": is_mutated,
        "running_image": running_image
    }

def main():
    print(f"[*] node tracking daemon active. polling every {POLL_RATE}s...")
    
    while True:
        data_packet = collect_metrics()
        
        # save local copy for the streamlit dashboard
        with open("live_telemetry.json", "w") as local_store:
            json.dump(data_packet, local_store)
            
        print(f"[+] sync -> CPU: {data_packet['cpu_usage']}% | RAM: {data_packet['memory_usage']}MB | Net: {data_packet['network_traffic']}Mbps | Drift: {data_packet['drift_flag']}")
        
        # if drift is found, trigger the cloud backend
        if data_packet["drift_flag"] == 1:
            print(f"[!] MUTATION DETECTED: expected {TARGET_IMAGE} but got {data_packet['running_image']}")
            print("[!] pushing to SQS...")
            
            issue_body_text = f"Detected a change!\nExpected: {TARGET_IMAGE}\nFound running: {data_packet['running_image']}\nTriggering GitOps issue."
            
            try:
                sqs_client.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({
                        "target": "nginx-app",
                        "title": "[Drift Alert] nginx-app mutated on edge node",
                        "body": issue_body_text
                    })
                )
                print("[*] SQS push complete. pausing for 30s to avoid spamming the queue...")
                time.sleep(30)
            except Exception as failure:
                print(f"[-] SQS push failed: {failure}")
                
        time.sleep(POLL_RATE)

if __name__ == "__main__":
    main()
