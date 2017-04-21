from django.core.management.base import BaseCommand
from wqxwq.util import export_wqx


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
        )
        parser.add_argument(
            '--start',
        )
        parser.add_argument(
            '--end',
        )

    def handle(self, **options):
        export_wqx(options['filename'], options['start'], options['end'])
