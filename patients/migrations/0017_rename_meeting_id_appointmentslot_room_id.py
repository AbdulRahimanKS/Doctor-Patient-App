# Generated by Django 5.1.3 on 2024-11-25 04:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0016_alter_appointmentslot_meeting_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointmentslot',
            old_name='meeting_id',
            new_name='room_id',
        ),
    ]
