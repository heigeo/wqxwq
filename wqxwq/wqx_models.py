from django.db import models
from wq.db.patterns import models as patterns
from climata.epa import WqxDomainIO
from django.core.exceptions import FieldDoesNotExist

_domain_io = {}


class WqxDomainModelManager(patterns.IdentifiedModelManager):
    def get_by_identifier(self, identifier, auto_create=False):
        try:
            return super(
                WqxDomainModelManager, self
            ).get_by_identifier(identifier)
        except self.model.DoesNotExist:
            obj = self.create_from_wqx(identifier)
            if not obj:
                if auto_create:
                    return self.create_by_natural_key(identifier)
                else:
                    raise self.model.DoesNotExist(
                        "%s is not a known domain value for %s" %
                        (identifier, self.wqx_domain)
                    )
            return obj

    @property
    def wqx_domain(self):
        return getattr(self.model, 'wqx_domain', self.model.__name__)

    def get_unused_values(self):
        if self.wqx_domain not in _domain_io:
            _domain_io[self.wqx_domain] = WqxDomainIO(domain=self.wqx_domain)

        existing = self.all().values_list('slug', flat=True)
        code_field = self.model.wqx_code_field
        return [
            value
            for value in _domain_io[self.wqx_domain]
            if getattr(value, code_field) not in existing
        ]

    def create_from_wqx(self, identifier):
        values = self.get_unused_values()
        code_field = self.model.wqx_code_field
        name_field = self.model.wqx_name_field

        found_value = None
        for value in values:
            if getattr(value, code_field) == identifier:
                found_value = value

        if not found_value:
            for value in values:
                if getattr(value, name_field) == identifier:
                    found_value = value

        if not found_value:
            return None

        kwargs = {
            'slug': getattr(found_value, code_field)[:50],
            'name': getattr(found_value, name_field),
        }
        for field_name in found_value._fields:
            if field_name in (code_field, name_field):
                continue
            try:
                field = self.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue

            val = getattr(found_value, field_name)
            if field.rel:
                val = field.rel.to.objects.find(val)
            elif isinstance(field, models.NullBooleanField):
                if val == 'Y':
                    val = True
                elif val == 'N':
                    val = False
            kwargs[field_name] = val

        return self.create(**kwargs)

    def filter(self, **kwargs):
        qs = super(WqxDomainModelManager, self).filter(**kwargs)
        filter_field = getattr(self.model, 'wqx_filter_field', None)

        if not qs.exists() and filter_field and filter_field in kwargs:
            filter_value = kwargs[filter_field]
            if isinstance(filter_value, models.Model):
                filter_value = filter_value.slug
            for value in self.get_unused_values():
                if getattr(value, filter_field) == filter_value:
                    self.create_from_wqx(
                        getattr(value, self.model.wqx_code_field)
                    )
            qs = super(WqxDomainModelManager, self).filter(**kwargs)

        return qs


class WqxDomainModel(patterns.IdentifiedModel):
    objects = WqxDomainModelManager()
    lastchangedate = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='last updated',
    )

    wqx_code_field = 'code'
    wqx_name_field = 'name'

    def __str__(self):
        if self.slug == self.name:
            return self.name
        return "%s: %s" % (self.slug, self.name)

    class Meta(patterns.IdentifiedModel.Meta):
        abstract = True
        ordering = ('slug',)
