from django.urls import path
from .views import TicketPurchaseView, PaystackWebhook, UserTicketsView

urlpatterns = [
    path('events/<int:event_id>/purchase/', TicketPurchaseView.as_view(), name='ticket-purchase'),
    path('paystack/webhook/', PaystackWebhook.as_view(), name='paystack-webhook'),
    path('tickets/', UserTicketsView.as_view(), name='user-tickets'),
]
