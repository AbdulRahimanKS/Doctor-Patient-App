# Generated by Django 5.1.3 on 2024-12-05 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0020_alter_appointmentrequest_slot'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientinfo',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='', max_length=10),
            preserve_default=False,
        ),
    ]