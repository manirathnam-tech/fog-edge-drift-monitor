import time
import requests
import os
import json
from queue_manager import pop_from_queue, QUEUE_FILE
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

def create_github_issue(target, reasons, remediation_plan):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("[WARN] GitHub credentials missing. Skipping issue creation.")
        return False
        
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    title = f"[Alert] Configuration Drift: {target}"
    body = (
        f"**Target Deployment:** `{target}`\n\n"
        f"**Issues Detected:**\n" + "".join([f"- {r}\n" for r in reasons]) + "\n"
        f"**Suggested Remediation:**\n"
        f"```bash\n{remediation_plan}\n```\n"
    )
    
    payload = {"title": title, "body": body, "labels": ["bug", "drift-alert"]}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"[SUCCESS] Issue created: {response.json().get('html_url')}")
            return True
        else:
            print(f"[ERROR] API request failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Network exception: {e}")
        return False

def start_worker_loop():
    print("Starting worker loop. Polling queue...")
    while True:
        job = pop_from_queue()
        if job:
            print(f"\n[INFO] Processing task for target: {job['target']}")
            
            create_github_issue(job['target'], job['reasons'], job['remediation_plan'])
            
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r") as f:
                    messages = json.load(f)
                
                messages = [m for m in messages if not (m['target'] == job['target'] and m['timestamp'] == job['timestamp'])]
                
                with open(QUEUE_FILE, "w") as f:
                    json.dump(messages, f, indent=4)
                    
            print(f"[INFO] Task complete. Returning to poll state.")
        
        time.sleep(2)

if __name__ == "__main__":
    try:
        start_worker_loop()
    except KeyboardInterrupt:
        print("\nWorker shutting down.")
