# Generated by Django 5.0.6 on 2024-06-05 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectApp', '0019_remove_parkinglot_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkinglot',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='parkinglot',
            name='longitude',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='parkinglot',
            name='price_per_hour',
            field=models.IntegerField(),
        ),
    ]
