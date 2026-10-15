from netmiko import ConnectHandler
import ntc_templates
import os
import json


def get_interfaces(ip, username, password):
    os.environ["NET_TEXTFSM"] = os.path.join(
        os.path.dirname(ntc_templates.__file__), "templates"
    )

    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "port": 2222,
        "username": username,
        "password": password,
        "fast_cli": False,
    }

    with ConnectHandler(**device) as conn:
        result = conn.send_command("show ip interface brief", use_textfsm=True)

    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == "__main__":
    ip = os.getenv("ROUTER_IP", "192.168.198.138")
    username = os.getenv("ROUTER_SSH_USER", "admin")
    password = os.environ["ROUTER_SSH_PASSWORD"]

    get_interfaces(ip, username, password)
