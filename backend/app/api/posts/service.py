from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from .repository import PostRepository, CommentRepository, ReactionRepository
from backend.app.api.users.repository import UserRepository
from .schemas import (
    PostCreateSchema,
    CommentCreateSchema,
    ReactionCreateSchema,
    empty_reactions_count,
)
from .image_utils import normalize_base64_image, ImageError


# ---------------------------------------------------------------------------
# Utilidades de serialización
# ---------------------------------------------------------------------------
_TZ_LOCAL = timezone(timedelta(hours=-6))


def _iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_TZ_LOCAL).isoformat()


def _fetch_usernames(docs: list[dict], id_field: str = "author_id") -> dict:
    """Devuelve {str(author_id): username} para una lista de documentos."""
    ids = list({str(d[id_field]) for d in docs if d.get(id_field)})
    if not ids:
        return {}
    return UserRepository.find_many_usernames(ids)


def _serialize_post(post: dict, author_username: str | None = None) -> dict:
    return {
        "id":              str(post["_id"]),
        "author_id":       str(post["author_id"]),
        "author_username": author_username,
        "content":         post.get("content", ""),
        "media_urls":      post.get("media_urls", []),
        # Imagen embebida — el frontend construye el data URL.
        "image_base64":    post.get("image_base64"),
        "image_mime":      post.get("image_mime"),
        "created_at":      _iso(post.get("created_at")),
        "updated_at":      _iso(post.get("updated_at")),
        "reactions_count": post.get("reactions_count", empty_reactions_count()),
        "comments_count":  post.get("comments_count", 0),
    }


def _serialize_comment(comment: dict, author_username: str | None = None) -> dict:
    return {
        "id":                str(comment["_id"]),
        "post_id":           str(comment["post_id"]),
        "author_id":         str(comment["author_id"]),
        "author_username":   author_username,
        "content":           comment.get("content", ""),
        "parent_comment_id": (
            str(comment["parent_comment_id"])
            if comment.get("parent_comment_id") else None
        ),
        "image_base64":      comment.get("image_base64"),
        "image_mime":        comment.get("image_mime"),
        "created_at":        _iso(comment.get("created_at")),
        "reactions_count":   comment.get("reactions_count", empty_reactions_count()),
    }


def _resolve_image_fields(
    image_b64: str | None, image_mime: str | None
) -> tuple[str | None, str | None, list[dict] | None]:
    """
    Si la petición incluye imagen, valida y normaliza los campos.
    Devuelve (b64_normalizado, mime_normalizado, errores_o_None).
    Si no hay imagen, devuelve (None, None, None).
    """
    if not image_b64:
        return None, None, None
    try:
        clean_b64, clean_mime = normalize_base64_image(image_b64, image_mime)
    except ImageError as ex:
        return None, None, [{"field": "image", "message": str(ex)}]
    return clean_b64, clean_mime, None


def _serialize_reaction(reaction: dict) -> dict:
    return {
        "id":            str(reaction["_id"]),
        "user_id":       str(reaction["user_id"]),
        "target_id":     str(reaction["target_id"]),
        "target_type":   reaction["target_type"],
        "reaction_type": reaction["reaction_type"],
        "created_at":    _iso(reaction.get("created_at")),
    }


def _validation_errors(exc: ValidationError) -> list[dict]:
    return [
        {"field": err["loc"][0] if err["loc"] else "body", "message": err["msg"]}
        for err in exc.errors()
    ]


def _is_valid_object_id(value: str) -> bool:
    try:
        ObjectId(value)
        return True
    except (InvalidId, TypeError):
        return False


# ===========================================================================
# POSTS
# ===========================================================================
class PostService:

    @staticmethod
    def create_post(author_id: str, data: dict | None) -> dict:
        if not author_id:
            return {"ok": False, "errors": [{"field": "author", "message": "Usuario no autenticado"}]}

        if not isinstance(data, dict):
            return {"ok": False, "errors": [{"field": "body", "message": "Body JSON requerido"}]}

        try:
            validated = PostCreateSchema(**data)
        except ValidationError as e:
            return {"ok": False, "errors": _validation_errors(e)}

        # Procesa la imagen (opcional) — valida tamaño/mime/decodificación.
        image_b64, image_mime, image_errs = _resolve_image_fields(
            validated.image_base64, validated.image_mime
        )
        if image_errs:
            return {"ok": False, "errors": image_errs}

        post_doc = {
            "author_id":       ObjectId(author_id),
            "content":         validated.content,
            "media_urls":      validated.media_urls,
            "image_base64":    image_b64,
            "image_mime":      image_mime,
            "reactions_count": empty_reactions_count(),
            "comments_count":  0,
            "created_at":      datetime.now(timezone.utc),
            "updated_at":      None,
        }

        post_id = PostRepository.insert_post(post_doc)
        if not post_id:
            return {"ok": False, "errors": [{"field": "database", "message": "Error guardando el post"}]}

        post_doc["_id"] = ObjectId(post_id)
        usernames = UserRepository.find_many_usernames([author_id])
        return {"ok": True, "post": _serialize_post(post_doc, usernames.get(author_id))}

    @staticmethod
    def list_posts(page: int = 1, page_size: int = 20) -> dict:
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        skip = (page - 1) * page_size

        posts = PostRepository.list_posts(skip=skip, limit=page_size)
        total = PostRepository.count_posts()
        usernames = _fetch_usernames(posts)

        return {
            "ok": True,
            "posts": [_serialize_post(p, usernames.get(str(p["author_id"]))) for p in posts],
            "pagination": {
                "page":       page,
                "page_size":  page_size,
                "total":      total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }

    @staticmethod
    def get_post_with_comments(post_id: str) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}

        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

        comments = CommentRepository.list_by_post(post_id, skip=0, limit=100)
        usernames = _fetch_usernames([post] + comments)

        return {
            "ok": True,
            "post":     _serialize_post(post, usernames.get(str(post["author_id"]))),
            "comments": [_serialize_comment(c, usernames.get(str(c["author_id"]))) for c in comments],
        }

    @staticmethod
    def delete_post(post_id: str, requester_id: str) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}

        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

        # Solo el autor puede eliminar
        if str(post.get("author_id")) != str(requester_id):
            return {"ok": False, "errors": [{"field": "auth", "message": "No autorizado para eliminar este post"}]}

        deleted = PostRepository.delete_by_id(post_id)
        if not deleted:
            return {"ok": False, "errors": [{"field": "database", "message": "Error eliminando el post"}]}

        # Cascada: comentarios + reacciones (de post y de comentarios)
        comments = CommentRepository.list_by_post(post_id, skip=0, limit=10_000)
        for c in comments:
            ReactionRepository.delete_by_target(str(c["_id"]), "comment")
        CommentRepository.delete_by_post(post_id)
        ReactionRepository.delete_by_target(post_id, "post")

        return {"ok": True, "message": "Post eliminado correctamente"}


# ===========================================================================
# COMMENTS
# ===========================================================================
class CommentService:

    @staticmethod
    def create_comment(post_id: str, author_id: str, data: dict | None) -> dict:
        if not author_id:
            return {"ok": False, "errors": [{"field": "author", "message": "Usuario no autenticado"}]}
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}
        if not isinstance(data, dict):
            return {"ok": False, "errors": [{"field": "body", "message": "Body JSON requerido"}]}

        try:
            validated = CommentCreateSchema(**data)
        except ValidationError as e:
            return {"ok": False, "errors": _validation_errors(e)}

        # El post objetivo debe existir
        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

        # Si es respuesta a otro comentario, validar que exista y pertenezca al mismo post
        parent_oid = None
        if validated.parent_comment_id:
            if not _is_valid_object_id(validated.parent_comment_id):
                return {"ok": False, "errors": [{"field": "parent_comment_id", "message": "Id inválido"}]}
            parent = CommentRepository.find_by_id(validated.parent_comment_id)
            if not parent:
                return {"ok": False, "errors": [{"field": "parent_comment_id", "message": "Comentario padre no encontrado"}]}
            if str(parent.get("post_id")) != str(post["_id"]):
                return {"ok": False, "errors": [{"field": "parent_comment_id", "message": "El comentario padre no pertenece al post"}]}
            parent_oid = ObjectId(validated.parent_comment_id)

        # Imagen opcional para el comentario / sub-comentario.
        image_b64, image_mime, image_errs = _resolve_image_fields(
            validated.image_base64, validated.image_mime
        )
        if image_errs:
            return {"ok": False, "errors": image_errs}

        comment_doc = {
            "post_id":           ObjectId(post_id),
            "author_id":         ObjectId(author_id),
            "content":           validated.content,
            "parent_comment_id": parent_oid,
            "image_base64":      image_b64,
            "image_mime":        image_mime,
            "reactions_count":   empty_reactions_count(),
            "created_at":        datetime.now(timezone.utc),
        }

        comment_id = CommentRepository.insert_comment(comment_doc)
        if not comment_id:
            return {"ok": False, "errors": [{"field": "database", "message": "Error guardando el comentario"}]}

        # Mantener `comments_count` del post sincronizado
        PostRepository.increment_comments(post_id, 1)

        comment_doc["_id"] = ObjectId(comment_id)
        usernames = UserRepository.find_many_usernames([author_id])
        return {"ok": True, "comment": _serialize_comment(comment_doc, usernames.get(author_id))}

    @staticmethod
    def list_comments(post_id: str, page: int = 1, page_size: int = 50) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}

        page = max(1, page)
        page_size = max(1, min(200, page_size))
        skip = (page - 1) * page_size

        comments = CommentRepository.list_by_post(post_id, skip=skip, limit=page_size)
        usernames = _fetch_usernames(comments)
        return {
            "ok": True,
            "comments": [_serialize_comment(c, usernames.get(str(c["author_id"]))) for c in comments],
            "pagination": {"page": page, "page_size": page_size},
        }

    @staticmethod
    def list_replies(post_id: str, comment_id: str, page: int = 1, page_size: int = 50) -> dict:
        if not _is_valid_object_id(post_id) or not _is_valid_object_id(comment_id):
            return {"ok": False, "errors": [{"field": "id", "message": "Id inválido"}]}

        comment = CommentRepository.find_by_id(comment_id)
        if not comment:
            return {"ok": False, "errors": [{"field": "comment", "message": "Comentario no encontrado"}]}
        if str(comment.get("post_id")) != str(post_id):
            return {"ok": False, "errors": [{"field": "comment", "message": "El comentario no pertenece al post"}]}

        page = max(1, page)
        page_size = max(1, min(200, page_size))
        skip = (page - 1) * page_size

        replies = CommentRepository.list_replies(comment_id, skip=skip, limit=page_size)
        usernames = _fetch_usernames(replies)
        return {
            "ok": True,
            "replies": [_serialize_comment(r, usernames.get(str(r["author_id"]))) for r in replies],
            "pagination": {"page": page, "page_size": page_size},
        }

    @staticmethod
    def delete_comment(post_id: str, comment_id: str, requester_id: str) -> dict:
        if not _is_valid_object_id(post_id) or not _is_valid_object_id(comment_id):
            return {"ok": False, "errors": [{"field": "id", "message": "Id inválido"}]}

        comment = CommentRepository.find_by_id(comment_id)
        if not comment:
            return {"ok": False, "errors": [{"field": "comment", "message": "Comentario no encontrado"}]}

        # Coherencia: el comentario debe pertenecer al post indicado
        if str(comment.get("post_id")) != str(post_id):
            return {"ok": False, "errors": [{"field": "comment", "message": "El comentario no pertenece al post"}]}

        # Permisos: autor del comentario o autor del post pueden borrarlo
        post = PostRepository.find_by_id(post_id)
        post_author = str(post.get("author_id")) if post else None
        comment_author = str(comment.get("author_id"))
        if str(requester_id) not in {comment_author, post_author}:
            return {"ok": False, "errors": [{"field": "auth", "message": "No autorizado para eliminar este comentario"}]}

        deleted = CommentRepository.delete_by_id(comment_id)
        if not deleted:
            return {"ok": False, "errors": [{"field": "database", "message": "Error eliminando el comentario"}]}

        # Cascada: reacciones del comentario + sus respuestas y sus reacciones
        ReactionRepository.delete_by_target(comment_id, "comment")
        replies = CommentRepository.list_replies(comment_id, skip=0, limit=10_000)
        for r in replies:
            ReactionRepository.delete_by_target(str(r["_id"]), "comment")
        CommentRepository.delete_replies_by_parent(comment_id)
        PostRepository.increment_comments(post_id, -1)

        return {"ok": True, "message": "Comentario eliminado correctamente"}


# ===========================================================================
# REACTIONS
# ===========================================================================
class ReactionService:
    """
    Reglas:
      - Un usuario puede tener UNA reacción activa por target.
      - Si reacciona con el mismo tipo que ya tiene → no-op (idempotente).
      - Si reacciona con tipo distinto → se actualiza, ajustando contadores.
      - DELETE → borra la reacción y decrementa el contador del tipo activo.
    """

    @staticmethod
    def _validate_payload(data: dict | None) -> tuple[ReactionCreateSchema | None, list[dict] | None]:
        if not isinstance(data, dict):
            return None, [{"field": "body", "message": "Body JSON requerido"}]
        try:
            return ReactionCreateSchema(**data), None
        except ValidationError as e:
            return None, _validation_errors(e)

    @staticmethod
    def react_to_post(post_id: str, user_id: str, data: dict | None) -> dict:
        if not user_id:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no autenticado"}]}
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id inválido"}]}

        validated, errors = ReactionService._validate_payload(data)
        if errors:
            return {"ok": False, "errors": errors}

        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

        return ReactionService._upsert_reaction(
            user_id=user_id,
            target_id=post_id,
            target_type="post",
            new_reaction=validated.reaction_type,
        )

    @staticmethod
    def remove_post_reaction(post_id: str, user_id: str) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id inválido"}]}
        return ReactionService._remove_reaction(user_id, post_id, "post")

    @staticmethod
    def react_to_comment(post_id: str, comment_id: str, user_id: str, data: dict | None) -> dict:
        if not user_id:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no autenticado"}]}
        if not _is_valid_object_id(post_id) or not _is_valid_object_id(comment_id):
            return {"ok": False, "errors": [{"field": "id", "message": "Id inválido"}]}

        validated, errors = ReactionService._validate_payload(data)
        if errors:
            return {"ok": False, "errors": errors}

        comment = CommentRepository.find_by_id(comment_id)
        if not comment:
            return {"ok": False, "errors": [{"field": "comment", "message": "Comentario no encontrado"}]}
        if str(comment.get("post_id")) != str(post_id):
            return {"ok": False, "errors": [{"field": "comment", "message": "El comentario no pertenece al post"}]}

        return ReactionService._upsert_reaction(
            user_id=user_id,
            target_id=comment_id,
            target_type="comment",
            new_reaction=validated.reaction_type,
        )

    @staticmethod
    def remove_comment_reaction(post_id: str, comment_id: str, user_id: str) -> dict:
        if not _is_valid_object_id(post_id) or not _is_valid_object_id(comment_id):
            return {"ok": False, "errors": [{"field": "id", "message": "Id inválido"}]}
        comment = CommentRepository.find_by_id(comment_id)
        if not comment:
            return {"ok": False, "errors": [{"field": "comment", "message": "Comentario no encontrado"}]}
        if str(comment.get("post_id")) != str(post_id):
            return {"ok": False, "errors": [{"field": "comment", "message": "El comentario no pertenece al post"}]}
        return ReactionService._remove_reaction(user_id, comment_id, "comment")

    # -- helpers internos ---------------------------------------------------
    @staticmethod
    def _increment_target(target_id: str, target_type: str, reaction_type: str, delta: int) -> None:
        if target_type == "post":
            PostRepository.increment_reaction(target_id, reaction_type, delta)
        else:
            CommentRepository.increment_reaction(target_id, reaction_type, delta)

    @staticmethod
    def _upsert_reaction(user_id: str, target_id: str, target_type: str, new_reaction: str) -> dict:
        existing = ReactionRepository.find_user_reaction(user_id, target_id, target_type)

        # Caso 1: no había reacción → insertar y subir contador
        if not existing:
            reaction_doc = {
                "user_id":       ObjectId(user_id),
                "target_id":     ObjectId(target_id),
                "target_type":   target_type,
                "reaction_type": new_reaction,
            }
            reaction_id = ReactionRepository.insert_reaction(reaction_doc)
            if not reaction_id:
                return {"ok": False, "errors": [{"field": "database", "message": "Error guardando la reacción"}]}
            ReactionService._increment_target(target_id, target_type, new_reaction, 1)
            reaction_doc["_id"] = ObjectId(reaction_id)
            return {"ok": True, "reaction": _serialize_reaction(reaction_doc), "action": "created"}

        # Caso 2: misma reacción → idempotente, no cambiamos contadores
        if existing["reaction_type"] == new_reaction:
            return {"ok": True, "reaction": _serialize_reaction(existing), "action": "unchanged"}

        # Caso 3: tipo distinto → swap (decrementar el viejo, incrementar el nuevo)
        old_type = existing["reaction_type"]
        updated = ReactionRepository.update_reaction_type(existing["_id"], new_reaction)
        if not updated:
            return {"ok": False, "errors": [{"field": "database", "message": "Error actualizando la reacción"}]}

        ReactionService._increment_target(target_id, target_type, old_type, -1)
        ReactionService._increment_target(target_id, target_type, new_reaction, 1)

        return {"ok": True, "reaction": _serialize_reaction(updated), "action": "updated"}

    @staticmethod
    def _remove_reaction(user_id: str, target_id: str, target_type: str) -> dict:
        existing = ReactionRepository.find_user_reaction(user_id, target_id, target_type)
        if not existing:
            return {"ok": False, "errors": [{"field": "reaction", "message": "No existe reacción del usuario"}]}

        deleted = ReactionRepository.delete_reaction(existing["_id"])
        if not deleted:
            return {"ok": False, "errors": [{"field": "database", "message": "Error eliminando la reacción"}]}

        ReactionService._increment_target(target_id, target_type, existing["reaction_type"], -1)
        return {"ok": True, "message": "Reacción eliminada"}
