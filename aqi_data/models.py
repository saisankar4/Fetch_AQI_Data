from mongoengine import Document, StringField, FloatField, DateTimeField, IntField
from datetime import datetime


class AQIData(Document):
    """
    MongoDB Document for storing AQI data fetched from the government API
    """
    state = StringField(required=True)
    city = StringField()
    pollutant_id = StringField(required=True)
    pollutant_name = StringField()
    value = FloatField()  # avg_value from API
    min_value = FloatField()
    max_value = FloatField()
    unit = StringField()
    sampling_date = StringField()
    sampling_time = StringField()
    station_name = StringField()
    latitude = StringField()
    longitude = StringField()
    timestamp = DateTimeField(default=datetime.now, required=True)
    api_response = StringField()  # Store raw JSON response for reference
    
    meta = {
        'collection': 'aqi_data',
        'indexes': [
            'state',
            'city',
            'pollutant_id',
            ('state', 'pollutant_id'),
            'timestamp',
            '-timestamp'
        ]
    }
    
    def __str__(self):
        return f"{self.state} - {self.city} - {self.pollutant_id}: {self.value} at {self.timestamp}"


class FetchLog(Document):
    """
    MongoDB Document for logging API fetch operations
    """
    state = StringField(required=True)
    pollutant_id = StringField(required=True)
    status = StringField(default='pending')  # pending, success, failed
    message = StringField()
    records_fetched = IntField(default=0)
    timestamp = DateTimeField(default=datetime.now, required=True)
    
    meta = {
        'collection': 'fetch_logs',
        'indexes': [
            'state',
            'pollutant_id',
            '-timestamp'
        ]
    }
    
    def __str__(self):
        return f"{self.state} - {self.pollutant_id}: {self.status} at {self.timestamp}"
