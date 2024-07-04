from django.contrib import admin

from .models import Book, Person


class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_name')

    def author_name(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'


class PersonAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')



admin.site.register(Book, BookAdmin)
admin.site.register(Person, PersonAdmin)
