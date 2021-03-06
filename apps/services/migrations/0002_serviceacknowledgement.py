# Generated by Django 3.1.1 on 2020-10-25 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceAcknowledgement',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('host_name', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'unique_together': {('host_name', 'name')},
            },
        ),
    ]
