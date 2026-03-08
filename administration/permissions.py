from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users (is_staff=True).
    All administration/ endpoints are protected by this.
    """
    message = "Access denied. Admin privileges required."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )


class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to superusers (is_superuser=True).
    Used for sensitive actions like creating/deleting admin accounts.
    """
    message = "Access denied. Superuser privileges required."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )