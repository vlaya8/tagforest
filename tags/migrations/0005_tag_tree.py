# Generated by Django 3.0.6 on 2020-05-17 18:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0004_auto_20200517_1931'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='tree',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tags.Tree'),
        ),
    ]