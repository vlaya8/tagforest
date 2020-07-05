from django.db import migrations

def fill_group_status(apps, schema_editor):
    TreeUserGroup = apps.get_model('tags', 'TreeUserGroup')
    for group in TreeUserGroup.objects.all():
        if group.listed_group:
            group.group_status = 'LIS'
        elif group.public_group:
            group.group_status = 'PUB'
        else:
            group.group_status = 'PRIV'
        group.save()

def rev_fill_group_status(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0039_treeusergroup_group_status'),
    ]

    operations = [
            migrations.RunPython(fill_group_status, rev_fill_group_status),
    ]
