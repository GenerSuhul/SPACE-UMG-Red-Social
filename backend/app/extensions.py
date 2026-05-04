# app/extensions.py
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from flask_cors import CORS

# Se crean SIN app — se vinculan luego con init_app()
# Esto es el patrón correcto para evitar importaciones circulares.
mongo   = PyMongo()
jwt     = JWTManager()
swagger = Swagger()
cors    = CORS()