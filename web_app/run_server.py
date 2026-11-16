"""Starts the Smart Screen web server.

Run it from this folder:    py run_server.py        (Windows)
                            python3 run_server.py   (Linux, macOS)
Stop it with Ctrl+C.

By default every device that can reach this computer can open the pages. To accept connections
from one network only, give this computer's address on that network:

    py run_server.py --host 100.64.0.10
"""
from __future__ import annotations

import argparse
import socket
from dataclasses import replace

from server.app import create_app
from server.config import ServerConfig


def read_command_line(defaults: ServerConfig) -> ServerConfig:
    parser = argparse.ArgumentParser(description="Starts the Smart Screen web server.")
    parser.add_argument("--host", default=defaults.host,
                        help="the address to listen on (default: every network this computer is on)")
    parser.add_argument("--port", type=int, default=defaults.port, help="the port to listen on")
    arguments = parser.parse_args()
    return replace(defaults, host=arguments.host, port=arguments.port)


def addresses_of_this_computer() -> list[str]:
    """This computer's addresses on the networks it is on, for typing into a phone."""
    try:
        found = socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
    except OSError:
        return []
    return sorted({entry[4][0] for entry in found if not entry[4][0].startswith("127.")})


def print_where_to_open(config: ServerConfig) -> None:
    print()
    print("Smart Screen server is running. Stop it with Ctrl+C.")
    print(f"  On this computer:  http://localhost:{config.port}")
    if config.host == "0.0.0.0":
        phone_addresses = addresses_of_this_computer()
    else:
        phone_addresses = [config.host]
    for address in phone_addresses:
        print(f"  The device page:   http://{address}:{config.port}/device")
    print()


def main() -> None:
    config = read_command_line(ServerConfig())
    app = create_app(config)
    print_where_to_open(config)
    # threaded=True: each connected page gets its own thread, so one page that keeps a
    # connection open does not block the others.
    app.run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()
