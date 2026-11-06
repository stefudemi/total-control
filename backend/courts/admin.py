from django.contrib import admin

from .models import Court


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'court_type', 'opening_time', 'closing_time', 'is_active')
    list_filter = ('court_type', 'is_active')
    search_fields = ('name',)
