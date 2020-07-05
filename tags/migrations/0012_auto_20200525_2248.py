from django.db import migrations

def set_default_user(apps, schema_editor):
    Entry = apps.get_model('tags', 'Entry')
    Tag = apps.get_model('tags', 'Tag')
    User = apps.get_model('auth', 'User')
    for entry in Entry.objects.all():
        entry.user = User.objects.first()
        entry.save()
    for tag in Tag.objects.all():
        tag.user = User.objects.first()
        tag.save()

def rev_set_default_user(apps, schema_editor):
    Entry = apps.get_model('tags', 'Entry')
    Tag = apps.get_model('tags', 'Tag')
    for entry in Entry.objects.all():
        entry.user = None
        entry.save()
    for tag in Tag.objects.all():
        tag.user = None
        tag.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0011_auto_20200525_2248'),
    ]

    operations = [
            migrations.RunPython(set_default_user, rev_set_default_user),
    ]
