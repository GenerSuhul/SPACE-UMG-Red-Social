from flask import request, jsonify as js
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import user_bp
from flasgger import swag_from

from .service import UserService

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
    El usuario se identifica a partir del JWT — no se acepta id en URL ni body.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)

    result = UserService.update_user(user_id, data)

    if not result["ok"]:
        # 404 si el usuario no existe, 400 para validación / conflictos
        errors = result.get("errors", [])
        if any(err.get("field") == "user" for err in errors):
            return js(result), 404
        return js(result), 400

    return js(result), 200