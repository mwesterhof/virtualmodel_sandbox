from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat

from .virtual import VirtualModel


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='books'
    )


class PrintableThing(VirtualModel):
    isolated_attributes = ['title', 'object_type']

    @classmethod
    def get_querysets(cls):
        return [
            Person.objects.annotate(
                title=Concat('first_name', Value(' '), 'last_name'),
                object_type=models.Value('PERSON')
            ),
            Book.objects.annotate(object_type=models.Value('BOOK')),
        ]

    def __str__(self):
        return f"<PrintableThing \"{self.title}\" />"
