# Generated by Django 5.0.3 on 2024-05-16 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskcontrol', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registertax',
            name='company',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='registertax',
            name='dbd_e_filling',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='registertax',
            name='sbt',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='registertax',
            name='sso',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='registertax',
            name='vat',
            field=models.BooleanField(default=False),
        ),
    ]
