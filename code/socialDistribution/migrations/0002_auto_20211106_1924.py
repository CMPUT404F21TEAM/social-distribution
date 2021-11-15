# Generated by Django 3.2.8 on 2021-11-07 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socialDistribution', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='localauthor',
            name='username',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AddConstraint(
            model_name='commentlike',
            constraint=models.UniqueConstraint(fields=('author', 'object'), name='unique_comment_like'),
        ),
        migrations.AddConstraint(
            model_name='postlike',
            constraint=models.UniqueConstraint(fields=('author', 'object'), name='unique_post_like'),
        ),
    ]