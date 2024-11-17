# hl7lw: A Lightweight HL7 2.x Parsing Library

[![pypi](https://img.shields.io/pypi/v/hl7lw)](https://pypi.org/project/hl7lw/)
[![Test-Status](https://github.com/acv/hl7lw/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/acv/hl7lw/actions/workflows/python-app.yml)

The hl7lw library aims to provide an extremely simple and lightweight
API to read, modify, and write HL7 2.x messages. Minimal processing is
done to the messages and most data access should feel very natural and
pythonic.

The library also includes an MLLP implementation for both client and
server.

All objects have docstrings.

```Python
import hl7lw

p = hl7lw.Hl7Parser()
m = p.parse_message(message_bytes)

if m["MSH-9.1"] == "ORU":
    m["ORC-1"] = "RP"

message_bytes = p.format_message(m)

report = "\n".join([obx[5] for obx in m.get_segments('OBX') if obx[2] in ('TX', 'FT', 'ST')])

c = hl7lw.MllpClient()
c.connect(host="127.0.0.1", port="1234")
c.send(message_bytes)
ack_bytes = c.recv()
c.close()

ack_m = p.parse_message(ack_bytes)
assert ack_m["MSA-1.1"] == "AA"
assert m["MSH-10"] == ack_m["MSA-2"]

```
