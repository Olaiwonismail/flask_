import pytest
import socketio
from app import create_app, db
from app.models import CallSession, Doctor, Patient

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        doctor = Doctor(
            name="Dr. Socket",
            specialization="Neurology",
            experience=8,
            email="socket_doctor@test.com",
            password="password",
            phone_number="1112223333"
        )
        patient = Patient(
            name="Socket Patient",
            age=25,
            gender="Female",
            email="socket_patient@test.com",
            password="password",
            phone_number="4445556666"
        )
        db.session.add(doctor)
        db.session.add(patient)
        db.session.commit()
        yield app
        db.drop_all()

@pytest.fixture
def sio_client(app):
    client = socketio.Client()
    yield client
    client.disconnect()

def test_socket_connection(app, sio_client):
    doctor = Doctor.query.filter_by(email="socket_doctor@test.com").first()
    
    # Create token for connection
    with app.app_context():
        from flask_jwt_extended import create_access_token
        identity = f"doctor|{doctor.id}"
        token = create_access_token(
            identity=identity,
            additional_claims={"role": "doctor", "email": doctor.email}
        )
    
    # Connect with token
    sio_client.connect(
        'http://localhost:5000', 
        headers={'Authorization': f'Bearer {token}'},
        transports=['websocket']
    )
    assert sio_client.connected

def test_message_events(app, sio_client):
    doctor = Doctor.query.filter_by(email="socket_doctor@test.com").first()
    patient = Patient.query.filter_by(email="socket_patient@test.com").first()
    
    # Create tokens
    with app.app_context():
        from flask_jwt_extended import create_access_token
        doctor_identity = f"doctor|{doctor.id}"
        doctor_token = create_access_token(
            identity=doctor_identity,
            additional_claims={"role": "doctor", "email": doctor.email}
        )
        patient_identity = f"patient|{patient.id}"
        patient_token = create_access_token(
            identity=patient_identity,
            additional_claims={"role": "patient", "email": patient.email}
        )
    
    # Setup patient client
    patient_client = socketio.Client()
    patient_client.connect(
        'http://localhost:5000', 
        headers={'Authorization': f'Bearer {patient_token}'},
        transports=['websocket']
    )
    
    # Setup doctor client
    sio_client.connect(
        'http://localhost:5000', 
        headers={'Authorization': f'Bearer {doctor_token}'},
        transports=['websocket']
    )
    
    # Doctor sends message to patient
    message_received = False
    def handle_message(data):
        nonlocal message_received
        message_received = True
        assert data['content'] == 'Socket test'
    
    patient_client.on('new_message', handle_message)
    
    sio_client.emit('send_message', {
        'receiver_type': 'patient',
        'receiver_id': patient.id,
        'content': 'Socket test'
    })
    
    # Wait for event
    patient_client.sleep(1)
    assert message_received
    
    patient_client.disconnect()

def test_call_events(app, sio_client):
    doctor = Doctor.query.filter_by(email="socket_doctor@test.com").first()
    patient = Patient.query.filter_by(email="socket_patient@test.com").first()
    
    # Create tokens
    with app.app_context():
        from flask_jwt_extended import create_access_token
        doctor_identity = f"doctor|{doctor.id}"
        doctor_token = create_access_token(
            identity=doctor_identity,
            additional_claims={"role": "doctor", "email": doctor.email}
        )
        patient_identity = f"patient|{patient.id}"
        patient_token = create_access_token(
            identity=patient_identity,
            additional_claims={"role": "patient", "email": patient.email}
        )
    
    # Setup patient client
    patient_client = socketio.Client()
    patient_client.connect(
        'http://localhost:5000', 
        headers={'Authorization': f'Bearer {patient_token}'},
        transports=['websocket']
    )
    
    # Setup doctor client
    sio_client.connect(
        'http://localhost:5000', 
        headers={'Authorization': f'Bearer {doctor_token}'},
        transports=['websocket']
    )
    
    # Test incoming call
    call_received = False
    def handle_incoming_call(data):
        nonlocal call_received
        call_received = True
        assert data['caller']['id'] == doctor.id
        assert data['caller']['type'] == 'doctor'
    
    patient_client.on('incoming_call', handle_incoming_call)
    
    # Doctor initiates call
    sio_client.emit('initiate_call', {
        'callee_type': 'patient',
        'callee_id': patient.id
    })
    
    # Wait for event
    patient_client.sleep(1)
    assert call_received
    
    # Test call acceptance
    call_accepted = False
    def handle_call_accepted(data):
        nonlocal call_accepted
        call_accepted = True
    
    sio_client.on('call_accepted', handle_call_accepted)
    
    # Patient accepts call
    call_session = CallSession.query.filter_by(
        caller_id=doctor.id,
        callee_id=patient.id
    ).first()
    
    patient_client.emit('accept_call', {'call_id': call_session.id})
    
    # Wait for event
    sio_client.sleep(1)
    assert call_accepted
    
    # Clean up
    patient_client.disconnect()