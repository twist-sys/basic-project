"""
WSGI File for TWIST.

This file is intended to work with both Django 1.3 and 1.4, and will allow for
configuration of development environment from Apache SetEnv directive.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "siteconfig.settings")

def _setup_application(environ, start_response):
    """
    Retrieve the relevant information from the WSGI environment and sets up the
    Django application.

    This function will (hopefully) be executed only once in the lifetime of the
    WSGI process, to initialize Django and reassign the 'application' variable.
    """

    # Retrieve the Deploy environment from the WSGI environment
    deploy_env = environ.get('DJANGO_DEPLOY_ENV', 'dev')
    os.environ['DJANGO_DEPLOY_ENV'] = deploy_env

    # See if Django version is 1.4 or 1.3
    import django

    if django.VERSION[1] == 4:
        # This is Django (probably) version 1.4
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()

    elif django.VERSION[1] == 3:
        import django.core.handlers.wsgi
        application = django.core.handlers.wsgi.WSGIHandler()

    else:
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['Cannot determine the correct Django version\n']

    # Pass the present request to the just initialized application.
    return application(environ, start_response)

application = _setup_application
