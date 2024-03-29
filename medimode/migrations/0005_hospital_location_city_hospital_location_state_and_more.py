# Generated by Django 4.1.1 on 2022-11-26 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medimode', '0004_document_doc_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='location_city',
            field=models.TextField(default='New Delhi', max_length=200),
        ),
        migrations.AddField(
            model_name='hospital',
            name='location_state',
            field=models.TextField(default='Delhi', max_length=200),
        ),
        migrations.AddField(
            model_name='insurance',
            name='location_city',
            field=models.TextField(default='New Delhi', max_length=200),
        ),
        migrations.AddField(
            model_name='insurance',
            name='location_state',
            field=models.TextField(default='Delhi', max_length=200),
        ),
        migrations.AddField(
            model_name='pharmacy',
            name='location_city',
            field=models.TextField(default='New Delhi', max_length=200),
        ),
        migrations.AddField(
            model_name='pharmacy',
            name='location_state',
            field=models.TextField(default='Delhi', max_length=200),
        ),
    ]
