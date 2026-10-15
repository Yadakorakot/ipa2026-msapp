import os
import json
import time
from datetime import datetime, timezone

import pika
from pymongo import MongoClient
from netmiko import ConnectHandler

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "ipa2026")


def get_router(ip):
    with MongoClient(MONGO_URI) as client:
        return client[DB_NAME]["routers"].find_one({"ip": ip})


def check_router(router):
    device = {
        "device_type": "cisco_ios",
        "host": router["ip"],
        "port": 2222,
        "username": router["username"],
        "password": router["password"],
        "conn_timeout": 10,
        "fast_cli": False,
    }

    with ConnectHandler(**device) as ssh:
        interfaces = ssh.send_command(
            "show ip interface brief", use_textfsm=True
        )

    return interfaces


def save_to_mongo(ip, interfaces):
    with MongoClient(MONGO_URI) as client:
        client[DB_NAME]["interface_status"].insert_one(
            {
                "router_ip": ip,
                "timestamp": datetime.now(timezone.utc),
                "interfaces": interfaces,
            }
        )

    print(f"Stored interface status for {ip}", flush=True)


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body.decode("utf-8"))
        ip = message["ip"]

        print(f"Received job for router {ip}", flush=True)

        router = get_router(ip)

        if router is None:
            print(f"Router {ip} not found in MongoDB", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        interfaces = check_router(router)

        if not isinstance(interfaces, list):
            raise ValueError("TextFSM parsing failed: expected a list")

        print(interfaces, flush=True)
        save_to_mongo(ip, interfaces)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Worker error: {e}", flush=True)

        # ป้องกันข้อความที่ผิดพลาดวนกลับมาไม่สิ้นสุด
        # สำหรับ Lab นี้ ข้อความที่ล้มเหลวจะไม่ถูกส่งกลับ Queue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)

    while True:
        try:
            print("Connecting to RabbitMQ...", flush=True)

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, credentials=credentials, heartbeat=120
                )
            )

            channel = connection.channel()
            channel.queue_declare(queue="router_jobs")
            channel.basic_qos(prefetch_count=1)

            print("Waiting for router jobs...", flush=True)

            channel.basic_consume(
                queue="router_jobs", on_message_callback=process_message
            )

            channel.start_consuming()

        except Exception as e:
            print(f"RabbitMQ connection error: {e}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
