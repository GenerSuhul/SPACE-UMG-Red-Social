# backend/app/api/lives/__init__.py
from flask import Blueprint

lives_bp = Blueprint('lives', __name__)

from . import routes
