#!/usr/bin/env python3
"""
Test consumer — kết nối NexmonManagement tới mock server, in packet nhận được.

Usage:
    python test_consumer.py
    python test_consumer.py --host 127.0.0.1 --port 9100
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from nexmon_management import NexmonManagement


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9100)
    args = parser.parse_args()

    client = NexmonManagement(args.host, args.port, maxsize=500)
    client.start()

    print("[Consumer] Đang nhận packet từ queue... (Ctrl+C để dừng)\n")

    count = 0
    t_start = time.monotonic()

    try:
        while True:
            packet = client.queue.get(timeout=5)
            count += 1

            if count <= 5 or count % 50 == 0:
                elapsed = time.monotonic() - t_start
                print(
                    f"[#{packet['packet_id']:>6}] "
                    f"rssi={packet['rssi']:>4} dBm | "
                    f"ts={packet['timestamp']:.3f} | "
                    f"csi={packet['csi'][:20]}... | "
                    f"queue={client.queue.qsize()} | "
                    f"rate={count / elapsed:.1f} pkt/s"
                )

    except KeyboardInterrupt:
        print(f"\n[Consumer] Dừng. Tổng nhận: {count} packets.")
    finally:
        client.stop()


if __name__ == "__main__":
    main()