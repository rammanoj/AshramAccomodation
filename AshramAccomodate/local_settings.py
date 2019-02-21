import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ashram',
        'USER': 'guest',
        'PASSWORD': 'guest',
        'HOST': 'localhost',
        'PORT': '',
    }
}

BASE_URL = 'http://127.0.0.1:8000/'

CELERY_BROKER_URL = 'amqp://hello:guest@localhost/myvhost'
DEBUG = True