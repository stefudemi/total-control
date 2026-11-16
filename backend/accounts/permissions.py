from rest_framework.permissions import SAFE_METHODS, BasePermission

from .roles import is_admin, is_staff_member


class IsAdmin(BasePermission):
    """Solo administradores (is_staff)."""

    message = 'Se requieren permisos de administrador.'

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsStaffMember(BasePermission):
    """Administradores y empleados activos del grupo Empleados."""

    message = 'Se requiere ser personal del complejo.'

    def has_permission(self, request, view):
        return is_staff_member(request.user)


class IsAdminOrReadOnlyStaff(BasePermission):
    """Lectura para todo el personal; escritura solo para administradores."""

    message = 'Se requieren permisos de administrador.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return is_staff_member(request.user)
        return is_admin(request.user)
