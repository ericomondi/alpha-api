#C:\flask_dev\flaskreact\app.py
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token,get_jwt,get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager #pip install Flask-JWT-Extended = https://pypi.org/project/Flask-JWT-Extended/
from flask_bcrypt import Bcrypt #pip install Flask-Bcrypt = https://pypi.org/project/Flask-Bcrypt/
from flask_cors import CORS #ModuleNotFoundError: No module named 'flask_cors' = pip install Flask-Cors
 
from models import db, User, app

CORS(app, supports_credentials=True)
 
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)
 
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True
 
bcrypt = Bcrypt(app)    
db.init_app(app)
  
with app.app_context():
    db.create_all()

