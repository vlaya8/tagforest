# Generated by Django 3.0.6 on 2020-06-13 17:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0023_auto_20200613_1857'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='treeusergroup',
            name='members',
        ),
        migrations.AddField(
            model_name='member',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.TreeUserGroup'),
        ),
    ]