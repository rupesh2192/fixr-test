from django.core.management.base import BaseCommand, CommandError

from ticket.models import Event


class Command(BaseCommand):
    help = 'Prints the summary of the given event id'

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int)

    def handle(self, *args, **options):
        try:
            event = Event.objects.get(pk=options["event_id"])
            self.stdout.write(self.style.SUCCESS(event.summary()))
        except Event.DoesNotExist:
            raise CommandError(f'Event with id {options["event_id"]} does not exist')
