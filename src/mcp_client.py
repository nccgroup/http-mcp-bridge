# Based on: https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/sse.py
# And: https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/streamable_http.py

from typing import Any, Literal
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import JSONRPCMessage
from mcp.shared.message import SessionMessage
from anyio import move_on_after, EndOfStream
from src.utils import log_info as raw_log_info
from src.utils import log_warning as raw_log_warning
from src.utils import log_error as raw_log_error
from src.utils import remove_headers

# Custom logging functions
def log_info(msg):
    return raw_log_info(f"[mcp_client] {msg}")

def log_warning(msg):
    return raw_log_warning(f"[mcp_client] {msg}")

def log_error(msg):
    return raw_log_error(f"[mcp_client] {msg}")

STREAMABLE_HTTP = 1
HTTP_SSE = 2
MCPTransport = Literal[STREAMABLE_HTTP, HTTP_SSE]

# MCPclient class to handle MCP connections
class MCPclient:
    def __init__(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: float = 5,
        read_timeout: float = 60 * 5,
        autodetect_transport: bool = True,
        deprecated_sse_transport: bool = False,
    ):
        self.url = url
        self.headers = remove_headers(headers, ["Content-Length"])
        self.timeout = timeout
        self.read_timeout = read_timeout
        self.read_stream = None
        self.write_stream = None
        self.autodetect_transport = autodetect_transport
        self.deprecated_sse_transport = deprecated_sse_transport

    async def _get_mcp_streams(self, deprecated_sse_transport):
        self._mcp_context, self.read_stream, self.write_stream = None, None, None

        if deprecated_sse_transport:
            self._mcp_context = sse_client(
                self.url,
                headers=self.headers,
                timeout=self.timeout,
                sse_read_timeout=self.read_timeout,
            )
            self.read_stream, self.write_stream = await self._mcp_context.__aenter__()
        else:
            self._mcp_context = streamablehttp_client(
                self.url,
                headers=self.headers,
                timeout=self.timeout,
                sse_read_timeout=self.read_timeout,
            )
            self.read_stream, self.write_stream, _ = await self._mcp_context.__aenter__()

    async def _try_transport_mechanism(self, transport: MCPTransport):
        await self._get_mcp_streams(transport == HTTP_SSE)

        # Send and Receive Ping
        try:
            await self.send({'method': 'ping', 'jsonrpc': '2.0', 'id': 0})
            await self.receive(3)
        except:
            return False
        finally:
            await self.close()
        
        return True

    async def connect(self):
        log_info("Connecting to MCP server...")
        log_info(f"URL: {self.url}")
        log_info(f"Headers: {self.headers}")

        if self.autodetect_transport:
            self.autodetect_transport = False
            if await self._try_transport_mechanism(STREAMABLE_HTTP):
                log_info("Streamable HTTP Transport")
                self.deprecated_sse_transport = False
            elif await self._try_transport_mechanism(HTTP_SSE):
                log_warning("SSE Transport (Deprecated)")
                self.deprecated_sse_transport = True
            else:
                log_error("Unknown Transport Mechanism")

        await self._get_mcp_streams(self.deprecated_sse_transport)
        log_info("MCP streams created")

    async def send(self, msg: str):
        if not self.write_stream:
            raise RuntimeError("MCPclient is not connected")
        
        session_message = SessionMessage(JSONRPCMessage(msg))
        await self.write_stream.send(session_message)

    async def receive(self, wait_timeout: int = 1):
        log_info("Receiving message...")
        if not self.read_stream:
            raise RuntimeError("MCPclient is not connected")
        try:
            message = []
            with move_on_after(wait_timeout) as cancel_scope:
                message = await self.read_stream.receive()
                log_info(f"Received message: {message}")

                # If the message is an exception, raise it
                if isinstance(message, Exception):
                    raise message
                
                # Garanting that the message is a list
                if not isinstance(message, list):
                    message = [message]

                # Parse the message to JSON
                for i in range(len(message)):
                    if isinstance(message[i], SessionMessage):
                        message[i] = message[i].message.dict()
                    elif isinstance(message[i], Exception):
                        raise message[i]
                    
                return message
                
            # Verify if the message was received within the timeout
            if cancel_scope.cancel_called:
                log_warning("Message receive timed out")
                message = []

            return message
        except EndOfStream:
            log_warning("End of stream reached")
            return []
        except Exception as e:
            log_error(f"Error receiving message: {e}")
            raise

    async def close(self):
        if self.write_stream:
            try:
                await self.write_stream.aclose()
            except Exception as e:
                log_error(f"Error closing write stream: {e}")
            self.write_stream = None
        if self.read_stream:
            try:
                await self.read_stream.aclose()
            except Exception as e:
                log_error(f"Error closing read stream: {e}")
            self.read_stream = None
        if self._mcp_context:
            try:
                await self._mcp_context.__aexit__(None, None, None)
            except Exception as e:
                log_error(f"Error closing MCP context: {e}")
            self._mcp_context = None