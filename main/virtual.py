from django.db import models
from django.db.models import Q, sql
from django.db.models.functions import Concat
from django.utils.functional import cached_property


class ThingIterable(models.query.BaseIterable):
    def __iter__(self):
        from .models import Thing  # TODO

        for obj in self.queryset:
            if isinstance(obj, Thing):
                yield Thing
            else:
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
        from .models import Thing  # TODO

        for obj in self._get_joined_qs():
            yield Thing(**obj)

    def _get_joined_qs(self):
        # TODO: apply filter to individual querysets as they are joined

        base_qs = self._deferred_querysets[0].values(*self.model.isolated_attributes)
        for other in self._deferred_querysets[1:]:
            base_qs = base_qs.union(other.values(*self.model.isolated_attributes))

        return base_qs

    def _filter_or_exclude_inplace(self, negate, args, kwargs):
        if negate:
            for qs in self._deferred_querysets:
                qs._query.add_q(~Q(*args, **kwargs))
        else:
            for qs in self._deferred_querysets:
                self._query.add_q(Q(*args, **kwargs))

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
        from .models import Book, Person, Thing  # TODO

        return ThingQuerySet(
            model=Thing,
            deferred_querysets=Thing.get_querysets(),
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


class VirtualModel:
    isolated_attributes = ['id']

    _meta = VirtualModelMeta(None)
    objects = _default_manager = ThingManager()

    def __init__(self, **kwargs):
        for attrib_name in self.isolated_attributes:
            setattr(self, attrib_name, kwargs[attrib_name])

    def __repr__(self):
        return str(self)
