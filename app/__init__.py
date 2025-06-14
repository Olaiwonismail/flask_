
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from app.config import Config




# Bootstrap()
db = SQLAlchemy()
bcrypt =Bcrypt()
# login_manager = LoginManager()
# login_manager.login_view = 'users.login'
# login_manager.login_message_category = 'info'


def create_app(config_class = Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    # login_manager.init_app(app)
    
    app.app_context().push()

    from app.users.routes import users
    from app.main.routes import main
    from app.auth.routes import auth
    from app.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    return app
