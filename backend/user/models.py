from datetime import datetime, timedelta
import os
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy
from django.utils import timezone
from uuid import uuid4

from .manager import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    '''Custom user model'''
    
    # Sign up modes
    EMAIL = 'email'
    GOOGLE = 'google'
    
    sign_up_modes = [
        (EMAIL, 'Email'),
        (GOOGLE, 'Google'),
    ]

    id = models.UUIDField(default=uuid4, primary_key=True)
    email = models.EmailField(gettext_lazy('email address'), unique=True, null=False)
    username = models.CharField(max_length=20, unique=True, null=False, default='')
    first_name = models.CharField(max_length=128, null=False)
    last_name = models.CharField(max_length=128, null=False)
    phone_number = models.CharField(max_length=15, null=False, default='')
    sign_up_mode = models.CharField(max_length=6, choices=sign_up_modes, default=EMAIL, null=False)
    is_verified = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
       

class OTP(models.Model):
    '''Model to store user OTP at sign up'''
    
    SIGNUP = 'signup'
    PASSWORD_RESET = 'passwordreset'
    LOGIN = 'login'
    
    otp_types = [
        (SIGNUP, 'Sign Up'),
        (PASSWORD_RESET, 'PasswordReset'),
        (LOGIN, 'Login')
    ]
    
    email = models.EmailField(null=False)
    otp = models.CharField(max_length=4, null=False)
    otp_type = models.CharField(max_length=13, choices=otp_types, default=SIGNUP, null=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    def __str__(self):
        return f'{self.email} | {self.otp} | {self.otp_type}'
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
        
    def is_expired(self):
        return self.expires_at.replace(tzinfo=None) < timezone.now().replace(tzinfo=None)
    
    class Meta:
        ordering = ['-created_at']