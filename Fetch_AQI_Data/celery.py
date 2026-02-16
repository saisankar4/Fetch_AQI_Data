import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fetch_AQI_Data.settings')

app = Celery('Fetch_AQI_Data')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule - Run fetch_aqi every hour
app.conf.beat_schedule = {
    'fetch-aqi-hourly': {
        'task': 'aqi_data.tasks.fetch_aqi_task',
        'schedule': crontab(minute=0),  # Run at the top of every hour
    },
}

app.conf.timezone = 'UTC'
