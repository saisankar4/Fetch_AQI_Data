from django.urls import path
from . import views

urlpatterns = [
    path('api-data/', views.APIDataView.as_view(), name='api-data'),  # Returns data from DB only
    path('aqi-data/', views.AQIDataListView.as_view(), name='aqi-data-list'),
    path('fetch-logs/', views.FetchLogsView.as_view(), name='fetch-logs'),
]
