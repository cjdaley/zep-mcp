import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from zep_cloud.client import Zep
from tools import register_all

load_dotenv()

api_key = os.environ.get("ZEP_API_KEY")
if not api_key:
    raise RuntimeError("ZEP_API_KEY environment variable is required")

zep = Zep(api_key=api_key)
mcp = FastMCP(name="zep-mcp")

toolsets = os.environ.get("ZEP_TOOLSETS", "memory,admin").split(",")
toolsets = [t.strip() for t in toolsets]
register_all(mcp, zep, toolsets)

if __name__ == "__main__":
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    app = mcp.http_app(transport="sse")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
