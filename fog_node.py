from fastapi import FastAPI, Request
import uvicorn
import requests
import json

app = FastAPI(title="Edge-AI Fog Node")

# Our GitOps "Source of Truth"
GOLDEN_RULES = {
    "nginx-baseline": {
        "expected_replicas": 3,
        "expected_image": "nginx:latest"
    }
}

def analyze_drift_with_llm(target, reasons):
    print(f"\n[AI-ANALYSIS] Waking up local Edge-AI (Phi-3) to analyze {target} drift...")
    
    # We construct a strict prompt for the DevOps AI
    prompt = f"""
    You are an autonomous Kubernetes DevOps AI.
    A configuration drift was detected in the deployment '{target}'.
    The following anomalies were found: {', '.join(reasons)}

    Provide a brief, 2-sentence explanation of why this is a risk, and state the exact `kubectl` command needed to fix it.
    """
    
    try:
        # Calling the local Ollama API
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "phi3",
            "prompt": prompt,
            "stream": False
        })
        
        if response.status_code == 200:
            ai_response = response.json().get("response", "")
            print(f"\n[AI-REMEDIATION PLAN]\n{ai_response}\n")
            return ai_response
        else:
            print(f"[ERROR] LLM returned status {response.status_code}")
            return "AI analysis failed."
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to local Ollama instance. Is it running?")
        return "AI offline."

@app.post("/api/v1/telemetry")
async def receive_telemetry(request: Request):
    payload = await request.json()
    target = payload.get("target")
    metrics = payload.get("metrics")
    
    print(f"\n[FOG NODE] Received telemetry for {target}...")
    
    rule = GOLDEN_RULES.get(target)
    if rule:
        drift_detected = False
        reasons = []
        
        if metrics.get("actual_replicas") != rule["expected_replicas"]:
            drift_detected = True
            reasons.append(f"Replica mismatch: Expected {rule['expected_replicas']}, Got {metrics.get('actual_replicas')}")
            
        if metrics.get("current_image") != rule["expected_image"]:
            drift_detected = True
            reasons.append(f"Image mismatch: Expected {rule['expected_image']}, Got {metrics.get('current_image')}")
            
        if drift_detected:
            print("[ALERT] Configuration Drift Detected!")
            for reason in reasons:
                print(f"  -> {reason}")
            
            # Waking up the LLM to process the anomaly
            ai_remediation = analyze_drift_with_llm(target, reasons)
            
            # --- NEW: Forward enriched payload to the Cloud Backend ---
            cloud_payload = {
                "target": target,
                "reasons": reasons,
                "remediation_plan": ai_remediation
            }
            try:
                print(f"\n[FOG NODE] Forwarding enriched payload to Cloud Backend...")
                requests.post("http://localhost:9000/cloud/ingest", json=cloud_payload)
            except Exception as e:
                print(f"[ERROR] Could not reach Cloud Backend: {e}")
            # ----------------------------------------------------------

            return {
                "status": "anomaly_detected", 
                "details": reasons,
                "remediation_plan": ai_remediation
            }
            
    print("[FOG NODE] Infrastructure is healthy. No drift detected.")
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting Fog Node API on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
