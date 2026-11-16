from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import PageNumberPagination

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
