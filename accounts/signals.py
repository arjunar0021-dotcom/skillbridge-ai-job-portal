from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Company, SeekerProfile, User


@receiver(post_save, sender=User)
def create_role_profile(sender, instance, created, **kwargs):
    """Every new seeker gets a profile; every new employer gets a company."""
    if not created:
        return
    if instance.role == User.Role.SEEKER:
        SeekerProfile.objects.get_or_create(user=instance)
    elif instance.role == User.Role.EMPLOYER:
        Company.objects.get_or_create(owner=instance, defaults={"name": instance.username})
