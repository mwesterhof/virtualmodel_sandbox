from django.contrib import admin

from .models import Book, Person


admin.site.register(Book)
admin.site.register(Person)
