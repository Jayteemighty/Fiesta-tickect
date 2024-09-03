from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/create/', views.EventCreateView.as_view(), name='event-create'),
    path('events/user/', views.UserEventListView.as_view(), name='user-event-list'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
]
