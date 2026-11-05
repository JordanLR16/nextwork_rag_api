import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..config import Settings
from ..dependencies import get_settings

router = APIRouter(prefix="/api/countries", tags=["geography"])


@router.get("")
def get_countries(settings: Settings = Depends(get_settings)):
    if not settings.countries_file.is_file():
        raise HTTPException(status_code=503, detail="Countries data not available")
    return FileResponse(settings.countries_file, media_type="application/geo+json")


@router.get("/{country_code}/regions")
def get_country_regions(country_code: str, settings: Settings = Depends(get_settings)):
    country_code = country_code.upper()
    if not re.fullmatch(r"[A-Z]{3}", country_code):
        raise HTTPException(status_code=400, detail="Expected a three-letter country code")
    regions_file = settings.regions_dir / country_code / "regions.geojson"
    if not regions_file.is_file():
        raise HTTPException(status_code=404, detail="Regions data not available for this country")
    return FileResponse(regions_file, media_type="application/geo+json")
