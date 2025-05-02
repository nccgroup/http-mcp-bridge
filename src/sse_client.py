# Based on: https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/sse.py

from typing import Any
from mcp.client.sse import sse_client
from mcp.types import JSONRPCMessage
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio import move_on_after, EndOfStream
from src.utils import log_info as raw_log_info
from src.utils import log_warning as raw_log_warning
from src.utils import log_error as raw_log_error
from src.utils import remove_headers

# Custom logging functions
def log_info(msg):
    return raw_log_info(f"[sse_client] {msg}")

def log_warning(msg):
    return raw_log_warning(f"[sse_client] {msg}")

def log_error(msg):
    return raw_log_error(f"[sse_client] {msg}")

# Extract the memory streams from the SSE client
async def extract_memory_streams(
    read_stream: MemoryObjectReceiveStream[JSONRPCMessage | Exception],
    write_stream: MemoryObjectSendStream[JSONRPCMessage],
):
    return read_stream, write_stream

# SSEClient class to handle SSE connections
class SSEClient:
    def __init__(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: float = 5,
        sse_read_timeout: float = 60 * 5,
    ):
        self.url = url
        self.headers = remove_headers(headers, ["Content-Length"])
        self.timeout = timeout
        self.sse_read_timeout = sse_read_timeout
        self.read_stream = None
        self.write_stream = None

    async def connect(self):
        log_error("Connecting to SSE server...")
        log_info(f"URL: {self.url}")
        log_info(f"Headers: {self.headers}")
        self._sse_context = sse_client(
            self.url,
            headers=self.headers,
            timeout=self.timeout,
            sse_read_timeout=self.sse_read_timeout,
        )
        log_error("SSE client context created")
        print(self._sse_context)
        streams = await self._sse_context.__aenter__()
        log_error("SSE streams created")
        self.read_stream, self.write_stream = await extract_memory_streams(*streams)
        log_error("SSE streams extracted")

    async def send(self, msg: str):
        if not self.write_stream:
            raise RuntimeError("SSEClient is not connected")
        
        json_message = JSONRPCMessage(msg)
        await self.write_stream.send(json_message)

    async def receive(self, wait_timeout: int = 1):
        log_info("Receiving message...")
        if not self.read_stream:
            raise RuntimeError("SSEClient is not connected")
        try:
            with move_on_after(wait_timeout) as cancel_scope:
                message = await self.read_stream.receive()
                log_info(f"Received message: {message}")
            # Verify if the message was received within the timeout
            if cancel_scope.cancel_called:
                log_warning("Message receive timed out")
                message = []

            # If the message is an exception, raise it
            if isinstance(message, Exception):
                raise message
            
            # Garanting that the message is a list
            if not isinstance(message, list):
                message = [message]

            # Parse the message to JSON
            for i in range(len(message)):
                if isinstance(message[i], JSONRPCMessage):
                    message[i] = message[i].dict()
                elif isinstance(message[i], Exception):
                    raise message[i]
                
            return message
        except EndOfStream:
            log_warning("End of stream reached")
            return []
        except Exception as e:
            log_error(f"Error receiving message: {e}")
            raise

    async def close(self):
        if self._sse_context:
            await self._sse_context.__aexit__(None, None, None)
            self._sse_context = None