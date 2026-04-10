# Project Structure

```text
DNS_Assisted_UDP_Video_Streaming_System/
├── client.py
├── dns_protocol.py
├── dns_server.py
├── video_server.py
├── config/
│   └── dns_records.txt
├── docs/
│   └── STRUCTURE.md
├── streaming_system/
│   ├── dns/
│   │   ├── protocol.py
│   │   └── server.py
│   └── video/
│       ├── client.py
│       └── server.py
├── README.md
└── requirements.txt
```

- Top-level scripts remain as simple entry points for demos and assignment submission.
- Core networking logic now lives inside the `streaming_system` package.
- Configuration data is isolated under `config/`.
- Documentation about layout lives under `docs/`.
