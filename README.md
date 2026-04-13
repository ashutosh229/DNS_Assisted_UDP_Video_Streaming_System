# DNS-Assisted UDP Video Streaming System

## Overview

This project implements a socket-programming-based application in which a client first resolves a video server domain name using a custom TCP DNS resolver and then starts a real-time UDP video streaming session using the resolved IP address.

The assignment is divided into three communicating components:

- A TCP-based DNS server
- A UDP-based video streaming server
- A client application that integrates both stages

The implementation uses only socket programming primitives for communication. The DNS stage uses TCP sockets, and the video streaming stage uses UDP sockets. Video frames are captured from a webcam using OpenCV, compressed into JPG format, fragmented into UDP-safe chunks, sent over the network, reassembled at the client, decoded, and displayed in real time.

## Core Idea

The core idea of the application is to simulate a simplified real-world workflow:

1. A client does not initially know the IP address of the video server.
2. The client sends a custom DNS query over TCP to a DNS server.
3. The DNS server checks a domain-to-IP mapping file and returns the matching IP address.
4. Only after successful DNS resolution, the client starts a UDP-based video streaming session to that IP address.
5. The client continues sending keep-alive packets so that the server knows the receiver is still active.

This separates the name-resolution phase from the media-delivery phase and demonstrates the use of different transport protocols for different needs:

- TCP for reliable DNS-style request/response exchange
- UDP for low-latency real-time media transmission

## System Description

The system consists of the following three modules:

### 1. DNS Server

The DNS server listens on a TCP port and accepts a DNS request containing:

- Transaction ID
- Domain Name

It looks up the requested domain in a text file containing domain-to-IP mappings and returns a response with:

- The same Transaction ID
- A success/failure indicator
- The resolved IP address if found

### 2. Video Streaming Server

The video streaming server listens on a UDP port. It captures frames from the webcam, compresses them into JPG format, and sends them continuously to the client. To support larger frames safely over UDP, each frame is split into multiple packets with a small custom header.

The server also tracks keep-alive packets from the client. If the client stops sending keep-alive messages for more than 200 milliseconds, the server pauses and waits for the next active client.

### 3. Client Application

The client first connects to the DNS server over TCP, resolves the configured domain name, prints the resolved domain and IP address, and only then starts the UDP video streaming phase.

The client:

- Sends keep-alive packets periodically to the video server
- Receives UDP frame fragments
- Reassembles full frames
- Decodes JPG data into images
- Displays the video in real time
- Skips incomplete frames to handle UDP packet loss smoothly

## Functional Requirements

The application satisfies the required functionality below.

### DNS Resolver Using TCP Sockets

- The client sends a DNS request containing:
  - Transaction ID
  - Domain Name
- The DNS server maintains a text file with at least 5 domain-to-IP mappings
- On receiving a request, the DNS server:
  - Searches the requested domain
  - Returns the same Transaction ID
  - Returns the resolved IP address if found
- The client displays:
  - `Domain: <domain_name>`
  - `IP Address: <resolved_ip>`

### UDP-Based Video Streaming

- The video server:
  - Captures live video from the webcam
  - Encodes frames using JPG compression
  - Serializes frames into UDP-transmittable chunks
  - Sends frames continuously using UDP
- The client:
  - Receives UDP packets
  - Reassembles complete frames
  - Decodes frames
  - Displays them in real time

### Integration Requirement

- The client first resolves the domain name using the custom DNS server
- The resolved IP address is then used to connect to the video server
- Video streaming begins only after successful DNS resolution

## Architecture

### High-Level Flow

```text
+-------------------+        TCP         +-------------------+
|      Client       | -----------------> |    DNS Server     |
|                   |   Query: domain    |                   |
|                   | <----------------- |   Response: IP    |
+-------------------+                    +-------------------+
          |
          | Resolved IP Address
          v
+-------------------+        UDP         +-------------------+
|      Client       | <----------------- |   Video Server    |
|  Receive Frames   |    JPG Chunks      |  Send Frames      |
|  Show Latency     | -----------------> |  Keep-Alive Rx    |
+-------------------+   Keep-Alive Msgs  +-------------------+
```

### Component Design

### DNS Module

- Located under `streaming_system/dns/`
- Uses a custom compact binary request/response format
- Uses `sendall()` and `recv()` on TCP sockets
- Reads mappings from `config/dns_records.txt`

### Video Module

- Located under `streaming_system/video/`
- Uses `sendto()` and `recvfrom()` on UDP sockets
- Compresses frames using OpenCV JPG encoding
- Splits frames into multiple UDP packets using a packet header containing:
  - Frame ID
  - Chunk index
  - Total chunk count
  - Timestamp

### Client Module

- Resolves the domain first over TCP
- Starts UDP reception only after DNS success
- Reassembles chunks into complete frames
- Computes and displays live latency using the frame timestamp

### Folder Structure

```text
DNS_Assisted_UDP_Video_Streaming_System/
|-- client.py
|-- dns_protocol.py
|-- dns_server.py
|-- video_server.py
|-- config/
|   `-- dns_records.txt
|-- docs/
|   `-- STRUCTURE.md
|-- streaming_system/
|   |-- dns/
|   |   |-- protocol.py
|   |   `-- server.py
|   `-- video/
|       |-- client.py
|       `-- server.py
|-- requirements.txt
`-- README.md
```

## Design Choices

### Why TCP for DNS

TCP provides reliable delivery and ordered data transfer. Since DNS resolution in this assignment is a request/response transaction and must return the correct transaction ID and IP address reliably, TCP is a good fit.

### Why UDP for Video Streaming

UDP reduces delay and avoids the overhead of retransmission. For real-time video, low latency is more important than perfect delivery. Missing packets are tolerated by skipping incomplete frames instead of blocking playback.

### Why JPG Encoding

Raw video frames are large. JPG compression significantly reduces bandwidth usage and makes it feasible to transmit webcam frames over UDP while maintaining reasonable smoothness.

## Challenges Addressed and Solutions

### 1. Packet Loss in UDP

#### Challenge

UDP does not guarantee packet delivery, order, or retransmission.

#### Solution

- Each video frame is split into numbered chunks
- The client collects chunks by frame ID
- If all chunks arrive, the frame is reconstructed and displayed
- If some chunks are missing, the incomplete frame is discarded after a short timeout
- Playback continues smoothly without freezing

### 2. Large Video Frames

#### Challenge

A compressed JPG frame may still be too large for safe transmission as a single UDP packet.

#### Solution

- Each frame is fragmented into smaller UDP-safe chunks
- A custom packet header is attached to each chunk
- The client reassembles chunks in the correct order

### 3. Real-Time Performance

#### Challenge

The system must maintain smooth playback with low latency.

#### Solution

- JPG compression reduces transmitted data size
- UDP is used instead of TCP for streaming
- Incomplete frames are skipped instead of retried
- Keep-alive is lightweight and periodic

### 4. Client Disconnect Detection

#### Challenge

The server must stop or pause transmission if the client closes the application.

#### Solution

- The client sends keep-alive packets every 100 ms
- The server tracks the most recent keep-alive timestamp
- If no keep-alive arrives for more than 200 ms, the server pauses streaming and waits for a new active client

### 5. DNS Before Streaming Integration

#### Challenge

The assignment requires that video streaming only starts after successful DNS resolution.

#### Solution

- The client performs the DNS lookup first
- Only after receiving a valid IP address does the client move to the UDP streaming stage

## System Constraints and Compliance

The following assignment constraints are followed by the implementation.

### Use Only Socket Programming

The application uses Python's low-level `socket` module directly.

### TCP for DNS Communication

The DNS server and DNS client logic use TCP sockets.

### UDP for Video Streaming

The video server and client use UDP sockets for frame transmission and keep-alive messaging.

### Use Basic Primitives Only

Communication uses socket operations such as:

- `sendall()`
- `recv()`
- `sendto()`
- `recvfrom()`

No high-level networking or messaging framework is used.

### No Wrapper-Based Networking APIs

The project does not use messaging middleware, RPC frameworks, HTTP streaming libraries, or other abstraction layers over sockets.

## Tech Stack

- Language: Python 3
- Networking: Python `socket` module
- Video Capture and Encoding: OpenCV (`cv2`)
- Byte Buffer Handling: NumPy

## Implementation Details

### DNS Request/Response Format

The custom DNS protocol uses a compact binary format.

#### DNS Request

- Transaction ID
- Domain name length
- Domain name bytes

#### DNS Response

- Transaction ID
- Found flag
- IP address length
- IP address bytes

### Video Packet Format

Each UDP packet contains:

- Frame ID
- Chunk index
- Total chunks
- Timestamp
- JPG data chunk

This allows the client to:

- Group chunks by frame
- Reassemble them in order
- Estimate end-to-end latency

## Setup

### Prerequisites

- Python 3.10 or above
- A working webcam
- Virtual environment recommended

### Clone / Open the Repository

If the repository is already available locally, open the project folder in your terminal or clone the git repository in case the folder is not available.

```powershell
git clone https://github.com/ashutosh229/DNS_Assisted_UDP_Video_Streaming_System.git
cd DNS_Assisted_UDP_Video_Streaming_System
```

### Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/Scripts/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Open three terminals in the project root.

### Step 1. Start the DNS Server

```bash
python dns_server.py
```

Expected behavior:

- Loads the domain-to-IP records
- Listens on TCP port `53535`

### Step 2. Start the Video Streaming Server

```bash
python video_server.py
```

Expected behavior:

- Opens the webcam
- Listens on UDP port `5005`
- Waits for a client keep-alive packet

### Step 3. Start the Client

```bash
python client.py --domain video.server.com
```

Expected behavior:

- Resolves the domain via the custom DNS server
- Prints the domain and resolved IP address
- Opens the real-time video display window
- Shows live latency on the video window

### Alternative Module-Based Commands

The same application can also be started using the package modules:

```bash
python -m streaming_system.dns.server
python -m streaming_system.video.server
python -m streaming_system.video.client --domain video.server.com
```

### How to Stop the Application

- To stop any running server or client in the terminal, press `Ctrl + C`
- To close the client video window, press `q`

## Results

The application was tested successfully with the following observed outcomes:

- The DNS server loaded 5 domain-to-IP mappings
- The client successfully resolved `video.server.com` to `127.0.0.1`
- The video server accepted the keep-alive message from the client
- The client opened a GUI window and displayed real-time webcam video
- Live latency was shown on the client window
- The client performed DNS resolution before starting streaming, satisfying the integration requirement

### Terminal Output

#### DNS Server

```text
Loaded 5 DNS records from config\dns_records.txt
DNS server listening on 0.0.0.0:53535
DNS request from 127.0.0.1:59426
Resolved video.server.com -> 127.0.0.1
```

#### Video Server

```text
Video server listening on 0.0.0.0:5005
Waiting for a client keep-alive...
Streaming client registered: 127.0.0.1:64389
```

#### Client

```text
Domain: video.server.com
IP Address: 127.0.0.1
```

## References

The following references were used during implementation and understanding:

1. Python Documentation, `socket` module
   https://docs.python.org/3/library/socket.html
2. Python Documentation, `struct` module
   https://docs.python.org/3/library/struct.html
3. OpenCV Documentation
   https://docs.opencv.org/
4. OpenCV Python Tutorials
   https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html
5. NumPy Documentation
   https://numpy.org/doc/

## Conclusion

This project successfully demonstrates the design and implementation of a DNS-assisted UDP video streaming system using socket programming only. It integrates reliable TCP-based name resolution with low-latency UDP-based media delivery, while also addressing practical networking challenges such as packet loss, frame fragmentation, real-time playback, and client disconnect detection through keep-alive monitoring.
