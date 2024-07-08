from django.core.management.base import BaseCommand

from main.models import PrintableThing


class Command(BaseCommand):
    def handle(self, *args, **options):
        for thing in PrintableThing.objects.all():
            print(f'{thing.id}: "{thing.title}" ({thing.object_type})')
