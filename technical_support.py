import os
import threading

import sqlalchemy as sa
import sqlalchemy.orm as so

from app import app, db
import sentry_sdk
# from rabbitmq.callback import handler_rabbitmq

# sentry_sdk.init(os.getenv("API_TOKEN_SENTRY"))
# reabbitmq = threading.Thread(target=handler_rabbitmq).start()
