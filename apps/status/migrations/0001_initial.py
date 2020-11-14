# Generated by Django 3.1.1 on 2020-10-13 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hosts', '0001_initial'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceStatusHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('host_name', models.CharField(max_length=64)),
                ('output', models.CharField(max_length=1024)),
                ('ret_code', models.SmallIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='services.servicestatus')),
            ],
            options={
                'ordering': ['host_name', 'name', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HostStatusHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_name', models.CharField(max_length=64)),
                ('output', models.CharField(max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='hosts.hoststatus')),
            ],
            options={
                'ordering': ['host_name', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='servicestatushistory',
            index=models.Index(fields=['host_name', 'name', '-created_at'], name='status_serv_host_na_2ad349_idx'),
        ),
        migrations.AddIndex(
            model_name='hoststatushistory',
            index=models.Index(fields=['host_name', '-created_at'], name='status_host_host_na_2f4e8c_idx'),
        ),
    ]
