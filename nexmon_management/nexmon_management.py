# app/adapters/nexmon_management.py
#
# TCP client đọc dữ liệu từ Nexmon-Collection.
# Nexmon-Collection sẽ mở TCP server, ví dụ: 127.0.0.1:9100
#
# Dữ liệu nhận theo format JSON Lines:
# {"device_id":"asus1","timestamp":...,"packet_id":1,"rssi":-45,"csi":"..."}\n
#
# Sau khi parse, mỗi packet được đưa vào queue.Queue để tầng trên xử lý tiếp.

import json
import queue
import socket
import threading
from typing import Optional

"""
@brief
"""
class NexmonManagement:
    def __init__(self, host: str, port: int, maxsize: int = 0):
        """
        @brief Intialize NexmonManagement
        @param host: host
        @param port: TCP port
        @param maxsize: queue size
        """
        self.host = host
        self.port = port

        self.sock: Optional[socket.socket] = None
        self.buffer = b""

        # Queue include packet JSON parsed.
        # Consumer call client.queue.get() to get each packet.
        self.queue: queue.Queue = queue.Queue(maxsize=maxsize)

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()


    def connect(self):
        """
        @brief Connect to TCP server - nexmon_collection
        """

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Timeout when connect in case nexmon_collection not yet run.
        self.sock.settimeout(3)
        self.sock.connect((self.host, self.port))

        # Read data timeout.
        self.sock.settimeout(0.5)

    def read_packet(self) -> Optional[dict]:
        """
        @brief Read 1 packet JSON line from TCP stream
        @return dict if ok
        @return None if data is empty
        """
        if self.sock is None:
            return None

        try:
            while b"\n" not in self.buffer:
                chunk = self.sock.recv(4096)

                if not chunk:
                    return None

                self.buffer += chunk

            line, self.buffer = self.buffer.split(b"\n", 1)

            if not line.strip():
                return None

            packet = json.loads(line.decode("utf-8"))

            return packet

        except socket.timeout:
            return None

        except Exception as e:
            print(f"[NexmonManagement] read_packet error: {e}")
            return None

    def _worker(self):
        """
        @brief Background thread: read automatically -> transfer to queue. stop when stop() be called.
        """
        while not self._stop_event.is_set():
            packet = self.read_packet()

            if packet is not None:
                try:
                    # block=False: nếu queue đầy (maxsize > 0) thì bỏ qua packet cũ nhất.
                    self.queue.put_nowait(packet)
                except queue.Full:
                    # Queue đầy → bỏ packet cũ nhất, nhường chỗ cho packet mới.
                    try:
                        self.queue.get_nowait()
                    except queue.Empty:
                        pass
                    self.queue.put_nowait(packet)

    def start(self):
        """
        @brief Connect and start read packet to queue in background thread.

        Usage:
            client = NexmonManagement("127.0.0.1", 9100)
            client.start()

            # csi_management get packet:
            packet = client.queue.get()
        """
        self.connect()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        print(f"[NexmonManagement] Connected to {self.host}:{self.port}, reading into queue.")

    def stop(self):
        """
        @brief Stop thread and close connection.
        """
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

        self.close()
        print("[NexmonManagement] Stopped.")

    def close(self):
        """
        @brief Close socket.
        """
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass

        self.sock = None
        self.buffer = b""


# Example
#
# client = NexmonManagement("127.0.0.1", 9100, maxsize=500)
# client.start()
#
# while True:
#     packet = client.queue.get()   # block cho đến khi có packet
#     print(packet["packet_id"], packet["rssi"])
