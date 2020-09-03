# Generated by Django 3.0.6 on 2020-09-03 22:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0052_auto_20200725_2358'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='name')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('added_date', models.DateTimeField(verbose_name='date added')),
                ('description', models.TextField(null=True, verbose_name='description')),
                ('state', models.IntegerField(default=0, verbose_name='state')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.TaskGroup')),
            ],
        ),
    ]
