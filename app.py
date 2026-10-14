from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")
db = client["ipa2026"]
routers = db["routers"]

@app.route("/")
def main():
    data = list(routers.find())
    return render_template("index.html", data=data)

@app.route("/add", methods=["POST"])
def add_router():
    ip = request.form.get("ip")
    username = request.form.get("username")
    password = request.form.get("password")

    if ip and username and password:
        routers.insert_one({
            "ip": ip,
            "username": username,
            "password": password
        })

    return redirect(url_for("main"))

@app.route("/delete/<id>", methods=["POST"])
def delete_router(id):
    if ObjectId.is_valid(id):
        routers.delete_one({"_id": ObjectId(id)})

    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
