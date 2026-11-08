"""Object permissions for blog resources."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    message = "Only the author can modify this resource."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            obj.author_id == request.user.pk or request.user.is_staff
        )


class IsStaffOrReadOnly(BasePermission):
    message = "Only staff members can change categories and tags."

    def has_permission(self, request, view) -> bool:
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and request.user.is_staff
        )
