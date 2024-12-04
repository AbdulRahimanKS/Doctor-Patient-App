# Generated by Django 5.1.3 on 2024-12-04 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0005_prescription_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved')], default='Pending', max_length=20),
        ),
    ]
