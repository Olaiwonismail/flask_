
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flasgger import Swagger
from app.config import Config
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

socketio = SocketIO(cors_allowed_origins="*")




# Bootstrap()
db = SQLAlchemy()
bcrypt =Bcrypt()
# login_manager = LoginManager()
# login_manager.login_view = 'users.login'
# login_manager.login_message_category = 'info'
swagger = Swagger()
jwt = JWTManager()

def create_app(config_class = Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    # login_manager.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*",async_mode='eventlet')
    app.app_context().push()

    # from  backend.app.users.doctor_routes import user
    from app.main.routes import main
    from app.auth.routes import auth
    from app.users.doctor_routes import doctor_bp
    from app.users.patient_routes import patient_bp
    from app.chat.routes import chat_bp
    # from app.errors.handlers import errors
    from app.appointments.routes import appointments_bp

    # app.register_blueprint(user)
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(chat_bp)
    # app.register_blueprint(errors)
    CORS(app)
    
    swagger.init_app(app)

    return app
