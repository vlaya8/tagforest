# Generated by Django 3.0.6 on 2020-05-22 01:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0007_auto_20200517_2036'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='tree',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Tree'),
        ),
    ]
