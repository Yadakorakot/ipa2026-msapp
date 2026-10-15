import os
import time
from bson import json_util

from producer import produce
from database import get_router_info


def scheduler():
    INTERVAL = 10.0
    next_run = time.monotonic()
    count = 0

    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")

    while True:
        now = time.time()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        ms = int((now % 1) * 1000)

        print(f"[{now_str}.{ms:03d}] run #{count}", flush=True)

        try:
            for data in get_router_info():
                router_data = {"ip": data["ip"], "username": data["username"]}

                body_bytes = json_util.dumps(router_data).encode("utf-8")

                produce(rabbitmq_host, body_bytes)

                print(f"Sent router: {data['ip']}", flush=True)

        except Exception as e:
            print(f"Error: {e}", flush=True)

        count += 1
        next_run += INTERVAL
        time.sleep(max(0.0, next_run - time.monotonic()))


if __name__ == "__main__":
    scheduler()
