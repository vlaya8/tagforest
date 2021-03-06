# Generated by Django 3.0.6 on 2020-06-11 20:27

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tags', '0016_auto_20200525_2315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='tree',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name'),
        ),
        migrations.AlterUniqueTogether(
            name='entry',
            unique_together={('name', 'user', 'tree')},
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('name', 'user', 'tree')},
        ),
        migrations.AlterUniqueTogether(
            name='tree',
            unique_together={('name', 'user')},
        ),
    ]
