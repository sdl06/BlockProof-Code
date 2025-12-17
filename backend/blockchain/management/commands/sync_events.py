"""
Django management command to manually sync blockchain events.
Useful for initial sync or catching up after downtime.
"""

from django.core.management.base import BaseCommand
from blockchain.tasks import index_blockchain_events


class Command(BaseCommand):
    help = 'Manually sync blockchain events to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run asynchronously via Celery',
        )

    def handle(self, *args, **options):
        if options['async']:
            index_blockchain_events.delay()
            self.stdout.write(
                self.style.SUCCESS('Event indexing task queued in Celery')
            )
        else:
            self.stdout.write('Starting event indexing...')
            index_blockchain_events()
            self.stdout.write(
                self.style.SUCCESS('Event indexing completed')
            )

