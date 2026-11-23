from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.permissions import IsStaffMember

from .models import Client
from .serializers import ClientSerializer


class ClientPagination(PageNumberPagination):
    page_size = 20


class ClientViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Clientes: listado paginado con búsqueda, alta y edición (sin borrado)."""

    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsStaffMember]
    pagination_class = ClientPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'phone']

    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Historial de reservas del cliente, de la más reciente a la más antigua."""
        from bookings.serializers import BookingSerializer

        client = self.get_object()
        qs = client.bookings.select_related(
            'court', 'client', 'created_by', 'cancelled_by'
        ).order_by('-start_at')
        return Response(BookingSerializer(qs, many=True).data)
