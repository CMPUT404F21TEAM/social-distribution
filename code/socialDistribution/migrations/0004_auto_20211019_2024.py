# Generated by Django 3.2.8 on 2021-10-20 02:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('socialDistribution', '0003_auto_20211011_1456'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='followers',
            field=models.ManyToManyField(blank=True, to='socialDistribution.Author'),
        ),
        migrations.AddField(
            model_name='post',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_post', to='socialDistribution.Author'),
        ),
        migrations.CreateModel(
            name='Inbox',
            fields=[
                ('author', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='socialDistribution.author')),
                ('follow_requests', models.ManyToManyField(blank=True, related_name='follow_requests', to='socialDistribution.Author')),
                ('posts', models.ManyToManyField(blank=True, related_name='pushed_posts', to='socialDistribution.Post')),
            ],
        ),
    ]
