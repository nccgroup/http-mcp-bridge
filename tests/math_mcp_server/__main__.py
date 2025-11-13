import logging, argparse
from mcp.server.fastmcp import FastMCP

DEFAULT_PORT = 9981

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Math MCP Server")
    parser.add_argument("--sse", action="store_true", help="Force using deprecated HTTP+SSE transport")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Server port (default {DEFAULT_PORT})")
    args = parser.parse_args()

    if args.sse:
        transport = "sse"
    else:
        transport = "streamable-http"

    mcp = FastMCP(
        "math_server",
        host ="localhost",
        port = args.port,
        stateless_http = True
    )

    logger.info(f"MCP server ({transport}) started on port {args.port}")
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Shutting down...")

@mcp.tool(name = "add_two_numbers")
def add_numbers(a: float, b: float) -> float:
    """Use this to add two numbers together.
    
    Args:
        a: The first number to add.
        b: The second number to add.
    
    Returns:
        output(float): The output containing the result
    """
    result = a + b
    logger.info(f">>> Tool: 'add' called with numbers '{a}' and '{b}'")
    return result


@mcp.tool(name = "subtract_two_numbers")
def subtract_numbers(a: float, b: float) -> float:
    """Use this to subtract two numbers.
    
    Args:
        a: The first number to subtract.
        b: The second number to subtract.
    
    Returns:
        output(float): The output containing the result
    """

    result = a - b
    logger.info(f">>> Tool: 'subtract' called with numbers '{a}' and '{b}'")
    return result