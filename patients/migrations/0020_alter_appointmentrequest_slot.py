# Generated by Django 5.1.3 on 2024-12-03 18:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0019_alter_doctorprofile_specialization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointmentrequest',
            name='slot',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slots', to='patients.appointmentslot'),
        ),
    ]
