import os
from pymongo import MongoClient

def get_router_info():
    mongo_uri = os.environ.get("MONGO_URI")
    db_name = os.environ.get("DB_NAME")

    client = MongoClient(mongo_uri)
    try:
        db = client[db_name]
        routers = db["routers"]
        return list(routers.find())
    finally:
        client.close()

if __name__ == "__main__":
    for router in get_router_info():
        print({
            "ip": router.get("ip"),
            "username": router.get("username")
        })
