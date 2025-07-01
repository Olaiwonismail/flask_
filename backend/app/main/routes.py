from flask import render_template, request, Blueprint

# from flask_login import login_required
main = Blueprint('main',__name__)

 
@main.route('/')
@main.route('/home')
# @login_required
def home():
    return 'home'

@main.route('/about')
def about():
    return 'about'
