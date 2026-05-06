from flask import request, jsonify as js
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import user_bp
from flasgger import swag_from

from .service import UserService
from backend.app.image_utils import file_storage_to_base64, ImageError


def _parse_user_payload() -> tuple[dict | None, dict | None]:
    """
    Lee el body de la request soportando:
      - application/json puro
      - multipart/form-data (campos de texto + archivo `avatar`)

    Devuelve (payload_dict, error_dict).
    """
    content_type = (request.content_type or "").lower()

    if "multipart/form-data" in content_type:
        data: dict = {}
        for key, value in request.form.items():
            data[key] = value

        file = request.files.get("avatar")
        if file is not None and getattr(file, "filename", ""):
            try:
                b64, mime = file_storage_to_base64(file)
            except ImageError as ex:
                return None, {
                    "ok": False,
                    "errors": [{"field": "avatar", "message": str(ex)}],
                }
            data["avatar_base64"] = b64
            data["avatar_mime"]   = mime
        return data, None

    return request.get_json(silent=True), None


@user_bp.route('/get_user', methods=['GET'])
@jwt_required()
@swag_from('docs/get_user.yml')
def get_user():
    """
    Api para visualizar datos del usuario
    """
    user_id = get_jwt_identity()
    result = UserService.find_by_id(user_id)

    if not result["ok"]:
        return js(result), 400

    return js(result), 200


@user_bp.route('/update_me', methods=['PUT', 'PATCH'])
@jwt_required()
@swag_from('docs/update_me.yml')
def update_me():
    """
    Api para actualizar parcialmente los datos del usuario autenticado.
    Acepta application/json o multipart/form-data (para subir avatar).
    El usuario se identifica a partir del JWT — no se acepta id en URL ni body.
    """
    user_id = get_jwt_identity()
    data, image_err = _parse_user_payload()
    if image_err:
        return js(image_err), 400

    result = UserService.update_user(user_id, data)

    if not result["ok"]:
        errors = result.get("errors", [])
        if any(err.get("field") == "user" for err in errors):
            return js(result), 404
        return js(result), 400

    return js(result), 200
