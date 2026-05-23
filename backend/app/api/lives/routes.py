# backend/app/api/lives/routes.py
from flask import jsonify as js, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import lives_bp
from .service import LiveService

@lives_bp.route('/', methods=['POST'])
@jwt_required()
def start_live():
    creator_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    title = data.get("title", "Transmisión en vivo de SPACE UMG")
    
    res = LiveService.start_live(creator_id, title)
    return js(res), 201

@lives_bp.route('/', methods=['GET'])
@jwt_required()
def list_active_lives():
    res = LiveService.list_active()
    return js(res), 200

@lives_bp.route('/<stream_id>/end', methods=['POST'])
@jwt_required()
def end_live(stream_id):
    creator_id = get_jwt_identity()
    res = LiveService.end_live(stream_id, creator_id)
    if not res.get("ok"):
        return js(res), 400
    return js(res), 200

@lives_bp.route('/<stream_id>/heartbeat', methods=['POST'])
@jwt_required()
def live_heartbeat(stream_id):
    res = LiveService.heartbeat(stream_id)
    if not res.get("ok"):
        return js(res), 400
    return js(res), 200
