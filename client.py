import argparse
import random
import socket
import struct
import threading
import time
from collections import defaultdict

import cv2
import numpy as np

from dns_protocol import build_dns_request, read_dns_response


KEEPALIVE_MESSAGE = b"KEEPALIVE"
PACKET_HEADER = struct.Struct("!I H H d")


def resolve_domain(
    dns_host: str, dns_port: int, domain_name: str, transaction_id: int | None = None
) -> str:
    request_id = transaction_id if transaction_id is not None else random.randint(0, 65535)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dns_socket:
        dns_socket.connect((dns_host, dns_port))
        dns_socket.sendall(build_dns_request(request_id, domain_name))
        response_id, ip_address = read_dns_response(dns_socket)

    if response_id != request_id:
        raise RuntimeError("DNS transaction ID mismatch.")
    if ip_address is None:
        raise RuntimeError(f"Domain not found: {domain_name}")
    return ip_address


def keepalive_loop(
    udp_socket: socket.socket,
    server_address: tuple[str, int],
    stop_event: threading.Event,
    interval_ms: int,
) -> None:
    interval_s = interval_ms / 1000.0
    while not stop_event.is_set():
        udp_socket.sendto(KEEPALIVE_MESSAGE, server_address)
        time.sleep(interval_s)


def run_video_client(server_ip: str, server_port: int, keepalive_interval_ms: int) -> None:
    server_address = (server_ip, server_port)
    stop_event = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.settimeout(1.0)
        udp_socket.sendto(KEEPALIVE_MESSAGE, server_address)

        keepalive_thread = threading.Thread(
            target=keepalive_loop,
            args=(udp_socket, server_address, stop_event, keepalive_interval_ms),
            daemon=True,
        )
        keepalive_thread.start()

        frame_chunks: dict[int, dict[int, bytes]] = defaultdict(dict)
        frame_received_at: dict[int, float] = {}

        try:
            while True:
                try:
                    packet, _ = udp_socket.recvfrom(65535)
                except socket.timeout:
                    continue

                if len(packet) < PACKET_HEADER.size:
                    continue

                frame_id, chunk_index, total_chunks, sent_at = PACKET_HEADER.unpack(
                    packet[: PACKET_HEADER.size]
                )
                payload = packet[PACKET_HEADER.size :]
                frame_chunks[frame_id][chunk_index] = payload
                frame_received_at.setdefault(frame_id, time.time())

                if len(frame_chunks[frame_id]) != total_chunks:
                    stale_frame_ids = [
                        existing_frame_id
                        for existing_frame_id, received_at in frame_received_at.items()
                        if time.time() - received_at > 1.0
                    ]
                    for stale_frame_id in stale_frame_ids:
                        frame_chunks.pop(stale_frame_id, None)
                        frame_received_at.pop(stale_frame_id, None)
                    continue

                encoded_frame = b"".join(
                    frame_chunks[frame_id][index] for index in range(total_chunks)
                )
                np_buffer = np.frombuffer(encoded_frame, dtype=np.uint8)
                frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
                if frame is None:
                    del frame_chunks[frame_id]
                    frame_received_at.pop(frame_id, None)
                    continue

                latency_ms = (time.time() - sent_at) * 1000.0
                cv2.putText(
                    frame,
                    f"Latency: {latency_ms:.1f} ms",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("UDP Video Stream", frame)

                completed_frames = [
                    existing_frame_id
                    for existing_frame_id in frame_chunks
                    if existing_frame_id <= frame_id
                ]
                for existing_frame_id in completed_frames:
                    del frame_chunks[existing_frame_id]
                    frame_received_at.pop(existing_frame_id, None)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            stop_event.set()
            cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DNS-assisted UDP video client")
    parser.add_argument(
        "--domain",
        default="video.server.com",
        help="Domain name to resolve through the custom DNS server",
    )
    parser.add_argument("--dns-host", default="127.0.0.1", help="DNS server host")
    parser.add_argument("--dns-port", type=int, default=53535, help="DNS server TCP port")
    parser.add_argument(
        "--video-port", type=int, default=5005, help="Video server UDP port"
    )
    parser.add_argument(
        "--keepalive-interval-ms",
        type=int,
        default=100,
        help="How often the client sends keep-alive packets",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    resolved_ip = resolve_domain(args.dns_host, args.dns_port, args.domain)
    print(f"Domain: {args.domain}")
    print(f"IP Address: {resolved_ip}")
    run_video_client(resolved_ip, args.video_port, args.keepalive_interval_ms)
