from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AQIData, FetchLog
import json
import requests


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
