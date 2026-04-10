import argparse
import socket
import struct
import time

import cv2


KEEPALIVE_MESSAGE = b"KEEPALIVE"
MAX_UDP_PAYLOAD = 60_000
PACKET_HEADER = struct.Struct("!I H H d")


def wait_for_client(
    server_socket: socket.socket, keepalive_timeout: float
) -> tuple[str, int] | None:
    print("Waiting for a client keep-alive...")
    while True:
        data, address = server_socket.recvfrom(1024)
        if data == KEEPALIVE_MESSAGE:
            print(f"Streaming client registered: {address[0]}:{address[1]}")
            return address
        if keepalive_timeout > 0:
            print(f"Ignored unexpected packet from {address}")


def encode_frame(capture: cv2.VideoCapture, jpeg_quality: int) -> bytes | None:
    ok, frame = capture.read()
    if not ok:
        return None

    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality],
    )
    if not success:
        return None

    return encoded.tobytes()


def send_frame(
    server_socket: socket.socket,
    client_address: tuple[str, int],
    frame_id: int,
    encoded_frame: bytes,
) -> None:
    max_chunk_size = MAX_UDP_PAYLOAD - PACKET_HEADER.size
    total_chunks = max(1, (len(encoded_frame) + max_chunk_size - 1) // max_chunk_size)
    sent_at = time.time()

    for chunk_index in range(total_chunks):
        start = chunk_index * max_chunk_size
        end = start + max_chunk_size
        chunk = encoded_frame[start:end]
        header = PACKET_HEADER.pack(frame_id, chunk_index, total_chunks, sent_at)
        server_socket.sendto(header + chunk, client_address)


def run_video_server(
    host: str,
    port: int,
    fps: int,
    jpeg_quality: int,
    keepalive_timeout_ms: int,
) -> None:
    keepalive_timeout = keepalive_timeout_ms / 1000.0
    frame_interval = 1.0 / fps

    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        raise RuntimeError("Unable to access the webcam.")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.bind((host, port))
            server_socket.settimeout(frame_interval)
            print(f"Video server listening on {host}:{port}")

            client_address = wait_for_client(server_socket, keepalive_timeout)
            last_keepalive_at = time.time()
            frame_id = 0

            while True:
                cycle_started = time.time()

                try:
                    while True:
                        data, address = server_socket.recvfrom(1024)
                        if data == KEEPALIVE_MESSAGE and address == client_address:
                            last_keepalive_at = time.time()
                        elif data == KEEPALIVE_MESSAGE and client_address is None:
                            client_address = address
                            last_keepalive_at = time.time()
                            print(f"Client connected: {address[0]}:{address[1]}")
                except socket.timeout:
                    pass

                if client_address is None:
                    client_address = wait_for_client(server_socket, keepalive_timeout)
                    last_keepalive_at = time.time()
                    continue

                if time.time() - last_keepalive_at > keepalive_timeout:
                    print("Client keep-alive timed out. Pausing stream.")
                    client_address = wait_for_client(server_socket, keepalive_timeout)
                    last_keepalive_at = time.time()
                    continue

                encoded_frame = encode_frame(capture, jpeg_quality)
                if encoded_frame is None:
                    continue

                send_frame(server_socket, client_address, frame_id, encoded_frame)
                frame_id += 1

                elapsed = time.time() - cycle_started
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
    finally:
        capture.release()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP video streaming server")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to bind")
    parser.add_argument("--port", type=int, default=5005, help="UDP port")
    parser.add_argument("--fps", type=int, default=20, help="Target frames per second")
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=70,
        help="JPEG quality from 0 to 100",
    )
    parser.add_argument(
        "--keepalive-timeout-ms",
        type=int,
        default=200,
        help="Stop sending when keep-alive is absent for this many milliseconds",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_video_server(
        args.host,
        args.port,
        args.fps,
        args.jpeg_quality,
        args.keepalive_timeout_ms,
    )


if __name__ == "__main__":
    main()
