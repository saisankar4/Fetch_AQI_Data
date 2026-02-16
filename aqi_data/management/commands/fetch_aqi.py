from django.core.management.base import BaseCommand
import requests
from aqi_data.models import AQIData, FetchLog
from datetime import datetime


class Command(BaseCommand):
    help = 'Fetch AQI data from the government API and store in MongoDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--state',
            type=str,
            help='Fetch data for a specific state',
        )
        parser.add_argument(
            '--pollutant',
            type=str,
            help='Fetch data for a specific pollutant',
        )

    def handle(self, *args, **options):
        state = options.get('state')
        pollutant = options.get('pollutant')

        # Replace these with actual government AQI API endpoints
        # Example: https://api.data.gov.in/resource/3b01bcb8-0b14-41b3-aadb-e1a27efc3ae2
        
        base_url = "https://api.data.gov.in/resource/3b01bcb8-0b14-41b3-aadb-e1a27efc3ae2"
        api_key = "579b464db66ec23bdd000001cadadb66113a49b34bd325f41040f74f"  # Get from data.gov.in
        
        params = {
            'api-key': api_key,
            'format': 'json',
            'limit': 1000
        }
        
        if state:
            params['filters[state]'] = state
        
        if pollutant:
            params['filters[pollutant_id]'] = pollutant

        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            records_count = 0
            
            if 'records' in data:
                for record in data['records']:
                    # Create or update AQI data
                    aqi_data = AQIData(
                        state=record.get('state', ''),
                        pollutant_id=record.get('pollutant_id', ''),
                        pollutant_name=record.get('pollutant_name', ''),
                        value=float(record.get('value', 0)) if record.get('value') else None,
                        unit=record.get('unit', ''),
                        sampling_date=record.get('sampling_date', ''),
                        sampling_time=record.get('sampling_time', ''),
                        station_name=record.get('station_name', ''),
                        api_response=str(record)
                    )
                    aqi_data.save()
                    records_count += 1
            
            # Log the fetch
            FetchLog(
                state=state or 'All',
                pollutant_id=pollutant or 'All',
                status='success',
                message=f'Successfully fetched {records_count} records',
                records_fetched=records_count
            ).save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fetched {records_count} AQI records'
                )
            )
        
        except requests.exceptions.RequestException as e:
            error_msg = f'Failed to fetch AQI data: {str(e)}'
            FetchLog(
                state=state or 'All',
                pollutant_id=pollutant or 'All',
                status='failed',
                message=error_msg,
                records_fetched=0
            ).save()
            
            self.stdout.write(
                self.style.ERROR(error_msg)
            )
        
        except Exception as e:
            error_msg = f'Error processing AQI data: {str(e)}'
            FetchLog(
                state=state or 'All',
                pollutant_id=pollutant or 'All',
                status='failed',
                message=error_msg,
                records_fetched=0
            ).save()
            
            self.stdout.write(
                self.style.ERROR(error_msg)
            )
