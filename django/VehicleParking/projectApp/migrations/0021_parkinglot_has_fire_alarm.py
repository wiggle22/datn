# Generated by Django 5.0.6 on 2024-06-11 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0020_parkinglot_latitude_parkinglot_longitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkinglot',
            name='has_fire_alarm',
            field=models.BooleanField(default=False),
        ),
    ]
