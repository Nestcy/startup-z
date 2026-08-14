from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup-stress-test-agent")

app = FastAPI(title="Startup Stress Test Agent - Desirability MVP")

# Comma-separated list of allowed origins, e.g. "https://your-ai-studio-app.web.app,http://localhost:5173"
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="")

@app.on_event("startup")
async def startup_event():
    logger.info("Startup Stress Test Agent starting up")
    # Could initialize shared resources here (cache, DB, etc.)
