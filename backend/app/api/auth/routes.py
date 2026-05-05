from flask import request, jsonify
from . import auth_bp
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

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


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@swag_from('docs/logout.yml')
def logout_user():
    """
    Ruta para cerrar sesión: revoca el token JWT actual añadiendo
    su JTI a la blocklist. Tras esta llamada, el token deja de ser
    válido para cualquier endpoint protegido.
    """
    jti = get_jwt().get("jti")
    user_id = get_jwt_identity()

    result = AuthService.logout(jti, user_id)

    if not result["ok"]:
        return jsonify({"ok": False, "errors": result["errors"]}), 400

    return jsonify({"ok": True, "message": "Sesión cerrada exitosamente"}), 200