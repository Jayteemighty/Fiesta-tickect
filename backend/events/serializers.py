from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'location', 'start_date', 'end_date',
            'start_time', 'end_time', 'price', 'payment_method', 'created_by',
        ]
