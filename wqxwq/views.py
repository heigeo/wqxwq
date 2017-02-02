from vera.results import views as vera
from .serializers import EventResultSerializer
from .models import Parameter


class ChartView(vera.ChartView):
    serializer_class = EventResultSerializer
    template_name = 'chart_display.html'

    def get_template_context(self, data):
        backend = self.filter_backends[0]()
        backend.request = self.request
        backend.view = self

        def make_url(slug):
            parts = self.request.path.split('/')
            parts = parts[:-1] + [slug, parts[-1]]
            return '/'.join(parts)

        label = ""
        params = backend.filter_options.get('parameter')
        addparams = []
        if params:
            label += " vs. ".join([param.name for param in params])
            if len(params) < 2:
                qs = self.filter_queryset(self.get_queryset())
                qs = qs.model.objects.filter(
                    event_id__in=qs.values_list('event_id', flat=True)
                )
                qs = qs.order_by('result_type_id').distinct('result_type_id')
                qs = qs.values_list('result_type_id', flat=True)
                paramset = set(Parameter.objects.filter(pk__in=qs))
                for param in params:
                    paramset.remove(param.content_object)

                addparams = [{
                    'url': make_url(param.slug),
                    'label': param.name,
                } for param in paramset]

        sites = backend.filter_options.get('site')
        site_links = []
        addsites = []

        if sites:
            if label:
                label += ' at '
            label += ", ".join([site.name for site in sites])

            if len(sites) == 1:
                site_links = [{
                    'url': 'sites/' + sites[0].slug,
                    'label':  "< Back to " + sites[0].name,
                }]

            siteset = set()
            for site in sites:
                for s in site.content_object.waterbody.site_set.all():
                    siteset.add(s)

            for site in sites:
                siteset.remove(site.content_object)

            addsites = [{
                'url': make_url(site.slug),
                'label': site.name,
            } for site in siteset]

        return {
            'title': label,
            'links': site_links,
            'addsites': sorted(addsites, key=lambda d: d['label']),
            'addparameters': sorted(addparams, key=lambda d: d['label']),
        }


class TimeSeriesView(ChartView):
    serializer_class = EventResultSerializer
    pandas_serializer_class = vera.PandasUnstackedSerializer


class ScatterView(ChartView):
    serializer_class = EventResultSerializer
    pandas_serializer_class = vera.PandasScatterSerializer


class BoxPlotView(ChartView):
    serializer_class = EventResultSerializer
    pandas_serializer_class = vera.PandasBoxplotSerializer
