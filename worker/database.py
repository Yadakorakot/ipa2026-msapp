from pymongo import MongoClient
from datetime import datetime, timezone
import os


def save_interface_status(router_ip, interfaces):
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "ipa2026")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["interface_status"]

    data = {
        "router_ip": router_ip,
        "timestamp": datetime.now(timezone.utc),
        "interfaces": interfaces,
    }

    collection.insert_one(data)
    client.close()

    print(f"Stored interface status for {router_ip}")
