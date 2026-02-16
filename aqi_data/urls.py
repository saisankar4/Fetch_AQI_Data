from django.urls import path
from . import views

urlpatterns = [
    path('aqi-data/', views.AQIDataListView.as_view(), name='aqi-data-list'),
    path('fetch-logs/', views.FetchLogsView.as_view(), name='fetch-logs'),
]
