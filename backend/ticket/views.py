from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Ticket, Payment
from .serializers import TicketSerializer, PaymentSerializer
from events.models import Event
#from paystackapi.paystack import Paystack

paystack = Paystack(secret_key="your_secret_key")


class TicketPurchaseView(APIView):
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        amount = event.price

        # Simulate calling Paystack to initiate a payment
        paystack_response = paystack.transaction.initialize(
            reference=f'{event_id}-{request.user.id}',
            amount=int(amount * 100),  # Paystack requires amount in kobo
            email=request.user.email
        )
        
        if paystack_response['status']:
            payment = Payment.objects.create(
                event=event,
                payer=request.user,
                amount=amount,
                payment_method="online",
                is_successful=True,
                reference=paystack_response['data']['reference']
            )
            ticket = Ticket.objects.create(
                event=event,
                buyer=request.user,
                amount_paid=amount
            )
            ticket_serializer = TicketSerializer(ticket)
            return Response(ticket_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)


class PaystackWebhook(APIView):
    def post(self, request):
        # Handle Paystack webhook for payment success
        data = request.data
        if data['event'] == 'charge.success':
            try:
                payment = Payment.objects.get(reference=data['data']['reference'])
                payment.is_successful = True
                payment.save()
                return Response(status=status.HTTP_200_OK)
            except Payment.DoesNotExist:
                return Response({"detail": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserTicketsView(APIView):
    def get(self, request):
        tickets = Ticket.objects.filter(buyer=request.user)
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)
