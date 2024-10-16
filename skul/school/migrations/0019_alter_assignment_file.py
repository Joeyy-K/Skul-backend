# Generated by Django 5.0.3 on 2024-09-22 18:51

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0018_schedules_publish_date_alter_schedules_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='assignements/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'])]),
        ),
    ]
