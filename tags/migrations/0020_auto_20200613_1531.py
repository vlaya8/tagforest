from django.db import migrations
from django.db import models

def add_roles(apps, schema_editor):

    GroupRole = apps.get_model('tags', 'GroupRole')
    GroupRole.objects.create(name="admin",
                         manage_users=True,
                         manage_entries=True)

    GroupRole.objects.create(name="writer",
                         manage_users=False,
                         manage_entries=True)

    GroupRole.objects.create(name="reader",
                         manage_users=False,
                         manage_entries=False)

def rev_add_roles(apps, schema_editor):

    GroupRole = apps.get_model('tags', 'GroupRole')
    GroupRole.objects.filter(name="admin").delete()
    GroupRole.objects.filter(name="writer").delete()
    GroupRole.objects.filter(name="reader").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0019_grouprole_name'),
    ]

    operations = [
        migrations.RunPython(add_roles, rev_add_roles),
    ]
