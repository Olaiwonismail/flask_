from datetime import datetime
from app import db
from flask_login import UserMixin
from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer as Serializer


# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

class User(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(20),unique=True,nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    image_file = db.Column(db.String(20),nullable=False,default = 'image.png')
    password = db.Column(db.String(50),nullable=False)
    

    # def get_reset_token(self):
    #     s = Serializer(current_app.config['SECRET_KEY'])
    #     return s.dumps({'user_id':self.id})

    # @staticmethod
    # def verify_reset_token(token):
    #     s = Serializer(current_app.config['SECRET_KEY'])
    #     try:
    #         user_id = s.loads(token)['user_id']
    #     except:
    #         return None
    #     return User.query.get(user_id)

    def __repr__(self):
        return f' User {self.username} ,{self.email} ,{self.image_file}'


