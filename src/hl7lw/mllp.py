import socket
from typing import Optional, Callable

from .exceptions import MllpConnectionError


START_BYTE = b'\x0B'
END_BYTES = b'\x1C\x0D'
BUFSIZE = 4096
MAX_MESSAGE_SIZE = 1 * 1024 * 1024  # 1 MB is probably reasonable.


class MllpClient:
    def __init__(self) -> None:
        self.socket: Optional[socket.socket] = None
        self.connected: bool = False
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.buffer: bytes = b''

    def close(self):
        if self.connected:
            self.connected = False
            self.buffer = b''
            self.socket.close()
        else:
            raise MllpConnectionError("Not connected!")

    def connect(self, host: str, port: int) -> None:
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
                buffer = b''
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
