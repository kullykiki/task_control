# Generated by Django 5.0.3 on 2024-06-18 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskcontrol', '0008_remove_task_engagement_task_engagement_detail'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='number',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
