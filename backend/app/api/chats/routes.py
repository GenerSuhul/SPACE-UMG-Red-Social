# backend/app/api/chats/routes.py
from flask import jsonify as js, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import chats_bp
from .service import ChatService

@chats_bp.route('/', methods=['POST'])
@jwt_required()
def get_or_create_chat():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    other_user_id = data.get("other_user_id")
    
    if not other_user_id:
        return js({"ok": False, "errors": [{"field": "other_user_id", "message": "other_user_id es requerido"}]}), 400
        
    res = ChatService.get_or_create_chat(user_id, other_user_id)
    if not res.get("ok"):
        return js(res), 400
    return js(res), 200

@chats_bp.route('/', methods=['GET'])
@jwt_required()
def list_chats():
    user_id = get_jwt_identity()
    res = ChatService.list_my_chats(user_id)
    return js(res), 200

@chats_bp.route('/<chat_id>/messages', methods=['GET'])
@jwt_required()
def list_messages(chat_id):
    user_id = get_jwt_identity()
    try:
        limit = int(request.args.get("limit", 50))
    except:
        limit = 50
    try:
        page = int(request.args.get("page", 1))
    except:
        page = 1
        
    res = ChatService.get_messages(chat_id, user_id, limit=limit, page=page)
    if not res.get("ok"):
        return js(res), 400
    return js(res), 200

@chats_bp.route('/<chat_id>/messages', methods=['POST'])
@jwt_required()
def send_message(chat_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    content = data.get("content")
    media_url = data.get("media_url")
    media_type = data.get("media_type")
    
    if not content and not media_url:
        return js({"ok": False, "errors": [{"field": "content", "message": "content o media_url es requerido"}]}), 400
        
    res = ChatService.send_message(chat_id, user_id, content, media_url=media_url, media_type=media_type)
    if not res.get("ok"):
        return js(res), 400
    return js(res), 200

@chats_bp.route('/<chat_id>/read', methods=['POST'])
@jwt_required()
def mark_read(chat_id):
    user_id = get_jwt_identity()
    res = ChatService.mark_chat_read(chat_id, user_id)
    if not res.get("ok"):
        return js(res), 400
    return js(res), 200
