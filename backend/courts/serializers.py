from rest_framework import serializers

from .models import Court


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = [
            'id', 'name', 'court_type', 'description',
            'opening_time', 'closing_time', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def validate(self, attrs):
        opening = attrs.get('opening_time', getattr(self.instance, 'opening_time', None))
        closing = attrs.get('closing_time', getattr(self.instance, 'closing_time', None))
        if opening and closing and opening >= closing:
            raise serializers.ValidationError(
                {'closing_time': 'La hora de cierre debe ser posterior a la de apertura.'}
            )
        return attrs


class AvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
