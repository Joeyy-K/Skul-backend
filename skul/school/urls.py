from django.urls import path
from . import views

urlpatterns = [
    path('schools/', views.SchoolList.as_view()),
    path('schools/<int:pk>/', views.SchoolDetail.as_view()),
    path('teachers/', views.TeacherList.as_view()),
    path('teachers/<int:pk>/', views.TeacherDetail.as_view()),
    path('students/', views.StudentList.as_view()),
    path('students/<int:pk>/', views.StudentDetail.as_view()),
]
