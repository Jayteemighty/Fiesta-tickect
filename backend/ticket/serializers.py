from rest_framework import serializers
from .models import Ticket, Payment


class TicketSerializer(serializers.ModelSerializer):
    event_name = serializers.ReadOnlyField(source='event.name')
    buyer_name = serializers.ReadOnlyField(source='buyer.username')

    class Meta:
        model = Ticket
        fields = ['event_name', 'buyer_name', 'qr_code', 'amount_paid', 'paid_at']


class PaymentSerializer(serializers.ModelSerializer):
    event_name = serializers.ReadOnlyField(source='event.name')
    payer_name = serializers.ReadOnlyField(source='payer.username')

    class Meta:
        model = Payment
        fields = ['event_name', 'payer_name', 'amount', 'payment_method', 'is_successful', 'reference', 'created_at']
