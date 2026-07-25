from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    """A booking may only be viewed/modified by the user who made it, or staff."""

    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user.is_staff or obj.user_id == request.user.id))
