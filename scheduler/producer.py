import os
import pika

def produce(host, body):
    username = os.environ.get("RABBITMQ_USER", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")

    credentials = pika.PlainCredentials(username, password)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            credentials=credentials
        )
    )

    try:
        channel = connection.channel()

        channel.exchange_declare(
            exchange="jobs",
            exchange_type="direct"
        )

        channel.queue_declare(queue="router_jobs")

        channel.queue_bind(
            queue="router_jobs",
            exchange="jobs",
            routing_key="check_interfaces"
        )

        channel.basic_publish(
            exchange="jobs",
            routing_key="check_interfaces",
            body=body
        )

    finally:
        connection.close()

if __name__ == "__main__":
    produce(
        os.environ.get("RABBITMQ_HOST", "localhost"),
        "192.168.1.44"
    )
