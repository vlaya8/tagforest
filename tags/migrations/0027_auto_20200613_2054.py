# Generated by Django 3.0.6 on 2020-06-13 18:54

from django.db import migrations

def replace_user_to_group(apps, schema_editor):

    TreeUserGroup = apps.get_model('tags', 'TreeUserGroup')
    Tree = apps.get_model('tags', 'Tree')
    Entry = apps.get_model('tags', 'Entry')
    Tag = apps.get_model('tags', 'Tag')

    for tree in Tree.objects.all():
        tree.group = TreeUserGroup.objects.filter(name=tree.user.username).filter(single_member=True).first()
        tree.save()

    for tag in Tag.objects.all():
        tag.group = TreeUserGroup.objects.filter(name=tag.user.username).filter(single_member=True).first()
        tag.save()

    for entry in Entry.objects.all():
        entry.group = TreeUserGroup.objects.filter(name=entry.user.username).filter(single_member=True).first()
        entry.save()

def rev_replace_user_to_group(apps, schema_editor):

    Tree = apps.get_model('tags', 'Tree')
    Entry = apps.get_model('tags', 'Entry')
    Tag = apps.get_model('tags', 'Tag')

    for tree in Tree.objects.all():
        tree.group = None
        tree.save()

    for tag in Tag.objects.all():
        tag.group = None
        tag.save()

    for entry in Entry.objects.all():
        entry.group = None
        entry.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0026_auto_20200613_2054'),
    ]

    operations = [
        migrations.RunPython(replace_user_to_group, rev_replace_user_to_group),
    ]
