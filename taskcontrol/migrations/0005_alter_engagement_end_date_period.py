# Generated by Django 5.0.3 on 2024-05-27 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskcontrol', '0004_alter_engagement_end_date_period_infinity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engagement',
            name='end_date_period',
            field=models.DateField(blank=True, null=True),
        ),
    ]
