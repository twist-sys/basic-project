from fabric.api import cd, run, puts, local, settings, hide, prompt, abort, prefix
from fabric.contrib.files import exists
from fabric import colors
import os

def _ensure_list(obj):
    """Always returns a list. If the original object is not a list, the
    returned value is a list with the given object as the only element.
    """
    if isinstance(obj, list):
        return obj
    else:
        return [obj,]


class BasicTarget(object):
    REPOSITORY_DIR = '' # Directory for the remote repository
    SITECONFIG_DIR = '' # Directory for the siteconfig
    VIRTUALENV_DIR = '' # Directory for the virtualenv
    MEDIA_DIR      = '' # Directory for media files
    STATIC_DIR     = '' # Directory for static files
    GIT_REPOSITORY = '' # Address for the central repository
    GIT_BRANCH     = '' # Name of the branch to be used on the remote repo
    GIT_REMOTE     = 'origin' # Name of the remote in the local repository
    APP_SERVERS    = []
    STATIC_SERVERS = []
    DB_SERVERS     = []
    DJANGO_DEPLOY_ENV = '' # Deploy environment for Django settings

    # Directory getter members
    def _get_repository_dir(self):
        return self.REPOSITORY_DIR

    def _get_siteconfig_dir(self):
        return self.SITECONFIG_DIR

    def _get_virtualenv_dir(self):
        return self.VIRTUALENV_DIR

    def _get_media_dir(self):
        return self.MEDIA_DIR

    def _get_static_dir(self):
        return self.STATIC_DIR

    # Server list getter members
    def _get_db_servers(self):
        return _ensure_list(self.DB_SERVERS)

    def _get_static_servers(self):
        return _ensure_list(self.STATIC_SERVERS)

    def _get_app_servers(self):
        return _ensure_list(self.APP_SERVERS)

    def get_roles(self):
        return {
            'app': self._get_app_servers(),
            'db': self._get_db_servers(),
            'static': self._get_static_servers(),
        }

    # Routines

    def git_remote_exists(self, remote_name):
        """Check if the local git repository has the given remote.
        """

        with settings(hide('running', 'stdout')):
            remotes = local('git remote', capture=True)
        print repr(remotes.split())
        print remote_name in remotes
        return remote_name in remotes

    def check_ssh_key(self):
        """Check for the presence of a SSH private key. If not, generate it and
        beg for the user to correctly add it to the repository.
        """

        if not exists('~/.ssh/id_rsa'):
            puts(colors.yellow('Creating SSH private key'))
            # Generate the private/public key pair
            run("ssh-keygen -q -N '' -f ~/.ssh/id_rsa")

            # Retrieve the public key
            with settings(hide('running', 'stdout')):
                pubkey = run('cat ~/.ssh/id_rsa.pub')

            # Beg the user to do the right thing with the key!

            puts(colors.red('The following public key was generated:'))
            puts('', show_prefix=False)
            puts(pubkey, show_prefix=False)
            puts('', show_prefix=False)
            prompt('Please add this SSH key to the repository and press any key'
                   ' to continue...')

    def setup_repository(self, force=False):
        """Creates the remote git repository and configures it to accept pushes
        to the current branch.
        """
        repo = self._get_repository_dir()
        if exists(repo):
            if force:
                puts(colors.yellow('Repository already exists. Forced removing'
                                   ' it.'))
                run('rm -rf ' + repo)
            else:
                puts(colors.red('Repository already exists. Refusing to'
                                ' recreate it.'))
                return

        # Check SSH keys
        self.check_ssh_key()

        # Attempt to clone the remote repository
        with settings(hide('warnings'), warn_only=True):
            result = run('git clone ' + self.GIT_REPOSITORY + ' ' + repo)
            if result.failed:
                # Failed clone. Probably the SSH key has not been correctly
                # added to the repository. Aid the user in this process
                with settings(hide('running', 'stdout')):
                    pubkey = run('cat ~/.ssh/id_rsa.pub')
                puts(colors.red('Failed to clone repository! Your SSH Public'
                               ' key is:'))
                puts('', show_prefix=False)
                puts(pubkey, show_prefix=False)
                puts('', show_prefix=False)
                abort('Cannot clone remote repository. Please check your public'
                      ' key and try again. If you have just added the key,'
                      ' please wait a few minutes before trying again.')

        # Checkout the correct branch
        if self.GIT_BRANCH != 'master':
            with cd(repo):
                run('git checkout -b %s origin/%s'
                    % (self.GIT_BRANCH, self.GIT_BRANCH))

    def setup_virtualenv(self, force=False):
        """Creates the virtualenv.
        """
        venv = self._get_virtualenv_dir()
        if exists(venv):
            if force:
                puts(colors.yellow('Virtualenv already exists. Forced removing'
                                   ' it.'))
                run('rm -rf ' + venv)
            else:
                puts(colors.red('Virtualenv already exists. Refusing to'
                                ' recreate it.'))
                return

        run("virtualenv --no-site-packages " + venv)

    def install_virtualenv(self, update=False):
        """Install or updates the virtualenv according to the requirements file.
        """
        venv = self._get_virtualenv_dir()
        activate = os.path.join(venv, 'bin/activate')
        requirements = os.path.join(self._get_repository_dir(),
                                    'requirements.txt')

        if not exists(venv):
            puts(colors.red('Cannot find virtualenv. Run setup_virtualenv '
                            'first!'))
            return

        if not exists(requirements):
            puts(colors.red('Cannot find requirements file.'))
            return

        run("source " + activate + " && pip install" + (" -U" if update else "")
            + " -r " + requirements)

    def git_pull(self):
        """Calls git pull on the remote host, taking care for not doing
        anything wrong with the repository.
        """

        repo = self._get_repository_dir()

        # Check if there are uncommited changes to the remote repository
        with cd(repo):
            with settings(
                    hide('warnings', 'running', 'stdout', 'stderr'),
                    warn_only=True):
                # Refresh the status of the index
                run('git update-index -q --ignore-submodules --refresh')
                diff_files = run('git diff-files --quiet --ignore-submodules')
                diff_index = run('git diff-index --cached --quiet'
                                 '  HEAD --ignore-submodules --')

                if diff_files.failed or diff_index.failed:
                    abort(colors.red('There are uncommited changes in the'
                                     ' remote repository. Will not continue.'))

            # Certify that we are in the correct branch
            with settings(
                    hide('warnings', 'running', 'stdout', 'stderr'),
                    warn_only=True):
                curr_branch = run('git symbolic-ref HEAD')
                # Strip the name of the branch, if any
                if curr_branch.failed:
                    curr_branch = "(none)"
                elif curr_branch.startswith('refs/heads/'):
                    curr_branch = curr_branch[11:]

            # Checkout the correct branch, if needed
            if curr_branch != self.GIT_BRANCH:
                puts(colors.yellow('Repository should be on branch %s but is on'
                                   ' %s. Correcting.'
                                   % (self.GIT_BRANCH, curr_branch)))
                with settings(hide('warnings'), warn_only=True):
                    result = run('git checkout ' + self.GIT_BRANCH)
                if result.failed:
                    puts(colors.yellow('Checkout failed. Trying to update'
                                       ' branches'))
                    run('git remote update')
                    run('git checkout -b %s origin/%s'
                        % (self.GIT_BRANCH, self.GIT_BRANCH))

            # Pull our branch
            puts(colors.green('Pulling changes'))
            run('git pull --ff-only origin %s:%s'
                % (self.GIT_BRANCH, self.GIT_BRANCH))

    def git_push(self):
        """Push the changes in the local repository to the central repository,
        if needed.
        """

        with settings(
                hide('warnings', 'running', 'stdout', 'stderr'),
                warn_only=True):

            # Warn if local branch is not the current branch.
            local_branch = local('git symbolic-ref HEAD', capture=True)
            if local_branch.failed:
                local_branch = '(none)'
            elif local_branch.startswith('refs/heads/'):
                local_branch = local_branch[11:]

            if local_branch != self.GIT_BRANCH:
                puts(colors.yellow('*** WARNING ***', bold=True) + ' '
                     + colors.yellow('Local branch is "%s". However, only'
                                     ' branch "%s" will be pushed.'
                                     % (local_branch, self.GIT_BRANCH)),
                     show_prefix=False)

            # Warn uncommited changes
            local('git update-index -q --ignore-submodules --refresh')
            diff_files = local('git diff-files --quiet --ignore-submodules',
                               capture=True)
            diff_index = local('git diff-index --cached --quiet'
                               '  HEAD --ignore-submodules --')

            if diff_files.failed or diff_index.failed:
                puts(colors.yellow('*** WARNING ***', bold=True) + ' '
                     + colors.yellow('You have uncommited changes. Unless you'
                                     ' commit and merge them to "%s", they will'
                                     ' not be deployed!' % self.GIT_BRANCH),
                     show_prefix=False)
        # Issue push
        local('git push %(remote)s %(branch)s:%(branch)s'
               % {'remote': self.GIT_REMOTE, 'branch': self.GIT_BRANCH})

    def restart_app(self):
        """Restart the application server by updating the modification time of
        the wsgi.py file.
        """
        wsgi_file = os.path.join(self._get_siteconfig_dir(), 'wsgi.py')
        puts(colors.green("Restarting Application Server"))
        run("touch " + wsgi_file)

    def run_django_manage(self, arguments):
        """Execute a manage.py command. The arguments parameter should be the
        arguments for the manage.py command.
        """

        venv = self._get_virtualenv_dir()
        activate = os.path.join(venv, 'bin/activate')

        with prefix("source " + activate):
            with cd(self._get_repository_dir()):
                run("export DJANGO_DEPLOY_ENV='" + self.DJANGO_DEPLOY_ENV +
                    "' && ./manage.py " + arguments)

    def db_migrate(self, do_syncdb=False, do_fake=False):
        """Execute syncdb and migrate for the database.
        """
        if do_syncdb:
            if do_fake:
                self.run_django_manage("syncdb --all")
            else:
                self.run_django_manage("syncdb")

        if do_fake:
            self.run_django_manage("migrate --fake")
        else:
            self.run_django_manage("migrate")

    def db_collectstatic(self):
        """Install static files.
        """
        self.run_django_manage("collectstatic --noinput -v 0")

class SimpleTarget(BasicTarget):
    """Simple target for small deploys. Everything is on the same host, and the
    deploy user on the server hosts only one application.
    """

    # Server configuration

    SERVER = ''

    def _get_servers(self):
        return _ensure_list(self.SERVER)

    _get_db_servers     = _get_servers
    _get_app_servers    = _get_servers
    _get_static_servers = _get_servers

    # Important paths

    PROJECT_DIR    = '~/project'
    VIRTUALENV_DIR = '~/venv'
    HTDOCS_DIR     = '~/public_html'

    def _get_repository_dir(self):
        return self.PROJECT_DIR

    def _get_siteconfig_dir(self):
        return os.path.join(self.PROJECT_DIR, 'siteconfig')

    def _get_media_dir(self):
        return os.path.join(self.HTDOCS_DIR, 'media')

    def _get_static_dir(self):
        return os.path.join(self.HTDOCS_DIR, 'static')


# Fill in the list of known targets
import deploy_targets
import inspect

TARGETS = {}

def _get_deploy_targets():
    """Searches the deploy_targets module for subclasses of BasicTarget.
    """
    for var_name, var in vars(deploy_targets).iteritems():
        if inspect.isclass(var):
            if issubclass(var, BasicTarget):
                TARGETS[var_name] = var

# Get list of targets before Fabric has time to mess them up!
if len(TARGETS) == 0:
    _get_deploy_targets()
