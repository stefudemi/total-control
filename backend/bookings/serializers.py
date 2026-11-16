from rest_framework import serializers

from clients.models import Client
from clients.serializers import ClientInputSerializer
from courts.models import Court

from .models import Booking


class UserRefSerializer(serializers.Serializer):
    username = serializers.CharField()
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, user):
        return user.get_full_name() or user.username


class BookingSerializer(serializers.ModelSerializer):
    court = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    created_by = UserRefSerializer(read_only=True)
    cancelled_by = UserRefSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'court', 'client', 'start_at', 'duration_minutes', 'end_at',
            'status', 'notes', 'created_by', 'created_at', 'cancelled_by', 'cancelled_at',
        ]

    def get_court(self, booking):
        return {'id': booking.court_id, 'name': booking.court.name}

    def get_client(self, booking):
        client = booking.client
        return {'id': client.id, 'full_name': client.full_name, 'phone': client.phone}


class BookingCreateSerializer(serializers.Serializer):
    court = serializers.PrimaryKeyRelatedField(queryset=Court.objects.all())
    start_at = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField()
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source='client_instance', required=False
    )
    client = ClientInputSerializer(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        has_id = 'client_instance' in attrs
        has_data = 'client' in attrs
        if has_id == has_data:
            raise serializers.ValidationError(
                {'client': ['Indicá client_id o los datos de client (solo uno de los dos).']}
            )
        return attrs


class BookingFilterSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    court = serializers.IntegerField(required=False)
    client = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=Booking.Status.choices, required=False)


class AgendaQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
