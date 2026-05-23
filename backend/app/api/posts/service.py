from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from .repository import PostRepository, CommentRepository, ReactionRepository
from backend.app.api.users.repository import UserRepository
from .schemas import (
    PostCreateSchema,
    PostUpdateSchema,
    CommentCreateSchema,
    ReactionCreateSchema,
    empty_reactions_count,
)
from .image_utils import normalize_base64_image, ImageError


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
    ids = list({str(d[id_field]) for d in docs if d.get(id_field)})
    if not ids:
        return {}
    return UserRepository.find_many_usernames(ids)


def _author_fields(profiles: dict, author_id: str) -> dict:
    profile = profiles.get(str(author_id)) or {}
    avatar_url = profile.get("avatar_url")
    return {
        "author_username":      profile.get("username"),
        "author_avatar_base64": None if avatar_url else profile.get("avatar_base64"),
        "author_avatar_mime":   profile.get("avatar_mime"),
        "author_avatar_url":    avatar_url,
    }


def _post_images(post: dict) -> list[dict]:
    images = post.get("images")
    if isinstance(images, list):
        return images
    old_b64  = post.get("image_base64")
    old_mime = post.get("image_mime")
    return [{"base64": old_b64, "mime": old_mime}] if old_b64 else []


def _serialize_post(post: dict, profiles: dict | None = None) -> dict:
    author_id = str(post["author_id"])
    author = _author_fields(profiles or {}, author_id)
    return {
        "id":                   str(post["_id"]),
        "author_id":            author_id,
        "author_username":      author["author_username"],
        "author_avatar_base64": author["author_avatar_base64"],
        "author_avatar_mime":   author["author_avatar_mime"],
        "author_avatar_url":    author["author_avatar_url"],
        "content":              post.get("content", ""),
        "media_urls":           post.get("media_urls", []),
        "images":               _post_images(post),
        "created_at":           _iso(post.get("created_at")),
        "updated_at":           _iso(post.get("updated_at")),
        "reactions_count":      post.get("reactions_count", empty_reactions_count()),
        "comments_count":       post.get("comments_count", 0),
        "type":                 post.get("type", "post"),
    }


def _serialize_comment(comment: dict, profiles: dict | None = None) -> dict:
    author_id = str(comment["author_id"])
    author = _author_fields(profiles or {}, author_id)
    return {
        "id":                   str(comment["_id"]),
        "post_id":              str(comment["post_id"]),
        "author_id":            author_id,
        "author_username":      author["author_username"],
        "author_avatar_base64": author["author_avatar_base64"],
        "author_avatar_mime":   author["author_avatar_mime"],
        "author_avatar_url":    author["author_avatar_url"],
        "content":              comment.get("content", ""),
        "parent_comment_id":    (
            str(comment["parent_comment_id"])
            if comment.get("parent_comment_id") else None
        ),
        "image_base64":         comment.get("image_base64"),
        "image_mime":           comment.get("image_mime"),
        "image_url":            comment.get("image_url"),
        "created_at":           _iso(comment.get("created_at")),
        "reactions_count":      comment.get("reactions_count", empty_reactions_count()),
    }


def _resolve_image_fields(
    image_b64: str | None, image_mime: str | None
) -> tuple[str | None, str | None, list[dict] | None]:
    if not image_b64:
        return None, None, None
    try:
        clean_b64, clean_mime = normalize_base64_image(image_b64, image_mime)
    except ImageError as ex:
        return None, None, [{"field": "image", "message": str(ex)}]
    return clean_b64, clean_mime, None


def _validate_images(raw_images: list) -> tuple[list[dict], list[dict] | None]:
    validated: list[dict] = []
    for i, img in enumerate(raw_images):
        b64  = img.base64 if hasattr(img, "base64") else img.get("base64", "")
        mime = img.mime   if hasattr(img, "mime")   else img.get("mime", "")
        try:
            clean_b64, clean_mime = normalize_base64_image(b64, mime)
        except ImageError as ex:
            return [], [{"field": f"images[{i}]", "message": str(ex)}]
        validated.append({"base64": clean_b64, "mime": clean_mime})
    return validated, None


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

        images, image_errs = _validate_images(validated.images)
        if image_errs:
            return {"ok": False, "errors": image_errs}

        post_doc = {
            "author_id":       ObjectId(author_id),
            "content":         validated.content,
            "media_urls":      validated.media_urls,
            "images":          images,
            "reactions_count": empty_reactions_count(),
            "comments_count":  0,
            "type":            validated.type or "post",
            "created_at":      datetime.now(timezone.utc),
            "updated_at":      None,
        }

        post_id = PostRepository.insert_post(post_doc)
        if not post_id:
            return {"ok": False, "errors": [{"field": "database", "message": "Error guardando el post"}]}

        post_doc["_id"] = ObjectId(post_id)
        
        try:
            from backend.app.api.notifications.service import NotificationService
            if validated.content.startswith("🔄 Repost @"):
                parts = validated.content.split(":", 1)
                if len(parts) > 0:
                    header = parts[0]
                    username = header.replace("🔄 Repost @", "").strip()
                    original_author = UserRepository.find_by_username(username.lower())
                    if original_author:
                        NotificationService.trigger_share(
                            sender_id=author_id,
                            receiver_id=str(original_author["_id"]),
                            post_id=str(post_id)
                        )
            
            NotificationService.trigger_mentions(
                sender_id=author_id,
                text=validated.content,
                post_id=str(post_id)
            )
        except Exception as ex:
            print(f"Error triggering repost or mention notifications: {ex}")

        profiles = UserRepository.find_many_usernames([author_id])
        return {"ok": True, "post": _serialize_post(post_doc, profiles)}

    @staticmethod
    def list_posts(page: int = 1, page_size: int = 20, post_type: str | None = None) -> dict:
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        skip = (page - 1) * page_size

        q = {}
        if post_type:
            q["type"] = post_type
        else:
            q["type"] = {"$in": ["post", None]}

        posts = PostRepository.list_posts(skip=skip, limit=page_size, query_filter=q)
        total = PostRepository.count_posts(query_filter=q)
        profiles = _fetch_usernames(posts)

        return {
            "ok": True,
            "posts": [_serialize_post(p, profiles) for p in posts],
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
        profiles = _fetch_usernames([post] + comments)

        return {
            "ok": True,
            "post":     _serialize_post(post, profiles),
            "comments": [_serialize_comment(c, profiles) for c in comments],
        }

    @staticmethod
    def update_post(post_id: str, requester_id: str, data: dict | None) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}
        if not isinstance(data, dict):
            return {"ok": False, "errors": [{"field": "body", "message": "Body JSON requerido"}]}

        try:
            validated = PostUpdateSchema(**data)
        except ValidationError as e:
            return {"ok": False, "errors": _validation_errors(e)}

        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

        if str(post.get("author_id")) != str(requester_id):
            return {"ok": False, "errors": [{"field": "auth", "message": "No autorizado para modificar este post"}]}

        update_fields: dict = {}

        if validated.content is not None:
            update_fields["content"] = validated.content

        if validated.media_urls is not None:
            update_fields["media_urls"] = validated.media_urls

        # images: None → no tocar; [] → vaciar; [...] → reemplazar
        if validated.images is not None:
            images, image_errs = _validate_images(validated.images)
            if image_errs:
                return {"ok": False, "errors": image_errs}
            update_fields["images"] = images

        if not update_fields:
            return {"ok": False, "errors": [{"field": "body", "message": "No se enviaron campos para actualizar"}]}

        update_fields["updated_at"] = datetime.now(timezone.utc)

        updated = PostRepository.update_by_id(post_id, update_fields)
        if not updated:
            return {"ok": False, "errors": [{"field": "database", "message": "Error actualizando el post"}]}

        profiles = UserRepository.find_many_usernames([str(updated["author_id"])])
        return {"ok": True, "post": _serialize_post(updated, profiles)}

    @staticmethod
    def list_posts_by_user(user_id: str, page: int = 1, page_size: int = 20) -> dict:
        if not _is_valid_object_id(user_id):
            return {"ok": False, "errors": [{"field": "user_id", "message": "Id de usuario inválido"}]}

        user = UserRepository.find_by_id(user_id)
        if not user:
            return {"ok": False, "errors": [{"field": "user", "message": "Usuario no encontrado"}]}

        page = max(1, page)
        page_size = max(1, min(100, page_size))
        skip = (page - 1) * page_size

        posts = PostRepository.list_by_author(user_id, skip=skip, limit=page_size)
        total = PostRepository.count_by_author(user_id)
        profiles = _fetch_usernames(posts)

        return {
            "ok": True,
            "posts": [_serialize_post(p, profiles) for p in posts],
            "pagination": {
                "page":        page,
                "page_size":   page_size,
                "total":       total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }

    @staticmethod
    def delete_post(post_id: str, requester_id: str) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}

        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

        if str(post.get("author_id")) != str(requester_id):
            return {"ok": False, "errors": [{"field": "auth", "message": "No autorizado para eliminar este post"}]}

        deleted = PostRepository.delete_by_id(post_id)
        if not deleted:
            return {"ok": False, "errors": [{"field": "database", "message": "Error eliminando el post"}]}

        comments = CommentRepository.list_by_post(post_id, skip=0, limit=10_000)
        for c in comments:
            ReactionRepository.delete_by_target(str(c["_id"]), "comment")
        CommentRepository.delete_by_post(post_id)
        ReactionRepository.delete_by_target(post_id, "post")

        return {"ok": True, "message": "Post eliminado correctamente"}


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

        post = PostRepository.find_by_id(post_id)
        if not post:
            return {"ok": False, "errors": [{"field": "post", "message": "Post no encontrado"}]}

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
            "image_url":         validated.image_url,
            "reactions_count":   empty_reactions_count(),
            "created_at":        datetime.now(timezone.utc),
        }

        comment_id = CommentRepository.insert_comment(comment_doc)
        if not comment_id:
            return {"ok": False, "errors": [{"field": "database", "message": "Error guardando el comentario"}]}

        PostRepository.increment_comments(post_id, 1)

        try:
            from backend.app.api.notifications.service import NotificationService
            post_owner_id = str(post["author_id"])
            NotificationService.trigger_comment(
                sender_id=author_id,
                receiver_id=post_owner_id,
                post_id=post_id,
                comment_text=validated.content
            )
            NotificationService.trigger_mentions(
                sender_id=author_id,
                text=validated.content,
                post_id=post_id
            )
        except Exception as ex:
            print(f"Error triggering comment or mention notifications: {ex}")

        comment_doc["_id"] = ObjectId(comment_id)
        profiles = UserRepository.find_many_usernames([author_id])
        return {"ok": True, "comment": _serialize_comment(comment_doc, profiles)}

    @staticmethod
    def list_comments(post_id: str, page: int = 1, page_size: int = 50) -> dict:
        if not _is_valid_object_id(post_id):
            return {"ok": False, "errors": [{"field": "post_id", "message": "Id de post inválido"}]}

        page = max(1, page)
        page_size = max(1, min(200, page_size))
        skip = (page - 1) * page_size

        comments = CommentRepository.list_by_post(post_id, skip=skip, limit=page_size)
        profiles = _fetch_usernames(comments)
        return {
            "ok": True,
            "comments": [_serialize_comment(c, profiles) for c in comments],
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
        profiles = _fetch_usernames(replies)
        return {
            "ok": True,
            "replies": [_serialize_comment(r, profiles) for r in replies],
            "pagination": {"page": page, "page_size": page_size},
        }

    @staticmethod
    def delete_comment(post_id: str, comment_id: str, requester_id: str) -> dict:
        if not _is_valid_object_id(post_id) or not _is_valid_object_id(comment_id):
            return {"ok": False, "errors": [{"field": "id", "message": "Id inválido"}]}

        comment = CommentRepository.find_by_id(comment_id)
        if not comment:
            return {"ok": False, "errors": [{"field": "comment", "message": "Comentario no encontrado"}]}

        if str(comment.get("post_id")) != str(post_id):
            return {"ok": False, "errors": [{"field": "comment", "message": "El comentario no pertenece al post"}]}

        post = PostRepository.find_by_id(post_id)
        post_author = str(post.get("author_id")) if post else None
        comment_author = str(comment.get("author_id"))
        if str(requester_id) not in {comment_author, post_author}:
            return {"ok": False, "errors": [{"field": "auth", "message": "No autorizado para eliminar este comentario"}]}

        deleted = CommentRepository.delete_by_id(comment_id)
        if not deleted:
            return {"ok": False, "errors": [{"field": "database", "message": "Error eliminando el comentario"}]}

        ReactionRepository.delete_by_target(comment_id, "comment")
        replies = CommentRepository.list_replies(comment_id, skip=0, limit=10_000)
        for r in replies:
            ReactionRepository.delete_by_target(str(r["_id"]), "comment")
        CommentRepository.delete_replies_by_parent(comment_id)
        PostRepository.increment_comments(post_id, -1)

        return {"ok": True, "message": "Comentario eliminado correctamente"}


class ReactionService:

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

    @staticmethod
    def _increment_target(target_id: str, target_type: str, reaction_type: str, delta: int) -> None:
        if target_type == "post":
            PostRepository.increment_reaction(target_id, reaction_type, delta)
        else:
            CommentRepository.increment_reaction(target_id, reaction_type, delta)

    @staticmethod
    def _upsert_reaction(user_id: str, target_id: str, target_type: str, new_reaction: str) -> dict:
        existing = ReactionRepository.find_user_reaction(user_id, target_id, target_type)

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
            
            if target_type == "post":
                try:
                    post = PostRepository.find_by_id(target_id)
                    if post:
                        post_owner_id = str(post["author_id"])
                        from backend.app.api.notifications.service import NotificationService
                        NotificationService.trigger_like(
                            sender_id=user_id,
                            receiver_id=post_owner_id,
                            post_id=target_id
                        )
                except Exception as ex:
                    print(f"Error triggering reaction/like notification: {ex}")
                    
            return {"ok": True, "reaction": _serialize_reaction(reaction_doc), "action": "created"}

        if existing["reaction_type"] == new_reaction:
            return {"ok": True, "reaction": _serialize_reaction(existing), "action": "unchanged"}

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
