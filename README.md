# nexmon_management

Read CSI packets from Nexmon-Collection via TCP and enqueue them to the handler.

---

## Structure
```text
📁 nexmon_management          <!-- Block 3.3.1 -->
├── APIs.md
├── csi_management.py         <!-- CSI management simulation (3.3.3) -->
├── nexmon_collection.py      <!-- Nexmon-Collection simulation (3.1) -->
├── nexmon_management.py      <!-- Nexmon management implementation (3.3.1) -->
└── .gitignore
```

## Usage

```python
from nexmon_management import NexmonManagement

mgr = NexmonManagement("127.0.0.1", 9100, maxsize=500)
mgr.start()

while True:
    packet = mgr.queue.get()   # Blocks until a packet is available
    print(packet["packet_id"], packet["rssi"], packet["csi"])

mgr.stop()
```

| Field | Type | Mô tả |
|---|---|---|
| `device_id` | str | ID thiết bị |
| `source` | str | Nguồn dữ liệu |
| `timestamp` | float | Unix timestamp (giây) |
| `packet_id` | int | Số thứ tự packet |
| `rssi` | int | RSSI (dBm) |
| `csi` | dict | CSI data (see details below) |

### `csi` keys

```json
{
  "device_id": "asus1",
  "source": "nexmon",
  "timestamp": 1716123456.789012,
  "packet_id": 1,
  "rssi": -45,
  "csi": {
    "seq": 12345,
    "bw": 80,
    "nfft": 256,
    "antennas": {
      "c0": [1.234567, 2.345678, 0.987654, "...256 values..."],
      "c1": [0.876543, 1.654321, 2.111111, "...256 values..."],
      "c2": [1.500000, 1.300000, 0.750000, "...256 values..."],
      "c3": [0.654321, 1.234567, 1.876543, "...256 values..."]
    }
  }
}
```

**Get field top-level:**
```python
packet["rssi"]        # -45
packet["csi"]["seq"]  # 12345
packet["csi"]["bw"]   # 80
```

**Get data antenna:**
```python
packet["csi"]["antennas"]["c0"]  # list 256 value of antenna 0
packet["csi"]["antennas"]["c1"]  # list 256 value of antenna 0
```

---

## Test

```bash
# Terminal 1
python nexmon_collection.py

# Terminal 2
python csi_management.py
```