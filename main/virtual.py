from django.db import models
from django.db.models import Q, sql
from django.db.models.functions import Cast, Concat
from django.utils.functional import cached_property


class VirtualModelIterable(models.query.BaseIterable):
    def __iter__(self):
        for obj in self.queryset:
            yield obj


class VirtualModelQuerySet(models.QuerySet):
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
        self._iterable_class = VirtualModelIterable
        self._fields = None
        self._defer_next_filter = False
        self._deferred_filter = None
        self._deferred_querysets = deferred_querysets

    def __iter__(self):
        for obj in self._get_joined_qs():
            yield self.model(**obj)

    def _annotate_merged_id(self, qs, i):
        isolated_attributes = list(self.model.isolated_attributes)

        return qs.annotate(
            _qs_id=models.Value(str(i)),
            _str_id=Cast('id', output_field=models.CharField())
        ).annotate(
            _merged_id=Concat('_qs_id', models.Value('_'), '_str_id')
        ).values(
            *(isolated_attributes + ['_merged_id']),
        ).annotate(
            id=models.F('_merged_id'),
            pk=models.F('_merged_id'),
        ).values(*isolated_attributes + ['id', 'pk'])

    def _get_joined_qs(self):
        # TODO: apply filter to individual querysets as they are joined

        base_qs = self._annotate_merged_id(
            self._deferred_querysets[0], 1
        )

        for i, other in enumerate(self._deferred_querysets[1:], start=2):
            base_qs = base_qs.union(
                self._annotate_merged_id(other, i)
            )

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



class VirtualModelManager(models.Manager):
    def register_virtual_model(self, model):
        self.model = model

    def get_queryset(self):
        return VirtualModelQuerySet(
            model=self.model,
            deferred_querysets=self.model.get_querysets(),
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
        self.model_name = 'VirtualModel'
        self.fields = []


class VirtualModelBase(type):
    def __new__(cls, *args, **kwargs):
        klass = super().__new__(cls, *args, **kwargs)

        manager = klass.objects
        manager.register_virtual_model(klass)
        klass.objects = klass._default_manager = manager

        return klass


class VirtualModel(metaclass=VirtualModelBase):
    isolated_attributes = ['id']

    _meta = VirtualModelMeta(None)
    objects = _default_manager = VirtualModelManager()

    def __init__(self, **kwargs):
        for attrib_name in self.isolated_attributes + ['id', 'pk']:
            setattr(self, attrib_name, kwargs[attrib_name])

    def __repr__(self):
        return str(self)
