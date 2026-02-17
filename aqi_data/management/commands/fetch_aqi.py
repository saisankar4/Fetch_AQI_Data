from django.core.management.base import BaseCommand
import requests
from aqi_data.models import AQIData, FetchLog
from datetime import datetime


def parse_aqi_record(record):
    """
    Parse API record and extract relevant fields for database storage
    """
    try:
        # Parse last_update to get sampling_date and sampling_time
        last_update = record.get('last_update', '')
        sampling_date = ''
        sampling_time = ''
        
        if last_update:
            # Format: '17-02-2026 21:00:00'
            parts = last_update.split(' ')
            if len(parts) == 2:
                sampling_date = parts[0]  # '17-02-2026'
                sampling_time = parts[1]  # '21:00:00'
        
        # Convert string values to float
        try:
            value = float(record.get('avg_value', 0)) if record.get('avg_value') else None
        except (ValueError, TypeError):
            value = None
        
        try:
            min_val = float(record.get('min_value', 0)) if record.get('min_value') else None
        except (ValueError, TypeError):
            min_val = None
        
        try:
            max_val = float(record.get('max_value', 0)) if record.get('max_value') else None
        except (ValueError, TypeError):
            max_val = None
        
        return {
            'state': record.get('state', ''),
            'city': record.get('city', ''),
            'pollutant_id': record.get('pollutant_id', ''),
            'pollutant_name': record.get('pollutant_name', ''),
            'value': value,
            'min_value': min_val,
            'max_value': max_val,
            'unit': record.get('unit', ''),
            'sampling_date': sampling_date,
            'sampling_time': sampling_time,
            'station_name': record.get('station', ''),
            'latitude': record.get('latitude', ''),
            'longitude': record.get('longitude', ''),
            'api_response': str(record)
        }
    except Exception as e:
        print(f"Error parsing record: {str(e)}")
        return None


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

        # Call data.gov.in API
        base_url = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
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
            
            # Debug output
            self.stdout.write(f'API Response Status: {response.status_code}')
            self.stdout.write(f'Response Keys: {list(data.keys())}')
            self.stdout.write(f'Total records available: {data.get("total", "N/A")}')
            self.stdout.write(f'Returned records count: {len(data.get("records", []))}')
            self.stdout.write(f'Count: {data.get("count", "N/A")}')
            self.stdout.write(f'Status: {data.get("status", "N/A")}')
            self.stdout.write(f'Message: {data.get("message", "N/A")}')
            
            if 'records' in data:
                for record in data['records']:
                    # Parse and save AQI data
                    try:
                        parsed_data = parse_aqi_record(record)
                        if parsed_data:
                            aqi_data = AQIData(
                                state=parsed_data['state'],
                                city=parsed_data['city'],
                                pollutant_id=parsed_data['pollutant_id'],
                                pollutant_name=parsed_data['pollutant_name'],
                                value=parsed_data['value'],
                                min_value=parsed_data['min_value'],
                                max_value=parsed_data['max_value'],
                                unit=parsed_data['unit'],
                                sampling_date=parsed_data['sampling_date'],
                                sampling_time=parsed_data['sampling_time'],
                                station_name=parsed_data['station_name'],
                                latitude=parsed_data['latitude'],
                                longitude=parsed_data['longitude'],
                                api_response=parsed_data['api_response']
                            )
                            aqi_data.save()
                            records_count += 1
                    except Exception as e:
                        self.stdout.write(f"Error storing record: {str(e)}")
            
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
