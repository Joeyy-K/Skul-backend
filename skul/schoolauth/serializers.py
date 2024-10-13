from rest_framework import serializers

from school.models import User, School, Teacher, Student, Assignment, AssignmentSubmission, Grade, Channel, Message, Feedback, Attendance, Event, Announcement

class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'type', 'is_visible_to_students', 'school']

class UserSerializer(serializers.ModelSerializer):
    channels = ChannelSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'is_school', 'is_teacher', 'is_student', 'channels']

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
        user.is_school = True
        user.save()
        school = School.objects.create(user=user, **validated_data)
        return school

class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'first_name', 'last_name', 'school']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        school_data = validated_data.pop('school')
        user = User.objects.create_user(**user_data)
        user.is_teacher = True
        user.save()

        if isinstance(school_data, School):
            school = school_data
        elif isinstance(school_data, int):
            school = School.objects.get(id=school_data)
        elif isinstance(school_data, dict) and 'id' in school_data:
            school = School.objects.get(id=school_data['id'])
        else:
            raise serializers.ValidationError("Invalid school data. Expected a School instance, an integer ID, or a dict with 'id'.")

        teacher = Teacher.objects.create(user=user, school=school, **validated_data)
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
        school_data = validated_data.pop('school')
        user = User.objects.create_user(**user_data)
        user.is_student = True
        user.save()

        if isinstance(school_data, School):
            school = school_data
        elif isinstance(school_data, int):
            school = School.objects.get(id=school_data)
        elif isinstance(school_data, dict) and 'id' in school_data:
            school = School.objects.get(id=school_data['id'])
        else:
            raise serializers.ValidationError("Invalid school data. Expected a School instance, an integer ID, or a dict with 'id'.")

        student = Student.objects.create(user=user, school=school, **validated_data)
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
        fields = ['id', 'title', 'description', 'due_date', 'teacher', 'file', 'grade' ]

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submission_date', 'file']

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'name', 'school', 'teacher']

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

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'publish_date', 'school', 'attachment']

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