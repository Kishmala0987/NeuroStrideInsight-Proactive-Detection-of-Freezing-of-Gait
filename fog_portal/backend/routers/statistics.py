"""
Statistics router — GET /api/stats
Population-level aggregate analytics across all subjects.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession
from ..db.database import get_db
from ..services.crud import get_population_stats

router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("/")
def get_stats(db: DBSession = Depends(get_db)):
    stats = get_population_stats(db)
    return JSONResponse(stats)
