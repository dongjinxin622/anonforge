import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


import uvicorn
from app.core.config import settings


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)