# Generated by Django 3.1.1 on 2020-10-12 00:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceConfig',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('command', models.CharField(max_length=64)),
                ('command_arguments', models.JSONField(max_length=1024)),
                ('location', models.CharField(max_length=64)),
                ('type', models.CharField(max_length=32)),
                ('hosts', models.CharField(default='', max_length=4096)),
                ('excluded_hosts', models.CharField(default='', max_length=4096)),
                ('config', models.JSONField(max_length=4096)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceStatus',
            fields=[
                ('name', models.CharField(max_length=8, primary_key=True, serialize=False, unique=True)),
                ('alias', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceToRun',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=64)),
                ('host_name', models.CharField(db_index=True, max_length=64)),
                ('command', models.CharField(max_length=64)),
                ('command_arguments', models.JSONField(max_length=1024)),
                ('output', models.CharField(max_length=2048)),
                ('attempts', models.SmallIntegerField(default=0)),
                ('hard_status', models.BooleanField(db_index=True, default=False)),
                ('executed_at', models.DateTimeField(auto_now=True)),
                ('current_status', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='services.servicestatus')),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('host_name', 'name')},
            },
        ),
    ]
