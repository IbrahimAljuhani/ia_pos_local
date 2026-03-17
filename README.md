# ia_pos_local — POS Local Terminal & Printer

**Author:** Ibrahim Aljuhani  
**Email:** info@ia.sa  
**Website:** https://ia.sa  
**Version:** 18.0.1.0.0  
**License:** LGPL-3  

---

## Overview

All-in-one POS module for Odoo 18 installations running on a **local server** (`http://`).  
No IoT Box or Raspberry Pi required — the Odoo server connects directly to all devices.

| Feature | Details |
|---------|---------|
| Mada payment | NeoLeap WebSocket protocol |
| Receipt printing | ESC/POS over TCP port 9100 |
| Kitchen printing | ESC/POS over TCP port 9100 |
| Multiple terminals | One IP per payment method |
| Multiple printers | One IP per printer |
| Test Connection | Button on each device form |

---

## Requirements

| Component | Details |
|-----------|---------|
| Odoo | 18.0 (Community or Enterprise) |
| Server | Local network — `http://` |
| Python libraries | `websocket-client`, `python-escpos`, `Pillow` |
| Network | Odoo server, printers, and terminals on the same LAN |

> **Note:** This module is designed for local servers only.  
> For cloud/external servers use `ia_mada_iot` with Raspberry Pi IoT Box instead.

---

## Installation

### Step 1 — Install Python libraries on the server

```bash
pip install websocket-client python-escpos Pillow
```

### Step 2 — Install the module

```bash
# Upload ia_pos_local.zip via WinSCP to /tmp/, then:
sudo unzip -o /tmp/ia_pos_local.zip -d /odoo/custom/addons/
sudo chown -R odoo:odoo /odoo/custom/addons/ia_pos_local

sudo -u odoo /odoo/venv/bin/python /odoo/odoo-bin \
  --config=/etc/odoo.conf \
  -d myodoo \
  -i ia_pos_local \
  --stop-after-init

sudo systemctl restart odoo
```

---

## Configuration

### Mada Terminals

Go to **POS → Configuration → Payment Methods → New**:

| Field | Value |
|-------|-------|
| Name | `Mada - Cashier` |
| Integration | Terminal |
| Integrate with | Mada Terminal (Local) |
| NeoLeap IP Address | `192.168.1.10` |

Click **Test Connection** to verify.

### Printers

Go to **POS → Configuration → Printers → New**:

| Field | Value |
|-------|-------|
| Name | `Cashier Printer` |
| Type | ESC/POS Network Printer (Local) |
| Printer IP Address | `192.168.1.101` |
| Port | `9100` |

Repeat for kitchen and drive-through printers.

---

## Multiple Devices

| Device | IP | Type |
|--------|----|------|
| Mada - Cashier | 192.168.1.10 | Payment terminal |
| Mada - Drive-through | 192.168.1.11 | Payment terminal |
| Cashier Printer | 192.168.1.101 | Receipt printer |
| Kitchen Printer | 192.168.1.102 | Order printer |
| Drive-through Printer | 192.168.1.103 | Order printer |

---

## NeoLeap Protocol

```
Server  →  ws://192.168.1.10:7000
  SEND  {"Command": "CHECK_STATUS"}
  RECV  {"EventName": "TERMINAL_STATUS", "TerminalStatus": "READY"}
  SEND  {"Command": "SALE", "Amount": "150.00", "AdditionalData": "order_uid"}
  RECV  {"EventName": "TERMINAL_RESPONSE", "JsonResult": {"StatusCode": "00"}}
```

| StatusCode | Meaning |
|------------|---------|
| `00` | Approved |
| `01` | Declined by bank |
| `11` | Cancelled by customer |

---

## File Structure

```
ia_pos_local/
├── __manifest__.py
├── __init__.py
├── CHANGELOG.md
├── README.md
├── models/
│   ├── pos_payment_method.py   ← mada_local terminal + neoleap_ip + test button
│   └── pos_printer.py          ← escpos_local printer + IP/port fields + test button
├── controllers/
│   ├── mada.py                 ← WebSocket proxy to NeoLeap
│   └── printer.py              ← TCP ESC/POS printing
└── static/src/app/
    ├── model.js                ← registers PaymentMadaLocal
    ├── payment_mada.js         ← POS payment logic, calls /ia_pos_local/mada/pay
    ├── payment_screen.js       ← PaymentScreen patches
    └── printer.js              ← EscPosLocalPrinter, calls /ia_pos_local/printer/print
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `websocket-client not installed` | `pip install websocket-client` on server |
| `python-escpos not installed` | `pip install python-escpos Pillow` on server |
| Terminal not responding | Check NeoLeap app is open and IP is correct |
| Printer not printing | Verify printer IP and port 9100 is reachable from server |
| `ping 192.168.1.x` fails | Check network — server and devices must be on same LAN |
