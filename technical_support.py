import os
import threading

import sentry_sdk
import sqlalchemy as sa
import sqlalchemy.orm as so

from app import app, db

# from rabbitmq.callback import handler_rabbitmq

sentry_sdk.init(os.getenv("API_TOKEN_SENTRY"))
# reabbitmq = threading.Thread(target=handler_rabbitmq).start()
