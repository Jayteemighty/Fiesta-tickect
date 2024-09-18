from django.db import models
from django.conf import settings
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File


class Ticket(models.Model):
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket for {self.event.name} bought by {self.buyer.username}"

    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr_data = f"Ticket for {self.buyer.username}, Event: {self.event.name}"
            qr_image = qrcode.make(qr_data)
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            self.qr_code.save(f'{self.buyer.username}-{self.event.id}.png', File(buffer), save=False)
        super().save(*args, **kwargs)


class Payment(models.Model):
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE)
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=[('online', 'Online'), ('onsite', 'Onsite')])
    is_successful = models.BooleanField(default=False)
    reference = models.CharField(max_length=255, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.payer.username} for {self.event.name}"
