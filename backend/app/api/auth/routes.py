from flask import request, jsonify
from . import auth_bp
from flasgger import swag_from

@auth_bp.route('/', methods=['GET'])
@swag_from("docs/base.yml")
def auth():
    """
    Ruta base de pruebas
    """
    return jsonify({"message": "Auth route is working!"})

@auth_bp.route('/login', methods=['POST'])
@swag_from("docs/login.yml")
def login():
    """
    Login de usuario
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    return jsonify({"message": f"Login attempt for user: {username}"})