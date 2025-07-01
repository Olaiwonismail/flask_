


from flask import Flask,Blueprint, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
import datetime
from app import db , bcrypt
from app.models import Patient,Doctor,BlacklistedToken
# from flask_bcrypt import bcrypt

auth = Blueprint('users',__name__)
SECRET_KEY = "access-secret"
REFRESH_SECRET = "refresh-secret"

# In-memory blacklist (use Redis or DB in production)
try:
    blacklisted_refresh_tokens = BlacklistedToken.query.all()
except:
    blacklisted_refresh_tokens = set()





def generate_tokens(user):
    # Determine user type and ID
    
    if user['type'] != 'patient' and user['type']!='doctor':
        
        raise ValueError("Invalid user type")
        
    
    # Create identity with type and ID
    identity = f"{user['type']}|{user['id']}"
    
    access_token = create_access_token(
        identity=identity,
        additional_claims={
            "role": user['type'] if hasattr(user, 'role') else user['type'],
            "email": user['email']
        },
        expires_delta=datetime.timedelta(days=7)
    )
    
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims={
            "role": user['role'] if hasattr(user, 'role') else user['type'],
            "email": user['email']
        },
        expires_delta=datetime.timedelta(days=7)
    )
    return access_token, refresh_token

@auth.route("/register", methods=["POST"])
def register():
    
    data = request.json
    if "name" not in data or "role" not in data or "password" not in data or "email" not in data:
        return jsonify({"error": "Missing fields"}), 400
    
    hashed_password =bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    # generate_password_hash(data["password"]).decode('utf-8')
    if data['role'] == 'doctor':
        if Doctor.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 400
        user = Doctor(
            name=data["name"],
            specialization=data.get("specialization"),
            experience=data.get("experience"),
            email=data.get("email"),
            password=hashed_password,
            phone_number=data.get("phone_number")
        )
    elif data['role'] == 'patient':
        if Patient.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 400
        user = Patient(
            name=data["name"],
            age=data.get("age"),
            gender=data.get("gender"),
            email=data.get("email"),
            password=hashed_password,
            phone_number=data.get("phone_number")
        )
    

    
    db.session.add(user)
    db.session.commit()
    
    # Here you would typically save the user to a database
    return jsonify({"message": "User registered successfully"}), 201



@auth.route("/login", methods=["POST"])
def login():
    
    data = request.json
    if "email" not in data or "password" not in data:
        
        return jsonify({"error": "Missing fields"}), 400
    user = Patient.query.filter_by(email=data["email"]).first()
    if not user:
        user = Doctor.query.filter_by(email=data["email"]).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        

    
    identity={'email': user.email, 'type': user.role,'id':user.id}
    if user and bcrypt.check_password_hash(user.password, data["password"]):
        
        access_token, refresh_token = generate_tokens(identity)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            'role': user.role,
        })

    return jsonify({"error": "Invalid credentials"}), 401


from flask_jwt_extended import get_jwt

@auth.route("/dashboard", methods=["POST"])
@jwt_required(refresh=True)
def protected():
    email = get_jwt_identity()
    role = get_jwt()["role"]
    access_token = create_access_token(
        identity=email,
        additional_claims={"role": role},
        expires_delta=datetime.timedelta(minutes=15)
    )
    return jsonify({"access_token": access_token})

from flask_jwt_extended import get_jwt

@auth.route('/user_info',methods=['POST'])
@jwt_required()
def user_info():
    email = get_jwt_identity()
    user = Patient.query.filter_by(email=email).first()
    if not user:
        user = Doctor.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
    user_data = {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone_number": user.phone_number,
    }

@auth.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]  # Unique ID of this token
    db.session.add(BlacklistedToken(token=jti))
    db.session.commit()
    return jsonify({"message": "Logged out"})




