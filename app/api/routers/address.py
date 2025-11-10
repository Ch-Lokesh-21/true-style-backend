from fastapi import APIRouter, Depends
from typing import Dict
from app.api.deps import get_current_user
router = APIRouter()
from app.services.address import get_location_service

@router.get("/{pincode}", dependencies=[Depends(get_current_user)])
async def get_location(pincode: int)->Dict:
    return await get_location_service(pincode)