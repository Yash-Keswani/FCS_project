# Generated by Django 4.1.1 on 2022-11-26 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medimode', '0005_hospital_location_city_hospital_location_state_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='stripe_acct',
            field=models.TextField(blank=True, max_length=100),
        ),
    ]
