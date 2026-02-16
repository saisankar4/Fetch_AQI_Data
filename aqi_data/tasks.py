from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def fetch_aqi_task():
    """
    Celery task to fetch AQI data every hour
    """
    try:
        logger.info('Starting hourly AQI data fetch...')
        call_command('fetch_aqi')
        logger.info('Hourly AQI data fetch completed successfully')
        return 'AQI data fetched successfully'
    except Exception as e:
        logger.error(f'Error in hourly AQI fetch: {str(e)}')
        return f'Error: {str(e)}'
