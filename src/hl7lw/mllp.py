import socket
from typing import Optional, Callable

from .exceptions import MllpConnectionError


START_BYTE = b'\x0B'
END_BYTES = b'\x1C\x0D'
BUFSIZE = 4096
MAX_MESSAGE_SIZE = 1 * 1024 * 1024  # 1 MB is probably reasonable.


class MllpClient:
    """
    MllpClient provides a simple API for a client to talk to an server, whether an
    integration engine, a RIS, a HIS, a PACS, whatever it is.

    The main assumption made is that messages will be sent one at a time, over a
    single connection. Encryption is not currently supported.

    There is a 1MB limit for the messages out of the box to control the memory usage,
    this can be changed by setting `hl7lw.mllp.MAX_MESSAGE_SIZE` to another value.

    The basic usage goes like:

    c = MllpClient()
    c.connect(host="127.0.0.1", port=1234)
    c.send(message)
    ack = c.recv()
    c.close()

    """
    def __init__(self) -> None:
        self.socket: Optional[socket.socket] = None
        self.connected: bool = False
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.buffer: bytes = b''

    def is_connected(self) -> bool:
        """
        Used to check if connected.
        """
        return self.connected

    def close(self) -> None:
        """
        Close the connection, also resets the internal state.

        Raises an `MllpConnectionError` if called on a closed connection.
        """
        if self.connected:
            self.connected = False
            self.buffer = b''
            self.socket.close()
        else:
            raise MllpConnectionError("Not connected!")

    def connect(self, host: str, port: int) -> None:
        """
        Connect to an `host` and `port`. Host will be resolved and it resolves to
        multiple IPv4 or IPv6 addresses, they will all be tried before giving up,
        see `socked.create_connection()` for details.

        If already connected, the previous connection is closed and the new connection
        is then opened.

        Network related exceptions will get wrapped into an `MllpConnectionError` and
        then returned.
        """
        self.host = host
        self.port = port
        if self.connected:
            # If we were connected, reset the state.
            self.connected = False
            self.buffer = b''
            self.socket.close()
        try:
            self.socket = socket.create_connection((host, port))
        except TimeoutError as e:
            raise MllpConnectionError(f"Timed out trying to connect to {host}:{port}") from e
        except OSError as e:
            raise MllpConnectionError(f"Failed to connect to {host}:{port}") from e
        self.connected = True

    def send(self, message: bytes, auto_reconnect: bool = True) -> None:
        """
        Send a `message` over the connection.
        
        If not connected and the `auto_reconnect` option is enabled, `connect()` will be
        called with the last connection details used. If `connect()` had yet to be called,
        no connection details will be available and an `MllpConnectionError` will be
        raised instead.

        Should sending fail with an exception, the connection will be closed before the
        exception is re-raised as an `MllpConnectionError`. There's no way to know how
        much of the message was sent.

        MLLP framing is handled by the method.
        """
        if not self.connected:
            if auto_reconnect:
                if self.host is None or self.port is None:
                    raise MllpConnectionError("No host configured!")
                self.connect(host=self.host, port=self.port)
            else:
                raise MllpConnectionError("Not connected!")
        try:
            self.socket.sendall(START_BYTE + message + END_BYTES)
        except Exception as e:
            self.socket.close()
            self.connected = False
            self.buffer = b''
            raise MllpConnectionError("Failed to send message to client.") from e
    
    def recv(self) -> bytes:
        """
        Receive a message from the connection. If there's multiple messages to
        be read, this method needs to be called repeatedly. The method will block
        until a message is available.

        If the connection is not connected, an `MllpConnectionError` will be raised.

        If there's any network error, an `MllpConnectionError` will be raised.

        If a message being read exceeds the maximum size, an `MllpConnectionError`
        will be raised.

        Whenever an exception is raised, the connection will also be closed if it
        wasn't closed already.

        WARNING: You are responsible to use this method to consume the ACKs from
        the other system. If you do not consume the ACKs, eventually the network
        buffers will fill and the other side will block trying to send a ACK. If
        you write an application that loops sending messages and it keeps stalling
        it might be that you are not consumming the ACKs! 
        """
        if not self.connected:
            # No point in connecting. Clients aren't normally polling in MLLP.
            # Maybe if asynch ACKs are used? But this client implementation really
            # isn't that smart.
            raise MllpConnectionError("Not connected!")
        # self.buffer is for any excess bytes after last message. A busy sender that
        # does not expect ack can send messages fast enough they run into each other.
        buffer = self.buffer
        self.buffer = b''
        while True:
            try:
                # This is slow for very large messages.
                buffer += self.socket.recv(BUFSIZE)
            except Exception as e:
                self.connected = False
                self.socket.close()
                raise MllpConnectionError("Failed to read from socket, closing it.") from e
            start = buffer.find(START_BYTE)
            if start == -1:
                # This only happens if buffer is only junk, so get rid of it to minimize
                # memory footprint.
                buffer = b''
            elif start > 0:
                # START_BYTE at index 0 is expected normal when message is split
                buffer = buffer[start:]
            end = buffer.find(END_BYTES)
            if end != -1:
                message = buffer[:end]
                self.buffer = buffer[end:]
                return message[1:]  # Discard leading START_BYTE
            if len(buffer) > MAX_MESSAGE_SIZE:
                self.connected = False
                self.socket.close()
                raise MllpConnectionError(f"Maximum messages size {MAX_MESSAGE_SIZE} exceeded!")


class MllpServer:
    def __init__(self, port: int, callback: Callable[[bytes], bytes]) -> None:
        self.portb = port
        self.read_buffers: dict[socket.socket, bytes] = {}
        self.write_buffers: dict[socket.socket, bytes] = {}
        self.callback = callback
    
    def serve(self):
        while True:
            pass
