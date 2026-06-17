import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import UploadFile

from app.core.exceptions import NotFoundException, ValidationException
from app.utils.supabase_client import get_supabase

BUCKET = "lead-attachments"
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf"}
ALLOWED_MIME_PREFIXES = ("image/", "video/")

ATTACHMENT_SELECT = (
    "id, lead_id, empresa_id, file_name, file_path, url, "
    "mime_type, file_size, uploaded_by, created_at"
)


def _is_allowed_mime_type(mime_type: str) -> bool:
    if mime_type in ALLOWED_MIME_TYPES:
        return True
    return any(mime_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES)


def _validate_uploaded_by(empresa_id: str, user_uuid: str) -> None:
    if not user_uuid or not user_uuid.strip():
        raise ValidationException("Informe uploaded_by com o UUID do usuário")

    result = (
        get_supabase()
        .table("profiles")
        .select("uuid")
        .eq("uuid", user_uuid.strip())
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise ValidationException(
            f"Usuário '{user_uuid}' não encontrado nesta empresa"
        )


def _build_file_path(empresa_id: str, lead_id: str, file_name: str) -> str:
    safe_name = file_name.replace(" ", "_")
    return f"{empresa_id}/{lead_id}/{int(time.time() * 1000)}-{safe_name}"


def _get_public_url(file_path: str) -> str:
    return get_supabase().storage.from_(BUCKET).get_public_url(file_path)


def _delete_from_storage(file_path: str | None) -> None:
    if not file_path:
        return
    try:
        get_supabase().storage.from_(BUCKET).remove([file_path])
    except Exception:
        pass


def _delete_from_storage_by_url(url: str | None) -> None:
    if not url:
        return
    try:
        parsed = urlparse(url)
        marker = f"/{BUCKET}/"
        idx = parsed.path.find(marker)
        if idx == -1:
            return
        object_path = parsed.path[idx + len(marker):]
        if object_path:
            get_supabase().storage.from_(BUCKET).remove([object_path])
    except Exception:
        pass


def _log_attachment_history(
    *,
    lead_id: str,
    empresa_id: str,
    change_type: str,
    file_name: str,
    changed_by: str | None = None,
) -> None:
    try:
        entry = {
            "lead_id": lead_id,
            "empresa_id": empresa_id,
            "change_type": change_type,
            "changed_by": changed_by,
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"file_name": file_name},
        }
        get_supabase().table("lead_pipeline_history").insert(entry).execute()
    except Exception:
        pass


async def list_attachments(empresa_id: str, lead_id: str) -> list[dict]:
    """Lista anexos de um lead, ordenados por data de criação (mais recentes primeiro)."""
    result = (
        get_supabase()
        .table("lead_attachments")
        .select(ATTACHMENT_SELECT)
        .eq("lead_id", lead_id)
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_attachment(
    empresa_id: str, lead_id: str, attachment_id: str
) -> dict:
    """Busca um anexo por ID."""
    result = (
        get_supabase()
        .table("lead_attachments")
        .select(ATTACHMENT_SELECT)
        .eq("id", attachment_id)
        .eq("lead_id", lead_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Anexo '{attachment_id}' não encontrado")

    return result.data[0]


async def upload_attachment(
    empresa_id: str,
    lead_id: str,
    file: UploadFile,
    uploaded_by: str,
) -> dict:
    """Faz upload de um arquivo para o storage e registra metadados no banco."""
    _validate_uploaded_by(empresa_id, uploaded_by)

    file_name = file.filename or "arquivo"
    mime_type = file.content_type or "application/octet-stream"
    file_bytes = await file.read()

    if len(file_bytes) > MAX_ATTACHMENT_SIZE:
        raise ValidationException("O arquivo excede o limite de 20MB.")

    if not _is_allowed_mime_type(mime_type):
        raise ValidationException(
            "Tipo de arquivo não permitido. Envie PDF, imagem ou vídeo."
        )

    file_path = _build_file_path(empresa_id, lead_id, file_name)
    supabase = get_supabase()

    try:
        supabase.storage.from_(BUCKET).upload(
            file_path,
            file_bytes,
            file_options={
                "content-type": mime_type,
                "cache-control": "3600",
                "upsert": "false",
            },
        )
    except Exception as exc:
        raise ValidationException(f"Erro ao enviar arquivo: {exc}") from exc

    public_url = _get_public_url(file_path)

    payload = {
        "lead_id": lead_id,
        "empresa_id": empresa_id,
        "file_name": file_name,
        "file_path": file_path,
        "url": public_url,
        "mime_type": mime_type,
        "file_size": len(file_bytes),
        "uploaded_by": uploaded_by.strip(),
    }

    result = supabase.table("lead_attachments").insert(payload).execute()

    if not result.data:
        _delete_from_storage(file_path)
        raise ValidationException("Erro ao registrar anexo no banco de dados")

    attachment = result.data[0]

    _log_attachment_history(
        lead_id=lead_id,
        empresa_id=empresa_id,
        change_type="attachment_added",
        file_name=file_name,
        changed_by=uploaded_by.strip(),
    )

    return attachment


async def delete_attachment(
    empresa_id: str, lead_id: str, attachment_id: str
) -> None:
    """Remove um anexo do storage e do banco de dados."""
    attachment = await get_attachment(empresa_id, lead_id, attachment_id)

    _delete_from_storage_by_url(attachment.get("url"))
    _delete_from_storage(attachment.get("file_path"))

    get_supabase().table("lead_attachments").delete().eq(
        "id", attachment_id
    ).eq("lead_id", lead_id).eq("empresa_id", empresa_id).execute()

    _log_attachment_history(
        lead_id=lead_id,
        empresa_id=empresa_id,
        change_type="attachment_removed",
        file_name=attachment.get("file_name", ""),
    )
