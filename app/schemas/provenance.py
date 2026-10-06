from pydantic import BaseModel, Field


class ProvenanceMetadata(BaseModel):
    filename: str | None = None
    size_bytes: int | None = None
    supplied_content_type: str | None = None
    content_type: str | None = None
    created_at: str | None = None
    modified_at: str | None = None
    software: str | None = None
    producer: str | None = None
    embedded: dict[str, str] = Field(default_factory=dict)


class ProvenanceResponse(BaseModel):
    available: bool
    provenance_present: bool | None = None
    c2pa_present: bool | None = None
    c2pa_verified: bool | None = None
    metadata: ProvenanceMetadata
    signals: dict[str, bool | None]
    warnings: list[str]
