import os
import secrets

import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from zep_cloud.client import Zep

from tools import register_all

load_dotenv()

api_key = os.environ.get("ZEP_API_KEY")
if not api_key:
    raise RuntimeError("ZEP_API_KEY environment variable is required")

mcp_token = os.environ.get("ZEP_MCP_TOKEN")
if not mcp_token:
    raise RuntimeError("ZEP_MCP_TOKEN environment variable is required")

zep = Zep(api_key=api_key)
mcp = FastMCP(name="zep-mcp")

toolsets = os.environ.get("ZEP_TOOLSETS", "memory,admin").split(",")
toolsets = [t.strip() for t in toolsets]
register_all(mcp, zep, toolsets)


class BearerTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "GET" and request.url.path in ("/", "/health"):
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        provided = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if not provided or not secrets.compare_digest(provided, mcp_token):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


if __name__ == "__main__":
    app = mcp.http_app(transport="streamable-http")
    app.add_middleware(BearerTokenMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
