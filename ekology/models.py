# mainapp/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class FoydalanuvchiProfil(models.Model):
    foydalanuvchi = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    jami_ball     = models.IntegerField(default=0)
    xabarlar_soni = models.IntegerField(default=0)
    yaratilgan    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.foydalanuvchi.email} — {self.jami_ball} ball"

    class Meta:
        ordering = ['-jami_ball']


class ChiqindiXabar(models.Model):
    TURI = [
        ('plastik',   'Plastik'),
        ('qurilish',  'Qurilish chiqindisi'),
        ('maishiy',   'Maishiy chiqindi'),
        ('kimyoviy',  'Kimyoviy chiqindi'),
        ('noaniq',    'Noaniq'),
    ]
    XAVFLILIK = [
        ('past',   'Past'),
        ('orta',   "O'rta"),
        ('yuqori', 'Yuqori'),
    ]
    HAJM = [
        ('kichik', 'Kichik'),   # hisobga olinmaydi
        ('orta',   "O'rta"),
        ('katta',  'Katta'),
    ]
    HOLATI = [
        ('kutilmoqda',  'Kutilmoqda'),   # AI tekshirmoqda
        ('qabul',       'Qabul qilindi'),
        ('rad',         'Rad etildi'),    # kichik chiqindi
        ('tasdiqlandi', 'Tasdiqlandi'),   # admin tasdiqladi
        ('tozalandi',   'Tozalandi'),     # admin tozalandi deb belgiladi
    ]

    foydalanuvchi = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xabarlar')
    turi          = models.CharField(max_length=20, choices=TURI, default='noaniq')
    xavflilik     = models.CharField(max_length=10, choices=XAVFLILIK, default='past')
    hajm          = models.CharField(max_length=10, choices=HAJM, default='orta')
    tavsif        = models.TextField(blank=True)
    latitude      = models.FloatField(default=41.2995)
    longitude     = models.FloatField(default=69.2401)
    holati        = models.CharField(max_length=20, choices=HOLATI, default='kutilmoqda')
    ball          = models.IntegerField(default=0)
    ai_tahlil     = models.TextField(blank=True)   # AI ning batafsil javobi
    sana          = models.DateTimeField(auto_now_add=True)
    tozalangan_sana = models.DateTimeField(null=True, blank=True)

    def xaritadan_ochirish_sanasi(self):
        """Tozalanganidan 7 kun keyin xaritadan o'chadi"""
        if self.tozalangan_sana:
            return self.tozalangan_sana + timedelta(days=7)
        return None

    def xaritada_korinsinmi(self):
        """Xaritada ko'rinish shartlari"""
        if self.holati not in ('tasdiqlandi', 'tozalandi'):
            return False
        if self.holati == 'tozalandi' and self.tozalangan_sana:
            if timezone.now() > self.tozalangan_sana + timedelta(days=7):
                return False
        return True

    def __str__(self):
        return f"{self.foydalanuvchi.email} — {self.turi} — {self.sana.strftime('%d.%m.%Y')}"

    class Meta:
        ordering = ['-sana']


class XabarRasm(models.Model):
    """Har bir xabarga tegishli rasmlar (5 tagacha)"""
    xabar    = models.ForeignKey(ChiqindiXabar, on_delete=models.CASCADE, related_name='rasmlar')
    rasm     = models.ImageField(upload_to='chiqindilar/%Y/%m/')
    ai_tahlil = models.TextField(blank=True)   # bu rasm uchun AI javobi
    tartib   = models.PositiveSmallIntegerField(default=0)  # 1-chi, 2-chi rasm
    sana     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rasm {self.tartib} — {self.xabar}"

    class Meta:
        ordering = ['tartib']
