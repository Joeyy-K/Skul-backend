from rest_framework import serializers
from school.models import User, School, Teacher, Student

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [ 'id', 'username', 'email', 'password', 'date_joined', 'last_login', 'is_school', 'is_teacher', 'is_student']
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
        fields = [ 'id', 'user', 'first_name', 'last_name', 'school']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        Teacher.objects.create(user=user, **validated_data)
        return user

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = [ 'id', 'user', 'first_name', 'last_name', 'school']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User(**user_data)
        user.set_password(user_data['password'])
        user.save()
        Student.objects.create(user=user, **validated_data)
        return user
