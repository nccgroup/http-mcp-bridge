from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from src.mcp_client import MCPclient
from src.utils import log_info, log_warning
from uuid import uuid4

connections = {}  # Dictionary to store active connections by session ID

@asynccontextmanager
async def lifespan(app: FastAPI):
    log_info("Starting up...")
    try:
        yield
    finally:
        log_info("Shutting down...")
        for session_id, client in connections.items():
            log_info(f"Closing connection for session ID: {session_id}")
            if client:
                await client.close()

app_http = FastAPI(lifespan=lifespan)

@app_http.get("/mcp")
@app_http.get("/mcp/messages")
@app_http.post("/mcp/messages/{session_id}")
async def sync_messages_endpoint(request: Request, session_id: str = None):
    # Check if the session ID is provided in the URL and valid
    if (not session_id) or (session_id not in connections):
        session_id = str(uuid4())
        connections[session_id] = None
        raise HTTPException(status_code=400, detail=f"Invalid session id. Try /mcp/messages/{session_id}")

    # Check if the session ID is already in use    
    if connections[session_id]:
        client = connections[session_id]
        log_info(f"Reusing existing connection for session ID: {session_id}")
    else:
        client = MCPclient(url=app_http.remote_url, headers=request.headers, autodetect_transport=False)
        await client.connect()
        connections[session_id] = client
        log_info(f"New connection established for session ID: {session_id}")

    # Obtain the timeout parameter from the query string (default to 5 seconds)
    timeout = request.query_params.get("timeout", 5)
    try:
        timeout = int(timeout)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid 'timeout' parameter. It must be an integer.")

    # Process the incoming request
    try:
        json_body = await request.json()
        log_info(f"Received request body: {json_body}")
        await client.send(json_body)
    except Exception as e:
        log_warning(f"Failed to process request: {e}")
        raise HTTPException(status_code=500, detail="Failed to process request")
    
    # Read the response from the server until no more received
    try:
        events = await client.receive(timeout)
        if events:
            log_info(f"Received events: {events}")
            return events
        log_warning("Timeout waiting for messages")
        return {"message": "Timeout waiting for messages"}
    except Exception as e:
        log_warning(f"Error while receiving messages: {e}")
        return {"message": f"Error while receiving messages: {e}"}

