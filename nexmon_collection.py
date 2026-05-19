#!/usr/bin/env python3
"""
Mock TCP server mô phỏng Nexmon-Collection.

Usage:
    python mock_nexmon_server.py
    python mock_nexmon_server.py --host 127.0.0.1 --port 9100 --rate 67
"""

import argparse
import base64
import json
import math
import random
import socket
import struct
import time


def make_fake_csi(nfft: int = 256, num_cores: int = 4) -> str:
    values = [
        abs(1.5 + 0.8 * math.sin(2 * math.pi * i / nfft + c * 0.7) + random.gauss(0, 0.15))
        for c in range(num_cores)
        for i in range(nfft)
    ]
    return base64.b64encode(struct.pack(f"{len(values)}f", *values)).decode()


def run(host: str, port: int, rate: int):
    interval = 1.0 / rate
    packet_id = 0

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(1)

    print(f"[MockServer] Listening on {host}:{port} — {rate} pkt/s")
    print("[MockServer] Chờ client kết nối...")

    conn, addr = server_sock.accept()
    print(f"[MockServer] Client kết nối: {addr}")

    try:
        while True:
            t0 = time.monotonic()
            packet_id += 1

            packet = {
                "device_id": "asus1",
                "timestamp": time.time(),
                "packet_id": packet_id,
                "rssi":      random.randint(-65, -35),
                "csi":       make_fake_csi(),
            }

            try:
                conn.sendall((json.dumps(packet) + "\n").encode())
            except BrokenPipeError:
                print("[MockServer] Client ngắt kết nối.")
                break

            if packet_id % 100 == 0:
                print(f"[MockServer] Đã gửi {packet_id} packets")

            sleep_time = interval - (time.monotonic() - t0)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[MockServer] Dừng.")
    finally:
        conn.close()
        server_sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--rate", type=int, default=67,
                        help="Số packet/giây (mặc định: 67 ~ 80MHz realtime)")
    args = parser.parse_args()
    run(args.host, args.port, args.rate)


if __name__ == "__main__":
    main()