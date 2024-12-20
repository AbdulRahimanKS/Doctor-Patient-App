# Generated by Django 5.1.3 on 2024-12-04 04:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0004_alter_prescription_doctor'),
        ('patients', '0020_alter_appointmentrequest_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='slot',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slot', to='patients.appointmentslot'),
        ),
    ]
