from django.db import models
from django.conf import settings

class Event(models.Model):
    PAYMENT_CHOICES = [
        ('online', 'Online'),
        ('onsite', 'On-site'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    start_time = models.TimeField()  # Added start time
    end_time = models.TimeField()    # Added end time
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Added price
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)  # Added payment method
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
