from wq.db.rest.serializers import LookupRelatedField
from wq.db.patterns import serializers as patterns
from vera.results import serializers as vera
from vera.series.serializers import EventSerializer, ReportSerializer
from rest_framework import serializers
from .models import Characteristic, ProjectParameter, Result
from django.db.models import Count


class WqxDomainField(LookupRelatedField):
    default_error_messages = {
        'does_not_exist': 'Domain value {value} not found.',
        'invalid': 'Invalid value',
    }

    def to_internal_value(self, data):
        try:
            return self.model.objects.get_by_identifier(data)
        except self.model.DoesNotExist:
            self.fail('does_not_exist', value=data)
        except (TypeError, ValueError):
            self.fail('invalid')


class WqxDomainSerializer(patterns.IdentifiedModelSerializer):
    pass


class WaterbodySerializer(patterns.IdentifiedModelSerializer):
    icon = serializers.ReadOnlyField()
    icon_url = serializers.ReadOnlyField()


class SiteSerializer(patterns.IdentifiedModelSerializer):
    icon = serializers.ReadOnlyField()
    icon_url = serializers.ReadOnlyField()

    parameters = serializers.SerializerMethodField()
    event_count = serializers.SerializerMethodField()

    def get_parameters(self, instance):
        request = self.context.get('request')
        if request and request.path.endswith('geojson'):
            return []
        type_ids = instance.eventresult_set.order_by(
            'result_type_id'
        ).distinct(
            'result_type_id'
        ).values_list('result_type_id', flat=True)

        params = []
        for param in Characteristic.objects.filter(pk__in=type_ids):
            results = instance.eventresult_set.filter(
                result_type=param
            ).order_by('event_date')

            params.append({
                'parameter_label': str(param),
                'parameter_id': param.slug,
                'count': results.count(),
                'first': results.first().event_date,
                'last': results.last().event_date,
            })

        return params

    def get_event_count(self, instance):
        return instance.event_set.count()

    class Meta(patterns.IdentifiedModelSerializer.Meta):
        html_list_exclude = ('identifiers', 'parameters')


class EventSerializer(EventSerializer):
    comment = serializers.SerializerMethodField()
    reports = serializers.SerializerMethodField()

    def get_comment(self, instance):
        comments = set(
            report.comment
            for report in instance.valid_reports
            if report.comment
        )
        return "\n".join(sorted(comments))

    def get_reports(self, instance):
        return [{
            'id': report.id,
            'label': report.activity_id or report.id
        } for report in instance.report_set.all()]


class ResultSerializer(vera.ResultSerializer):
    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(
            ResultSerializer, self
        ).build_relational_field(field_name, relation_info)
        if field_class == LookupRelatedField:
            field_class = WqxDomainField
        return field_class, field_kwargs


class ReportSerializer(ReportSerializer):
    results = ResultSerializer(many=True)

    def get_wq_config(self):
        conf = super().get_wq_config()
        for field in conf['form']:
            if field['name'] == 'results':
                field['initial']['filter'] = {'projects': '{{project_id}}'}
        return conf


class EventResultSerializer(vera.EventResultSerializer):
    type = serializers.ReadOnlyField(source='event_type.slug')
    tb = serializers.SerializerMethodField()
    depth = serializers.ReadOnlyField(source='event_depth')

    def get_tb(self, instance):
        if instance.event_depth:
            if instance.event_depth < 5:
                return "top"
            else:
                return "bottom"

    class Meta:
        pandas_index = ['date', 'type', 'depth']
        pandas_unstacked_header = ['site', 'tb', 'parameter', 'units']

        pandas_scatter_coord = ['units', 'parameter']
        pandas_scatter_header = ['site']

        pandas_boxplot_group = 'site'
        pandas_boxplot_date = 'date'
        pandas_boxplot_header = ['units', 'parameter', 'tb', 'depth', 'type']


class ProjectParameterSerializer(patterns.AttachmentSerializer):
    class Meta(patterns.AttachmentSerializer.Meta):
        model = ProjectParameter
        exclude = ('project',)
        object_field = 'project'
        wq_config = {
            'initial': 3,
        }


class ProjectSerializer(patterns.IdentifiedModelSerializer):
    parameters = ProjectParameterSerializer(many=True, required=False)


_characteristic_defaults = {}


class CharacteristicSerializer(patterns.IdentifiedModelSerializer):
    projects = serializers.SerializerMethodField()
    default_speciations = serializers.SerializerMethodField()
    default_units = serializers.SerializerMethodField()
    default_methods = serializers.SerializerMethodField()

    def get_default_speciations(self, instance):
        return self.get_default_choices('speciation', instance)

    def get_default_units(self, instance):
        return self.get_default_choices('unit', instance)

    def get_default_methods(self, instance):
        return self.get_default_choices('method', instance)

    def get_default_choices(self, field, instance):
        _characteristic_defaults.setdefault(field, {})
        defaults = _characteristic_defaults[field]

        if instance.pk not in defaults:
            ids = Result.objects.filter(
                type=instance
            ).values_list(field + '__slug').annotate(
                Count('id')
            ).order_by('-id__count')
            defaults[instance.pk] = [id[0] for id in ids]

        return defaults[instance.pk]

    def get_projects(self, instance):
        return [project.project.slug for project in instance.projects.all()]
