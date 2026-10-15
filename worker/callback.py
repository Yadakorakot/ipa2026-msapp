import os
import json
from router_client import get_interfaces


def callback(ch, method, props, body):
    job = json.loads(body.decode())

    router_ip = job["ip"]
    username = job["username"]
    password = job.get("password") or os.environ["ROUTER_SSH_PASSWORD"]

    print(f"Received job for router {router_ip}", flush=True)

    try:
        get_interfaces(router_ip, username, password)
    except Exception as e:
        print(f"Error: {e}", flush=True)
