import logging
import os

from fabric.decorators import hosts, task
from fabric.operations import run, get
from fabric.state import env

WEB_SERVERS = ['128.199.139.143']
QA_WEB_SERVER = '128.199.184.177'
DB_SERVER = '128.199.250.240'
QA_DB_SERVER = '188.166.242.79'

env.forward_agent = True
env.port = 1463

# Workaround for: No handlers could be found for logger "paramiko.transport"
# (see https://github.com/fabric/fabric/issues/51#issuecomment-96341022)
logging.basicConfig()
paramiko_logger = logging.getLogger("paramiko.transport")
paramiko_logger.disabled = True

DATA_DUMP_DIR = '../openshiksha-data/'

@task
@hosts(WEB_SERVERS + [DB_SERVER])
def deploy():
    run("devops/deploy.sh")


@task
@hosts([QA_WEB_SERVER, QA_DB_SERVER])
def qa_deploy():
    run("devops/qa-deploy.sh")


@task
@hosts([DB_SERVER])
def cabinet_deploy():
    run("devops/deploy.sh")


@task
@hosts([QA_DB_SERVER])
def qa_cabinet_deploy():
    run("devops/qa-deploy.sh")


@task
@hosts(WEB_SERVERS + [DB_SERVER])
def deploy_clean():
    run("devops/deploy.sh -x")


@task
@hosts([QA_WEB_SERVER, QA_DB_SERVER])
def qa_deploy_clean():
    run("devops/qa-deploy.sh -x")

@task
@hosts(WEB_SERVERS + [DB_SERVER])
def dd_restart():
    run("sudo /etc/init.d/datadog-agent restart")


@task
@hosts(WEB_SERVERS[0])
def db_health_check():
    run("./manage.py runscript scripts.database.enforcer")


@task
@hosts(QA_WEB_SERVER)
def qa_db_health_check():
    run("./manage.py runscript scripts.database.enforcer")


@task
@hosts(WEB_SERVERS[0])
def grab_data_dump(filename):
    filename = filename + '.json'

    run("scripts/fixtures/dump-data.sh %s" % filename)
    get(os.path.join("~/openshiksha", filename), os.path.join(DATA_DUMP_DIR, filename))
    run("rm " + filename)

@task
@hosts(QA_WEB_SERVER)
def qa_grab_data_dump(filename):
    filename = filename + '.json'

    run("scripts/fixtures/dump-data.sh %s" % filename)
    get(os.path.join("~/openshiksha", filename), os.path.join(DATA_DUMP_DIR, filename))
    run("rm " + filename)
