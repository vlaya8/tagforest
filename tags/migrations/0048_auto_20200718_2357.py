from django.db import migrations

def default_entry_display(apps, schema_editor):
    Tree = apps.get_model('tags', 'Tree')
    for tree in Tree.objects.all():
        tree.entry_display = "CPL"
        tree.save()

def rev_default_entry_display(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0047_auto_20200718_2145'),
    ]

    operations = [
            migrations.RunPython(default_entry_display, rev_default_entry_display),
    ]
