from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app.r2_storage import (
    upload_avatar,
    upload_post_media,
    upload_reel,
    upload_story,
    upload_chat_media
)

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/avatar", methods=["POST"])
@jwt_required()
def api_upload_avatar():
    file = request.files.get("file") or request.files.get("avatar")
    if not file:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": "No se envió ningún archivo"}]}), 400
    try:
        url = upload_avatar(file)
        return jsonify({"ok": True, "url": url}), 200
    except ValueError as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": str(e)}], "url": None}), 400
    except Exception as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": f"Error interno: {str(e)}"}], "url": None}), 500

@upload_bp.route("/post", methods=["POST"])
@jwt_required()
def api_upload_post():
    file = request.files.get("file") or request.files.get("images") or request.files.get("image")
    if not file:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": "No se envió ningún archivo"}]}), 400
    try:
        url = upload_post_media(file)
        return jsonify({"ok": True, "url": url}), 200
    except ValueError as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": str(e)}], "url": None}), 400
    except Exception as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": f"Error interno: {str(e)}"}], "url": None}), 500

@upload_bp.route("/reel", methods=["POST"])
@jwt_required()
def api_upload_reel():
    file = request.files.get("file") or request.files.get("video")
    if not file:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": "No se envió ningún archivo"}]}), 400
    try:
        url = upload_reel(file)
        return jsonify({"ok": True, "url": url}), 200
    except ValueError as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": str(e)}], "url": None}), 400
    except Exception as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": f"Error interno: {str(e)}"}], "url": None}), 500

@upload_bp.route("/story", methods=["POST"])
@jwt_required()
def api_upload_story():
    file = request.files.get("file") or request.files.get("images") or request.files.get("video")
    if not file:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": "No se envió ningún archivo"}]}), 400
    try:
        url = upload_story(file)
        return jsonify({"ok": True, "url": url}), 200
    except ValueError as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": str(e)}], "url": None}), 400
    except Exception as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": f"Error interno: {str(e)}"}], "url": None}), 500

@upload_bp.route("/chat", methods=["POST"])
@jwt_required()
def api_upload_chat():
    file = request.files.get("file") or request.files.get("images") or request.files.get("video")
    if not file:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": "No se envió ningún archivo"}]}), 400
    try:
        url = upload_chat_media(file)
        return jsonify({"ok": True, "url": url}), 200
    except ValueError as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": str(e)}], "url": None}), 400
    except Exception as e:
        return jsonify({"ok": False, "errors": [{"field": "file", "message": f"Error interno: {str(e)}"}], "url": None}), 500
