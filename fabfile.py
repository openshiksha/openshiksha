import logging
import os

DATA_DUMP_DIR = '../openshiksha-data/'


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
