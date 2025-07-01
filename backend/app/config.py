# from datetime 
import datetime
import os

from dotenv import load_dotenv
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URL")
    SECRET_KEY=os.getenv("SECRET_KEY")
    JWT_SECRET_KEY= os.getenv("SECRET_KEY")  # Replace with your secret
    JWT_TOKEN_LOCATION= ['headers']  # or ['cookies'] if you're using cookies
    JWT_ACCESS_TOKEN_EXPIRES= datetime.timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES= datetime.timedelta(days=7)
    JWT_HEADER_NAME= 'Authorization'
    JWT_HEADER_TYPE= 'Bearer'
    JWT_IDENTITY_CLAIM='sub'  # default, don't change
    JWT_ENCODE_ISSUER='your-app'  # optional
    JWT_DECODE_AUDIENCE=None