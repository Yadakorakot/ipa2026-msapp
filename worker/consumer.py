import os
import time
import pika
from callback import callback

user = os.getenv("RABBITMQ_DEFAULT_USER", "admin")
pwd = os.getenv("RABBITMQ_DEFAULT_PASS", "rabbitmq")


def consume(host):
    for attempt in range(10):
        try:
            print(f"Connecting to RabbitMQ (try {attempt})...", flush=True)
            creds = pika.PlainCredentials(user, pwd)
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(host, credentials=creds)
            )
            break
        except Exception as e:
            print(f"Failed: {e}", flush=True)
            time.sleep(5)
    else:
        print("Could not connect after 10 attempts")
        return

    ch = conn.channel()
    ch.queue_declare(queue="router_jobs")
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(
        queue="router_jobs", on_message_callback=callback, auto_ack=True
    )
    print("Waiting for messages...", flush=True)
    ch.start_consuming()


if __name__ == "__main__":
    consume("localhost")
