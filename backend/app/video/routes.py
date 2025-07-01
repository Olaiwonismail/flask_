from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_identity
from app import db, socketio
from app.models import CallSession, Doctor, Patient
import uuid
import datetime

video_bp = Blueprint('video', __name__)

def get_user_role_and_id():
    """Get current user's role and ID based on JWT"""
    user_id = current_identity.id
    if Doctor.query.get(user_id):
        return 'doctor', user_id
    elif Patient.query.get(user_id):
        return 'patient', user_id
    return None, None

@video_bp.route('/initiate', methods=['POST'])
@jwt_required()
def initiate_call():
    data = request.get_json()
    callee_email = data.get('callee_email')
    
    caller_role, caller_id = get_user_role_and_id()
    
    # Find callee
    callee = Doctor.query.filter_by(email=callee_email).first() or \
             Patient.query.filter_by(email=callee_email).first()
    
    if not callee:
        return jsonify({'error': 'User not found'}), 404
    
    callee_role = 'doctor' if isinstance(callee, Doctor) else 'patient'
    
    # Create call session
    call_id = str(uuid.uuid4())
    call_session = CallSession(
        id=call_id,
        caller_id=caller_id,
        caller_role=caller_role,
        callee_id=callee.id,
        callee_role=callee_role
    )
    
    db.session.add(call_session)
    db.session.commit()
    
    # Notify callee
    socketio.emit('incoming_call', {
        'call_id': call_id,
        'caller_id': caller_id,
        'caller_role': caller_role
    }, room=callee.email)
    
    return jsonify({
        'call_id': call_id,
        'message': 'Call initiated'
    }), 201

@video_bp.route('/end/<call_id>', methods=['POST'])
@jwt_required()
def end_call(call_id):
    call_session = CallSession.query.get(call_id)
    if not call_session:
        return jsonify({'error': 'Call not found'}), 404
    
    call_session.status = 'completed'
    call_session.end_time = datetime.datetime.utcnow()
    db.session.commit()
    
    # Notify both parties
    socketio.emit('call_ended', {'call_id': call_id}, room=get_user_email(call_session.caller_id, call_session.caller_role))
    socketio.emit('call_ended', {'call_id': call_id}, room=get_user_email(call_session.callee_id, call_session.callee_role))
    
    return jsonify({'message': 'Call ended'}), 200

def get_user_email(user_id, role):
    if role == 'doctor':
        return Doctor.query.get(user_id).email
    return Patient.query.get(user_id).email

# WebRTC signaling endpoints
@video_bp.route('/webrtc/config')
@jwt_required()
def webrtc_config():
    return jsonify({
        'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]
    }), 200