from django.contrib.auth import authenticate, get_user_model
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdmin
from .serializers import LoginSerializer, UserBriefSerializer, UserSerializer

User = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = authenticate(request, username=data['username'], password=data['password'])
        if user is None:
            # authenticate rechaza a los inactivos: se distingue para dar un mensaje claro.
            existing = User.objects.filter(username=data['username']).first()
            if existing and not existing.is_active and existing.check_password(data['password']):
                return Response(
                    {'detail': 'El usuario está desactivado.'}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'detail': 'Usuario o contraseña incorrectos.'}, status=status.HTTP_400_BAD_REQUEST
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserBriefSerializer(user).data})


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserBriefSerializer(request.user).data)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Gestión de usuarios (solo admin). Sin borrado: se desactivan."""

    queryset = User.objects.order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def _set_active(self, value):
        user = self.get_object()
        if not value and user.pk == self.request.user.pk:
            return Response(
                {'detail': 'No podés desactivarte a vos mismo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = value
        user.save(update_fields=['is_active'])
        if not value:
            Token.objects.filter(user=user).delete()
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        return self._set_active(True)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        return self._set_active(False)
