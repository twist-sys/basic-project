#!/usr/bin/env python
import os
import sys

_SETTINGS = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "siteconfig.settings")

if __name__ == "__main__":

    # Work around Mac OS X Lion locale misconfiguration
    curr_locale = os.environ.get('LC_CTYPE','UTF-8')
    if curr_locale == 'UTF-8':
        os.environ['LC_CTYPE'] = 'en_US.UTF-8'

    import django
    if django.VERSION[1] == 4:
        # This is (probably) Django 1.4. Let's do it its way

        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)

    elif django.VERSION[1] == 3:
        # This is (probably) Django 1.3
        from django.core.management import execute_manager

        settings = __import__(_SETTINGS, globals(), locals(), ['*'])
        execute_manager(settings)
    else:
        sys.stderr.write("I was expecting Django versions 1.3 or 1.4. It appears you are using version %s.\n"
                         % ('.'.join([str(x) for x in django.VERSION]), ))
        sys.exit(1)
