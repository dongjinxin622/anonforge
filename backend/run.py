import sys
import asyncio
import selectors

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    if sys.platform == "win32":
        # psycopg 要求 SelectorEventLoop，在 Windows 上显式指定
        loop = asyncio.SelectorEventLoop()
        config = uvicorn.Config("app.main:app", host=settings.host, port=settings.port, loop="asyncio")
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())
    else:
        uvicorn.run("app.main:app", host=settings.host, port=settings.port)