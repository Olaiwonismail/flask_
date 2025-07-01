from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required


from app.models import Appointment ,Doctor, Patient

from app import db

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    data = request.get_json()
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
    # return user_email
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    try:
        doctor_id = data['doctor_id']
        patient_id = user.id
        title = data['title']
        description = data['description']
        
        status = data.get('status', 'Pending')  # Default to 'Pending' if not provided
        new_appointment = Appointment(
            title=title,
            description=description,
            
            patient_id=patient_id,
            doctor_id=doctor_id,
            status=status
        )
        print(new_appointment)
        db.session.add(new_appointment)
        db.session.commit()
        return jsonify({'message': 'Appointment created successfully'}), 201
    except KeyError as e:
        return jsonify({'error': f'Missing field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@appointments_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    appointment = Appointment.query.first()
    
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
  
    if not user:
        user =Doctor.query.filter(Doctor.email == user_email).first()
       
  
    print( user.id != appointment.doctor_id)
    if user.id != appointment.patient_id and user.id != appointment.doctor_id:
        return jsonify({'error': 'Unauthorized access to appointment data'}), 403
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    return jsonify({
        'id': appointment.id,
        'title': appointment.title,
        'description': appointment.description,
        'date_created': appointment.date_created.isoformat(),
        'date_appointment': appointment.date_appointment.isoformat(),
        'patient_id': appointment.patient_id,
        'doctor_id': appointment.doctor_id,
        'status': appointment.status
    }), 200

@appointments_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
  
    if not user:
        user =Doctor.query.filter(Doctor.email == user_email).first()

    if user.id != appointment.patient_id and user.id != appointment.doctor_id:
        return jsonify({'error': 'Unauthorized access to appointment data'}), 403
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    try:
        appointment.title = data.get('title', appointment.title)
        appointment.description = data.get('description', appointment.description)
        appointment.date_appointment = data.get('date_appointment', appointment.date_appointment)
        appointment.status = data.get('status', appointment.status)
        db.session.commit()
        return jsonify({'message': 'Appointment updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@appointments_bp.route('/cancel_appointment/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def cancel_appointment(appointment_id):

    appointment = Appointment.query.get(appointment_id)
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
  
    if not user:
        user =Doctor.query.filter(Doctor.email == user_email).first()

    if user.id != appointment.patient_id and user.id != appointment.doctor_id:
        return jsonify({'error': f'Unnauthorized access to appointment { user.id,appointment.doctor_id}'}), 403
    
    appointment.status = 'cancelled'
    db.session.commit()
    return jsonify({'message': 'Appointment cancelled successfully'}), 200

@appointments_bp.route('/appointment_completed/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def appointment_completed(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
  
    if user.id != appointment.patient_id and user.id != appointment.doctor_id:
        return jsonify({'error': 'Unauthorized access to appointment data'}), 403
    
    appointment.status = 'completed'
    # appointment.occured = True
    db.session.commit()
    return jsonify({'message': 'Appointment completed successfully'}), 200


@appointments_bp.route('/confirm_appointment/<int:id>',methods=['PUT'])
@jwt_required()
def confirm_appointment(id):
    # data = request.get_json()
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
  
    if 'doctor'  not in user_role  :
        return jsonify({'error': 'Unauthorized access to confirm appointment'}), 403
    appointment = Appointment.query.get(id)
    appointment.status = 'confirmed'
    db.session.commit()
    return jsonify({'message': 'Appointment confirmed successfully'}), 200    
    
@appointments_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    user_role = get_jwt_identity()
    user_email = get_jwt()["email"]
    user = Patient.query.filter(Patient.email == user_email).first()
  
    if user.id != appointment.patient_id and user.id != appointment.doctor_id:
        return jsonify({'error': 'Unauthorized access to appointment data'}), 403
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    try:
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'message': 'Appointment deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
   