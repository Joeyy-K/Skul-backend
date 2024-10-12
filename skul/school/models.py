from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import cloudinary
import cloudinary.uploader
import io

class Channel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=[('class', 'Class'), ('school', 'School'), ('teacher', 'Teacher')])
    is_visible_to_students = models.BooleanField(default=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='channels')
    users = models.ManyToManyField('User', related_name='channels')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class User(AbstractUser):
    is_school = models.BooleanField('is_school', default=False)
    is_teacher = models.BooleanField('is_teacher', default=False)
    is_student = models.BooleanField('is_student', default=False)
    avatar = CloudinaryField('avatar', null=True, blank=True)
 
    def generate_avatar(self):
        img = Image.new('RGB', (128, 128), color=self.get_background_color())
        d = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 64)
        except IOError:
            font = ImageFont.load_default()
        
        initials = self.get_avatar_text()
        
        bbox = font.getbbox(initials)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        position = ((128-text_width)/2, (128-text_height)/2 - bbox[1])
        
        d.text(position, initials, fill=(255, 255, 255), font=font)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(buffer, folder="avatars")
        
        # Save the Cloudinary public_id to the avatar field
        self.avatar = result['public_id']

class School(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,  null=True)
    full_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    @property
    def student_count(self):
        return self.student_set.count()

    @property
    def teacher_count(self):
        return self.teacher_set.count()

    def create_channel(self, name):
        channel = Channel.objects.create(name=name, school=self)
        self.user_set.update(channel=channel)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade = models.OneToOneField('Grade', on_delete=models.SET_NULL, null=True, blank=True, related_name='grade_teacher')

    @property
    def school_name(self):
        return self.school.full_name
    
    @property
    def grade_name(self):
        return self.grade.name

class Grade(models.Model):
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='grades')
    teacher = models.OneToOneField(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_grade')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.teacher:
            self.teacher.grade = self
            self.teacher.save()
        else:
            #to note: If no teacher is assigned, ensure any previously assigned teacher is updated
            Teacher.objects.filter(grade=self).update(grade=None)

    @property
    def school_name(self):
        return self.school.full_name
    
    @property
    def teacher_name(self):
        return self.teacher.first_name + " " + self.teacher.last_name

    @property
    def student_count(self):
        return self.student_set.count()

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    grade = models.ForeignKey('Grade', on_delete=models.CASCADE)
    file = CloudinaryField('file', 
                           resource_type='auto', 
                           null=True, 
                           blank=True)
    image = CloudinaryField('image', 
                            null=True, 
                            blank=True)

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    file = CloudinaryField('file', resource_type='auto')

    @property
    def student_name(self):
        return self.student.full_name

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='channel_messages', null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Schedules(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    publish_date = models.DateTimeField(auto_now_add=True)
    file = CloudinaryField('file', 
                           resource_type='auto', 
                           null=True, 
                           blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='schedules') 
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
