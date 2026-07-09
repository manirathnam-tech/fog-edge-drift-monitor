from fastapi import FastAPI, BackgroundTasks, Request
import uvicorn

app = FastAPI(title="Scalable Cloud Backend")

# Simulating a cloud database to store alerts for our upcoming Dashboard
db_alerts = []

def process_alert_worker(payload):
    """Simulates a Serverless Worker pulling from a Queue"""
    print(f"\n[CLOUD WORKER] Picking up payload from queue for target: {payload.get('target')}")
    
    # Store the alert so the dashboard can read it later
    db_alerts.append(payload)
    
    print(f"[CLOUD WORKER] Alert processed and saved to database.")
    print(f"  -> AI Remediation Plan Logged: {payload.get('remediation_plan')[:50]}...")

@app.post("/cloud/ingest")
async def ingest_telemetry(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    
    # Immediately add the heavy processing to a background task (Queue simulation)
    background_tasks.add_task(process_alert_worker, payload)
    
    # Instantly return a 202 Accepted so the Fog Node isn't kept waiting
    return {"status": "queued", "message": "Payload safely ingested into cloud queue."}

@app.get("/cloud/alerts")
def get_alerts():
    """Endpoint for our Dashboard to pull active alerts"""
    return {"active_alerts": db_alerts}

if __name__ == "__main__":
    print("Starting Cloud Backend on port 9000...")
    uvicorn.run(app, host="0.0.0.0", port=9000)
