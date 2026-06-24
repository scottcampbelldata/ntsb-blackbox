from fastapi import APIRouter

from backend.app.context.gdelt import fetch_related_coverage

router = APIRouter(prefix="/api")


@router.get("/context")
async def context(
    make: str | None = None,
    model: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year: int | None = None,
):
    return await fetch_related_coverage(make=make, model=model, city=city, state=state, year=year)
