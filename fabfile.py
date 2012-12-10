import os
import deploy as deploy_conf

from fabric.api import env, task, roles, run, execute, sudo
from fabric import colors
from fabric.utils import abort

import inspect

################################################################################
# Tasks for managing Deploy Targets
################################################################################
@task(alias='t')
def target(target_name):
    """Select the deploy target.
    """
    if not target_name in deploy_conf.TARGETS:
        abort('Deploy target "%s" not found.' % target_name)

    target_class = deploy_conf.TARGETS[target_name]
    target = target_class()
    env['deploy_target'] = target
    env.roledefs.update(target.get_roles())

    print (colors.green("Selected deploy target ")
            + colors.green(target_name, bold=True))

@task
def list_targets():
    """List all the available targets
    """

    targets = deploy_conf.TARGETS.keys()

    print 'Available targets:'
    print '\n'.join(targets)

################################################################################
# Auxiliary tasks
################################################################################

@task()
@roles('app', 'db', 'static')
def git_pull():
    """Pull changes to the repository of all remote hosts.
    """
    env.deploy_target.git_pull()

@task
@roles('app', 'db', 'static')
def setup_repository(force=False):
    """Clone the remote repository, creating the SSH keys if necessary.
    """
    env.deploy_target.setup_repository(force)

@task
@roles('app', 'db', 'static')
def setup_virtualenv(force=False):
    """Create the virtualenv and install the packages from the requirements
    file.
    """
    env.deploy_target.setup_virtualenv(force)
    env.deploy_target.install_virtualenv(update=False)

@task
@roles('app', 'db', 'static')
def update_virtualenv():
    """Update the virtualenv according to the requirements file.
    """
    env.deploy_target.install_virtualenv(update=True)

################################################################################
# Main Tasks
################################################################################

@task
@roles('app')
def restart_app():
    """Restart the application server.
    """
    env.deploy_target.restart_app()

@task()
def deploy():
    """Deploy the application to the selected deploy target.
    """
    # Push local changes to central repository
    env.deploy_target.git_push()

    # Pull changes on remote repositories
    execute(git_pull)

    # Restart application server
    execute(restart_app)

@task
@roles('db')
def migrate(syncdb=False, fake=False):
    """Execute syncdb and migrate in the database hosts.
    """
    env.deploy_target.db_migrate(syncdb, fake)

@task
@roles('static')
def collectstatic():
    """Execute collectstatic on static file hosts.
    """
    env.deploy_target.db_collectstatic()

@task()
def setup():
    """Initial setup of the remote hosts.
    """
    # Set up git repository
    execute(setup_repository)

    # Set up virtualenv
    execute(setup_virtualenv)

    # Sync and Migrate database
    execute(migrate, True, True)

    # Collect static files
    execute(collectstatic)

    # Restart application servers
    execute(restart_app)

################################################################################
# Tasks for manually executing manage.py commands
################################################################################
@task
@roles('app')
def app_manage(arguments):
    """Execute the given manage.py command in Aplication hosts.
    """
    env.deploy_target.run_django_manage(arguments)

@task
@roles('db')
def db_manage(arguments):
    """Execute the given manage.py command in Database hosts.
    """
    env.deploy_target.run_django_manage(arguments)

@task
@roles('static')
def static_manage(arguments):
    """Execute the given manage.py command in Static File hosts.
    """
    env.deploy_target.run_django_manage(arguments)

################################################################################
# Auxiliary tasks for helping with SSH public key authentication
################################################################################
def _read_key_file(key_file):
    """Helper function that returns your SSH public from the given filename.
    """
    key_file = os.path.expanduser(key_file)
    if not key_file.endswith('pub'):
        raise RuntimeWarning('Trying to push non-public part of key pair')
    with open(key_file) as f:
        return f.read().strip()

@task
def push_key(keyfile='~/.ssh/id_rsa.pub'):
    """Adds your private key to the list of authorized keys to log into the
    remote account.
    """
    key = _read_key_file(keyfile)
    run('mkdir -p ~/.ssh && chmod 0700 ~/.ssh')
    run("echo '" + key + "' >> ~/.ssh/authorized_keys")

@task
def push_key_sudo(user,keyfile='~/.ssh/id_rsa.pub'):
    """Adds your private key to the list of authorized keys for another
    account on the remote host, via sudo.
    """
    key = _read_key_file(keyfile)
    sudo('mkdir -p ~%(user)s/.ssh && chmod 0700 ~%(user)s/.ssh'%{'user': user},
          user=user)
    sudo("echo '" + key + "' >> ~%(user)s/.ssh/authorized_keys"%{'user': user},
         user=user)
