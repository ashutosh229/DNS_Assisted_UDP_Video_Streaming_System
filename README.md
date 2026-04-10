# DNS-Assisted UDP Video Streaming System

This project implements the required three-part socket programming system:

- A custom TCP DNS server
- A UDP real-time video streaming server
- A client that resolves the server domain first, then starts video streaming

## Project Layout

- `client.py`: Top-level client entry point
- `dns_server.py`: Top-level DNS server entry point
- `video_server.py`: Top-level video server entry point
- `dns_protocol.py`: Compatibility import for the shared DNS protocol
- `streaming_system/`: Core application package
- `config/dns_records.txt`: Domain to IP mappings
- `docs/STRUCTURE.md`: Folder structure overview

## Requirements

- Python 3.10+
- A working webcam
- OpenCV and NumPy

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run Order

Start the DNS server:

```powershell
python dns_server.py
```

Start the video server:

```powershell
python video_server.py
```

Start the client:

```powershell
python client.py --domain video.server.com
```

You can also run the packaged modules directly:

```powershell
python -m streaming_system.dns.server
python -m streaming_system.video.server
python -m streaming_system.video.client --domain video.server.com
```

## Expected Output

On the client:

```text
Domain: video.server.com
IP Address: 127.0.0.1
```

Then an OpenCV window opens and displays the real-time UDP video stream.

## Notes

- DNS resolution happens before video streaming starts.
- Frames are JPEG-compressed before transmission to reduce bandwidth usage.
- Large frames are split into multiple UDP packets and reassembled by the client.
- Missing UDP packets are tolerated by skipping incomplete frames.
- The client sends keep-alive packets every 100 ms.
- The server stops sending if no keep-alive arrives for 200 ms.
- Press `q` in the client video window to close the stream.
