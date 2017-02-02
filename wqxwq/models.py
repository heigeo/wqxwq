from django.contrib.gis.db import models
from wq.db.patterns import models as patterns
from vera import base_models as vera


class Spreadsheet(patterns.LabelModel):
    file = models.FileField()

    wq_label_template = "{{file.name}}"


class WaterbodyType(patterns.IdentifiedModel):
    icon = models.ImageField(upload_to='icons')


class Waterbody(patterns.IdentifiedModel):
    type = models.ForeignKey(WaterbodyType)

    @property
    def icon(self):
        return self.type.slug

    @property
    def icon_url(self):
        return self.type.icon.url

    wq_label_template = "{{name}}"

    class Meta(patterns.IdentifiedModel.Meta):
        verbose_name_plural = "waterbodies"


class Site(vera.BaseSite):
    geometry = models.PointField(srid=4326)
    waterbody = models.ForeignKey(Waterbody)

    @property
    def icon(self):
        return self.waterbody.icon

    @property
    def icon_url(self):
        return self.waterbody.icon_url


class ParameterMethod(patterns.IdentifiedModel):
    context = models.CharField(max_length=10)
    description = models.TextField()


class Parameter(vera.BaseParameter):
    method = models.ForeignKey(ParameterMethod, null=True, blank=True)


class EventType(patterns.IdentifiedModel):
    pass


class Event(vera.BaseEvent):
    type = models.ForeignKey(EventType)
    date = models.DateField()
    depth = models.FloatField(null=True, blank=True)

    wq_label_template = "{{site.name}} on {{date}}"

    class Meta:
        unique_together = [['site', 'date', 'type', 'depth']]
        ordering = ('-date',)


class Report(vera.BaseReport):
    time = models.TimeField(null=True, blank=True)
    activity_id = models.CharField(max_length=50, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)


class Result(vera.BaseResult):
    QUALIFIER_CHOICES = (
        ("<", "Less Than"),
        (">", "Greater Than"),
        ("ND", "Not Detected"),
        ("NR", "Not Reported"),
        ("QL", "Quantification Limit"),
    )
    method = models.ForeignKey(ParameterMethod, null=True, blank=True)
    qualifier = models.CharField(
        max_length=2, null=True, blank=True, choices=QUALIFIER_CHOICES
    )
    comment = models.TextField(null=True, blank=True)

    @property
    def value(self):
        val = super(Result, self).value
        if self.qualifier in ("ND", "QL"):
            return self.qualifier
        elif self.qualifier is not None:
            return "%s %s" % (self.qualifier, val)
        else:
            return val

    @value.setter
    def value(self, val):
        choice_codes = [c[0] for c in self.QUALIFIER_CHOICES]
        if val == "Not Reported":
            val = "NR"
        if isinstance(val, str) and val.strip() in choice_codes:
            self.qualifier = val.strip()
            val = None

        elif (self.type.is_numeric
                and isinstance(val, str)
                and len(val) > 0
                and val[0] in choice_codes):
            self.qualifier = val[0]
            val = val[1:].strip()
            if val in choice_codes:
                self.qualifier = val
                val = None

        vera.BaseResult.value.fset(self, val)


EventResult = vera.create_eventresult_model(Event, Result)
