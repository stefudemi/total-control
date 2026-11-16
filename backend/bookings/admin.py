from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('court', 'client', 'start_at', 'duration_minutes', 'status')
    list_filter = ('status', 'court')
    date_hierarchy = 'start_at'
    raw_id_fields = ('client',)
