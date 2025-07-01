from datetime import datetime
import uuid
from app import db
from flask_login import UserMixin
from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer as Serializer



class Doctor(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(100),nullable=False)
    specialization = db.Column(db.String(100),nullable=False)
    experience = db.Column(db.Integer,nullable=False)
    date_created = db.Column(db.DateTime,default=datetime.utcnow)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(),nullable=False)
    role = db.Column(db.String(20),default='doctor')  # doctor, admin
    phone_number = db.Column(db.String(15),nullable=False)
    appointments = db.relationship('Appointment',backref='doctor',lazy=True)

class Patient(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(100),nullable=False)
    age = db.Column(db.Integer,nullable=False)
    gender = db.Column(db.String(10),nullable=False)
    date_created = db.Column(db.DateTime,default=datetime.utcnow)
    appointments = db.relationship('Appointment',backref='patient',lazy=True)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(),nullable=False)
    role = db.Column(db.String(20),default='patient')  # doctor, admin

    phone_number = db.Column(db.String(15),nullable=False)


class Appointment(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    title = db.Column(db.String(100),nullable=False)
    description = db.Column(db.Text,nullable=False)
    date_created = db.Column(db.DateTime,default=datetime.utcnow)
    date_appointment = db.Column(db.DateTime,nullable=False,default = datetime.utcnow)
    patient_id = db.Column(db.Integer,db.ForeignKey('patient.id'),nullable=False)
    doctor_id = db.Column(db.Integer,db.ForeignKey('doctor.id'),nullable=False)
    status = db.Column(db.String(20),default='Pending')  # Pending, Confirmed, Cancelled,Completed
    # occured = db.Column(db.Boolean, default=False)  # To track if the appointment has occurred
    # patient = db.relationship('Patient', backref='appointments')
    # doctor = db.relationship('Doctor', backref='appointments')
    def __repr__(self):
        return f'Appointment {self.title} on {self.date_appointment}'
    
class BlacklistedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # 'doctor' or 'patient'
    receiver_id = db.Column(db.Integer, nullable=False)
    receiver_type = db.Column(db.String(10), nullable=False)  # 'doctor' or 'patient'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class CallSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    caller_id = db.Column(db.Integer, nullable=False)
    caller_type = db.Column(db.String(10), nullable=False)  # 'doctor' or 'patient'
    callee_id = db.Column(db.Integer, nullable=False)
    callee_type = db.Column(db.String(10), nullable=False)  # 'doctor' or 'patient'
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='initiated')  # initiated, ongoing, completed