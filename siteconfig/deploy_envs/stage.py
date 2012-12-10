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
        'NAME': os.path.join(_DB_DIR, 'stage.sqlite3'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

MEDIA_ROOT  = '/home/<PROJECT_USERNAME>/public_html/media/'
STATIC_ROOT = '/home/<PROJECT_USERNAME>/public_html/static/'

MEDIA_URL   = 'http://<PROJECT_USERNAME>.twistsystems.com/media/'
STATIC_URL  = 'http://<PROJECT_USERNAME>.twistsystems.com/static/'
