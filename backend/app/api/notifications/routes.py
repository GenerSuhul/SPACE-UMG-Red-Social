# backend/app/api/notifications/routes.py
from flask import jsonify as js, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import notifications_bp
from .service import NotificationService

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    try:
        limit = int(request.args.get("limit", 20))
    except:
        limit = 20
    result = NotificationService.list_notifications(user_id, limit=limit)
    return js(result), 200

@notifications_bp.route('/read', methods=['POST'])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    result = NotificationService.mark_all_read(user_id)
    return js(result), 200
