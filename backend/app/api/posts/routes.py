from flask import request, jsonify as js
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from

from . import posts_bp
from .service import PostService, CommentService, ReactionService
from .image_utils import file_storage_to_base64, ImageError


# ===========================================================================
# Helpers
# ===========================================================================
def _status_for_errors(errors: list[dict], default: int = 400) -> int:
    """
    Mapea errores de service a status HTTP.
    Convención: 'post' / 'comment' / 'user' no encontrados → 404,
    'auth' → 403, todo lo demás → 400.
    """
    if not errors:
        return default
    fields = {e.get("field") for e in errors}
    if "post" in fields or "comment" in fields:
        for e in errors:
            if "no encontrado" in (e.get("message") or "").lower():
                return 404
    if "auth" in fields:
        return 403
    return default


def _parse_payload_with_optional_image() -> tuple[dict | None, dict | None]:
    """
    Lee el body de la request soportando dos formatos:
      - application/json puro
      - multipart/form-data (campos de texto + archivo `image`)

    Devuelve (payload_dict, error_dict).
    Si hay error procesando el archivo, payload es None y error trae el
    diccionario en formato `{"ok": False, "errors": [...]}`.
    """
    content_type = (request.content_type or "").lower()

    # --- multipart: combinamos campos de texto + archivo `image` ---
    if "multipart/form-data" in content_type:
        data: dict = {}
        # form puede traer todos los campos como strings
        for key, value in request.form.items():
            # `media_urls` puede venir repetido; preferimos getlist en ese caso
            if key == "media_urls":
                continue
            data[key] = value
        media_urls = request.form.getlist("media_urls")
        if media_urls:
            data["media_urls"] = media_urls

        file = request.files.get("image")
        if file is not None and getattr(file, "filename", ""):
            try:
                b64, mime = file_storage_to_base64(file)
            except ImageError as ex:
                return None, {
                    "ok": False,
                    "errors": [{"field": "image", "message": str(ex)}],
                }
            data["image_base64"] = b64
            data["image_mime"]   = mime
        return data, None

    # --- JSON puro (comportamiento previo intacto) ---
    return request.get_json(silent=True), None


# ===========================================================================
# POSTS
# ===========================================================================
@posts_bp.route('/', methods=['POST'])
@jwt_required()
@swag_from('docs/create_post.yml')
def create_post():
    """Crea una nueva publicación del usuario autenticado.

    Acepta tanto application/json como multipart/form-data (para subir imagen).
    """
    user_id = get_jwt_identity()
    data, image_err = _parse_payload_with_optional_image()
    if image_err:
        return js(image_err), 400

    result = PostService.create_post(user_id, data)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 201


@posts_bp.route('/', methods=['GET'])
@jwt_required()
@swag_from('docs/list_posts.yml')
def list_posts():
    """Listado paginado de posts (feed)."""
    page = int(request.args.get("page", 1) or 1)
    page_size = int(request.args.get("page_size", 20) or 20)

    result = PostService.list_posts(page=page, page_size=page_size)
    return js(result), 200


@posts_bp.route('/<post_id>', methods=['GET'])
@jwt_required()
@swag_from('docs/get_post.yml')
def get_post(post_id: str):
    """Obtiene un post junto con sus comentarios."""
    result = PostService.get_post_with_comments(post_id)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200


@posts_bp.route('/<post_id>', methods=['DELETE'])
@jwt_required()
@swag_from('docs/delete_post.yml')
def delete_post(post_id: str):
    """Elimina un post (solo el autor)."""
    user_id = get_jwt_identity()
    result = PostService.delete_post(post_id, user_id)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200


# ===========================================================================
# COMMENTS
# ===========================================================================
@posts_bp.route('/<post_id>/comments', methods=['POST'])
@jwt_required()
@swag_from('docs/create_comment.yml')
def create_comment(post_id: str):
    """Agrega un comentario (o respuesta) a un post.

    Acepta application/json o multipart/form-data si se adjunta imagen.
    Para crear un subcomentario se usa el mismo endpoint enviando
    `parent_comment_id` en el body.
    """
    user_id = get_jwt_identity()
    data, image_err = _parse_payload_with_optional_image()
    if image_err:
        return js(image_err), 400

    result = CommentService.create_comment(post_id, user_id, data)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 201


@posts_bp.route('/<post_id>/comments', methods=['GET'])
@jwt_required()
@swag_from('docs/list_comments.yml')
def list_comments(post_id: str):
    """Lista los comentarios de un post."""
    page = int(request.args.get("page", 1) or 1)
    page_size = int(request.args.get("page_size", 50) or 50)

    result = CommentService.list_comments(post_id, page=page, page_size=page_size)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200


@posts_bp.route('/<post_id>/comments/<comment_id>/replies', methods=['GET'])
@jwt_required()
def list_replies(post_id: str, comment_id: str):
    """Lista las respuestas de un comentario específico."""
    page = int(request.args.get("page", 1) or 1)
    page_size = int(request.args.get("page_size", 50) or 50)

    result = CommentService.list_replies(post_id, comment_id, page=page, page_size=page_size)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200


@posts_bp.route('/<post_id>/comments/<comment_id>', methods=['DELETE'])
@jwt_required()
@swag_from('docs/delete_comment.yml')
def delete_comment(post_id: str, comment_id: str):
    """Elimina un comentario (autor del comentario o del post)."""
    user_id = get_jwt_identity()
    result = CommentService.delete_comment(post_id, comment_id, user_id)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200


# ===========================================================================
# REACTIONS
# ===========================================================================
@posts_bp.route('/<post_id>/reactions', methods=['POST'])
@jwt_required()
@swag_from('docs/react_post.yml')
def react_to_post(post_id: str):
    """Reacciona a un post. Body: {"reaction_type": "like"}."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)

    result = ReactionService.react_to_post(post_id, user_id, data)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))

    status = 201 if result.get("action") == "created" else 200
    return js(result), status


@posts_bp.route('/<post_id>/reactions', methods=['DELETE'])
@jwt_required()
@swag_from('docs/remove_post_reaction.yml')
def remove_post_reaction(post_id: str):
    """Elimina la reacción del usuario autenticado sobre un post."""
    user_id = get_jwt_identity()
    result = ReactionService.remove_post_reaction(post_id, user_id)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200


@posts_bp.route('/<post_id>/comments/<comment_id>/reactions', methods=['POST'])
@jwt_required()
@swag_from('docs/react_comment.yml')
def react_to_comment(post_id: str, comment_id: str):
    """Reacciona a un comentario. Body: {"reaction_type": "like"}."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)

    result = ReactionService.react_to_comment(post_id, comment_id, user_id, data)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))

    status = 201 if result.get("action") == "created" else 200
    return js(result), status


@posts_bp.route('/<post_id>/comments/<comment_id>/reactions', methods=['DELETE'])
@jwt_required()
@swag_from('docs/remove_comment_reaction.yml')
def remove_comment_reaction(post_id: str, comment_id: str):
    """Elimina la reacción del usuario autenticado sobre un comentario."""
    user_id = get_jwt_identity()
    result = ReactionService.remove_comment_reaction(post_id, comment_id, user_id)
    if not result["ok"]:
        return js(result), _status_for_errors(result.get("errors", []))
    return js(result), 200
