from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import random
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
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
 
    def generate_avatar(self):
        # Generate a 128x128 image
        img = Image.new('RGB', (128, 128), color=self.get_background_color())
        d = ImageDraw.Draw(img)
        
        # Use a default font if the specified font is not available
        try:
            font = ImageFont.truetype("arial.ttf", 64)
        except IOError:
            font = ImageFont.load_default()
        
        initials = self.get_avatar_text()
        
        # Get the bounding box of the text
        bbox = font.getbbox(initials)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position to center the text
        position = ((128-text_width)/2, (128-text_height)/2 - bbox[1])  # Adjust for font baseline
        
        # Draw the text
        d.text(position, initials, fill=(255, 255, 255), font=font)
        
        # Save the image to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        
        # Save the image to the avatar field
        self.avatar.save(f'{self.username}_avatar.png', ContentFile(buffer.getvalue()), save=False)

    def get_avatar_text(self):
        if self.is_school:
            return self.school.full_name[:2].upper() if hasattr(self, 'school') else 'SC'
        elif self.is_teacher:
            return self.teacher.first_name[0].upper() if hasattr(self, 'teacher') else 'T'
        elif self.is_student:
            return self.student.first_name[0].upper() if hasattr(self, 'student') else 'S'
        else:
            return self.username[0].upper()

    def get_background_color(self):
        # Generate a random pastel color
        return (
            random.randint(100, 200),
            random.randint(100, 200),
            random.randint(100, 200)
        )

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.generate_avatar()
        super().save(*args, **kwargs)

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
            # If no teacher is assigned, ensure any previously assigned teacher is updated
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
    file = models.FileField(
        upload_to='assignements/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'])]
    )
    image = models.ImageField(upload_to='assignments/images/', null=True, blank=True)

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='assignments/')

    @property
    def student_name(self):
        return self.student.full_name

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='channel_messages', null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_feedbacks')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedbacks')
    visible_to_students = models.BooleanField(default=True)

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[('present', 'Present'), ('absent', 'Absent'), ('tardy', 'Tardy')])
    notes = models.TextField(blank=True, null=True)

class Schedules(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    publish_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        upload_to='schedules/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'])]
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='schedules') 
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
