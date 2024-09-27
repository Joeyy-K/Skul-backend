from django.http import JsonResponse
from django.db.models import Prefetch, Q
from django.db import transaction
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .permissions import IsEventCreator, IsSchoolAdmin
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from rest_framework.views import APIView
from school.models import School, Teacher, Student, Assignment, AssignmentSubmission, Grade, Channel, Message, Feedback, Attendance, Schedules
from schoolauth.serializers import UserSerializer, SchoolSerializer, TeacherSerializer, StudentSerializer, AssignmentSerializer,AssignmentSubmissionSerializer, AssignmentSubmissionStatusSerializer, GradeSerializer, ChannelSerializer, MessageSerializer, FeedbackSerializer, AttendanceSerializer, SchedulesSerializer, StudentRegistrationSerializer, TeacherRegistrationSerializer, UserProfileSerializer

User = get_user_model()

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class DeleteChannel(APIView):
    def delete(self, request, channel_id):
        try:
            channel = Channel.objects.get(id=channel_id)

            if channel.creator.id != request.user.id:
                return Response({"error": "You don't have permission to delete this channel"}, status=status.HTTP_403_FORBIDDEN)
            
            channel.delete()
            return Response({"message": "Channel deleted successfully"}, status=status.HTTP_200_OK)
        except Channel.DoesNotExist:
            return Response({"error": "Channel not found"}, status=status.HTTP_404_NOT_FOUND)

class SchoolUsersView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        return User.objects.filter(
            Q(student__school__id=school_id) |
            Q(teacher__school__id=school_id)
        ).prefetch_related(
            Prefetch('student', queryset=Student.objects.select_related('school')),
            Prefetch('teacher', queryset=Teacher.objects.select_related('school'))
        ).distinct()
    
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned users,
        by filtering against a `category` query parameter in the URL.
        """
        queryset = User.objects.all()
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        if category is not None:
            if category == 'teachers':
                queryset = queryset.filter(is_teacher=True)
            elif category == 'students':
                queryset = queryset.filter(is_student=True)
        if search is not None:
            queryset = queryset.filter(first_name__icontains=search) | queryset.filter(last_name__icontains=search)
        return queryset

class SchoolList(generics.ListCreateAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class SchoolDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        student_count = instance.student_set.count()
        teacher_count = instance.teacher_set.count()
        data['student_count'] = student_count
        data['teacher_count'] = teacher_count

        return Response(data)

class TeacherList(generics.ListCreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied

class TeacherViewSet(generics.ListCreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.query_params.get('school_id', None)
        if school_id is not None:
            school = get_object_or_404(School, id=school_id)
            return Teacher.objects.filter(school=school).select_related('user', 'school')
        return Teacher.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

        serializer = StudentSerializer(student, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class TeacherRegistration(APIView):
    def post(self, request, format=None):
        request_data = request.data.copy()
        request_data['role'] = 'teacher'

        serializer = TeacherRegistrationSerializer(data=request_data)
        if serializer.is_valid():
            teacher = serializer.save()
            return Response(TeacherSerializer(teacher).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnassignTeacher(APIView):
    permission_classes = [IsSchoolAdmin]

    def post(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)

            grade = teacher.grade
            
            if grade:
                grade.teacher = None
                grade.save()
    
            teacher.grade = None
            teacher.save()
            
            return Response({"message": "Teacher unassigned from grade successfully"}, status=status.HTTP_200_OK)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

class DeleteTeacher(APIView):
    permission_classes = [IsSchoolAdmin]

    def delete(self, request, teacher_id):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            teacher.user.delete()
            return Response({"message": "Teacher deleted successfully"}, status=status.HTTP_200_OK)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)
    
class StudentListByGrade(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        grade_id = self.kwargs.get('grade_id')
        grade = get_object_or_404(Grade, id=grade_id)
        return Student.objects.filter(grade=grade)

class StudentList(generics.ListCreateAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get('school_id', None)
        grade_id = self.request.query_params.get('grade_id', None)

        if school_id is not None:
            school = get_object_or_404(School, id=school_id)
            queryset = Student.objects.filter(school=school)

            if grade_id is not None:
                grade = get_object_or_404(Grade, id=grade_id)
                queryset = queryset.filter(grade=grade)

            return queryset.select_related('school', 'grade')

        return Student.objects.none()

class StudentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

class StudentRegistration(APIView):
    def post(self, request, format=None):
        request_data = request.data.copy()
        request_data['role'] = 'student' 

        serializer = StudentRegistrationSerializer(data=request_data)
        if serializer.is_valid():
            student = serializer.save()
            return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnassignStudentFromGrade(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            if request.user.is_teacher or request.user.is_school:
                student.grade = None
                student.save()
                return Response({"message": "Student unassigned from grade successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "You don't have permission to unassign students"}, status=status.HTTP_403_FORBIDDEN)
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

class DeleteStudent(APIView):
    permission_classes = [IsAuthenticated, IsSchoolAdmin]

    def delete(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            student.delete()
            return Response({"message": "Student deleted successfully"}, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

class UnassignStudentFromGrade(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            if request.user.is_teacher or request.user.is_school:
                if student.grade:
                    old_grade = student.grade
                    student.grade = None
                    student.save()
                    return Response({
                        "message": f"Student '{student.full_name}' unassigned from grade '{old_grade.name}' successfully"
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "message": f"Student '{student.full_name}' is not currently assigned to any grade"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "You don't have permission to unassign students"
                }, status=status.HTTP_403_FORBIDDEN)
        except Student.DoesNotExist:
            return Response({
                "error": f"Student with id {student_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)

class GradeTeacherUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, grade_id):
        grade = get_object_or_404(Grade, id=grade_id)
        teacher_id = request.data.get('teacher_id')

        if not teacher_id:
            return Response({
                "error": "Teacher ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        teacher = get_object_or_404(Teacher, id=teacher_id)

        if grade.teacher:
            if grade.teacher == teacher:
                return Response({
                    "message": f"Teacher '{teacher.first_name} {teacher.last_name}' is already assigned to grade '{grade.name}'"
                }, status=status.HTTP_400_BAD_REQUEST)
            old_teacher = grade.teacher
            old_teacher.grade = None
            old_teacher.save()

        if teacher.grade:
            return Response({
                "error": f"Teacher '{teacher.first_name} {teacher.last_name}' is already assigned to grade '{teacher.grade.name}'"
            }, status=status.HTTP_400_BAD_REQUEST)

        grade.teacher = teacher
        grade.save()
        
        return Response({
            "message": f"Teacher '{teacher.first_name} {teacher.last_name}' successfully assigned to grade '{grade.name}'"
        }, status=status.HTTP_200_OK)

class GradeStudentUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, grade_id):
        grade = get_object_or_404(Grade, id=grade_id)
        student_id = request.data.get('student_id')

        if not student_id:
            return Response({
                "error": "Student ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(Student, id=student_id)

        if student.grade:
            if student.grade == grade:
                return Response({
                    "message": f"Student '{student.full_name}' is already assigned to grade '{grade.name}'"
                }, status=status.HTTP_400_BAD_REQUEST)
            old_grade = student.grade

        student.grade = grade
        student.save()

        return Response({
            "message": f"Student '{student.full_name}' successfully assigned to grade '{grade.name}'"
            + (f" (previously in grade '{old_grade.name}')" if 'old_grade' in locals() else "")
        }, status=status.HTTP_200_OK)


class AssignmentList(generics.ListCreateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'teacher'):
            # User is a teacher
            return Assignment.objects.filter(teacher=user.teacher)
        elif hasattr(user, 'student'):
            # User is a student
            student = user.student
            if student.grade:
                return Assignment.objects.filter(grade=student.grade)
            else:
                # If the student doesn't have a grade assigned, return an empty queryset
                return Assignment.objects.none()
        else:
            # User is neither a teacher nor a student
            return Assignment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'teacher'):
            serializer.save(teacher=user.teacher)
        else:
            raise PermissionDenied("Only teachers can create assignments.")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AssignmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

class AssignmentSubmissionList(generics.ListCreateAPIView):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer

class AssignmentSubmissionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = AssignmentSubmissionSerializer

class AssignmentSubmissionStatusView(generics.RetrieveAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSubmissionStatusSerializer

    def retrieve(self, request, *args, **kwargs):
        assignment = self.get_object()
        grade = assignment.grade
        students = Student.objects.filter(grade=grade)

        student_data = []
        for student in students:
            submission = AssignmentSubmission.objects.filter(assignment=assignment, student=student).first()
            student_data.append({
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'has_submitted': submission is not None,
                'submission_date': submission.submission_date if submission else None
            })

        serializer = self.get_serializer({
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date,
            'students': student_data
        })

        return Response(serializer.data)

class GradeList(generics.ListCreateAPIView):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get('school_id', None)
        if school_id is not None:
            school = get_object_or_404(School, id=school_id)
            return Grade.objects.filter(school=school)
        return Grade.objects.none()

    def perform_create(self, serializer):
        school_id = self.request.data.get('school')
        school = School.objects.get(id=school_id)
        serializer.save(school=school)

class GradeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

    
class RemoveStudentFromGrade(APIView):
    def post(self, request, grade_id):
        grade = get_object_or_404(Grade, id=grade_id)
        student_id = request.data.get('student_id')
        student = get_object_or_404(Student, id=student_id)
        student.grade = None
        student.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DeleteGrade(APIView):
    def delete(self, request, grade_id):
        try:
            grade = Grade.objects.get(id=grade_id)
            
            Teacher.objects.filter(grade=grade).update(grade=None)
            
            Student.objects.filter(grade=grade).update(grade=None)
            
            grade.delete()
            return Response({"message": "Grade deleted successfully"}, status=status.HTTP_200_OK)
        except Grade.DoesNotExist:
            return Response({"error": "Grade not found"}, status=status.HTTP_404_NOT_FOUND)

class ChannelList(generics.ListCreateAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return a list of all the channels for the currently authenticated user's school.
        """
        user = self.request.user
        try:
            school = user.school
            return Channel.objects.filter(school=school).select_related('school')
        except ObjectDoesNotExist:
            return Channel.objects.none()

    def perform_create(self, serializer):
        """
        Create a new channel associated with the current user's school.
        """
        try:
            serializer.save(creator=self.request.user, school=self.request.user.school)
        except ObjectDoesNotExist:
            raise ValidationError("User is not associated with any school.")

class ChannelDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

class ChannelCreate(generics.CreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer

    def perform_create(self, serializer):
        channel = serializer.save()
        school = School.objects.get(id=self.request.data['school'])
        school.user_set.update(channel=channel)

class AddUserToChannelView(APIView):
    def post(self, request, channel_id, user_id):
        try:
            channel = Channel.objects.get(id=channel_id)
            user = User.objects.get(id=user_id)

            channel.users.add(user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Channel.DoesNotExist:
            return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
class ChannelUsersView(APIView):
    def get(self, request, channel_id):
        try:
            channel = Channel.objects.get(id=channel_id)
            users = channel.users.all()
            user_data = UserSerializer(users, many=True).data
            return Response(user_data)
        except Channel.DoesNotExist:
            return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
        
class UserChannelListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        channels = Channel.objects.filter(users=user)
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data)
        
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        channel_id = self.kwargs['channel_id']
        return Message.objects.filter(channel_id=channel_id)

class MessageCreateView(APIView):
    def post(self, request, channel_id):
        channel = Channel.objects.get(id=channel_id)
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user, channel=channel)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    
class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = SchedulesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'school'):
            return Schedules.objects.filter(school=user.school)
        elif hasattr(user, 'teacher'):
            return Schedules.objects.filter(school=user.teacher.school)
        elif hasattr(user, 'student'):
            return Schedules.objects.filter(school=user.student.school)
        else:
            return Schedules.objects.none()

    def perform_create(self, serializer):
        file = self.request.data.get('file')
        if file:
            try:
                FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'])(file)
            except ValidationError as e:
                raise ValidationError({'file': e.messages})

        user = self.request.user
        if hasattr(user, 'school'):
            school = user.school
        elif hasattr(user, 'teacher'):
            school = user.teacher.school
        elif hasattr(user, 'student'):
            school = user.student.school
        else:
            raise ValidationError({'school': 'User is not associated with any school.'})

        serializer.save(creator=user, school=school)

class ScheduleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SchedulesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Schedules.objects.filter(school=self.request.user.school)

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