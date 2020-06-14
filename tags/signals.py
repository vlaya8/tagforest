from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from tags.models import TreeUserGroup, Role, Member

# Each user must have a group with only them in it
@receiver(post_save, sender=User)
def create_group(sender, instance, created, **kwargs):
    if created:
        admin_role = Role.objects.filter(name="admin").first()
        group = TreeUserGroup.objects.create(name=instance.username,
                                     single_member=True)
        member = Member.objects.create(user=instance, role=admin_role, group=group)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, created, **kwargs):
    instance.profile.Save()
