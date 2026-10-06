from fastapi import APIRouter, File, UploadFile

from app.schemas.provenance import ProvenanceResponse
from app.services.provenance import analyze_provenance


router = APIRouter(tags=["Provenance"])


@router.post("/provenance/analyze", response_model=ProvenanceResponse)
def analyze_uploaded_provenance(file: UploadFile = File(...)):
    return analyze_provenance(
        file.file,
        filename=file.filename,
        supplied_content_type=file.content_type,
    )
