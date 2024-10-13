from rest_framework import serializers
from school.models import User, School, Teacher, Student, Assignment, AssignmentSubmission, Grade, Channel, Message, Schedules
from django.conf import settings
from cloudinary.utils import cloudinary_url

class UserProfileSerializer(serializers.ModelSerializer):
    school_info = serializers.SerializerMethodField()
    teacher_info = serializers.SerializerMethodField()
    student_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_school', 'is_teacher', 'is_student', 'school_info', 'teacher_info', 'student_info']
        extra_kwargs = {'username': {'required': False}}

    def get_school_info(self, obj):
        if obj.is_school:
            school = School.objects.get(user=obj)
            return {
                'full_name': school.full_name,
                'location': school.location
            }
        return None

    def get_teacher_info(self, obj):
        if obj.is_teacher:
            teacher = Teacher.objects.get(user=obj)
            return {
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'school': teacher.school.full_name if teacher.school else None,
                'grade': teacher.grade.name if teacher.grade else None
            }
        return None

    def get_student_info(self, obj):
        if obj.is_student:
            student = Student.objects.get(user=obj)
            return {
                'first_name': student.first_name,
                'last_name': student.last_name,
                'school': student.school.full_name if student.school else None,
                'grade': student.grade.name if student.grade else None
            }
        return None

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ['username', 'email', 'first_name', 'last_name']:
                setattr(instance, attr, value)
        instance.save()

        if instance.is_school:
            school = School.objects.get(user=instance)
            school_data = validated_data.get('school_info', {})
            for attr, value in school_data.items():
                setattr(school, attr, value)
            school.save()
        elif instance.is_teacher:
            teacher = Teacher.objects.get(user=instance)
            teacher_data = validated_data.get('teacher_info', {})
            for attr, value in teacher_data.items():
                setattr(teacher, attr, value)
            teacher.save()
        elif instance.is_student:
            student = Student.objects.get(user=instance)
            student_data = validated_data.get('student_info', {})
            for attr, value in student_data.items():
                setattr(student, attr, value)
            student.save()

        return instance
    
class ChannelSerializer(serializers.ModelSerializer):
    creator = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'type', 'is_visible_to_students', 'school', 'creator']

from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    channels = ChannelSerializer(many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_school', 'is_teacher', 'is_student', 'channels', 'avatar_url']
        extra_kwargs = {'password': {'write_only': True}}

    def get_avatar_url(self, obj):
        if obj.avatar:
            return cloudinary_url(obj.avatar.public_id)[0]
        return None

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class SchoolSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = School
        fields = ['id', 'user', 'full_name', 'location']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        school = School.objects.create(user=user, **validated_data)
        return school

class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'first_name', 'last_name', 'school', 'grade', 'user', 'school_name', 'grade_name']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

    def create_student(self, student_data):
        user_data = student_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        student = Student.objects.create(user=user, **student_data)
        return student
    
class TeacherRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=255, required=True)
    last_name = serializers.CharField(max_length=255, required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    school = serializers.IntegerField(required=True)
    role = serializers.CharField(required=True)

    def create(self, validated_data):
        user_data = {
            'username': validated_data.get('username'),
            'password': validated_data.get('password'),
            'email': validated_data.get('email'),
            'is_teacher': validated_data.get('role') == 'teacher',
        }
        user = User.objects.create_user(**user_data)

        school_id = validated_data.get('school')
        school = School.objects.get(id=school_id)

        teacher = Teacher.objects.create(
            user=user,
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            school=school,
        )

        return teacher

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    school_name = serializers.SerializerMethodField()
    grade_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'user', 'first_name', 'last_name', 'school', 'grade', 'school_name', 'grade_name']

    def get_school_name(self, obj):
        return obj.school.full_name if obj.school else None

    def get_grade_name(self, obj):
        return obj.grade.name if obj.grade else None
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student
    
class StudentRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=255, required=True)
    last_name = serializers.CharField(max_length=255, required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    school = serializers.IntegerField(required=True)
    grade = serializers.IntegerField(required=False, allow_null=True)
    role = serializers.CharField(required=True)

    def create(self, validated_data):
        user_data = {
            'username': validated_data.get('username'),
            'password': validated_data.get('password'),
            'email': validated_data.get('email'),
            'is_student': validated_data.get('role') == 'student',
        }
        user = User.objects.create_user(**user_data)

        school_id = validated_data.get('school')
        grade_id = validated_data.get('grade')

        school = School.objects.get(id=school_id)
        grade = None if grade_id is None else Grade.objects.get(id=grade_id)

        student = Student.objects.create(
            user=user,
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            school=school,
            grade=grade
        )

        return student
    
class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'teacher', 'grade', 'file']

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submission_date', 'file', 'student_name']

class StudentSubmissionStatusSerializer(serializers.ModelSerializer):
    has_submitted = serializers.BooleanField()
    submission_date = serializers.DateTimeField()

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'has_submitted', 'submission_date']

class AssignmentSubmissionStatusSerializer(serializers.ModelSerializer):
    students = StudentSubmissionStatusSerializer(many=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'students']

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'name', 'school', 'teacher', 'school_name', 'teacher_name']

    def create(self, validated_data):
        school_data = validated_data.pop('school', None)
        if school_data:
            school = School.objects.get(id=school_data.id)
            grade = Grade.objects.create(
                name=validated_data.get('name'),
                school=school
            )
        else:
            grade = Grade.objects.create(**validated_data)

        return grade

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'channel', 'content', 'timestamp']    

class SchedulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedules
        fields = ['id', 'title', 'description', 'file', 'school', 'creator', 'publish_date' ]