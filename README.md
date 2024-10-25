# hl7lw: A Lightweight HL7 2.x Parsing Library

[![pypi](https://img.shields.io/pypi/v/hl7lw)](https://pypi.org/project/hl7lw/)
[![Test-Status](https://github.com/acv/hl7lw/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/acv/hl7lw/actions/workflows/python-app.yml)

The hl7lw library aims to provide an extremely simple and lightweight
API to read, modify, and write HL7 2.x messages. Minimal processing is
done to the messages and most data access should feel very natural and
pythonic.

```Python
import hl7lw

p = hl7lw.Hl7Parser()
m = p.parse_message(message_bytes)

if m["MSH-9.1"] == "ORU":
    m["ORC-1"] = "RP"

message_bytes = p.format_message(m)
```
