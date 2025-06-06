# Generated by Django 5.0.6 on 2024-06-15 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0026_alter_reservation_reserved_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='parkinglot',
            old_name='price_per_hour',
            new_name='price_per_hour_after_two_hours',
        ),
        migrations.RemoveField(
            model_name='parkinglot',
            name='description',
        ),
        migrations.RemoveField(
            model_name='parkinglot',
            name='has_cctv',
        ),
        migrations.RemoveField(
            model_name='parkinglot',
            name='has_fire_alarm',
        ),
        migrations.RemoveField(
            model_name='parkinglot',
            name='has_security_guard',
        ),
        migrations.RemoveField(
            model_name='parkinglot',
            name='is_open_on_weekends',
        ),
        migrations.AddField(
            model_name='parkinglot',
            name='price_for_first_two_hours',
            field=models.IntegerField(default=0),
        ),
    ]
