import deploy

class stage(deploy.SimpleTarget):
    GIT_REPOSITORY = 'git@github.com:twistsys/basic-project.git'
    GIT_BRANCH = 'master'
    SERVER = 'demo@server.mydomain.com'
    DJANGO_DEPLOY_ENV = 'stage'

