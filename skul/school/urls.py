from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'teachers', views.TeacherViewSet)
router.register(r'feedbacks', views.FeedbackViewSet)

urlpatterns = [
    path('schools/', views.SchoolList.as_view()),
    path('schools/<int:pk>/', views.SchoolDetail.as_view()),
    path('students/', views.StudentList.as_view()),
    path('students/<int:pk>/', views.StudentDetail.as_view()),
    path('assignments/', views.AssignmentList.as_view()),
    path('assignments/<int:pk>/', views.AssignmentDetail.as_view()),
    path('assignment-submissions/', views.AssignmentSubmissionList.as_view()),
    path('assignment-submissions/<int:pk>/', views.AssignmentSubmissionDetail.as_view()),
    path('grades/', views.GradeList.as_view()),
    path('grades/<int:pk>/', views.GradeDetail.as_view()),
    path('channels/create/', views.ChannelCreate.as_view(), name='channel-create'),
    path('messages/', views.MessageList.as_view(), name='message-list'), 
    path('attendance/', views.AttendanceList.as_view(), name='attendance-list'),
    path('attendance/<int:pk>/', views.AttendanceDetail.as_view(), name='attendance-detail'),
    path('students/<int:student_id>/attendance/', views.AttendanceByStudent.as_view(), name='attendance-by-student'),
    path('events/', views.EventList.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetail.as_view(), name='event-detail'),
    path('events/by-entity/', views.EventsByEntity.as_view(), name='events-by-entity'),

    path('announcements/', views.AnnouncementList.as_view({'get': 'list', 'post': 'create'}), name='announcement-list'),
    path('announcements/<int:pk>/', views.AnnouncementList.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='announcement-detail'),

    path('feedbacks/<int:feedback_id>/delete/', views.delete_feedback, name='delete_feedback'),
    
    path('channels/', views.ChannelList.as_view(), name='channel-list'),
    path('channels/<int:pk>/', views.ChannelDetail.as_view(), name='channel-detail'),
    path('', include(router.urls)),
]

