"""
Helper functions to the configuration process
"""

import os

# Important paths
DEPLOY_ENVS_DIR = os.path.dirname(os.path.realpath(__file__))
SITECONFIG_DIR  = os.path.normpath(os.path.join(DEPLOY_ENVS_DIR, '../'))
PROJECT_DIR     = os.path.normpath(os.path.join(DEPLOY_ENVS_DIR, '../../'))

USER_SECRETS_DIR = os.path.join(os.environ.get('HOME', ''), '.twistsecrets/')

def get_secret_key():
    """
    Retrieve the SECRET_KEY for the current site. If it doesn't exist, it will
    be created.

    The SECRET_KEY will be looked up at the following locations:

    - ~/.twistsecrets/site_key.txt
    - local_site_key.txt

    If none exist, the second file will be created with a random site key.
    """
    # Try the User secret
    user_secrets = os.path.join(USER_SECRETS_DIR, 'site_key.txt')
    if os.path.exists(user_secrets):
        with open(user_secrets, 'r') as f:
            secret = f.read().strip()
        return secret

    # User secret not found. Let's try local key
    local_key = os.path.join(DEPLOY_ENVS_DIR, 'local_site_key.txt')
    if not os.path.exists(local_key):
        # Key file not found. Let's create one and fill it with random chars
        from random import choice
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        new_key = ''.join([choice(allowed_chars) for i in range(50)])
        # Save the new key to the file
        with open(local_key, 'w') as f:
            f.write(new_key + '\n')

    # At this point the local secret exists or (hopefully) have been created.
    # Let's load it, then.
    with open(local_key, 'r') as f:
        secret = f.read().strip()
    return secret
