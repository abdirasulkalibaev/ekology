# mainapp/signals.py
# Yangi user ro'yxatdan o'tganda avtomatik profil yaratish

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import FoydalanuvchiProfil


@receiver(post_save, sender=User)
def profil_yaratish(sender, instance, created, **kwargs):
    """Yangi user yaratilganda avtomatik profil yaratiladi"""
    if created:
        FoydalanuvchiProfil.objects.get_or_create(foydalanuvchi=instance)
