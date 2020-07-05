from django.db import migrations
from django.db import models

def add_single_groups(apps, schema_editor):

    Role = apps.get_model('tags', 'Role')
    TreeUserGroup = apps.get_model('tags', 'TreeUserGroup')
    Member = apps.get_model('tags', 'Member')
    User = apps.get_model('auth', 'User')

    TreeUserGroup.objects.all().delete()
    Member.objects.all().delete()

    admin_role = Role.objects.filter(name="admin").first()

    for user in User.objects.all():

        group = TreeUserGroup.objects.create(name=user.username,
                                     single_member=True)
        member = Member.objects.create(user=user, role=admin_role, group=group)

def rev_add_single_groups(apps, schema_editor):

    TreeUserGroup = apps.get_model('tags', 'TreeUserGroup')
    User = apps.get_model('auth', 'User')

    TreeUserGroup.objects.all().delete()
    Member.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0024_auto_20200613_1940'),
    ]

    operations = [
        migrations.RunPython(add_single_groups, rev_add_single_groups),
    ]
