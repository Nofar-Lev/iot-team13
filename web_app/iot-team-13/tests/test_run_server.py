"""Starting the server: choosing the port, checking that it is free, and the addresses printed."""
import socket
from dataclasses import replace

import pytest

from run_server import (
    port_in_use_message, read_command_line, something_already_answers, where_to_open,
    why_port_cannot_be_used,
)
from server.config import ServerConfig

THIS_COMPUTER = "127.0.0.1"


@pytest.fixture
def port_taken_by_another_program():
    """A port that something is listening on, for as long as the test runs."""
    with socket.socket() as other_program:
        other_program.bind((THIS_COMPUTER, 0))   # 0 asks the system for any free port
        other_program.listen()
        yield other_program.getsockname()[1]


def a_free_port() -> int:
    with socket.socket() as probe:
        probe.bind((THIS_COMPUTER, 0))
        return probe.getsockname()[1]


def test_a_free_port_can_be_used():
    assert why_port_cannot_be_used(THIS_COMPUTER, a_free_port()) is None


def test_a_port_that_another_program_listens_on_cannot_be_used(port_taken_by_another_program):
    reason = why_port_cannot_be_used(THIS_COMPUTER, port_taken_by_another_program)
    assert reason


def test_a_program_that_listens_on_localhost_only_is_noticed(port_taken_by_another_program):
    # On Windows our server could start next to such a program, and the browser would then
    # reach that program and wait forever. So the check asks "does something answer?" first.
    assert something_already_answers(port_taken_by_another_program)
    reason = why_port_cannot_be_used("0.0.0.0", port_taken_by_another_program)
    assert reason == "another program already answers on it"


def test_nothing_answers_on_a_free_port():
    assert not something_already_answers(a_free_port())


def test_checking_a_port_does_not_keep_it(port_taken_by_another_program):
    free_port = a_free_port()
    assert why_port_cannot_be_used(THIS_COMPUTER, free_port) is None
    assert why_port_cannot_be_used(THIS_COMPUTER, free_port) is None   # still free the second time


def test_the_message_names_the_port_and_suggests_another():
    message = port_in_use_message(23633, "address already in use")
    assert "Port 23633" in message
    assert "--port 23634" in message


# --- Choosing the port --------------------------------------------------------------------------

def test_the_port_given_on_the_command_line_is_used():
    config = read_command_line(ServerConfig(), ["--port", "23634"])
    assert config.port == 23634
    assert config.host == ServerConfig().host


def test_there_is_no_default_port():
    assert ServerConfig().port is None


def test_starting_without_a_port_stops_and_explains_how_to_choose_one():
    with pytest.raises(SystemExit) as stopped:
        read_command_line(ServerConfig(), [])
    message = str(stopped.value)
    assert "Choose a port" in message
    assert "--port" in message


def test_a_host_alone_is_not_enough():
    with pytest.raises(SystemExit) as stopped:
        read_command_line(ServerConfig(), ["--host", "127.0.0.1"])
    assert "Choose a port" in str(stopped.value)


@pytest.mark.parametrize("not_a_usable_port", ["0", "80", "1023", "65536", "-5"])
def test_a_number_that_cannot_be_a_port_is_refused(not_a_usable_port):
    with pytest.raises(SystemExit) as stopped:
        read_command_line(ServerConfig(), ["--port", not_a_usable_port])
    assert "cannot be a port" in str(stopped.value)


@pytest.mark.parametrize("usable_port", ["1024", "8080", "65535"])
def test_the_whole_range_of_ordinary_ports_is_accepted(usable_port):
    assert read_command_line(ServerConfig(), ["--port", usable_port]).port == int(usable_port)


# --- The addresses printed at the start ---------------------------------------------------------

# The configuration as it is once a port was chosen.
WITH_A_PORT = replace(ServerConfig(), port=23633)

def test_listening_everywhere_means_localhost_here_and_every_address_for_a_phone():
    on_this_computer, for_a_phone = where_to_open(WITH_A_PORT, ["192.168.1.20", "100.64.0.10"])
    assert on_this_computer == "http://localhost:23633/iot-team-13"
    assert for_a_phone == ["http://192.168.1.20:23633/iot-team-13", "http://100.64.0.10:23633/iot-team-13"]


def test_listening_on_one_address_means_localhost_does_not_work():
    one_network = replace(WITH_A_PORT, host="100.64.0.10")
    on_this_computer, for_a_phone = where_to_open(one_network, ["192.168.1.20", "100.64.0.10"])
    assert on_this_computer == "http://100.64.0.10:23633/iot-team-13"
    assert for_a_phone == ["http://100.64.0.10:23633/iot-team-13"]


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_listening_on_this_computer_only_offers_no_address_for_a_phone(host):
    on_this_computer, for_a_phone = where_to_open(replace(WITH_A_PORT, host=host), ["192.168.1.20"])
    assert on_this_computer == "http://localhost:23633/iot-team-13"
    assert for_a_phone == []


def test_an_app_at_the_top_of_the_address_is_printed_without_a_path():
    on_this_computer, for_a_phone = where_to_open(replace(WITH_A_PORT, app_path=""), ["192.168.1.20"])
    assert on_this_computer == "http://localhost:23633"
    assert for_a_phone == ["http://192.168.1.20:23633"]
