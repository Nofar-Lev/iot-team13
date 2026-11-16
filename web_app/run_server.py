"""Starts the Smart Screen web server.

Run it from this folder, and choose a port:

    py run_server.py --port 23634        (Windows)
    python3 run_server.py --port 23634   (Linux, macOS)

Stop it with Ctrl+C.

The port must be given every time; there is no default. Any free number from 1024 to 65535
will do.

By default every device that can reach this computer can open the pages. To accept connections
from one network only, also give this computer's address on that network:

    py run_server.py --port 23634 --host 100.64.0.10
"""
from __future__ import annotations

import argparse
import os
import socket
import sys
from dataclasses import replace
from typing import Optional

from server.app import create_app
from server.config import ServerConfig


# Hosts that mean "listen on every network this computer is on".
EVERY_NETWORK = ("0.0.0.0", "")
# Hosts that mean "this computer only": nothing else can connect, not even a phone.
THIS_COMPUTER_ONLY = ("127.0.0.1", "localhost")


# Ports below 1024 belong to the system; 65535 is the largest port number there is.
SMALLEST_PORT, LARGEST_PORT = 1024, 65535

HOW_TO_CHOOSE_A_PORT = (
    "\nChoose a port for the server. It must be given every time, for example:\n\n"
    "    py run_server.py --port 23634\n\n"
    f"Any free number from {SMALLEST_PORT} to {LARGEST_PORT} will do.\n"
)


def read_command_line(defaults: ServerConfig, command_line: Optional[list[str]] = None) -> ServerConfig:
    """The configuration for this run. Stops with an explanation if no usable port was given.

    command_line is what was typed after the program's name; left out, it is read from the
    real command line.
    """
    parser = argparse.ArgumentParser(description="Starts the Smart Screen web server.")
    parser.add_argument("--port", type=int,
                        help=f"the port to listen on, {SMALLEST_PORT} to {LARGEST_PORT} (required)")
    parser.add_argument("--host", default=defaults.host,
                        help="the address to listen on (default: every network this computer is on)")
    arguments = parser.parse_args(command_line)

    if arguments.port is None:
        sys.exit(HOW_TO_CHOOSE_A_PORT)
    if not SMALLEST_PORT <= arguments.port <= LARGEST_PORT:
        sys.exit(f"\n{arguments.port} cannot be a port here.\n" + HOW_TO_CHOOSE_A_PORT)
    return replace(defaults, host=arguments.host, port=arguments.port)


# How long to wait for an answer when checking whether a program already holds the port.
ANSWER_WAIT_SECONDS = 0.5


def something_already_answers(port: int, addresses: tuple = ("127.0.0.1", "::1")) -> bool:
    """Is a program on this computer already accepting connections on this port?

    Both forms of "localhost" are tried: the old one (127.0.0.1) and the new one (::1).
    A browser that is given "localhost" tries the new form first.
    """
    for address in addresses:
        try:
            with socket.create_connection((address, port), timeout=ANSWER_WAIT_SECONDS):
                return True
        except OSError:
            continue
    return False


def why_port_cannot_be_used(host: str, port: int) -> Optional[str]:
    """The reason the server cannot listen on this port, or None if it can.

    Checked before the server starts. Two checks, because on Windows the second one alone can
    pass while another program holds the port:

    1. Does something already answer on localhost at this port? Windows lets our server
       start next to a program that listens on localhost only (a port forwarded by an editor
       or by a container tool, for example). The browser would then reach that program and
       not our server, and the page would load forever.
    2. Can the port be opened at all?
    """
    listens_on_localhost = host in EVERY_NETWORK or host in THIS_COMPUTER_ONLY
    already_answering = something_already_answers(port) if listens_on_localhost \
        else something_already_answers(port, addresses=(host,))
    if already_answering:
        return "another program already answers on it"

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if os.name != "nt":
            # On Linux and macOS a port stays "busy" for a short while after a server stops.
            # This setting says that is fine, as the server itself does; a port that another
            # program is listening on is still refused.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind((host, port))
    except OSError as problem:
        return str(problem)
    finally:
        probe.close()
    return None


def port_in_use_message(port: int, reason: str) -> str:
    return (
        f"\nPort {port} cannot be used on this computer ({reason}).\n"
        "Another program may be using it (a port that an editor or a container tool forwards\n"
        "counts too), or Windows may have set it aside.\n"
        f"Start the server on another port, for example:  py run_server.py --port {port + 1}\n"
    )


def addresses_of_this_computer() -> list[str]:
    """This computer's addresses on the networks it is on, for typing into a phone."""
    try:
        found = socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
    except OSError:
        return []
    return sorted({entry[4][0] for entry in found if not entry[4][0].startswith("127.")})


def where_to_open(config: ServerConfig, computer_addresses: list[str]) -> tuple[str, list[str]]:
    """The address to open on this computer, and the addresses a phone can use.

    Which addresses work depends on where the server listens. Told to listen on one address
    only, it answers on that address and on no other: "localhost" then does NOT work, even on
    this computer.
    """
    if config.host in EVERY_NETWORK:
        return f"http://localhost:{config.port}", [f"http://{a}:{config.port}" for a in computer_addresses]
    if config.host in THIS_COMPUTER_ONLY:
        return f"http://localhost:{config.port}", []
    only_address = f"http://{config.host}:{config.port}"
    return only_address, [only_address]


def print_where_to_open(config: ServerConfig) -> None:
    on_this_computer, for_a_phone = where_to_open(config, addresses_of_this_computer())
    print()
    print("Smart Screen server is running. Stop it with Ctrl+C.")
    print(f"  On this computer:  {on_this_computer}")
    for address in for_a_phone:
        print(f"  The device page:   {address}/device")
    if config.host in THIS_COMPUTER_ONLY:
        print("  Other devices cannot connect: the server listens on this computer only.")
    elif config.host not in EVERY_NETWORK:
        print(f"  It listens on {config.host} only, so http://localhost:{config.port} will not work.")
    print()


def main() -> None:
    config = read_command_line(ServerConfig())
    reason = why_port_cannot_be_used(config.host, config.port)
    if reason is not None:
        sys.exit(port_in_use_message(config.port, reason))
    app = create_app(config)
    print_where_to_open(config)
    # threaded=True: each connected page gets its own thread, so one page that keeps a
    # connection open does not block the others.
    app.run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()
