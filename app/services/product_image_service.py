from app.core.exceptions import NotFoundException, ValidationException
from app.services.product_service import _delete_image_from_storage
from app.utils.supabase_client import get_supabase

IMAGE_SELECT = "id, product_id, empresa_id, url, position, created_at"


async def list_product_images(empresa_id: str, product_id: str) -> list[dict]:
    """Lista imagens de um produto, ordenadas por position."""
    supabase = get_supabase()

    result = (
        supabase.table("product_images")
        .select(IMAGE_SELECT)
        .eq("product_id", product_id)
        .eq("empresa_id", empresa_id)
        .order("position", desc=False)
        .execute()
    )
    return result.data or []


async def get_product_image(empresa_id: str, image_id: str) -> dict:
    """Busca uma imagem por ID."""
    supabase = get_supabase()

    result = (
        supabase.table("product_images")
        .select(IMAGE_SELECT)
        .eq("id", image_id)
        .eq("empresa_id", empresa_id)
        .execute()
    )

    if not result.data:
        raise NotFoundException(f"Imagem '{image_id}' não encontrada")

    return result.data[0]


async def attach_product_image(
    empresa_id: str, product_id: str, url: str, position: int = 0
) -> dict:
    """Anexa uma imagem (já hospedada externamente) a um produto."""
    supabase = get_supabase()

    payload = {
        "empresa_id": empresa_id,
        "product_id": product_id,
        "url": url,
        "position": position,
    }
    result = supabase.table("product_images").insert(payload).execute()
    return result.data[0]


async def delete_product_image(empresa_id: str, image_id: str) -> None:
    """Remove a imagem do banco e do storage."""
    image = await get_product_image(empresa_id, image_id)

    _delete_image_from_storage(image.get("url"))

    get_supabase().table("product_images").delete().eq("id", image_id).eq(
        "empresa_id", empresa_id
    ).execute()


async def reorder_product_images(
    empresa_id: str, product_id: str, image_ids: list[str]
) -> list[dict]:
    """Reordena as imagens de um produto pela ordem dos IDs informados."""
    if not image_ids:
        raise ValidationException("Informe pelo menos um image_id")

    supabase = get_supabase()

    existing = await list_product_images(empresa_id, product_id)
    existing_ids = {img["id"] for img in existing}
    missing = [img_id for img_id in image_ids if img_id not in existing_ids]
    if missing:
        raise ValidationException(
            f"Imagens não pertencem ao produto: {', '.join(missing)}"
        )

    for index, image_id in enumerate(image_ids):
        supabase.table("product_images").update({"position": index}).eq(
            "id", image_id
        ).eq("product_id", product_id).eq("empresa_id", empresa_id).execute()

    return await list_product_images(empresa_id, product_id)
