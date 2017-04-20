from wq.db import rest
from wq.db.patterns import rest as patterns
from .models import (
    Characteristic, MethodSpeciation, AnalyticalMethod, MeasureUnit,
    Spreadsheet, WaterbodyType, Waterbody,
    ActivityType, Site, Event, Report, Project,
)
from .serializers import (
    WqxDomainSerializer, CharacteristicSerializer,
    WaterbodySerializer, SiteSerializer, ProjectSerializer,
    EventSerializer, ReportSerializer,
)
from .views import WqxDomainViewSet
from django.db.utils import ProgrammingError


# Domain models
rest.router.register_serializer(Characteristic, CharacteristicSerializer)
rest.router.register_viewset(Characteristic, WqxDomainViewSet)
wqx_opts = dict(
    fields="__all__",
    serializer=WqxDomainSerializer,
    viewset=WqxDomainViewSet,
    cache="all",
)
rest.router.register_model(AnalyticalMethod, **wqx_opts)
rest.router.register_model(MethodSpeciation, **wqx_opts)
rest.router.register_model(MeasureUnit, **wqx_opts)
rest.router.register_model(ActivityType, **wqx_opts)

# Models and pages unique to wqxwq
rest.router.register_model(
    Spreadsheet,
    fields=["id", "file"],
    cache="none",
)
rest.router.register_model(
    WaterbodyType,
    fields="__all__",
    serializer=patterns.IdentifiedModelSerializer,
    cache="all",
)
rest.router.register_model(
    Waterbody,
    fields="__all__",
    serializer=WaterbodySerializer,
    cache="all",
)
rest.router.register_model(
    Project,
    fields="__all__",
    serializer=ProjectSerializer,
    cache="all",
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
rest.router.update_config(
    Site,
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

rest.router.register_serializer(Site, SiteSerializer)
rest.router.register_serializer(Event, EventSerializer)
rest.router.register_serializer(Report, ReportSerializer)
