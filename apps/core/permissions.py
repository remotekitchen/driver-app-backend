from django.conf import settings
from rest_framework.permissions import BasePermission
SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class IsOwnerRoleOrReadOnly(BasePermission):
    """
    Custom permission:
    - SAFE_METHODS: allowed to everyone.
    - Other methods: allowed only to users with role='owner' or is_superuser.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated and
            (request.user.role == "owner" or request.user.is_superuser)
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        # For Store
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # For Menu
        if hasattr(obj, 'store') and hasattr(obj.store, 'owner'):
            return obj.store.owner == request.user

        # For MenuItem
        if hasattr(obj, 'menu') and hasattr(obj.menu, 'store') and hasattr(obj.menu.store, 'owner'):
            return obj.menu.store.owner == request.user

        # For ModifierGroup: obj.menu_item.menu.store.owner
        if hasattr(obj, 'menu_item') and hasattr(obj.menu_item, 'menu') and hasattr(obj.menu_item.menu, 'store') and hasattr(obj.menu_item.menu.store, 'owner'):
            return obj.menu_item.menu.store.owner == request.user

        return False