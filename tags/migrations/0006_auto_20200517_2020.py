# Generated by Django 3.0.6 on 2020-05-17 18:20

from django.db import migrations
from django.db import models
from tags.models import Tree,Tag

def set_default_tree(apps, schema_editor):
    Tag = apps.get_model('tags', 'Tag')
    Tree = apps.get_model('tags', 'Tree')
    for tag in Tag.objects.all():
        tag.tree = Tree.objects.first()
        tag.save()

def rev_set_default_tree(apps, schema_editor):
    Tag = apps.get_model('tags', 'Tag')
    for tag in Tag.objects.all():
        tag.tree = None
        tag.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0005_tag_tree'),
    ]

    operations = [
            migrations.RunPython(set_default_tree, rev_set_default_tree),
    ]