"""
Dashboard API — returns seeded demo records for the live demo page.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/demo-runs", summary="Get all seeded demo runs for the dashboard")
async def get_demo_runs() -> dict:
    from app.services.cache import get_all_demo_runs
    records = get_all_demo_runs()
    return {
        "total": len(records),
        "runs": records,
    }


@router.get("/hospitals", summary="Get hospital master list")
async def get_hospitals() -> dict:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"))
    try:
        from seed_demo_data import ALL_HOSPITALS
        return {"total": len(ALL_HOSPITALS), "hospitals": ALL_HOSPITALS}
    except Exception:
        return {"total": 0, "hospitals": [], "error": "Seed data not available"}
