from rest_framework import permissions


class IsSpaceOwnerOrReadOnly(permissions.BasePermission):
    """Anyone can read; only staff or designated space-owner accounts can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_space_owner))
