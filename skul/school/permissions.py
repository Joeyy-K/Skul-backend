from rest_framework.permissions import BasePermission
from school.models import School, Teacher

class IsEventCreator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_teacher or user.is_school)

class IsTeacherOrSchool(BasePermission):
    """
    Custom permission to only allow teachers or schools to create announcements.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if the user is a teacher or a school
        if request.user.is_teacher or request.user.is_school:
            return True

        # If none of the above conditions are met, deny permission
        return False