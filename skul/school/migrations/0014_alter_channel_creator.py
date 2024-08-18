# Generated by Django 5.0.3 on 2024-08-16 15:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0013_channel_creator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
