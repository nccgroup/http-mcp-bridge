import logging
from typing import Any

def log_info(msg):
    logging.getLogger("uvicorn.info").info(msg)

def log_warning(msg):
    logging.getLogger("uvicorn.info").warning(msg)

def log_error(msg):
    logging.getLogger("uvicorn.info").error(msg)

def remove_headers(headers: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    new_headers = dict(headers)
    for key in keys:
        key = key.lower()
        if key in new_headers:
            del new_headers[key]
    return new_headers

# FUNCTIONS FOR DEBUGGING RAW REQUESTS AND RESPONSES
async def log_request(request):
    print("\n=== RAW REQUEST ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Headers: {dict(request.headers)}")
    if hasattr(request, 'content'):
        print(f"Content: {request.content}")
    print()

async def log_response(response):
    print("=== RAW RESPONSE ===")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    # Only try to access content if it has been read
    try:
        if hasattr(response, 'is_stream_consumed') and response.is_stream_consumed:
            print(f"Content: {response.content[:500]}..." if len(response.content) > 500 else f"Content: {response.content}")
    except Exception as e:
        print(f"Content: <streaming - {e}>")
    print()