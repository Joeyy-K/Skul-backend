from rest_framework import generics
from school.models import School, Teacher, Student
from schoolauth.serializers import SchoolSerializer, TeacherSerializer, StudentSerializer

class SchoolList(generics.ListCreateAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class SchoolDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class TeacherList(generics.ListCreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

class TeacherDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer

class StudentList(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

class StudentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
