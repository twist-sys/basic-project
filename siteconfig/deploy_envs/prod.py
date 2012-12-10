import _helper
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

_DB_DIR = os.path.join(_helper.SITECONFIG_DIR, 'db/')
try:
    os.mkdir(_DB_DIR)
except OSError:
    pass

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(_DB_DIR, 'prod.sqlite3'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

MEDIA_ROOT = os.path.join(_helper.SITECONFIG_DIR, 'media/')
STATIC_ROOT = ''
