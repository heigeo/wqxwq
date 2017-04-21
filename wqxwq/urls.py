from django.conf.urls import url
from .views import TimeSeriesView, ScatterView, BoxPlotView, WqxExportView
from rest_framework.urlpatterns import format_suffix_patterns


urlpatterns = format_suffix_patterns([
    url('^(?P<ids>[^\.]+)/timeseries$', TimeSeriesView.as_view()),
    url('^(?P<ids>[^\.]+)/scatter$', ScatterView.as_view()),
    url('^(?P<ids>[^\.]+)/boxplot$', BoxPlotView.as_view()),
    url('^wqx$', WqxExportView.as_view()),
])
