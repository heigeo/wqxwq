from tempfile import mkstemp
from .models import EventResult
from collections import OrderedDict
from wq.io import ExcelFileIO
import datetime
from django.utils.timezone import make_aware
from django.conf import settings
import os


def get_project_name():
    return getattr(settings, 'PROJECT_NAME', 'PROJECT_NAME')


def generate_filename(start_date, end_date, format):
    if start_date == end_date:
        date_range = start_date
    else:
        date_range = "{start_date} to {end_date}".format(
            start_date=start_date,
            end_date=end_date,
        )
    return "{project_name} {date_range}.{format}".format(
        project_name=get_project_name(),
        date_range=date_range,
        format=format,
    )


def get_timezone(result):
    date = result.event_date
    time = result.result_report.time
    if not time:
        return None
    return make_aware(datetime.datetime.combine(date, time)).tzname()


field_map = OrderedDict([
    ("Project ID",                                 "result_report.project.name"), # noqa
    ("Monitoring Location ID",                     "event_site.slug"),
    ("Activity ID",                                "result_report.activity_id"), # noqa
    ("Activity Type",                              "event_type.name"),
    ("Activity Media Name",                        lambda r: "Water"), # noqa
    ("Activity Start Date",                        "event_date"),
    ("Activity Start Time",                        "result_report.time"),
    ("Activity Start Time Zone",                   get_timezone),
    ("Activity Depth/Height Measure",               "event_depth"),
    ("Activity Depth/Height Unit",                  lambda r: "ft" if r.event_depth else None), # noqa
    ("Sample Collection Method ID",                 None),
    ("Sample Collection Equipment Name",            None),
    ("Sample Collection Equipment Comment",         None),
    ("Data Logger Line",                            None),
    ("Characteristic Name",                         "result_type.name"),
    ("Method Speciation",                           "result_speciation.name"),
    ("Result Detection Condition",                  None),
    ("Result Value",                                "result_value"),
    ("Result Unit",                                 "result_unit.slug"),
    ("Result Measure Qualifier",                    None),
    ("Result Sample Fraction",                      None),
    ("Result Status ID",                            None),
    ("Statistical Base Code",                       None),
    ("Result Value Type",                           None),
    ("Result Analytical Method ID",                 "result_method.slug"),
    ("Result Analytical Method Context",            "result_method.contextcode.slug"), # noqa
    ("Analysis Start Date",                         None),
    ("Result Detection/Quantitation Limit Type",    None),
    ("Result Detection/Quantitation Limit Measure", None),
    ("Result Detection/Quantitation Limit Unit",    None),
    ("Result Comment",                              "result_comment"),
])


def export_wqx(filename=None, start_date=None, end_date=None):
    qs = EventResult.objects.order_by(
        'event_date',
        'result_report__time',
        'result_report__entered'
    )
    if start_date:
        qs = qs.filter(event_date__gte=start_date)
    if end_date:
        qs = qs.filter(event_date__lte=end_date)

    if qs.exists():
        date_range = (qs.first().event_date, qs.last().event_date)
    else:
        date_range = (
            start_date or end_date or "First",
            end_date or start_date or "Last"
        )

    if filename is None:
        filename = generate_filename(date_range[0], date_range[1], 'xlsx')
        print('Saved to "%s"' % filename)

    excelio = ExcelFileIO(
        filename=filename,
        field_names=list(field_map.keys()),
    )

    for result in qs:
        vals = {}
        for name, lookup in field_map.items():
            field = excelio.map_field(name)
            if lookup is None:
                value = None
            elif callable(lookup):
                value = lookup(result)
            else:
                parts = lookup.split('.')
                value = result
                for part in parts:
                    value = getattr(value, part)
                    if value is None:
                        break
            vals[field] = value

        excelio.append(excelio.create(**vals))
    excelio.save()
    return date_range


def export_wqx_bytes(format='xlsx', start_date=None, end_date=None):
    file, filename = mkstemp(suffix='.' + format)
    os.close(file)
    os.unlink(filename)
    start, end = export_wqx(filename, start_date, end_date)
    file = open(filename, 'rb')
    output = file.read()
    file.close()
    os.unlink(filename)
    return output, start, end
