from fastapi import APIRouter


router = APIRouter(
    tags=["Health"]
)


@router.get("/health")
def health_check():
    """
    Check whether the InsightsOps API is running.
    """

    return {
        "status": "healthy",
        "service": "InsightsOps API"
    }