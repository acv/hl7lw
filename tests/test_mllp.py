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


def test_client_connect_twice(mocker) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mock_create_connection = mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    c.connect(host='test2', port=1234)
    assert mock_create_connection.call_count == 2
    assert mock_socket.close.called
    assert mock_socket.close.call_count == 1
    assert c.connected
    assert c.host == 'test2'
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


def test_get_message_exception(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    e = OSError("socket")
    mock_socket = mocker.patch('socket.socket')
    mock_socket.recv.side_effect = [START_BYTE + trivial_a08, e]
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    with pytest.raises(MllpConnectionError, match=r'^Failed to read from socket, closing it.'):
        c.recv()
    assert mock_socket.recv.call_count == 2


def test_get_message_no_connected(mocker) -> None:
    c = MllpClient()
    with pytest.raises(MllpConnectionError, match=r'^Not connected!'):
        c.recv()


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


def test_two_messages_in_one_packet(mocker) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mock_socket.recv.return_value = START_BYTE + b"message1" + END_BYTES + START_BYTE + b"message2" + END_BYTES
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    received1 = c.recv()
    received2 = c.recv()
    assert received1 == b"message1"
    assert received2 == b"message2"


def test_send_message(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    c.send(trivial_a08)
    assert mock_socket.sendall.call_args == call(START_BYTE + trivial_a08 + END_BYTES)


def test_send_message_not_connected_default(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    assert c.connected == True
    c.close()
    assert mock_socket.close.called
    assert c.connected == False
    c.send(trivial_a08)
    assert mock_socket.sendall.call_args == call(START_BYTE + trivial_a08 + END_BYTES)


def test_close_unopened():
    c = MllpClient()
    with pytest.raises(MllpConnectionError, match=r'^Not connected!'):
        c.close()


def test_send_message_not_connected_no_auto_reconnect(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    mock_socket = mocker.patch('socket.socket')
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    assert c.connected == True
    c.close()
    assert mock_socket.close.called
    assert c.connected == False
    with pytest.raises(MllpConnectionError, match=r'^Not connected!'):
        c.send(trivial_a08, auto_reconnect=False)


def test_send_message_never_connected_default(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    with pytest.raises(MllpConnectionError, match=r'^No host configured!'):
        c.send(trivial_a08)


def test_send_message_exception(mocker, trivial_a08: bytes) -> None:
    c = MllpClient()
    e = OSError("socket")
    mock_socket = mocker.patch('socket.socket')
    mock_socket.sendall.side_effect = e
    mocker.patch("socket.create_connection", return_value=mock_socket)
    c.connect(host='test', port=1234)
    with pytest.raises(MllpConnectionError, match=r'^Failed to send message to client.'):
        c.send(trivial_a08)
