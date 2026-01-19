from .connection import get_db, engine, SessionLocal, Base
from .models import HedgeFundFlow, HedgeFundFlowRun, HedgeFundFlowRunCycle, ApiKey

__all__ = [
    "get_db",
    "engine",
    "SessionLocal",
    "Base",
    "HedgeFundFlow",
    "HedgeFundFlowRun",
    "HedgeFundFlowRunCycle",
    "ApiKey",
]


def register_research_models():
    """
    Lazy import research models to avoid circular imports.
    Call this after the app is fully initialized.
    """
    from app.backend.models.memo import Memo
    from app.backend.models.investment import Investment
    from app.backend.models.analyst_stats import AnalystStats
    return Memo, Investment, AnalystStats
