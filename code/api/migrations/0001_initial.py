# Generated by Django 3.2.8 on 2021-11-23 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host', models.CharField(max_length=200)),
                ('api_prefix', models.CharField(blank=True, default='/api', max_length=200)),
                ('username', models.CharField(max_length=200)),
                ('password', models.CharField(max_length=200)),
                ('remote_credentials', models.BooleanField(default=False)),
            ],
        ),
    ]
