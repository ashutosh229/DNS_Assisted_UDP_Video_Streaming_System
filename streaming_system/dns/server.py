import argparse
import socket
from pathlib import Path

from streaming_system.dns.protocol import build_dns_response, read_dns_request


def load_dns_records(records_file: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in records_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        domain_name, ip_address = stripped.split()
        records[domain_name.lower()] = ip_address
    return records


def handle_client(client_socket: socket.socket, records: dict[str, str]) -> None:
    with client_socket:
        transaction_id, domain_name = read_dns_request(client_socket)
        ip_address = records.get(domain_name.lower())
        client_socket.sendall(build_dns_response(transaction_id, ip_address))
        if ip_address:
            print(f"Resolved {domain_name} -> {ip_address}")
        else:
            print(f"No mapping found for {domain_name}")


def run_dns_server(host: str, port: int, records_file: Path) -> None:
    records = load_dns_records(records_file)
    print(f"Loaded {len(records)} DNS records from {records_file}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"DNS server listening on {host}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"DNS request from {client_address[0]}:{client_address[1]}")
            try:
                handle_client(client_socket, records)
            except Exception as error:
                print(f"Failed to process DNS request: {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Custom TCP DNS server")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to bind")
    parser.add_argument("--port", type=int, default=53535, help="TCP port")
    parser.add_argument(
        "--records-file",
        type=Path,
        default=Path("config/dns_records.txt"),
        help="Path to the domain -> IP mapping file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dns_server(args.host, args.port, args.records_file)


if __name__ == "__main__":
    main()
