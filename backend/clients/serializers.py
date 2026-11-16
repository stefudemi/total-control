from rest_framework import serializers

from .models import Client, normalize_phone


class ClientSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=30)

    class Meta:
        model = Client
        fields = ['id', 'first_name', 'last_name', 'phone', 'email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_phone(self, value):
        phone = normalize_phone(value)
        digits = phone.lstrip('+')
        if not (6 <= len(digits) <= 15):
            raise serializers.ValidationError('El teléfono debe tener entre 6 y 15 dígitos.')
        duplicates = Client.objects.filter(phone=phone)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError('Ya existe un cliente con ese teléfono.')
        return phone


class ClientInputSerializer(serializers.Serializer):
    """Datos de cliente embebidos en una reserva (sin chequeo de unicidad)."""

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True, default='')

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if not (6 <= len(phone.lstrip('+')) <= 15):
            raise serializers.ValidationError('El teléfono debe tener entre 6 y 15 dígitos.')
        return phone
