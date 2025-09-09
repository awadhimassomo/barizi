from rest_framework.permissions import BasePermission

class IsOperator(BasePermission):
    """
    Allows access only to users with the role of 'operator'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'operator'

class IsPlanner(BasePermission):
    """
    Allows access only to users with the role of 'planner'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'planner'
    
class IsVendor(BasePermission): 
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'vendor'

class IsCustomer(BasePermission):  
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'
