import json
import os
import time

QUEUE_FILE = "local_message_queue.json"

def push_to_queue(payload):
    """Adds a new message payload to our local persistent queue."""
    messages = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                messages = []
                
    payload["timestamp"] = time.time()
    payload["status"] = "pending"
    messages.append(payload)
    
    with open(QUEUE_FILE, "w") as f:
        json.dump(messages, f, indent=4)
    print(f"[QUEUE] Successfully enqueued task for target: {payload.get('target')}")

def pop_from_queue():
    """Retrieves and removes the oldest pending message from the queue."""
    if not os.path.exists(QUEUE_FILE):
        return None
        
    with open(QUEUE_FILE, "r") as f:
        try:
            messages = json.load(f)
        except json.JSONDecodeError:
            return None
            
    for msg in messages:
        if msg["status"] == "pending":
            msg["status"] = "processing"
            # Save state
            with open(QUEUE_FILE, "w") as f:
                json.dump(messages, f, indent=4)
            return msg
            
    return None

def clear_resolved_messages():
    """Removes processed messages from the queue store."""
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                return
        # Keep only pending or stuck messages for safety, or clear out completed
        remain = [m for m in messages if m["status"] == "pending"]
        with open(QUEUE_FILE, "w") as f:
            json.dump(remain, f, indent=4)
