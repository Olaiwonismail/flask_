from flask import jsonify, render_template, url_for, flash, redirect, request, Blueprint


from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Doctor, Patient
from app import db

doctor_bp = Blueprint('doctors', __name__)

@doctor_bp.route('/get_doctors_data', methods=['POST'])
@jwt_required()
def get_doctors_data():
    id = request.json.get('id')
    
    if not id:
        return {'error': 'No doctor ID provided'}, 400
 
    doctor = Doctor.query.get(id)
    if not doctor:
        return {'error': 'Doctor not found'}, 404
    return {
        'id': doctor.id,
        'name': doctor.name,
        'email': doctor.email,
        'specialization': doctor.specialization,
        'phone_number': doctor.phone_number,
        'experience': doctor.experience,
        
    }, 200


@doctor_bp.route('/get_doctors_appointment', methods=['POST'])
@jwt_required()
def get_doctors_appointment():
    id = request.json.get('id')
    user = Doctor.query.get(id)
    
    if not id:
        return {'error': 'No doctor ID provided'}, 400
    
    if id != user.id:
        return {'error': 'Unauthorized access to doctor appointments'}, 403
    
    appointments = Doctor.query.filter_by(id=id).first().appointments
    if not appointments:
        return {'error': 'No appointments found for this doctor'}, 404
    
    appointments_data = []
    for appointment in appointments:
        appointments_data.append({
            'id': appointment.id,
            'title': appointment.title,
            'description': appointment.description,
            'date_created': appointment.date_created.isoformat(),
            'date_appointment': appointment.date_appointment.isoformat(),
            'patient_id': appointment.patient_id,
            'doctor_id': appointment.doctor_id,
            'status': appointment.status
        })
    
    return {'appointments':appointments_data}, 200


@doctor_bp.route('/get_patients_by_doctor', methods=['POST'])
@jwt_required()
def get_patients_by_doctor():
    doctor_id = request.json.get('id')
    
    # Validate doctor ID
    if not doctor_id:
        return jsonify({'error': 'Doctor ID is required'}), 400
    
    # Verify doctor exists
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    # Authorization check - ensure logged-in doctor matches requested ID
    if doctor_id != doctor.id:
        return jsonify({'error': 'Unauthorized access to doctor data'}), 403
    
    # Get distinct patients from appointments
    appointments = doctor.appointments
    
    if not appointments:
        return jsonify({'error': 'No appointments found for this doctor'}), 404
    
    # Collect unique patient IDs
    patient_ids = {app.patient_id for app in appointments}
    
    # Retrieve patient details
    patients = []
    for patient_id in patient_ids:
        patient = Patient.query.get(patient_id)
        if patient:
            patients.append({
                'id': patient.id,
                'name': patient.name,
                'email': patient.email,
                'phone': patient.phone_number,
                'age': patient.age,
                'gender': patient.gender
            })
    
    return jsonify({'patients': patients}), 200