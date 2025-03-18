from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User


@receiver(post_save, sender=User)
def user_to_inactive(sender, instance, created, **kwargs):
    if created:
        instance.is_active = False
        instance.save()

