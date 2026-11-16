from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsStaffMember
from courts.models import Court
from courts.services import get_day_bookings, get_day_slots

from .models import Booking
from .serializers import (
    AgendaQuerySerializer,
    BookingCreateSerializer,
    BookingFilterSerializer,
    BookingSerializer,
)
from .services import BookingError, cancel_booking, create_booking


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Reservas: listado con filtros, alta y cancelación (sin edición ni borrado)."""

    queryset = Booking.objects.select_related('court', 'client', 'created_by', 'cancelled_by')
    serializer_class = BookingSerializer
    permission_classes = [IsStaffMember]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != 'list':
            return qs
        filters = BookingFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        data = filters.validated_data
        if 'date' in data:
            tz = timezone.get_current_timezone()
            start = datetime.combine(data['date'], datetime.min.time(), tzinfo=tz)
            qs = qs.filter(start_at__gte=start, start_at__lt=start + timedelta(days=1))
        if 'court' in data:
            qs = qs.filter(court_id=data['court'])
        if 'client' in data:
            qs = qs.filter(client_id=data['client'])
        if 'status' in data:
            qs = qs.filter(status=data['status'])
        return qs

    def create(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            booking = create_booking(
                court=data['court'],
                start_at=data['start_at'],
                duration_minutes=data['duration_minutes'],
                created_by=request.user,
                client=data.get('client_instance'),
                client_data=data.get('client'),
                notes=data['notes'],
            )
        except BookingError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        booking = self.get_queryset().get(pk=booking.pk)
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        try:
            booking = cancel_booking(booking, request.user)
        except BookingError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        booking = self.get_queryset().get(pk=booking.pk)
        return Response(self.get_serializer(booking).data)


class AgendaView(APIView):
    """Canchas activas con sus franjas y reservas del día (una consulta de reservas)."""

    permission_classes = [IsStaffMember]

    def get(self, request):
        query = AgendaQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        day = query.validated_data['date']
        courts = list(Court.objects.filter(is_active=True))
        bookings = get_day_bookings(day, courts=courts)
        by_court = {court.id: [] for court in courts}
        for booking in bookings:
            by_court[booking.court_id].append(booking)
        return Response({
            'date': day,
            'courts': [
                {
                    'id': court.id,
                    'name': court.name,
                    'court_type': court.court_type,
                    'opening_time': court.opening_time,
                    'closing_time': court.closing_time,
                    'slots': get_day_slots(court, day, bookings=by_court[court.id]),
                    'bookings': BookingSerializer(by_court[court.id], many=True).data,
                }
                for court in courts
            ],
        })
