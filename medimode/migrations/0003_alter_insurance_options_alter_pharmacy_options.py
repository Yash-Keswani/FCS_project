# Generated by Django 4.1.1 on 2022-10-26 13:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('medimode', '0002_document_hospital_insurance_pharmacy_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='insurance',
            options={'verbose_name_plural': 'Insurance Firms'},
        ),
        migrations.AlterModelOptions(
            name='pharmacy',
            options={'verbose_name_plural': 'Pharmacies'},
        ),
    ]
