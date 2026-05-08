import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.whatsapp_inbox import WhatsAppInbox
from models.device import Device
from services.whatsapp_engine_service import WhatsAppEngineService
from services.uuid_service import UUIDService
from utils.phone_utils import normalize_phone

logger = logging.getLogger(__name__)


def _extract_messages(engine_payload: Any) -> List[Dict[str, Any]]:
    """
    Normalize engine responses into a list[dict].
    We support common shapes:
      - {"messages": [...]}
      - {"data": {"messages": [...]}}
      - {"data": [...]}
      - [...]
    """
    if engine_payload is None:
        return []
    if isinstance(engine_payload, list):
        return [m for m in engine_payload if isinstance(m, dict)]
    if isinstance(engine_payload, dict):
        if isinstance(engine_payload.get("messages"), list):
            return [m for m in engine_payload["messages"] if isinstance(m, dict)]
        data = engine_payload.get("data")
        if isinstance(data, list):
            return [m for m in data if isinstance(m, dict)]
        if isinstance(data, dict) and isinstance(data.get("messages"), list):
            return [m for m in data["messages"] if isinstance(m, dict)]
    return []


def _parse_timestamp(ts: Any) -> Optional[datetime]:
    """
    Best-effort timestamp parsing.
    Accepts:
      - unix seconds (int/float)
      - unix ms (int/float > 10^12)
      - ISO strings (handled lightly)
    """
    try:
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            # heuristic: ms timestamps are huge
            if ts > 1_000_000_000_000:
                return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if isinstance(ts, str):
            # Try ISO 8601
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                return None
        return None
    except Exception:
        return None


def backfill_unread_messages_for_device(db: Session, device_id: str, limit: int = 200) -> Dict[str, Any]:
    """
    Pull unread/history from engine (if supported) and insert into WhatsAppInbox.
    Safe to run multiple times (dedup by message_id).
    """
    device_uuid = UUIDService.safe_convert(device_id)
    if not device_uuid:
        return {"success": False, "error": "invalid_device_id"}

    device = db.query(Device).filter(Device.device_id == device_uuid).first()
    if not device:
        return {"success": False, "error": "device_not_found"}

    engine = WhatsAppEngineService(db=None)
    fetch = engine.fetch_unread_messages(device_id=str(device.device_id), limit=limit)
    if not fetch.get("success"):
        # Not supported is not fatal — just report.
        return {"success": False, "error": fetch.get("error"), "details": fetch.get("details"), "status_code": fetch.get("status_code")}

    endpoint_used = fetch.get("endpoint")
    raw = fetch.get("data")
    messages = _extract_messages(raw)

    inserted = 0
    skipped = 0
    duplicates = 0
    non_individual = 0
    invalid_phone = 0

    for m in messages:
        remote_jid = m.get("remoteJid") or m.get("jid") or m.get("remote_jid")
        if remote_jid and ("@g.us" in remote_jid or "@broadcast" in remote_jid):
            non_individual += 1
            continue

        # individual check: allow s.whatsapp.net and lid; if missing, still attempt phone
        if remote_jid and ("@s.whatsapp.net" not in remote_jid and "@lid" not in remote_jid):
            non_individual += 1
            continue

        msg_id = m.get("message_id") or m.get("messageId") or m.get("id")
        if msg_id:
            exists = db.query(WhatsAppInbox).filter(WhatsAppInbox.message_id == str(msg_id)).first()
            if exists:
                duplicates += 1
                continue

        from_me = bool(m.get("from_me") or m.get("fromMe") or m.get("fromMe") is True)
        # Backfill is for unread incoming. If engine doesn't provide unread flag, we still store incoming only.
        unread_flag = m.get("unread")
        if unread_flag is False:
            skipped += 1
            continue
        if from_me:
            skipped += 1
            continue

        phone = None
        if remote_jid:
            phone = remote_jid.split("@")[0]
        if not phone:
            phone = m.get("phone") or m.get("phone_number") or m.get("sender")
        phone = normalize_phone(phone) if phone else None
        if not phone:
            invalid_phone += 1
            continue

        push_name = m.get("push_name") or m.get("pushName") or m.get("name")
        text = m.get("message") or m.get("text") or m.get("body")

        incoming_time = (
            _parse_timestamp(m.get("timestamp"))
            or _parse_timestamp(m.get("t"))
            or _parse_timestamp(m.get("time"))
            or datetime.now(timezone.utc)
        )

        row = WhatsAppInbox(
            device_id=device.device_id,
            phone_number=phone,
            contact_name=push_name or phone,
            chat_type="individual",
            incoming_message=text,
            message_id=str(msg_id) if msg_id else None,
            incoming_time=incoming_time,
            is_read=False,          # unread incoming
            is_replied=False,
            is_outgoing=False,
            remote_jid=remote_jid,
        )
        db.add(row)
        inserted += 1

    if inserted:
        db.commit()

    logger.info(
        f"[BACKFILL] device={device.device_id} endpoint={endpoint_used} fetched={len(messages)} "
        f"inserted={inserted} dup={duplicates} skipped={skipped} non_individual={non_individual} invalid_phone={invalid_phone}"
    )

    return {
        "success": True,
        "endpoint": endpoint_used,
        "fetched": len(messages),
        "inserted": inserted,
        "duplicates": duplicates,
        "skipped": skipped,
        "non_individual": non_individual,
        "invalid_phone": invalid_phone,
    }

