# Generated by Django 3.0.6 on 2020-05-25 21:14

from django.db import migrations
from django.contrib.auth.models import User

def set_default_user(apps, schema_editor):
    Tree = apps.get_model('tags', 'Tree')
    User = apps.get_model('auth', 'User')
    for tree in Tree.objects.all():
        tree.user = User.objects.first()
        tree.save()

def rev_set_default_user(apps, schema_editor):
    Tree = apps.get_model('tags', 'Tree')
    for tree in Tree.objects.all():
        tree.user = None
        tree.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0014_tree_user'),
    ]

    operations = [
            migrations.RunPython(set_default_user, rev_set_default_user),
    ]