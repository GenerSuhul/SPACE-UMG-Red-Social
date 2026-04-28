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