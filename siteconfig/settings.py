"""
Settings for the current site. This file is heavily based on David Cramer's
post on http://justcramer.com/2011/01/13/settings-in-django/
"""
import os

# Load configuration defaults
from deploy_envs.defaults import *

# Load deploy environment specific settings

DJANGO_DEPLOY_ENV = os.environ.get('DJANGO_DEPLOY_ENV', 'dev')
if DJANGO_DEPLOY_ENV != 'defaults':
    module = __import__('deploy_envs.' + DJANGO_DEPLOY_ENV,
                        globals(), locals(), ['*'])

    for k in dir(module):
        if k[0] == '_':
            continue
        locals()[k] = getattr(module, k)


## Remove disabled apps

if 'DISABLED_APPS' in locals():
    INSTALLED_APPS = [k for k in INSTALLED_APPS if k not in DISABLED_APPS]

    MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
    DATABASE_ROUTERS = list(DATABASE_ROUTERS)
    TEMPLATE_CONTEXT_PROCESSORS = list(TEMPLATE_CONTEXT_PROCESSORS)

    for a in DISABLED_APPS:
        for x, m in enumerate(MIDDLEWARE_CLASSES):
            if m.startswith(a):
                MIDDLEWARE_CLASSES.pop(x)

        for x, m in enumerate(TEMPLATE_CONTEXT_PROCESSORS):
            if m.startswith(a):
                TEMPLATE_CONTEXT_PROCESSORS.pop(x)

        for x, m in enumerate(DATABASE_ROUTERS):
            if m.startswith(a):
                DATABASE_ROUTERS.pop(x)
