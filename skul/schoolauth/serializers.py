from rest_framework import serializers
from school.models import User, School, Teacher, Student, Assignment, AssignmentSubmission, Grade, Channel, Message, Feedback, Attendance, Event, Announcement

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'date_joined', 'last_login', 'is_school', 'is_teacher', 'is_student', 'channel'] 
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class SchoolSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = School
        fields = [ 'id', 'user', 'full_name', 'location']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        School.objects.create(user=user, **validated_data)
        return user

class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'first_name', 'last_name', 'school', 'grade']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        Teacher.objects.create(user=user, **validated_data)
        return user

    def create_student(self, student_data):
        user_data = student_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        student = Student.objects.create(user=user, **student_data)
        return student

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = ['id', 'user', 'first_name', 'last_name', 'school', 'grade']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        Student.objects.create(user=user, **validated_data)
        return user
    
class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'teacher', 'file', 'grade' ]

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submission_date', 'file']

class GradeSerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True)
    teacher = TeacherSerializer()

    class Meta:
        model = Grade
        fields = ['id', 'name', 'school', 'teacher', 'students']

    def update(self, instance, validated_data):
        students_data = validated_data.pop('students')
        instance = super().update(instance, validated_data)

        for student_data in students_data:
            student, created = Student.objects.get_or_create(**student_data)
            instance.students.add(student)

        return instance

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'publish_date', 'school', 'attachment']

class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'type', 'is_visible_to_students', 'school']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'channel', 'content', 'timestamp']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['content', 'sender', 'receiver', 'visible_to_students']

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'date', 'status', 'notes']       

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'event_type', 'related_entities', 'related_teachers']