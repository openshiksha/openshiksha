"""Record one Postgres backup attempt as a ``BackupRun`` row (BAK-4).

Called best-effort by the prod backup CronJob after a successful ``mc cp`` (a
failure to record must never fail the backup itself — the caller chains it with
``|| true``). Its only consumer is the ``openshiksha_backup_age_seconds``
freshness gauge on the MET-2 collector, which Batch 4 alerting fires on.

Usage:
    python manage.py record_backup_run --status success --size 12345 --key postgres/openshiksha-....dump.gz
"""

from django.core.management.base import BaseCommand

from openshiksha.apps.core.models import BackupRun


class Command(BaseCommand):
    help = "Record a Postgres backup attempt (writes a core.BackupRun row)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            choices=[BackupRun.Status.SUCCESS, BackupRun.Status.FAILURE],
            default=BackupRun.Status.SUCCESS,
            help="Outcome of the backup attempt (default: success).",
        )
        parser.add_argument("--size", type=int, default=None, help="Compressed dump size in bytes.")
        parser.add_argument("--key", default="", help="S3 object key of the uploaded dump.")

    def handle(self, *args, **options):
        run = BackupRun.objects.create(
            status=options["status"],
            size_bytes=options["size"],
            object_key=options["key"] or "",
        )
        self.stdout.write(self.style.SUCCESS(f"Recorded {run}"))
