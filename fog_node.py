import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from queue_manager import enqueue_remediation_task

# initialize api gateway
app = FastAPI(title="Edge-AI Fog Node API Gateway")

# define expected telemetry payload structure
class TelemetryPayload(BaseModel):
    target: str
    expected_replicas: int
    actual_replicas: int


def analyze_drift_with_llm(target, expected, actual):
    print(f"\n[AI-ANALYSIS] Waking up local Edge-AI (Phi-3) to analyze {target} drift...")

    # construct prompt for local inference
    prompt = (
        f"Analyze configuration drift for {target}. Expected {expected} replicas, "
        f"but found {actual}. Provide a risk explanation and the kubectl command "
        f"to scale it back to {expected}."
    )

    # local llm inference execution goes here
    remediation_plan = f"""Risk Explanation: The configuration drift in this case indicates that only {actual} replica (pod) is currently running instead of the expected {expected}, which could lead to potential issues with high availability and load balancing within the application deployment.

Kubectl Command: To restore the state to its intended baseline, scale up the deployment back to {expected} pods using `kubectl`. The following command will forcefully create additional replicas:

```bash
kubectl scale deploy/{target} --replicas={expected} -n default
```
"""

    print("\n[AI-REMEDIATION PLAN GENERATED]")
    print(remediation_plan)
    return remediation_plan


@app.post("/api/v1/telemetry")
async def process_telemetry(payload: TelemetryPayload):
    print(f"\n[FOG NODE] Received incoming telemetry stream for target: {payload.target}...")

    # evaluate drift against declarative baseline
    if payload.expected_replicas != payload.actual_replicas:
        print(f"[ALERT] Active Configuration Drift Detected for {payload.target}!")
        print(f"  -> Replica mismatch: Expected {payload.expected_replicas}, Got {payload.actual_replicas}")

        # trigger edge ai analysis
        remediation_plan = analyze_drift_with_llm(
            payload.target,
            payload.expected_replicas,
            payload.actual_replicas
        )

        print("\n[FOG NODE] Offloading enriched payload to cloud message queue...")

        # package and send to aws sqs
        issue_title = f"[Alert] Configuration Drift: {payload.target}"
        success = enqueue_remediation_task(
            target_deployment=payload.target,
            issue_title=issue_title,
            issue_body=remediation_plan
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to enqueue remediation task to SQS")

        return {"status": "drift_detected_and_enqueued"}

    return {"status": "healthy"}


if __name__ == "__main__":
    print("Initializing Edge-AI Fog Node API Gateway on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
