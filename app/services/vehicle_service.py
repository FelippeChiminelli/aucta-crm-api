from app.utils.supabase_client import get_supabase

VEHICLE_SELECT = (
    "id, external_id, titulo_veiculo, modelo_veiculo, marca_veiculo, "
    "ano_veiculo, ano_fabric_veiculo, color_veiculo, price_veiculo, "
    "promotion_price, accessories_veiculo, plate_veiculo, "
    "quilometragem_veiculo, cambio_veiculo, combustivel_veiculo, "
    "created_at, updated_at"
)

IMAGE_SELECT = "id, url, position"


async def list_vehicles(empresa_id: str) -> list[dict]:
    """Lista todos os veículos do estoque de uma empresa com imagens."""
    supabase = get_supabase()

    result = (
        supabase.table("vehicles")
        .select(f"{VEHICLE_SELECT}, vehicle_images({IMAGE_SELECT})")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .execute()
    )

    vehicles = result.data or []

    # Normalizar chave das imagens e ordenar por position
    for vehicle in vehicles:
        images = vehicle.pop("vehicle_images", []) or []
        images.sort(key=lambda img: img.get("position", 0))
        vehicle["images"] = images

    return vehicles
