from flask import request, jsonify
from . import auth_bp

@auth_bp.route('/', methods=['GET'])
def auth():
    return jsonify({"message": "Auth route is working!"})