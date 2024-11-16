import socket
from typing import Optional, Callable

from .exceptions import MllpConnectionError


START_BYTE = b'\x0B'
END_BYTES = b'\x1C\x0D'
BUFSIZE = 4096


class MllpClient:
    def __init__(self) -> None:
        self.socket: Optional[socket.socket] = None
        self.connected: bool = False
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.buffer: bytes = b''
    
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
            raise e
    
    def recv(self) -> bytes:
        buffer = self.buffer
        start = buffer.find(START_BYTE)
        if start != -1:
            buffer = buffer[start:]
        else:
            buffer = b''
        while True:
            try:
                buffer += self.socket.recv(BUFSIZE)
            except Exception as e:
                self.buffer = b''
                self.connected = False
                self.socket.close()
                raise e
            if start == -1:
                start = buffer.find(START_BYTE)
                if start == -1:
                    buffer = b''
                else:
                    buffer = buffer[start:]
            end = buffer.find(END_BYTES)
            if end != -1:
                message = buffer[:end]
                self.buffer = buffer[end:]
                return message[1:]  # Discard leading START_BYTE


class MllpServer:
    def __init__(self, port: int, callback: Callable[[bytes], bytes]) -> None:
        self.portb = port
        self.read_buffers: dict[socket.socket, bytes] = {}
        self.write_buffers: dict[socket.socket, bytes] = {}
        self.callback = callback
    
    def serve(self):
        while True:
            pass
