# Author: Manirathnam
# Course: Fog and Edge Computing
# Desc: AWS Lambda worker. Reads from SQS and creates GitHub issues via API.

import json
import urllib.request
import os

def lambda_handler(event, context):
    # pull token securely from lambda env vars
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_owner = "manirathnam-tech"
    repo_name = "fog-edge-drift-monitor"
    
    for record in event['Records']:
        try:
            # parse the payload from fog_node.py
            message_body = json.loads(record['body'])
            
            target = message_body.get("target", "Unknown Target")
            issue_title = message_body.get("title", f"[Alert] Configuration Drift: {target}")
            issue_body = message_body.get("body", "No plan provided.")
            
            # hit github API to open an issue
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = json.dumps({
                "title": issue_title, 
                "body": issue_body, 
                "labels": ["drift-alert"]
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                print(f"Success! GitOps issue created for {target}. HTTP Status: {response.status}")
                
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            raise e
            
    return {
        'statusCode': 200,
        'body': json.dumps('SQS messages successfully processed and pushed to GitHub.')
    }
