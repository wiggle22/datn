# Generated by Django 5.0.6 on 2024-05-29 04:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0013_alter_parkingrecord_rfid_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment_VNPay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('vnp_transaction_no', models.CharField(max_length=8)),
                ('vnp_response_code', models.CharField(max_length=2)),
                ('reservation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='projectApp.reservation')),
            ],
        ),
    ]
