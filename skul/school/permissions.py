from rest_framework.permissions import BasePermission
from school.models import School, Teacher

class IsSchoolAdmin(BasePermission):
    """
    school admins for their own school's resources.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or not user.is_school:
            return False

        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            queryset = queryset.filter(school=user.school)
            view.queryset = queryset

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated or not user.is_school:
            return False

        return obj.school == user.school

class IsEventCreator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_teacher or user.is_school)

class IsTeacherOrSchool(BasePermission):
    """
    allow teachers or schools to create announcements.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_teacher or request.user.is_school:
            return True

        return False