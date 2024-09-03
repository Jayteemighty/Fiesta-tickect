from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'start_date', 'end_date', 'start_time', 'end_time', 'price', 'payment_method', 'created_by', 'created_at')
    list_filter = ('location', 'start_date', 'payment_method')
    search_fields = ('name', 'location', 'created_by__email')
    date_hierarchy = 'start_date'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
