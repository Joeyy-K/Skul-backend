from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_school = models.BooleanField('is_school', default=False)
    is_teacher = models.BooleanField('is_teacher', default=False)
    is_student = models.BooleanField('is_student', default=False)

class School(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,  null=True)
    full_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

