from wq.db import rest
from wq.db.patterns import rest as patterns
from .models import (
    Spreadsheet, WaterbodyType, Waterbody, ParameterMethod, EventType,
    Site, Event, Report
)
from .serializers import (
    WaterbodySerializer, SiteSerializer, EventSerializer, ReportSerializer
)
from django.db.utils import ProgrammingError


# Models and pages unique to wqxwq
rest.router.register_model(
    Spreadsheet,
    fields=["id", "file"],
)
rest.router.register_model(
    WaterbodyType,
    fields="__all__",
    serializer=patterns.IdentifiedModelSerializer,
)
rest.router.register_model(
    Waterbody,
    fields="__all__",
    serializer=WaterbodySerializer,
)
rest.router.register_model(
    ParameterMethod,
    fields="__all__",
    serializer=patterns.IdentifiedModelSerializer,
)
rest.router.register_model(
    EventType,
    fields="__all__",
    serializer=patterns.IdentifiedModelSerializer,
)
rest.router.add_page('index', {
    'url': '',
    'map': {
        'layers': [{
            'name': 'Sites',
            'type': 'geojson',
            'url': 'sites.geojson',
            'popup': 'site',
            'icon': '{{icon}}',
        }]
    }
})

try:
    icons = [{
        'name': wt.slug,
        'url': wt.icon.url,
    } for wt in WaterbodyType.objects.all()]
except ProgrammingError:
    pass
else:
    rest.router.set_extra_config(
        icons=icons,
    )

rest.router.set_extra_config(
    chartapp={
        'label_template': (
            "{{#parameter}}"
            "{{{parameter}}}"
            "{{#units}} ({{{units}}}){{/units}}"
            " at "
            "{{/parameter}}"
            "{{{site}}}"
            "{{#tb}} ({{tb}}){{/tb}}"
        ),
    },
)


# Override configuration for vera models
rest.router.register_serializer(Site, SiteSerializer)
rest.router.update_config(
    Site,
    max_local_pages=0,
    partial=True,
    map=[{
        'mode': 'list',
        'layers': [{
            'name': 'Sites',
            'type': 'geojson',
            'url': '{{{url}}}.geojson',
            'icon': '{{icon}}',
            'popup': 'site',
            'cluster': True,
        }]
    }, {
        'mode': 'detail',
        'layers': [{
            'name': 'Site',
            'type': 'geojson',
            'url': 'sites/{{id}}.geojson',
            'icon': '{{icon}}',
        }]
    }],
)


def event_filter(qs, req):
    if req.path == '/events.json':
        return qs.objects.none()
    else:
        return qs

rest.router.register_serializer(Event, EventSerializer)
rest.router.register_filter(Event, event_filter)
rest.router.update_config(Event, max_local_pages=0)


def report_filter(qs, req):
    if req.path in ('/reports.json', '/reports', '/reports/'):
        if req.user.is_authenticated:
            return qs.filter(user=req.user)
        else:
            return qs.none()
    return qs

rest.router.register_serializer(Report, ReportSerializer)
rest.router.register_filter(Report, report_filter)
