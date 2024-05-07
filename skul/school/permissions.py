from rest_framework.permissions import BasePermission
from school.models import School, Teacher

class IsSchoolAdmin(BasePermission):
    """
    Allows access only to school admins for their own school's resources.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or not user.is_school:
            return False

        # Allow school admins to perform any action on their own school's resources
        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            queryset = queryset.filter(school=user.school)
            view.queryset = queryset

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated or not user.is_school:
            return False

        # Allow school admins to perform any action on their own school's resources
        return obj.school == user.school

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