# Generated by Django 5.0.3 on 2024-06-07 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskcontrol', '0006_engagementdetail_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engagementdetail',
            name='status',
            field=models.CharField(default='OPEN_JOB', max_length=20),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(default='OPEN_JOB', max_length=20),
        ),
    ]