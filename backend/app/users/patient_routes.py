from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
patient_bp = Blueprint('patients', __name__)

from app.models import Appointment, Doctor, Patient
from app import db

@patient_bp.route('/get_patients_data', methods=['POST'])
@jwt_required()
def get_patients_data():
    id = request.json.get('id')
    # user_email = get_jwt_identity()
    patient = Patient.query.get(id)
    print(patient)

    if not id:
        return jsonify({'error': 'No patient ID provided'}), 400
    if id != patient.id and patient.role != 'doctor':
        return jsonify({'error': 'Unauthorized access to patient data'}), 403
    patient = Patient.query.get(id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    return jsonify({
        'id': patient.id,
        'name': patient.name,
        'email': patient.email,
        'phone': patient.phone_number,
        'age': patient.age,
        'gender': patient.gender,
        
    })
    

@patient_bp.route('/get_patients_appointment',methods=['POST'])
@jwt_required()
def get_patients_appointment():
    id = request.json.get('id')
    
    patient = Patient.query.filter_by(id=id).first()

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    if id != patient.id:
        return jsonify({"error": "Unauthorized access"}), 403

    if not id:
        return jsonify({'error': 'No patient ID provided'}), 400
    if id != patient.id:
        return jsonify({'error': 'Unauthorized access to patient appointments'}), 403
    appointment = Appointment.query.filter_by(patient_id=id).all()
    if not appointment:
        return jsonify({'error': 'No appointments found for this patient'}), 404
    appointments_data = []
    print('hyrhrhr') 
    for apps in appointment:
        appointments_data.append({
            'id': apps.id,
            'title': apps.title,
            'description': apps.description,
            'date_created': apps.date_created.isoformat(),
            'date_appointment': apps.date_appointment.isoformat(),
            'patient_id': apps.patient_id,
            'doctor_id': apps.doctor_id,
            'status': apps.status
        })
    print(appointments_data)    
    return {'appointments':appointments_data}, 200 

@patient_bp.route('/get_doctors_by_patient', methods=['POST'])
@jwt_required()
def get_doctors_by_patient():
    patient_id = request.json.get('id')
    
    # Validate patient ID
    if not patient_id:
        return jsonify({'error': 'Patient ID is required'}), 400
    
    # Verify patient exists
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Authorization check
    if patient_id != patient.id:
        return jsonify({'error': 'Unauthorized access to patient data'}), 403
    
    # Get distinct doctors from appointments
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    
    if not appointments:
        return jsonify({'error': 'No appointments found for this patient'}), 404
    
    # Collect unique doctor IDs
    doctor_ids = {app.doctor_id for app in appointments}
    
    # Retrieve doctor details
    doctors = []
    for doc_id in doctor_ids:
        doctor = Doctor.query.get(doc_id)
        if doctor:
            doctors.append({
                'id': doctor.id,
                'name': doctor.name,
                'specialization': doctor.specialization,
                'email': doctor.email,
                'phone_number': doctor.phone_number,
                'experience': doctor.experience
            })
    
    return jsonify({'doctors': doctors}), 200