from django.db import migrations
from django.db import models

def add_single_groups(apps, schema_editor):

    Role = apps.get_model('tags', 'Role')
    TreeUserGroup = apps.get_model('tags', 'TreeUserGroup')
    Member = apps.get_model('tags', 'Member')
    User = apps.get_model('auth', 'User')

    admin_role = Role.objects.filter(name="admin").first()

    for user in User.objects.all():

        member = Member.objects.create(user=user, role=admin_role)
        group = TreeUserGroup.objects.create(name=user.username,
                                     single_member=True)
        group.members.add(member)

def rev_add_single_groups(apps, schema_editor):

    TreeUserGroup = apps.get_model('tags', 'TreeUserGroup')
    User = apps.get_model('auth', 'User')

    for user in User.objects.all():
        query = TreeUserGroup.objects.filter(name=user.username).filter(single_member=True)
        if len(query) > 0:
            group = query.first()
            group.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0022_auto_20200613_1849'),
    ]

    operations = [
        migrations.RunPython(add_single_groups, rev_add_single_groups),
    ]
