import threading
import websocket
import queue
import json

class WSThread:
    def __init__(self, url):
        self.url = url
        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()
        self.running = True

        self.ws = websocket.create_connection(self.url, ping_interval=20)

        self.send_thread = threading.Thread(target=self.send_loop, daemon=True)
        self.recv_thread = threading.Thread(target=self.recv_loop, daemon=True)
        self.send_thread.start()
        self.recv_thread.start()

    def send_loop(self):
        while self.running:
            try:
                payload = self.send_queue.get(timeout=1)
                self.ws.send(json.dumps(payload))
            except queue.Empty:
                continue
            except Exception as e:
                print("WebSocket send error:", e)
                self.running = False
                break

    def recv_loop(self):
        while self.running:
            try:
                data = self.ws.recv()
                if isinstance(data, bytes):
                    while self.recv_queue.qsize() >= 5:
                        try:
                            self.recv_queue.get_nowait()
                        except queue.Empty:
                            break
                    self.recv_queue.put(data)
                elif data == "":
                    continue
                else:
                    print("WebSocket text message:", data)
            except websocket.WebSocketConnectionClosedException:
                print("WebSocket connection closed")
                self.running = False
                break
            except Exception as e:
                print("WebSocket recv error:", e)
                self.running = False
                break

    def send_payload(self, payload):
        while not self.send_queue.empty():
            try:
                self.send_queue.get_nowait()
            except queue.Empty:
                break
        self.send_queue.put(payload)

    def get_result(self):
        try:
            return self.recv_queue.get()
        except queue.Empty:
            return None

    def close(self):
        self.running = False
        self.ws.close()