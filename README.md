# HTTP MCP Bridge

This project implements an HTTP server that acts as a bridge between HTTP/1.1 requests and Server-Sent Events (SSE) using the `mcp` python library ([GitHub](https://github.com/modelcontextprotocol/python-sdk/)).

The main purpose of this initiative is to be able to use HTTP security tools to test remote MCP servers using the HTTP+SSE transport mechanism.

## Installation

To get started, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd http-mcp-bridge
pip install -r requirements.txt
```

## Running The Bridge

To run the HTTP server, execute the following command:

```bash
python3 main.py --remote-url="http://127.0.0.1:8787/sse"
```

The HTTP server will be listening in the default interface and port (`http://127.0.0.1:8000`), and the SEE connection will be established to the provided remote URL (`http://127.0.0.1:8787/sse`). A remote MCP server with HTTP+SSE support should exist in the given url.

You can then send HTTP requests to the server, which will relay them to the SSE clients.

## Remote MCP Servers (for testing purposes)

* [Cloudflare - Build a Remote MCP server](https://developers.cloudflare.com/agents/guides/remote-mcp-server/)

## Usage

The original HTTP+SSE mechanism establishes a read channel with the `/see` endpoint and a write channel with the `/messages/` endpoint. This HTTP to MCP Bridge forward HTTP requests to the write channel, and waits for the response (if applicable) in the read channel. Once received, that response is forwarded as the response of the HTTP request.

HTTP requests support the parameter `timeout`, which limits the maximum amount of seconds that the bridge waits for the response in the read channel before returning and error message. If timeout is zero, the HTTP to MCP Bridge does not wait at all.

### Obtaining Bridge Session ID

Since the HTTP to MCP Bridge supports several sessions with the MCP server, the first step is to obtain a session id, which will be used in further requests.

Request:
```http
GET /sse/messages HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
User-Agent: python-httpx/0.28.1
Content-Type: application/json
Cache-Control: no-store
Content-Length: 0
```

Response:
```http
HTTP/1.1 400 Bad Request
date: Fri, 02 May 2025 15:40:32 GMT
server: uvicorn
content-length: 87
content-type: application/json
```
```json
{"detail":"Invalid session id. Try /sse/messages/7fc2cce5-3b0b-4d63-9df6-e703c1df091c"}
```

This session id is different and independent than the session id established between the SSE client and the server. The latter is handled by the `mcp` library under the hood.

### Initialization Handshake

The first step in an MCP communication is the initialization handshake, where both peers share their available capabilities.

Request:
```http
POST /sse/messages/7fc2cce5-3b0b-4d63-9df6-e703c1df091c HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
User-Agent: python-httpx/0.28.1
Content-Type: application/json
Cache-Control: no-store
Authorization: Bearer [REDACTED]
Content-Length: 213
```
```json
{"method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"sampling": {}, "roots": {"listChanged": true}}, "clientInfo": {"name": "mcp", "version": "0.1.0"}}, "jsonrpc": "2.0", "id": 0}
```

Response:
```json
[{"jsonrpc":"2.0","id":0,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"Demo","version":"1.0.0"}}}]
```

### Handshake ACK Notification

The handshake needs to be closed using this message, which does not have a response, so we can use `timeout=0` at this time. We will receive a timeout error message, but that is expected.

Request:
```http
POST /sse/messages/7fc2cce5-3b0b-4d63-9df6-e703c1df091c?timeout=0 HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
User-Agent: python-httpx/0.28.1
Content-Type: application/json
Cache-Control: no-store
Authorization: Bearer [REDACTED]
Content-Length: 54
```
```json
{"method":"notifications/initialized","jsonrpc":"2.0"}
```

Response:
```json
{"message":"Timeout waiting for messages"}
```

### Tool Listing

Once the handshake has been completed, we can invoke the methods available, such as `tools/list` (listing tools).

Request:
```http
POST /sse/messages/7fc2cce5-3b0b-4d63-9df6-e703c1df091c HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
User-Agent: python-httpx/0.28.1
Content-Type: application/json
Cache-Control: no-store
Authorization: Bearer [REDACTED]
Content-Length: 46
```
```json
{"method":"tools/list","jsonrpc":"2.0","id":1}
```

Response:
```json
[{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"add","inputSchema":{"type":"object","properties":{"a":{"type":"number"},"b":{"type":"number"}},"required":["a","b"],"additionalProperties":false,"$schema":"http://json-schema.org/draft-07/schema#"}}]}}]
```

### Tool Calling

Finally, we can invoke tools or make use of other capabilities.

Request:
```http
POST /sse/messages/7fc2cce5-3b0b-4d63-9df6-e703c1df091c HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
User-Agent: python-httpx/0.28.1
Content-Type: application/json
Cache-Control: no-store
Authorization: Bearer [REDACTED]
Content-Length: 100
```
```json
{"method":"tools/call","params":{"name":"add","arguments":{"a":1, "b":2 }},"jsonrpc":"2.0","id":2}
```

Response:
```json
[{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"3"}]}}]
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.