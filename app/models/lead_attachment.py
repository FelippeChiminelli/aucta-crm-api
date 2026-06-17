from pydantic import BaseModel


class LeadAttachmentResponse(BaseModel):
    """Anexo de arquivo vinculado a um lead."""

    id: str
    lead_id: str
    empresa_id: str
    file_name: str
    file_path: str
    url: str
    mime_type: str
    file_size: int
    uploaded_by: str
    created_at: str
