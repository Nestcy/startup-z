from fastapi import FastAPI
from app.api.routes import router as api_router
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup-stress-test-agent")

app = FastAPI(title="Startup Stress Test Agent - Desirability MVP")

app.include_router(api_router, prefix="")

@app.on_event("startup")
async def startup_event():
    logger.info("Startup Stress Test Agent starting up")
    # Could initialize shared resources here (cache, DB, etc.)
