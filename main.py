import argparse
from uvicorn import run
from src.utils import log_info
from src.http_to_mcp import app_http

def main():
    parser = argparse.ArgumentParser(description="HTTP to MCP Bridge")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--http-port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--remote-url", type=str, required=True, help="Remote URL to connect to: http://127.0.0.1:8081")

    args = parser.parse_args()

    log_info(f"Starting HTTP server listening at {args.host}:{args.http_port} with remote URL: {args.remote_url}")
    app_http.remote_url = args.remote_url
    run("src.http_to_mcp:app_http", host=args.host, port=args.http_port, reload=args.reload)

if __name__ == "__main__":
    main()