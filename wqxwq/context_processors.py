from .util import get_project_name
import datetime


def project_name(request):
    return {'project_name': get_project_name()}


def current_year(request):
    return {'current_year': datetime.date.today().year}


def all(request):
    context = {}
    for fn in [project_name, current_year]:
        context.update(fn(request))
    return context
