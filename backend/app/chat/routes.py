# app/routes/chat.py
import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_socketio import emit, join_room
from app import db, socketio
from app.models import Message, CallSession, Doctor, Patient

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Helper to parse identity
def get_current_user():
    identity = get_jwt_identity()
    user_type, user_id = identity.split('|')
    return {'type': user_type, 'id': int(user_id)}

# ======================
# MESSAGING ENDPOINTS
# ======================

@chat_bp.route('/messages/send', methods=['POST'])
@jwt_required()
def send_message():
    current_user = get_current_user()
    data = request.get_json()
    
    # Validate input
    required = ['receiver_type', 'receiver_id', 'content']
    if not all(key in data for key in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create new message
    new_message = Message(
        sender_id=current_user['id'],
        sender_type=current_user['type'],
        receiver_id=data['receiver_id'],
        receiver_type=data['receiver_type'],
        content=data['content']
    )
    print(f"Sending message from {current_user['type']} {current_user['id']} to {data['receiver_type']} {data['receiver_id']}: {data['content']}")
    db.session.add(new_message)
    db.session.commit()
    
    # Notify receiver via SocketIO
    receiver_room = f"{data['receiver_type']}_{data['receiver_id']}"
    socketio.emit('new_message', {
        'id': new_message.id,
        'sender_id': current_user['id'],
        'sender_type': current_user['type'],
        'content': new_message.content,
        'timestamp': new_message.timestamp.isoformat()
    }, room=receiver_room)
    
    return jsonify({
        'message': 'Message sent',
        'id': new_message.id
    }), 201

@chat_bp.route('/messages/<receiver_type>/<int:receiver_id>', methods=['GET'])
@jwt_required()
def get_conversation(receiver_type, receiver_id):
    current_user = get_current_user()
    
    # Get conversation
    messages = Message.query.filter(
        (((Message.sender_type == current_user['type']) & 
          (Message.sender_id == current_user['id']) &
          (Message.receiver_type == receiver_type) &
          (Message.receiver_id == receiver_id)) |
         ((Message.sender_type == receiver_type) & 
          (Message.sender_id == receiver_id) &
          (Message.receiver_type == current_user['type']) &
          (Message.receiver_id == current_user['id'])))
    ).order_by(Message.timestamp.asc()).all()
    
    # Mark received messages as read
    for msg in messages:
        if (msg.receiver_type == current_user['type'] and 
            msg.receiver_id == current_user['id'] and 
            not msg.read):
            msg.read = True
    db.session.commit()
    
    return jsonify([{
        'id': m.id,
        'sender_type': m.sender_type,
        'sender_id': m.sender_id,
        'content': m.content,
        'timestamp': m.timestamp.isoformat(),
        'read': m.read
    } for m in messages]), 200

# ======================
# VIDEO CALL ENDPOINTS
# ======================

@chat_bp.route('/call/initiate', methods=['POST'])
@jwt_required()
def initiate_call():
    current_user = get_current_user()
    data = request.get_json()
    
    # Validate input
    if not all(key in data for key in ['callee_type', 'callee_id']):
        return jsonify({'error': 'Missing callee information'}), 400
    
    # Create call session
    call_session = CallSession(
        caller_id=current_user['id'],
        caller_type=current_user['type'],
        callee_id=data['callee_id'],
        callee_type=data['callee_type'],
    )
    
    db.session.add(call_session)
    db.session.commit()
    
    # Notify callee via SocketIO
    callee_room = f"{data['callee_type']}_{data['callee_id']}"
    socketio.emit('incoming_call', {
        'call_id': call_session.id,
        'caller': {
            'type': current_user['type'],
            'id': current_user['id']
        }
    }, room=callee_room)
    
    return jsonify({
        'call_id': call_session.id,
        'status': 'initiated'
    }), 201

@chat_bp.route('/call/end/<call_id>', methods=['POST'])
@jwt_required()
def end_call(call_id):
    current_user = get_current_user()
    call_session = CallSession.query.get(call_id)
    
    if not call_session:
        return jsonify({'error': 'Call session not found'}), 404
    
    # Verify user is part of the call
    if not ((current_user['type'] == call_session.caller_type and 
             current_user['id'] == call_session.caller_id) or
            (current_user['type'] == call_session.callee_type and 
             current_user['id'] == call_session.callee_id)):
        return jsonify({'error': 'Not authorized'}), 403
    
    # Update call status
    call_session.status = 'completed'
    call_session.end_time = datetime.datetime.utcnow()
    db.session.commit()
    
    # Notify both parties
    caller_room = f"{call_session.caller_type}_{call_session.caller_id}"
    callee_room = f"{call_session.callee_type}_{call_session.callee_id}"
    
    socketio.emit('call_ended', {
        'call_id': call_id
    }, room=caller_room)
    socketio.emit('call_ended', {
        'call_id': call_id
    }, room=callee_room)
    
    return jsonify({'message': 'Call ended'}), 200

# ======================
# SOCKETIO HANDLERS
# ======================
from flask_jwt_extended import decode_token

@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    if not token:
        return False
    
    try:
        # Use Flask-JWT-Extended's decoder
        decoded = decode_token(token)
        identity = decoded['sub']
        user_type, user_id = identity.split('|')
        
        # Join user's personal room
        user_room = f"{user_type}_{user_id}"
        join_room(user_room)
        emit('connected', {'status': 'authenticated'})
        
    except Exception as e:
        current_app.logger.error(f"SocketIO auth failed: {str(e)}")
        return False
    
@socketio.on('webrtc_offer')
def handle_offer(data):
    # Forward offer to callee
    target_room = f"{data['callee_type']}_{data['callee_id']}"
    emit('webrtc_offer', data, room=target_room)

@socketio.on('webrtc_answer')
def handle_answer(data):
    # Forward answer to caller
    target_room = f"{data['caller_type']}_{data['caller_id']}"
    emit('webrtc_answer', data, room=target_room)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    # Forward ICE candidate
    target_room = f"{data['target_type']}_{data['target_id']}"
    emit('ice_candidate', data, room=target_room)

@socketio.on('accept_call')
def handle_accept_call(data):
    call_id = data['call_id']
    call_session = CallSession.query.get(call_id)
    
    if call_session:
        call_session.status = 'ongoing'
        db.session.commit()
        
        # Notify caller
        caller_room = f"{call_session.caller_type}_{call_session.caller_id}"
        emit('call_accepted', {'call_id': call_id}, room=caller_room)

@socketio.on('reject_call')
def handle_reject_call(data):
    call_id = data['call_id']
    call_session = CallSession.query.get(call_id)
    
    if call_session:
        call_session.status = 'completed'
        call_session.end_time = datetime.datetime.utcnow()
        db.session.commit()
        
        # Notify caller
        caller_room = f"{call_session.caller_type}_{call_session.caller_id}"
        emit('call_rejected', {'call_id': call_id}, room=caller_room)