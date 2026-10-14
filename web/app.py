import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "ipa2026")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

routers = db["routers"]
interface_status = db["interface_status"]

@app.route("/")
def index():
    router_list = list(routers.find().sort("ip", 1))
    return render_template("index.html", routers=router_list)

@app.route("/add", methods=["POST"])
def add_router():
    ip = request.form.get("ip", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if ip and username and password:
        routers.update_one(
            {"ip": ip},
            {"$set": {
                "ip": ip,
                "username": username,
                "password": password
            }},
            upsert=True
        )

    return redirect(url_for("index"))

@app.route("/delete/<path:ip>", methods=["POST"])
def delete_router(ip):
    routers.delete_one({"ip": ip})
    return redirect(url_for("index"))

@app.route("/router/<path:ip>")
def router_detail(ip):
    router = routers.find_one({"ip": ip})

    if router is None:
        return "Router not found", 404

    # เอาข้อมูลที่ตรวจสอบล่าสุดเพียง 3 ครั้ง
    records = list(
        interface_status.find({"router_ip": ip})
        .sort("timestamp", -1)
        .limit(3)
    )

    rows = []

    for record in records:
        timestamp = record.get("timestamp")

        if timestamp:
            timestamp_text = timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ) + " UTC"
        else:
            timestamp_text = "-"

        for interface in record.get("interfaces", []):
            rows.append({
                "timestamp": timestamp_text,
                "interface": interface.get("interface", "-"),
                "ip_address": interface.get("ip_address", "-"),
                "status": interface.get("status", "-"),
                "proto": interface.get("proto", "-")
            })

    return render_template(
        "router_detail.html",
        router=router,
        rows=rows
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
