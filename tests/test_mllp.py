import pytest
from unittest.mock import call
from src.hl7lw.mllp import MllpClient, MllpServer, START_BYTE, END_BYTES
from src.hl7lw.exceptions import MllpConnectionError


def test_client_connect(mocker) -> None:
    c = MllpClient()
    sentinel_socket = object()
    mock_create_connection = mocker.patch("socket.create_connection", return_value=sentinel_socket)
    c.connect(host='test', port=1234)
    mock_create_connection.assert_called_once_with(('test', 1234))
    assert c.socket is sentinel_socket
    assert c.connected
    assert c.host == 'test'
    assert c.port == 1234


def test_client_connect_timeout(mocker) -> None:
    c = MllpClient()
    e = TimeoutError("test")
    mock_create_connection = mocker.patch("socket.create_connection", side_effect=e)
    with pytest.raises(MllpConnectionError, match=r'^Timed out trying.*'):
        c.connect(host='test', port=1234)
    mock_create_connection.assert_called_once_with(('test', 1234))


def test_client_connect_error(mocker) -> None:
    c = MllpClient()
    e = OSError("test")
    mock_create_connection = mocker.patch("socket.create_connection", side_effect=e)
    with pytest.raises(MllpConnectionError, match=r'^Failed to connect to test:1234'):
        c.connect(host='test', port=1234)
    mock_create_connection.assert_called_once_with(('test', 1234))


def test_get_message(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mock_socket.recv.return_value = START_BYTE + trivial_a08 + END_BYTES
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    received = c.recv()
    assert received == trivial_a08


def test_get_message_fragmented(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mock_socket.recv.side_effect = [START_BYTE + trivial_a08[:100], trivial_a08[100:] + END_BYTES]
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    received = c.recv()
    assert received == trivial_a08


def test_get_message_junk_before_and_after(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mock_socket.recv.side_effect = [
        b"junk" + END_BYTES + b"junk",
        b"more_junk" + START_BYTE + trivial_a08[:100],
        trivial_a08[100:] + END_BYTES + b"even more junk",
        b"excess junk",
    ]
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    received = c.recv()
    assert received == trivial_a08
    assert mock_socket.recv.call_count == 3


def test_send_message(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    c.send(trivial_a08)
    assert mock_socket.sendall.call_args == call(START_BYTE + trivial_a08 + END_BYTES)