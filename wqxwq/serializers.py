from wq.db.patterns import serializers as patterns
from vera.results import serializers as vera
from vera.series.serializers import EventSerializer, ReportSerializer
from rest_framework import serializers
from .models import Parameter


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
        for param in Parameter.objects.filter(pk__in=type_ids):
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


class ReportSerializer(ReportSerializer):
    def get_wq_config(self):
        conf = super().get_wq_config()
        for field in conf['form']:
            if field['name'] == 'results':
                field['initial'] = None
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
