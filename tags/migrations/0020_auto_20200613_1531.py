from django.db import migrations
from django.db import models
from tags.models import Role

def add_roles(apps, schema_editor):

    Role.objects.create(name="admin",
                         manage_users=True,
                         manage_entries=True)

    Role.objects.create(name="writer",
                         manage_users=False,
                         manage_entries=True)

    Role.objects.create(name="reader",
                         manage_users=False,
                         manage_entries=False)

def rev_add_roles(apps, schema_editor):

    Role.objects.filter(name="admin").delete()
    Role.objects.filter(name="writer").delete()
    Role.objects.filter(name="reader").delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0019_grouprole_name'),
    ]

    operations = [
        migrations.RunPython(add_roles, rev_add_roles),
    ]
