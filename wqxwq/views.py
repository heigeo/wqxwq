from wq.db.rest.views import ModelViewSet, SimpleView
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.renderers import BaseRenderer
from vera.results import views as vera
from .serializers import EventResultSerializer
from .models import Characteristic
from .util import export_wqx_bytes, generate_filename


class WqxDomainViewSet(ModelViewSet):
    @list_route(methods=["GET"])
    def unused(self, request, *args, **kwargs):
        data = [{
            'id': getattr(row, self.model.wqx_code_field),
            'label': getattr(row, self.model.wqx_name_field),
        } for row in self.model.objects.get_unused_values()]
        return Response({
            'count': len(data),
            'list': data,
        })


class ChartFilterBackend(vera.ChartFilterBackend):
    def filter_by_characteristic(self, qs, ids):
        return self.filter_by_parameter(qs, ids)


class ChartView(vera.ChartView):
    serializer_class = EventResultSerializer
    template_name = 'chart_display.html'
    filter_backends = [ChartFilterBackend]

    def get_template_context(self, data):
        backend = self.filter_backends[0]()
        backend.request = self.request
        backend.view = self

        def make_url(slug):
            parts = self.request.path.split('/')
            parts = parts[:-1] + [slug, parts[-1]]
            return '/'.join(parts)

        label = ""
        params = backend.filter_options.get('characteristic')
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
                paramset = set(Characteristic.objects.filter(pk__in=qs))
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


class FileRenderer(BaseRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        return data


class ExcelRenderer(FileRenderer):
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # noqa
    format = "xlsx"


class OldExcelRenderer(FileRenderer):
    media_type = "application/vnd.ms-excel"
    format = "xls"


class WqxExportView(SimpleView):
    renderer_classes = [ExcelRenderer, OldExcelRenderer]

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        format = request.accepted_renderer.format
        data, start, end = export_wqx_bytes(format, start_date, end_date)
        filename = generate_filename(start, end, format)
        return Response(
            data,
            headers={
               'Content-Disposition': 'attachment; filename="%s"' % filename,
            }
        )
