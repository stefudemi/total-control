from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .roles import EMPLOYEES_GROUP, get_role

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class UserBriefSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role']

    def get_role(self, user):
        return get_role(user)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'first_name', 'last_name',
            'email', 'is_active', 'role',
        ]
        read_only_fields = ['id', 'is_active', 'role']

    def get_role(self, user):
        return get_role(user)

    def validate(self, attrs):
        if 'password' in attrs:
            candidate = self.instance or User(
                **{k: v for k, v in attrs.items() if k != 'password'}
            )
            try:
                validate_password(attrs['password'], candidate)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        group, _ = Group.objects.get_or_create(name=EMPLOYEES_GROUP)
        user.groups.add(group)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
