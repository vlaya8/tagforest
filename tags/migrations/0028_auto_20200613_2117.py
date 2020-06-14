# Generated by Django 3.0.6 on 2020-06-13 19:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0027_auto_20200613_2054'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='entry',
            unique_together={('name', 'group', 'tree')},
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('name', 'group', 'tree')},
        ),
        migrations.AlterUniqueTogether(
            name='tree',
            unique_together={('name', 'group')},
        ),
        migrations.RemoveField(
            model_name='entry',
            name='user',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='user',
        ),
        migrations.RemoveField(
            model_name='tree',
            name='user',
        ),
    ]