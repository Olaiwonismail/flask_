from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User
# 
# from app.auth.utils import save_pic, send_reset_email
users= Blueprint('users',__name__)

@users.route('/account',methods = ['POST','GET'])
def account():
    pass 
@users.route("/user/<username>")
def user_posts(username):
    return username


