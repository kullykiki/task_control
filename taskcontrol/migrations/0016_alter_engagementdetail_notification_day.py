# Generated by Django 5.0.3 on 2024-06-28 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskcontrol', '0015_engagementdetail_notification_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engagementdetail',
            name='notification_day',
            field=models.DateField(blank=True, null=True),
        ),
    ]
