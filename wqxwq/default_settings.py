from wq.db.default_settings import ( # noqa
    TEMPLATES,
    SESSION_COOKIE_HTTPONLY,
    REST_FRAMEWORK,
    SOCIAL_AUTH_PIPELINE,
    ANONYMOUS_PERMISSIONS,
    SRID,
    DEFAULT_AUTH_GROUP,
    DISAMBIGUATE,
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'rest_framework',

    'wq.db.rest',
    'wq.db.rest.auth',

    'data_wizard',
    'rest_pandas',
    'wq.db.patterns.identify',

    'vera.params',
    'vera.series',
    'vera.results',

    'wqxwq',
]

WQ_SITE_MODEL = "wqxwq.Site"
WQ_PARAMETER_MODEL = "wqxwq.Characteristic"
WQ_EVENT_MODEL = "wqxwq.Event"
WQ_REPORT_MODEL = "wqxwq.Report"
WQ_RESULT_MODEL = "wqxwq.Result"
WQ_EVENTRESULT_MODEL = "wqxwq.EventResult"
WQ_DEFAULT_REPORT_STATUS = 1

TEMPLATES[0]['OPTIONS']['context_processors'] += (
    'wqxwq.context_processors.all',
)
