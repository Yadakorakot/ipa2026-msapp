import socket
import threading
import paramiko

HOST = "0.0.0.0"
PORT = 2222

USERNAME = "admin"
PASSWORD = "lab123"

PROMPT = "MockRouter#"

INTERFACES = (
    "Interface              IP-Address      OK? Method Status"
    "                Protocol\n"
    "GigabitEthernet0/0     192.168.198.138 YES manual up"
    "                    up\n"
    "GigabitEthernet0/1     unassigned      YES unset  administratively down down\n"
    "GigabitEthernet0/2     unassigned      YES unset  administratively down down\n"
)


class SSHServer(paramiko.ServerInterface):

    def __init__(self):
        self.shell_event = threading.Event()

    def check_auth_password(self, username, password):
        if username == USERNAME and password == PASSWORD:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, *args):
        return True

    def check_channel_shell_request(self, channel):
        self.shell_event.set()
        return True


def handle_client(client, host_key):
    transport = None

    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)

        server = SSHServer()
        transport.start_server(server=server)

        channel = transport.accept(15)
        if channel is None:
            return

        if not server.shell_event.wait(10):
            return

        channel.send(
            ("\r\nWelcome to Mock Cisco Router\r\n" + PROMPT + " ").encode()
        )

        buffer = ""

        while True:
            data = channel.recv(1024)

            if not data:
                break

            for char in data.decode("utf-8", errors="ignore"):

                if char in ("\r", "\n"):
                    command = buffer.strip()
                    buffer = ""

                    if not command:
                        channel.send(("\r\n" + PROMPT + " ").encode())
                        continue

                    if command in ("exit", "logout"):
                        channel.send(b"\r\nBye\r\n")
                        return

                    elif command == "enable":
                        response = "\r\n" + PROMPT + " "

                    elif command.startswith("terminal "):
                        response = "\r\n" + command + "\r\n" + PROMPT + " "

                    elif command == "show ip interface brief":
                        response = (
                            "\r\n"
                            + command
                            + "\r\n"
                            + INTERFACES
                            + "\r\n"
                            + PROMPT
                            + " "
                        )

                    elif command == "show version":
                        response = (
                            "\r\nCisco IOS Software (Mock Lab)\r\n"
                            + PROMPT
                            + " "
                        )

                    else:
                        response = (
                            "\r\n% Invalid input detected\r\n" + PROMPT + " "
                        )

                    channel.send(response.encode())

                elif char in ("\x08", "\x7f"):
                    buffer = buffer[:-1]

                elif char.isprintable():
                    buffer += char

    except Exception as e:
        print("Client error:", e, flush=True)

    finally:
        if transport:
            transport.close()
        else:
            client.close()


def main():
    host_key = paramiko.RSAKey.generate(2048)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(10)

    print(f"Mock Cisco SSH running on port {PORT}", flush=True)

    try:
        while True:
            client, address = sock.accept()

            print(f"Connection from {address}", flush=True)

            threading.Thread(
                target=handle_client, args=(client, host_key), daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\nStopping Mock Router")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
