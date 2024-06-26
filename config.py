import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))
# test

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "test_secret_key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
