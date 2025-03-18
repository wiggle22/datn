# Generated by Django 5.0.6 on 2024-05-21 07:53

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0003_alter_parkinglot_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservation_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('reserved_from', models.DateTimeField()),
                ('reserved_to', models.DateTimeField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='projectApp.customer')),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='projectApp.parkinglot')),
            ],
        ),
    ]
