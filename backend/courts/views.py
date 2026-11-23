from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrReadOnlyStaff

from .models import Court
from .serializers import AvailabilityQuerySerializer, CourtSerializer
from .services import CourtError, deactivate_court, get_day_slots


class CourtViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD de canchas (sin borrado: se desactivan)."""

    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    permission_classes = [IsAdminOrReadOnlyStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.query_params.get('active')
        if active is not None:
            qs = qs.filter(is_active=active.lower() in ('1', 'true'))
        return qs

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        court = self.get_object()
        court.is_active = True
        court.save(update_fields=['is_active', 'updated_at'])
        return Response(self.get_serializer(court).data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        court = self.get_object()
        try:
            deactivate_court(court)
        except CourtError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(court).data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        court = self.get_object()
        query = AvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        day = query.validated_data['date']
        return Response({
            'court': court.id,
            'date': day,
            'is_active': court.is_active,
            'slots': get_day_slots(court, day),
        })
