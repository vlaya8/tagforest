from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from tags.models import TreeUserGroup, Role, Member

# Each user must have a group with only them in it
@receiver(post_save, sender=User)
def create_group(sender, instance, created, **kwargs):
    if created:
        admin_role = Role.objects.filter(name="admin")
        member = Member.objects.create(user=instance, role=admin_role)
        group = TreeUserGroup.objects.create(name=instance.name,
                                     single_member=True)
        group.members.add(member)


