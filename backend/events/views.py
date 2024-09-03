from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer

# View for creating an event
class EventCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

# View for listing all events
class EventListView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

# View for listing events created by the authenticated user
class UserEventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(created_by=self.request.user)

# View for retrieving, updating, or deleting event details
class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.created_by == self.request.user or self.request.user.is_superuser:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this event.")
