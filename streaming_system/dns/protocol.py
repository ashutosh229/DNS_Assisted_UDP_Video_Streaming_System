import socket
import struct


REQUEST_HEADER = struct.Struct("!H H")
RESPONSE_HEADER = struct.Struct("!H B H")


def build_dns_request(transaction_id: int, domain_name: str) -> bytes:
    encoded_name = domain_name.encode("utf-8")
    return REQUEST_HEADER.pack(transaction_id, len(encoded_name)) + encoded_name


def read_dns_request(sock: socket.socket) -> tuple[int, str]:
    header = recv_exact(sock, REQUEST_HEADER.size)
    transaction_id, name_length = REQUEST_HEADER.unpack(header)
    domain_name = recv_exact(sock, name_length).decode("utf-8")
    return transaction_id, domain_name


def build_dns_response(transaction_id: int, ip_address: str | None) -> bytes:
    if ip_address is None:
        return RESPONSE_HEADER.pack(transaction_id, 0, 0)

    encoded_ip = ip_address.encode("utf-8")
    return RESPONSE_HEADER.pack(transaction_id, 1, len(encoded_ip)) + encoded_ip


def read_dns_response(sock: socket.socket) -> tuple[int, str | None]:
    header = recv_exact(sock, RESPONSE_HEADER.size)
    transaction_id, found_flag, ip_length = RESPONSE_HEADER.unpack(header)
    if not found_flag:
        return transaction_id, None

    ip_address = recv_exact(sock, ip_length).decode("utf-8")
    return transaction_id, ip_address


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        data = sock.recv(size - len(chunks))
        if not data:
            raise ConnectionError("Socket closed while reading message.")
        chunks.extend(data)
    return bytes(chunks)
