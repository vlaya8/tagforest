from django.db import migrations
from django.db import models

def add_profile(apps, schema_editor):

    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('tags', 'Profile')

    for user in User.objects.all():
        try:
            user.profile
        except User.RelatedObjectDoesNotExist:
            Profile.objects.create(user=user)

def rev_add_profile(apps, schema_editor):

    Profile = apps.get_model('tags', 'Profile')

    for profile in Profile.objects.all():
        profile.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0033_auto_20200614_1518'),
    ]

    operations = [
        migrations.RunPython(add_profile, rev_add_profile),
    ]
