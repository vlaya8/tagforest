# Generated by Django 3.0.6 on 2020-06-14 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0034_auto_20200614_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='saved_groups',
            field=models.ManyToManyField(blank=True, to='tags.TreeUserGroup'),
        ),
    ]