from django.http import JsonResponse
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .permissions import IsEventCreator, IsTeacherOrSchool
from school.models import School, Teacher, Student, Assignment, AssignmentSubmission, Grade, Channel, Message, Feedback, Attendance, Event, Announcement
from schoolauth.serializers import SchoolSerializer, TeacherSerializer, StudentSerializer, AssignmentSerializer,AssignmentSubmissionSerializer, GradeSerializer, ChannelSerializer, MessageSerializer, FeedbackSerializer, AttendanceSerializer, EventSerializer, AnnouncementSerializer
import logging

logger = logging.getLogger(__name__)

class SchoolList(generics.ListCreateAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class SchoolDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class TeacherList(generics.ListCreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

User = get_user_model()

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

    @action(detail=True, methods=['post'])
    def transfer_student(self, request, pk=None):
        teacher = self.get_object()
        student_id = request.data.get('student_id')
        new_school_id = request.data.get('new_school_id')
        new_grade_id = request.data.get('new_grade_id')

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise ObjectDoesNotExist("The requested student was not found.")

        try:
            new_school = School.objects.get(id=new_school_id)
            new_grade = Grade.objects.get(id=new_grade_id)
        except (School.DoesNotExist, Grade.DoesNotExist):
            raise ObjectDoesNotExist("The requested school or grade was not found.")

        if student.school == new_school:
            raise ValidationError("Student is already enrolled in the specified school.")

        if student.school not in teacher.school.school_set.all():
            raise PermissionDenied("You do not have permission to transfer students from this school.")

        student.school = new_school
        student.grade = new_grade
        student.save()

        if new_school.channel:
            student.user.channel = new_school.channel
            student.user.save()

        serializer = StudentSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StudentList(generics.ListCreateAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        queryset = Student.objects.all()
        grade_id = self.request.query_params.get('grade', None)
        if grade_id is not None:
            grade = get_object_or_404(Grade, id=grade_id)
            queryset = queryset.filter(grade=grade)
        return queryset

class StudentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

class AssignmentList(generics.ListCreateAPIView):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        """
        This view should return a list of all the assignments
        for the currently authenticated teacher.
        """
        user = self.request.user
        if user.is_authenticated:
            teacher = user.teacher
            return Assignment.objects.filter(teacher=teacher)
        else:
            return Assignment.objects.none()  


class AssignmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

class AssignmentSubmissionList(generics.ListCreateAPIView):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer

class AssignmentSubmissionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer

class GradeList(generics.ListCreateAPIView):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class GradeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class ChannelList(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

class ChannelCreate(generics.CreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

    def perform_create(self, serializer):
        channel = serializer.save()
        school = School.objects.get(id=self.request.data['school'])
        school.user_set.update(channel=channel)

class MessageList(generics.ListCreateAPIView):
    queryset = Message.objects.filter(channel__isnull=False)
    serializer_class = MessageSerializer

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_student:
                return Feedback.objects.filter(visible_to_students=True)
            elif user.is_teacher or user.is_school:
                return Feedback.objects.all()
        return Feedback.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_teacher:
            serializer.save(sender=self.request.user, visible_to_students=False)
        else:
            serializer.save(sender=self.request.user)

def delete_feedback(request, feedback_id):
    if request.method == 'DELETE':
        feedback = get_object_or_404(Feedback, id=feedback_id)
        feedback.delete()
        return JsonResponse({'message': 'Feedback deleted successfully.'})
    else:
        return JsonResponse({'error': 'Invalid method'})

class AttendanceByStudent(generics.ListAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        student_id = self.kwargs['student_id']
        return Attendance.objects.filter(student_id=student_id)
    
class EventList(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class EventDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class EventsByEntity(generics.ListAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        entity_type = self.request.query_params.get('entity_type', None)
        entity_id = self.request.query_params.get('entity_id', None)

        if entity_type == 'student':
            return Event.objects.filter(related_entities__id=entity_id)
        elif entity_type == 'teacher':
            return Event.objects.filter(related_teachers__id=entity_id)
        else:
            return Event.objects.none()

class AnnouncementDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

class ChannelList(generics.ListCreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

class ChannelDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer   

class EventList(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsEventCreator()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class AnnouncementList(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_student:
                return Announcement.objects.all()
            elif user.is_teacher or user.is_school:
                return Announcement.objects.all()
        return Announcement.objects.none()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class AttendanceList(generics.ListCreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            return Attendance.objects.filter(student__school=user.teacher.school)
        elif user.is_student:
            return Attendance.objects.filter(student=user.student)
        return Attendance.objects.none()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher)

class AttendanceDetail(generics.RetrieveAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_object(self):
        attendance = super().get_object()
        user = self.request.user
        if user.is_student and attendance.student == user.student:
            return attendance
        elif user.is_teacher and attendance.student.school == user.teacher.school:
            return attendance
        raise PermissionDenied("You don't have permission to access this attendance record.")