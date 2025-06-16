
from flask import Blueprint

auth = Blueprint('auth',__name__)


@auth.route('/login')
def login():
    return "Login Page"

@auth.route('/logout')  
def logout():
    return "Logout Page"

@auth.route('/register')
def register():
    return "Register Page"