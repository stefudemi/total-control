from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AgendaView, BookingViewSet

router = DefaultRouter()
router.register('bookings', BookingViewSet, basename='booking')

urlpatterns = [path('agenda/', AgendaView.as_view())] + router.urls
