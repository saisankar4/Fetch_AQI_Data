from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AQIData, FetchLog
import json
import requests
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


class APIDataView(APIView):
    """
    API endpoint to retrieve AQI data from the database only.
    This is called by the UI to get cached data fetched automatically every hour.
    """
    def get(self, request):
        state = request.query_params.get('state')
        pollutant_id = request.query_params.get('pollutant_id')
        limit = int(request.query_params.get('limit', 100000))
        
        try:
            # Build query filter
            query_filter = {}
            if state:
                query_filter['state'] = state
            if pollutant_id:
                query_filter['pollutant_id'] = pollutant_id
            
            # Query from database, sorted by latest timestamp
            aqi_records = AQIData.objects(**query_filter).order_by('-timestamp')[:limit]
            
            # Format response data
            result = []
            for record in aqi_records:
                result.append({
                    'id': str(record.id),
                    'state': record.state,
                    'city': record.city,
                    'pollutant_id': record.pollutant_id,
                    'pollutant_name': record.pollutant_name,
                    'value': record.value,
                    'min_value': record.min_value,
                    'max_value': record.max_value,
                    'unit': record.unit,
                    'sampling_date': record.sampling_date,
                    'sampling_time': record.sampling_time,
                    'station_name': record.station_name,
                    'latitude': record.latitude,
                    'longitude': record.longitude,
                    'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                })
            
            return Response({
                'status': 'success',
                'count': len(result),
                'records': result
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AQIDataListView(APIView):
    """
    API endpoint to retrieve AQI data from data.gov.in API
    """
    def get(self, request):
        state = request.query_params.get('state')
        pollutant_id = request.query_params.get('pollutant_id')
        limit = int(request.query_params.get('limit', 1000))
        
        # Call data.gov.in API - Check your resource ID at https://data.gov.in
        base_url = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
        api_key = "579b464db66ec23bdd000001cadadb66113a49b34bd325f41040f74f"
        
        params = {
            'api-key': api_key,
            'format': 'json',
            'limit': limit,
            'offset': 0
        }
        
        if state:
            params['filters[state]'] = state
        
        if pollutant_id:
            params['filters[pollutant_id]'] = pollutant_id
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            api_data = response.json()
            
            # Check for API errors
            if api_data.get('status') == 'error':
                return Response({
                    'status': 'error',
                    'message': api_data.get('message', 'API Error'),
                    'details': 'Invalid resource ID. Please verify the resource ID at https://data.gov.in'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = []
            if 'records' in api_data:
                for record in api_data['records']:
                    # Parse and store record in database
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
                    except Exception as e:
                        print(f"Error storing record: {str(e)}")
                    
                    result.append({
                        'country': record.get('country', ''),
                        'state': record.get('state', ''),
                        'city': record.get('city', ''),
                        'station': record.get('station', ''),
                        'last_update': record.get('last_update', ''),
                        'latitude': record.get('latitude', ''),
                        'longitude': record.get('longitude', ''),
                        'pollutant_id': record.get('pollutant_id', ''),
                        'min_value': record.get('min_value', ''),
                        'max_value': record.get('max_value', ''),
                        'avg_value': record.get('avg_value', ''),
                    })
            
            return Response({
                'status': 'success',
                'count': len(result),
                'total': api_data.get('total', 0),
                'records': result
            }, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            return Response({'error': f'Failed to fetch from gov.in: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchLogsView(APIView):
    """
    API endpoint to view fetch operation logs
    """
    def get(self, request):
        state = request.query_params.get('state')
        limit = int(request.query_params.get('limit', 50))
        
        query = {}
        if state:
            query['state'] = state
        
        try:
            logs = FetchLog.objects(**query).order_by('-timestamp')[:limit]
            result = []
            for log in logs:
                result.append({
                    'state': log.state,
                    'pollutant_id': log.pollutant_id,
                    'status': log.status,
                    'message': log.message,
                    'records_fetched': log.records_fetched,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None
                })
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
