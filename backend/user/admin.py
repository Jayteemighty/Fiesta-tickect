from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import OTP
from .forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password', 'first_name', 'username',
         'last_name', 'phone_number', 'sign_up_mode')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
        })
    )
    model = User
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('email', 'id', 'username', 'first_name', 'last_name', 'phone_number', 'is_active', 'is_verified', 'sign_up_mode')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(User, UserAdmin)
admin.site.register(OTP)