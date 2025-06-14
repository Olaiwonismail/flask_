from flask import Blueprint

users = Blueprint('users',__name__)


@users.route('/login')
def login():
    return "Login Page"

@users.route('/logout')  
def logout():
    return "Logout Page"

@users.route('/register')
def register():
    return "Register Page"
