from flask import request, jsonify
from . import auth_bp
from flasgger import swag_from

from .services import AuthService

@auth_bp.route('/register', methods=['POST'])
@swag_from('docs/register.yml')
def register_user():
    """
    Ruta de registro de usuario
    """
    data = request.get_json()

    result = AuthService.register(data)

    if not result["ok"]:
        return jsonify({"ok": False, "errors": result["errors"]}), 400
    
    return jsonify({"ok": True, "user_id": result["user_id"]}), 201

@auth_bp.route('/login', methods=['POST'])
@swag_from('docs/login.yml')
def login_user():
    """
    Ruta para login de usuarios
    """

    data = request.get_json()

    result = AuthService.login(data)

    if not result["ok"]:
        return jsonify({"ok": False, "errors": result["errors"]}), 400
    
    return jsonify({"ok": True, "token": result["access_token"]}), 201