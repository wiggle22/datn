# Generated by Django 5.0.6 on 2024-06-29 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0030_reservation_is_cancelled'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingspot',
            name='is_avaiable',
            field=models.BooleanField(default=False),
        ),
    ]
