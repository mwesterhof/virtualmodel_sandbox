from django.core.management.base import BaseCommand

from main.models import Thing


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(Thing.objects.all())
        print()

        for thing in Thing.objects.all():
            print(f'{thing.id}: "{thing.title}" ({thing.object_type})')
