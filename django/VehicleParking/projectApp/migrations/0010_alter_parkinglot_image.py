# Generated by Django 5.0.6 on 2024-05-27 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0009_alter_parkinglot_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parkinglot',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='parking_lot_images/'),
        ),
    ]
