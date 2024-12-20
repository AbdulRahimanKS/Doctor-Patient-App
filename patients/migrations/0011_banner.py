# Generated by Django 5.1.3 on 2024-11-22 09:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0010_alter_appointmentslot_zoom_meeting_start_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(upload_to='banners/')),
                ('banner_type', models.CharField(choices=[('doctor_profile', 'Doctor Profile'), ('doctor_list', 'All Doctors'), ('custom_url', 'Custom URL')], default='custom_url', max_length=50)),
                ('custom_url', models.URLField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='banners', to='patients.doctorprofile')),
            ],
        ),
    ]
