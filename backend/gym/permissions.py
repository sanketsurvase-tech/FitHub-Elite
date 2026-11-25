from rest_framework.permissions import BasePermission, SAFE_METHODS


class RolePermission(BasePermission):
    def has_permission(self, request, view):
        role = getattr(request.user, "role", None)
        action_roles = getattr(view, "action_write_roles", {}).get(getattr(view, "action", None))
        if action_roles is not None:
            return role in action_roles
        if request.method in SAFE_METHODS:
            return role in getattr(view, "read_roles", {"admin"})
        return role in getattr(view, "write_roles", {"admin"})
