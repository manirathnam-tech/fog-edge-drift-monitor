import os
import json
import boto3
from dotenv import load_dotenv

# load environment variables
load_dotenv()
SQS_QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL")

# initialize sqs client
sqs = boto3.client('sqs', region_name='us-east-1')

def enqueue_remediation_task(target_deployment, issue_title, issue_body):
    payload = {
        "target": target_deployment,
        "title": issue_title,
        "body": issue_body
    }
    
    try:
        response = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(payload)
        )
        print(f"[SQS] Successfully enqueued task for target: {target_deployment}. Message ID: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"[SQS ERROR] Failed to enqueue task: {str(e)}")
        return False
