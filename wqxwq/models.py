from django.contrib.gis.db import models
from wq.db.patterns import models as patterns
from vera import base_models as vera
from .wqx_models import WqxDomainModel, WqxDomainModelManager


# WQX Domain tables

class AnalyticalMethodContext(WqxDomainModel):
    pass


class AnalyticalMethod(WqxDomainModel):
    contextcode = models.ForeignKey(
        AnalyticalMethodContext,
        null=True,
        blank=True,
        verbose_name='context',
    )
    description = models.TextField()
    url = models.URLField()

    wqx_code_field = 'id'


class Characteristic(vera.BaseParameter):
    objects = WqxDomainModelManager()
    lastchangedate = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='last updated'
    )

    samplefractionrequired = models.NullBooleanField(
        verbose_name="requires sample fraction"
    )
    picklist = models.NullBooleanField(
        verbose_name='has choices',
    )

    wqx_code_field = 'name'
    wqx_name_field = 'name'

    def __str__(self):
        return self.name

    @property
    def choices(self):
        if not self.picklist:
            return []
        return CharacteristicChoice.objects.filter(
            characteristic=self
        )


class CharacteristicChoice(WqxDomainModel):
    code = models.CharField(max_length=20, null=True, blank=True)
    characteristic = models.ForeignKey(Characteristic)

    wqx_domain = 'CharacteristicWithPickList'
    wqx_code_field = 'uniqueidentifier'
    wqx_name_field = 'description'
    wqx_filter_field = 'characteristic'


class MethodSpeciation(WqxDomainModel):
    wqx_code_field = 'name'
    wqx_name_field = 'name'


class ActivityType(WqxDomainModel):
    description = models.TextField(null=True, blank=True)

    wqx_code_field = 'abbreviation'
    wqx_name_field = 'code'

    analyticalmethodrequired = models.NullBooleanField(
        verbose_name='requires analytical method',
    )
    monitoringlocationrequired = models.NullBooleanField(
        verbose_name='requires monitoring location',
    )


class MeasureUnit(WqxDomainModel):
    wqx_code_field = 'code'
    wqx_name_field = 'description'


# Vera & Data Wizard Models
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


class Event(vera.BaseEvent):
    type = models.ForeignKey(ActivityType)
    date = models.DateField()
    depth = models.FloatField(null=True, blank=True)

    wq_label_template = "{{site.name}} on {{date}}"

    class Meta:
        unique_together = [['site', 'date', 'type', 'depth']]
        ordering = ('-date',)


class Result(vera.BaseResult):
    QUALIFIER_CHOICES = (
        ("<", "Less Than"),
        (">", "Greater Than"),
        ("ND", "Not Detected"),
        ("NR", "Not Reported"),
        ("QL", "Quantification Limit"),
    )
    speciation = models.ForeignKey(MethodSpeciation, null=True, blank=True)
    method = models.ForeignKey(AnalyticalMethod, null=True, blank=True)
    unit = models.ForeignKey(MeasureUnit, null=True, blank=True)

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


class Project(patterns.IdentifiedModel):
    description = models.TextField(null=True, blank=True)


class ProjectParameter(models.Model):
    project = models.ForeignKey(Project, related_name="parameters")
    parameter = models.ForeignKey(Characteristic, related_name="projects")


class Report(vera.BaseReport):
    project = models.ForeignKey(Project, null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    activity_id = models.CharField(max_length=50, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)


EventResult = vera.create_eventresult_model(Event, Result)
