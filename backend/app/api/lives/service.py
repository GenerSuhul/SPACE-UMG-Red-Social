# backend/app/api/lives/service.py
import random
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from .repository import LiveRepository

_TZ_LOCAL = timezone(timedelta(hours=-6))

def _iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_TZ_LOCAL).isoformat()

SIMULATED_COMMENTS = [
    "¡Increíble transmisión! Saludos desde la UMG.",
    "¡SPACE UMG está genial! 🚀",
    "Hola, ¿de qué trata el proyecto hoy?",
    "¡Excelente UI, se ve súper premium!",
    "¿Este chat se actualiza en tiempo real?",
    "Qué buen diseño, mucho mejor que la competencia.",
    "Saludos de la facultad de Ingeniería en Sistemas.",
    "¡Apoyando el directo! 👍",
    "¡Felicitaciones por la tesis de Base de Datos!",
    "¿Habrá sección de preguntas al final?",
    "Me encanta la paleta de colores azul y blanco, ¡muy institucional!",
    "SPACE UMG al 100% 🤩",
    "¡Excelente iniciativa!",
    "Wow, me gusta mucho cómo corre el live stream."
]

SIMULATED_USERNAMES = [
    "carlos_umg", "sofia.sistemas", "estudiante_bd2", "mario_mariano", "ana_galvez",
    "ingenieria_umg", "luis_tech", "valery_code", "diego_mariano", "elena_systems"
]

class LiveService:

    @staticmethod
    def _is_valid_object_id(value: str) -> bool:
        try:
            ObjectId(value)
            return True
        except (InvalidId, TypeError):
            return False

    @staticmethod
    def start_live(creator_id: str, title: str) -> dict:
        title = (title or "").strip() or "Transmisión en vivo de SPACE UMG"
        stream = LiveRepository.create_stream(creator_id, title)
        return {"ok": True, "stream": LiveService._serialize_stream(stream)}

    @staticmethod
    def list_active() -> dict:
        streams = LiveRepository.list_active_streams()
        return {"ok": True, "streams": [LiveService._serialize_stream(s) for s in streams]}

    @staticmethod
    def end_live(stream_id: str, creator_id: str) -> dict:
        if not LiveService._is_valid_object_id(stream_id):
            return {"ok": False, "errors": [{"field": "stream_id", "message": "Id de stream inválido"}]}
        
        stream = LiveRepository.find_stream_by_id(stream_id)
        if not stream:
            return {"ok": False, "errors": [{"field": "stream", "message": "Transmisión no encontrada"}]}
            
        if str(stream.get("creator_id")) != str(creator_id):
            return {"ok": False, "errors": [{"field": "auth", "message": "No estás autorizado para finalizar este directo"}]}

        ended = LiveRepository.end_stream(stream_id, creator_id)
        if not ended:
            return {"ok": False, "errors": [{"field": "database", "message": "Error finalizando transmisión"}]}
            
        return {"ok": True, "stream": LiveService._serialize_stream(ended)}

    @staticmethod
    def heartbeat(stream_id: str) -> dict:
        """Mantiene activo el live y simula eventos: cambio en espectadores y nuevos comentarios de audiencia."""
        if not LiveService._is_valid_object_id(stream_id):
            return {"ok": False, "errors": [{"field": "stream_id", "message": "Id de stream inválido"}]}
            
        stream = LiveRepository.find_stream_by_id(stream_id)
        if not stream or stream.get("status") == "ended":
            return {"ok": False, "errors": [{"field": "stream", "message": "La transmisión ha finalizado"}]}
            
        # Simular fluctuación en viewers (delta entre -2 y +4)
        viewers_delta = random.choice([-2, -1, 0, 1, 2, 3, 4])
        updated = LiveRepository.update_viewers(stream_id, viewers_delta)
        if not updated:
            updated = stream

        # Generar comentarios simulados
        # Entre 0 y 2 comentarios nuevos por heartbeat
        simulated_chat = []
        comments_count = random.choice([0, 1, 2])
        for _ in range(comments_count):
            simulated_chat.append({
                "username": random.choice(SIMULATED_USERNAMES),
                "content": random.choice(SIMULATED_COMMENTS),
                "created_at": _iso(datetime.now(timezone.utc))
            })

        serialized = LiveService._serialize_stream(updated)
        return {
            "ok": True,
            "stream": serialized,
            "simulated_chat": simulated_chat
        }

    @staticmethod
    def _serialize_stream(stream: dict) -> dict:
        return {
            "id": str(stream["_id"]),
            "creator_id": str(stream["creator_id"]),
            "creator_username": stream.get("creator_username", "Usuario UMG"),
            "creator_avatar_base64": stream.get("creator_avatar_base64"),
            "creator_avatar_mime": stream.get("creator_avatar_mime"),
            "title": stream.get("title", ""),
            "status": stream.get("status", "live"),
            "viewers_count": stream.get("viewers_count", 0),
            "created_at": _iso(stream.get("created_at")),
            "ended_at": _iso(stream.get("ended_at"))
        }
