# Generated by Django 3.2.8 on 2021-11-22 06:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('PL', 'text/plain'), ('MD', 'text/markdown')], max_length=2)),
                ('comment', models.CharField(max_length=200)),
                ('pub_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='LocalPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('public_id', models.URLField()),
                ('description', models.CharField(max_length=50)),
                ('content_type', models.CharField(choices=[('MD', 'text/markdown'), ('PL', 'text/plain'), ('B64', 'application/base64'), ('PNG', 'image/png;base64'), ('JPEG', 'image/jpeg;base64')], default='PL', max_length=4)),
                ('content', models.BinaryField(blank=True, max_length=4096, null=True)),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('visibility', models.CharField(choices=[('PB', 'PUBLIC'), ('FR', 'FRIEND'), ('PR', 'PRIVATE')], default='PB', max_length=10)),
                ('unlisted', models.BooleanField(default=False)),
                ('categories', models.ManyToManyField(blank=True, to='socialDistribution.Category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LocalAuthor',
            fields=[
                ('author_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='socialDistribution.author')),
                ('username', models.CharField(max_length=50, unique=True)),
                ('displayName', models.CharField(max_length=50)),
                ('githubUrl', models.CharField(max_length=50, null=True)),
                ('profileImageUrl', models.CharField(max_length=50, null=True)),
            ],
            bases=('socialDistribution.author',),
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialDistribution.author')),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='socialDistribution.localpost')),
            ],
        ),
        migrations.CreateModel(
            name='InboxPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('public_id', models.URLField()),
                ('description', models.CharField(max_length=50)),
                ('content_type', models.CharField(choices=[('MD', 'text/markdown'), ('PL', 'text/plain'), ('B64', 'application/base64'), ('PNG', 'image/png;base64'), ('JPEG', 'image/jpeg;base64')], default='PL', max_length=4)),
                ('content', models.BinaryField(blank=True, max_length=4096, null=True)),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('visibility', models.CharField(choices=[('PB', 'PUBLIC'), ('FR', 'FRIEND'), ('PR', 'PRIVATE')], default='PB', max_length=10)),
                ('unlisted', models.BooleanField(default=False)),
                ('source', models.URLField(max_length=2048)),
                ('origin', models.URLField(max_length=2048)),
                ('author', models.URLField(max_length=2048)),
                ('_author_json', jsonfield.fields.JSONField()),
                ('categories', models.ManyToManyField(blank=True, to='socialDistribution.Category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following', to='socialDistribution.author')),
            ],
        ),
        migrations.CreateModel(
            name='CommentLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialDistribution.author')),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='socialDistribution.comment')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialDistribution.localpost'),
        ),
        migrations.AddConstraint(
            model_name='postlike',
            constraint=models.UniqueConstraint(fields=('author', 'object'), name='unique_post_like'),
        ),
        migrations.AddField(
            model_name='localpost',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='socialDistribution.localauthor'),
        ),
        migrations.AddField(
            model_name='localauthor',
            name='follow_requests',
            field=models.ManyToManyField(related_name='sent_follow_requests', to='socialDistribution.Author'),
        ),
        migrations.AddField(
            model_name='localauthor',
            name='inbox_posts',
            field=models.ManyToManyField(to='socialDistribution.InboxPost'),
        ),
        migrations.AddField(
            model_name='localauthor',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='follow',
            name='object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follows', to='socialDistribution.localauthor'),
        ),
        migrations.AddConstraint(
            model_name='commentlike',
            constraint=models.UniqueConstraint(fields=('author', 'object'), name='unique_comment_like'),
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialDistribution.localauthor'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('actor', 'object'), name='unique_follow'),
        ),
    ]
