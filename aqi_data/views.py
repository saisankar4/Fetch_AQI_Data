from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AQIData, FetchLog
import json


class AQIDataListView(APIView):
    """
    API endpoint to retrieve AQI data for a state and pollutant
    """
    def get(self, request):
        state = request.query_params.get('state')
        pollutant_id = request.query_params.get('pollutant_id')
        limit = int(request.query_params.get('limit', 100))
        
        query = {}
        if state:
            query['state'] = state
        if pollutant_id:
            query['pollutant_id'] = pollutant_id
        
        try:
            data = AQIData.objects(**query).order_by('-timestamp')[:limit]
            result = []
            for item in data:
                result.append({
                    'state': item.state,
                    'pollutant_id': item.pollutant_id,
                    'pollutant_name': item.pollutant_name,
                    'value': item.value,
                    'unit': item.unit,
                    'sampling_date': item.sampling_date,
                    'sampling_time': item.sampling_time,
                    'station_name': item.station_name,
                    'timestamp': item.timestamp.isoformat() if item.timestamp else None
                })
            return Response(result, status=status.HTTP_200_OK)
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
