from flask import request, jsonify as js
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import user_bp
from flasgger import swag_from

from .service import UserService
from backend.app.image_utils import file_storage_to_base64, ImageError


def _parse_user_payload() -> tuple[dict | None, dict | None]:
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
    user_id = get_jwt_identity()
    result = UserService.find_by_id(user_id)

    if not result["ok"]:
        return js(result), 400

    return js(result), 200


@user_bp.route('/update_me', methods=['PUT', 'PATCH'])
@jwt_required()
@swag_from('docs/update_me.yml')
def update_me():
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


@user_bp.route('/search', methods=['GET'])
@jwt_required()
@swag_from('docs/search_users.yml')
def search_users():
    query = request.args.get("q", "").strip()
    try:
        limit = int(request.args.get("limit", 20))
    except (ValueError, TypeError):
        limit = 20

    result = UserService.search_users(query, limit=limit)
    if not result["ok"]:
        return js(result), 400
    return js(result), 200


@user_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
@swag_from('docs/get_user_by_id.yml')
def get_user_by_id(user_id: str):
    current_user_id = get_jwt_identity()
    result = UserService.get_public_profile(user_id, current_user_id)
    if not result["ok"]:
        errors = result.get("errors", [])
        if any(err.get("field") == "user" for err in errors):
            return js(result), 404
        return js(result), 400
    return js(result), 200


@user_bp.route('/me/follows', methods=['GET'])
@jwt_required()
@swag_from('docs/my_follows.yml')
def my_follows():
    user_id = get_jwt_identity()
    result = UserService.get_my_follow_lists(user_id)
    if not result["ok"]:
        return js(result), 400
    return js(result), 200


@user_bp.route('/follow/<target_user_id>', methods=['POST'])
@jwt_required()
@swag_from('docs/toggle_follow.yml')
def toggle_follow(target_user_id: str):
    current_user_id = get_jwt_identity()
    result = UserService.toggle_follow(current_user_id, target_user_id)

    if not result["ok"]:
        errors = result.get("errors", [])
        if any(err.get("field") == "user" for err in errors):
            return js(result), 404
        return js(result), 400

    return js(result), 200
