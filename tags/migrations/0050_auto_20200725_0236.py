# Generated by Django 3.0.6 on 2020-07-25 00:36

from django.db import migrations

def set_default_language(apps, schema_editor):

    Profile = apps.get_model('tags', 'Profile')

    for profile in Profile.objects.all():

        profile.language = 'fr'
        profile.save()

def rev_set_default_language(apps, schema_editor):

    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0049_profile_language'),
    ]

    operations = [
        migrations.RunPython(set_default_language, rev_set_default_language),
    ]
