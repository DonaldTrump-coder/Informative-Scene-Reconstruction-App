import socket
from urllib.parse import urlparse

def is_server_running(url, timeout=2):
    try:
        parsed = urlparse(url)

        host = parsed.hostname
        port = parsed.port

        if port is None:
            if parsed.scheme == "https" or parsed.scheme == "wss":
                port = 443
            else:
                port = 80

        with socket.create_connection((host, port), timeout=timeout):
            return True

    except Exception:
        return False