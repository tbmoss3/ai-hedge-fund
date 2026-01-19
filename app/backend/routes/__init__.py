from fastapi import APIRouter

from app.backend.routes.hedge_fund import router as hedge_fund_router
from app.backend.routes.health import router as health_router
from app.backend.routes.storage import router as storage_router
from app.backend.routes.flows import router as flows_router
from app.backend.routes.flow_runs import router as flow_runs_router
from app.backend.routes.ollama import router as ollama_router
from app.backend.routes.language_models import router as language_models_router
from app.backend.routes.api_keys import router as api_keys_router
from app.backend.routes.inbox import router as inbox_router
from app.backend.routes.investments import router as investments_router
from app.backend.routes.analysts import router as analysts_router

# Main API router
api_router = APIRouter()

# Health routes at root level (for Railway healthcheck)
api_router.include_router(health_router, tags=["health"])

# Original routes (no prefix for backwards compatibility)
api_router.include_router(hedge_fund_router, tags=["hedge-fund"])
api_router.include_router(storage_router, tags=["storage"])
api_router.include_router(flows_router, tags=["flows"])
api_router.include_router(flow_runs_router, tags=["flow-runs"])
api_router.include_router(ollama_router, tags=["ollama"])
api_router.include_router(language_models_router, tags=["language-models"])
api_router.include_router(api_keys_router, tags=["api-keys"])

# Research routes with /api prefix (for Vercel frontend)
api_router.include_router(inbox_router, prefix="/api", tags=["inbox"])
api_router.include_router(investments_router, prefix="/api", tags=["investments"])
api_router.include_router(analysts_router, prefix="/api", tags=["analysts"])
