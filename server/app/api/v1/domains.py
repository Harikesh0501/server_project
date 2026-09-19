from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.domain import DomainCheckResponse
from app.services.domain_service import DomainService

router = APIRouter(prefix="/domains", tags=["Domains"])

@router.get("/check", response_model=DomainCheckResponse)
async def check_domain_availability(
    name: str = Query(..., min_length=1, max_length=63, description="Subdomain slug to verify"),
    db: AsyncSession = Depends(get_db)
):
    """
    Checks if a chosen subdomain is available for hosting.
    If already registered or reserved, returns available=False with user-friendly suggestions.
    """
    return await DomainService.check_availability(raw_name=name, db=db)
