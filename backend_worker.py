import os
import time
import json
import boto3
import requests
from dotenv import load_dotenv

# load environment configurations
load_dotenv()
SQS_QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# initialize sqs client
sqs = boto3.client('sqs', region_name='us-east-1')

def create_github_issue(title, body):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"title": title, "body": body, "labels": ["drift-alert"]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(f"[SUCCESS] Issue created: {response.json()['html_url']}")
            return True
        print(f"[ERROR] Failed to create issue. Status: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] GitHub API request failed: {str(e)}")
        return False

def poll_sqs():
    print("Starting SQS worker loop. Long-polling AWS SQS queue...")
    while True:
        try:
            # poll for messages with a 10-second wait time to reduce api calls
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            messages = response.get('Messages', [])
            if not messages:
                continue

            for message in messages:
                receipt_handle = message['ReceiptHandle']
                body = json.loads(message['Body'])
                
                print(f"\n[INFO] Processing SQS task for target: {body['target']}")
                
                success = create_github_issue(body['title'], body['body'])
                
                if success:
                    # delete message from queue after successful processing
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=receipt_handle
                    )
                    print("[INFO] Task complete. Message securely purged from SQS queue.")
                    
        except Exception as e:
            print(f"[ERROR] SQS polling failed: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    poll_sqs()
