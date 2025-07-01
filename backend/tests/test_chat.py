import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from app import create_app, db
from app.models import Doctor, Patient, Message, CallSession
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        # Create test users
        doctor = Doctor(
            name="Dr. Test",
            specialization="Cardiology",
            experience=10,
            email="doctor@test.com",
            password="password",
            phone_number="1234567890"
        )
        patient = Patient(
            name="Patient Test",
            age=30,
            gender="Male",
            email="patient@test.com",
            password="password",
            phone_number="0987654321"
        )
        db.session.add(doctor)
        db.session.add(patient)
        db.session.commit()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def get_auth_headers(user_type, user_id, email):
    identity = f"{user_type}|{user_id}"
    access_token = create_access_token(
        identity=identity,
        additional_claims={"role": user_type, "email": email}
    )
    return {'Authorization': f'Bearer {access_token}'}

def test_send_message(client):
    # Get doctor and patient
    doctor = Doctor.query.filter_by(email="doctor@test.com").first()
    patient = Patient.query.filter_by(email="patient@test.com").first()
    
    # Doctor sends message to patient
    headers = get_auth_headers('doctor', doctor.id, doctor.email)
    response = client.post('/api/chat/messages/send', json={
        'receiver_type': 'patient',
        'receiver_id': patient.id,
        'content': 'Hello patient'
    }, headers=headers)
    
    assert response.status_code == 201
    assert 'id' in response.json
    
    # Patient sends message to doctor
    headers = get_auth_headers('patient', patient.id, patient.email)
    response = client.post('/api/chat/messages/send', json={
        'receiver_type': 'doctor',
        'receiver_id': doctor.id,
        'content': 'Hello doctor'
    }, headers=headers)
    
    assert response.status_code == 201

def test_get_conversation(client):
    doctor = Doctor.query.filter_by(email="doctor@test.com").first()
    patient = Patient.query.filter_by(email="patient@test.com").first()
    
    # Send a message first
    headers = get_auth_headers('doctor', doctor.id, doctor.email)
    client.post('/api/chat/messages/send', json={
        'receiver_type': 'patient',
        'receiver_id': patient.id,
        'content': 'Test message'
    }, headers=headers)
    
    # Get conversation
    headers = get_auth_headers('patient', patient.id, patient.email)
    response = client.get(f'/api/chat/messages/doctor/{doctor.id}', headers=headers)
    
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['content'] == 'Test message'
    assert response.json[0]['read'] == True

def test_initiate_call(client):
    doctor = Doctor.query.filter_by(email="doctor@test.com").first()
    patient = Patient.query.filter_by(email="patient@test.com").first()
    
    # Doctor initiates call to patient
    headers = get_auth_headers('doctor', doctor.id, doctor.email)
    response = client.post('/api/chat/call/initiate', json={
        'callee_type': 'patient',
        'callee_id': patient.id
    }, headers=headers)
    
    assert response.status_code == 201
    assert 'call_id' in response.json
    
    # Verify call session created
    call_session = CallSession.query.first()
    assert call_session is not None
    assert call_session.caller_id == doctor.id
    assert call_session.callee_id == patient.id

def test_end_call(client):
    doctor = Doctor.query.filter_by(email="doctor@test.com").first()
    patient = Patient.query.filter_by(email="patient@test.com").first()
    
    # Create a call first
    headers = get_auth_headers('doctor', doctor.id, doctor.email)
    response = client.post('/api/chat/call/initiate', json={
        'callee_type': 'patient',
        'callee_id': patient.id
    }, headers=headers)
    call_id = response.json['call_id']
    
    # End the call
    response = client.post(f'/api/chat/call/end/{call_id}', headers=headers)
    assert response.status_code == 200
    
    # Verify call status updated
    call_session = CallSession.query.get(call_id)
    assert call_session.status == 'completed'
    assert call_session.end_time is not None