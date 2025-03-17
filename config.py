import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))
# test

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "test_secret_key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Flask email
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")