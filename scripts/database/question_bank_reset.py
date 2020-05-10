# truncates the following tables in the database and then reloads all the question bank fixtures
import os

from django.core.management import call_command
from django.db import connection

from openshiksha.settings import PROJECT_ROOT


def raw_sql_execute(sql_cmd):
    with connection.cursor() as conn:
        conn.execute(sql_cmd)


TRUNCATE_CMD_BEGIN = """

BEGIN;
SET FOREIGN_KEY_CHECKS = 0;

"""

TRUNCATE_CMD_END = """

SET FOREIGN_KEY_CHECKS = 1;
COMMIT;
"""


def get_table_truncation_statements(tables):
    statements = []
    for table in tables:
        statements.append("TRUNCATE `%s`;" % table)
    return '\n'.join(statements)


def truncate_tables(tables):
    raw_sql_execute(TRUNCATE_CMD_BEGIN + get_table_truncation_statements(tables) + TRUNCATE_CMD_END)

def run():
    # first truncate all tables which form the question bank
    truncate_tables([
        'core_question',
        'core_questionsubpart',
        'core_questiontag',
        'core_assignmentquestionslist',
        'core_assignmentquestionslist_questions',
        'core_question_tags'
    ])

    # now reload all question bank fixtures

    for fixture in sorted(os.listdir(os.path.join(PROJECT_ROOT, 'core', 'fixtures', 'qb')),
                          key=lambda x: int(x.split('.')[0].split('to')[0])):
        call_command('loaddata', os.path.join('qb', fixture))

