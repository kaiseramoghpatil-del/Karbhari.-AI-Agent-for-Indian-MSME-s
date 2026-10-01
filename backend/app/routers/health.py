from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "karbhari-backend"}
