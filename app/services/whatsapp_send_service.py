"""Serviço de integração com o webhook n8n para envio de mensagens WhatsApp.

Mantém a integração externa isolada do CRUD do chat (`chat_service`),
facilitando evoluções futuras (retry, circuit-breaker, fila assíncrona, etc.).
"""

from __future__ import annotations

import random
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services import chat_service


def _generate_alet_num() -> int:
    """Gera um número aleatório de 6 dígitos (compatível com o CRM)."""
    return random.randint(100000, 999999)


def _build_webhook_payload(
    *,
    empresa_id: str,
    conversation_id: str,
    instance_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Monta o body enviado ao webhook n8n (mesmo formato do CRM)."""
    media_url = payload.get("media_url")
    return {
        "action": "send_message",
        "conversation_id": conversation_id,
        "instance_id": instance_id,
        "message_type": payload.get("message_type", "text"),
        "content": payload.get("content"),
        "media_url": str(media_url) if media_url is not None else None,
        "empresa_id": empresa_id,
        "alet_num": _generate_alet_num(),
    }


def _parse_webhook_response(response: httpx.Response) -> dict[str, Any] | None:
    """Tenta decodificar a resposta do webhook como JSON; senão devolve `None`."""
    try:
        data = response.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else {"data": data}


async def send_whatsapp_message(
    empresa_id: str,
    conversation_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Dispara o webhook n8n responsável pelo envio da mensagem.

    Fluxo:
        1. Valida o tenant + carrega a conversa via `chat_service.get_conversation`.
        2. Garante que a conversa tenha `instance_id` vinculado.
        3. Faz POST no webhook configurado em `N8N_WEBHOOK_SEND_MESSAGE_URL`.
        4. Mapeia erros de timeout (504) e respostas não-2xx (502).
    """
    conversation = await chat_service.get_conversation(empresa_id, conversation_id)

    instance_id = conversation.get("instance_id")
    if not instance_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Conversa não possui `instance_id` vinculado; impossível enviar "
                "mensagem via WhatsApp."
            ),
        )

    settings = get_settings()
    body = _build_webhook_payload(
        empresa_id=empresa_id,
        conversation_id=conversation_id,
        instance_id=instance_id,
        payload=payload,
    )

    try:
        async with httpx.AsyncClient(
            timeout=settings.N8N_WEBHOOK_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(
                settings.N8N_WEBHOOK_SEND_MESSAGE_URL,
                json=body,
                headers={"Accept": "application/json"},
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout ao contatar o webhook do n8n.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao contatar o webhook do n8n: {exc}",
        ) from exc

    webhook_response = _parse_webhook_response(response)

    if response.is_error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Webhook n8n respondeu com erro.",
                "status_code": response.status_code,
                "webhook_response": webhook_response,
            },
        )

    return {
        "status": "sent",
        "webhook_response": webhook_response,
        "error": None,
    }
