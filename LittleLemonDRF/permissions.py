from rest_framework import permissions

class IsManagerOrAdmin(permissions.BasePermission):
    message = "You are not a manager/admin to be authorized to access to this endpoint."
    def has_permission(self, request, view):
        is_manager = request.user.groups.filter(name='Manager').exists()
        is_admin = request.user.is_superuser
        return is_manager or is_admin

class IsAdmin(permissions.BasePermission):
    message = "You need to be admin to be authorized to access to this endpoint."
    def has_permission(self, request, view):
        return request.user.is_superuser

class IsCustomer(permissions.BasePermission):
    message = "You are not a customer to be authorized to access to this endpoint."
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Customer').exists()

class IsDeliveryCrew(permissions.BasePermission):
    message = "You are not a delivery crew to be authorized to access to this endpoint."
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Delivery Crew').exists()