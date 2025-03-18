# Generated by Django 5.0.6 on 2024-06-16 20:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0027_rename_price_per_hour_parkinglot_price_per_hour_after_two_hours_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParkingSpot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spot_number', models.CharField(max_length=10)),
                ('is_reserved', models.BooleanField(default=False)),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spots', to='projectApp.parkinglot')),
            ],
        ),
        migrations.AddField(
            model_name='reservation',
            name='spot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='projectApp.parkingspot'),
        ),
    ]
