from django.db import models
from django.db.models import sql
from django.utils.functional import cached_property


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name_plural = 'People'


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='books'
    )

    def __str__(self):
        return self.title


class ThingIterable(models.query.BaseIterable):
    def __iter__(self):
        for obj in self.queryset:
            yield Thing(**obj)


class ThingQuerySet(models.QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None, deferred_querysets=None):
        self.model = model
        self._db = using
        self._hints = hints or {}
        self._query = query or sql.Query(self.model)
        self._result_cache = None
        self._sticky_filter = False
        self._for_write = False
        self._prefetch_related_lookups = ()
        self._prefetch_done = False
        self._known_related_objects = {}  # {rel_field: {pk: rel_obj}}
        self._iterable_class = ThingIterable
        self._fields = None
        self._defer_next_filter = False
        self._deferred_filter = None
        self._deferred_querysets = deferred_querysets

    def __iter__(self):
        for obj in self._joined_qs:
            yield Thing(**obj)

    @cached_property
    def _joined_qs(self):
        # TODO: apply filter to individual querysets as they are joined

        base_qs = self._deferred_querysets[0]
        for other in self._deferred_querysets[1:]:
            base_qs = base_qs.union(other)

        return base_qs

    def _clone(self):
        c = self.__class__(
            model=self.model,
            query=self.query.chain(),
            using=self._db,
            hints=self._hints,
            deferred_querysets=self._deferred_querysets,
        )
        c._sticky_filter = self._sticky_filter
        c._for_write = self._for_write
        c._prefetch_related_lookups = self._prefetch_related_lookups[:]
        c._known_related_objects = self._known_related_objects
        c._iterable_class = self._iterable_class
        c._fields = self._fields
        return c



class ThingManager(models.Manager):
    def get_queryset(self):
        return ThingQuerySet(
            model=Thing,
            deferred_querysets=[
                Person.objects.annotate(title=models.F('first_name'), object_type=models.Value('PERSON')).values('id', 'title', 'object_type'),
                Book.objects.annotate(object_type=models.Value('BOOK')).values('id', 'title', 'object_type'),
            ],
        )

    # def get_queryset(self):
    #     qs_set = [
    #         Person.objects.annotate(title=models.F('first_name'), object_type=models.Value('PERSON')).values('id', 'title', 'object_type'),
    #         Book.objects.annotate(object_type=models.Value('BOOK')).values('id', 'title', 'object_type'),
    #     ]

    #     result = qs_set[0]
    #     for sub_qs in qs_set[1:]:
    #         result = result.union(sub_qs)

    #     return result


class VirtualModelMeta:
    def __init__(self, model):
        self.app_label = 'main'
        self.model = model
        self.model_name = 'Thing'
        self.fields = []


class Thing:
    _meta = VirtualModelMeta(None)

    def __init__(self, id, title, object_type):
        self.id = id
        self.title = title
        self.object_type = object_type

    objects = _default_manager = ThingManager()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"<Thing \"{self.title}\" />"
