from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from sqlalchemy import text

from app.backend.routes import api_router
from app.backend.database.connection import engine
from app.backend.database.models import Base
from app.backend.models.watchlist import Watchlist  # Import to register model with Base
from app.backend.services.ollama_service import ollama_service
from app.backend.services.scheduler_service import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Hedge Fund API", description="Backend API for AI Hedge Fund", version="0.1.0")

# Initialize database tables (this is safe to run multiple times)
Base.metadata.create_all(bind=engine)


def run_migrations():
    """Run database migrations to add missing columns."""
    migrations = [
        "ALTER TABLE memos ADD COLUMN IF NOT EXISTS catalysts JSON;",
        "ALTER TABLE memos ADD COLUMN IF NOT EXISTS conviction_breakdown JSON;",
        "ALTER TABLE memos ADD COLUMN IF NOT EXISTS macro_context JSON;",
        "ALTER TABLE memos ADD COLUMN IF NOT EXISTS position_sizing JSON;",
    ]

    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Migration OK: {sql[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.info(f"Column already exists, skipping")
                else:
                    logger.warning(f"Migration warning: {e}")


# Run migrations on startup
try:
    run_migrations()
    logger.info("Database migrations completed")
except Exception as e:
    logger.warning(f"Could not run migrations: {e}")


@app.get("/api/migrate", tags=["admin"])
async def trigger_migration():
    """Manually trigger database migrations."""
    try:
        run_migrations()
        return {"status": "success", "message": "Migrations completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Configure CORS - allow all Vercel preview URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Startup event to check Ollama availability and start scheduler."""
    # Start the scheduler for monthly scans
    try:
        start_scheduler()
        logger.info("✓ Scheduler started - monthly scans enabled")
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")

    # Check Ollama availability
    try:
        logger.info("Checking Ollama availability...")
        status = await ollama_service.check_ollama_status()

        if status["installed"]:
            if status["running"]:
                logger.info(f"✓ Ollama is installed and running at {status['server_url']}")
                if status["available_models"]:
                    logger.info(f"✓ Available models: {', '.join(status['available_models'])}")
                else:
                    logger.info("ℹ No models are currently downloaded")
            else:
                logger.info("ℹ Ollama is installed but not running")
                logger.info("ℹ You can start it from the Settings page or manually with 'ollama serve'")
        else:
            logger.info("ℹ Ollama is not installed. Install it to use local models.")
            logger.info("ℹ Visit https://ollama.com to download and install Ollama")

    except Exception as e:
        logger.warning(f"Could not check Ollama status: {e}")
        logger.info("ℹ Ollama integration is available if you install it later")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event to stop scheduler."""
    try:
        stop_scheduler()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")
