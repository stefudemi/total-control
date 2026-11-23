EMPLOYEES_GROUP = 'Empleados'


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.is_active and user.is_staff)


def is_staff_member(user) -> bool:
    if not (user and user.is_authenticated and user.is_active):
        return False
    return user.is_staff or user.groups.filter(name=EMPLOYEES_GROUP).exists()


def get_role(user) -> str:
    return 'admin' if user.is_staff else 'employee'
