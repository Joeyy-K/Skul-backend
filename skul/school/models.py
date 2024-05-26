from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

class Channel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=[('class', 'Class'), ('school', 'School'), ('teacher', 'Teacher')])
    is_visible_to_students = models.BooleanField(default=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='channels')
    users = models.ManyToManyField('User', related_name='channels')

class User(AbstractUser):
    is_school = models.BooleanField('is_school', default=False)
    is_teacher = models.BooleanField('is_teacher', default=False)
    is_student = models.BooleanField('is_student', default=False)

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

class Grade(models.Model):
    name = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='grades')
    teacher = models.OneToOneField(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_grade')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.teacher:
            self.teacher.grade = self
            self.teacher.save()

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
    GRADE_CHOICES = [
        ('1', 'First Grade'),
        ('2', 'Second Grade'),
        ('3', 'Third Grade'),
        ('4', 'Fourth Grade'),
        ('5', 'Fifth Grade'),
        ('6', 'Sixth Grade'),
        ('7', 'Seventh Grade'),
        ('8', 'Eighth Grade'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, null=True)
    file = models.FileField(upload_to='assignments/', null=True, blank=True,
                            validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt'])])
    image = models.ImageField(upload_to='assignments/images/', null=True, blank=True)


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='assignments/')

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

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    event_type = models.CharField(max_length=50, choices=[('assignment', 'Assignment'), ('exam', 'Exam'), ('activity', 'Activity'), ('other', 'Other')])
    related_entities = models.ManyToManyField(Student, related_name='events', blank=True)
    related_teachers = models.ManyToManyField(Teacher, related_name='events', blank=True)

class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    publish_date = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='announcements') 
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')

