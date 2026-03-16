# mainapp/views.py ga welcome sahifa qo'shish uchun
# Mavjud views.py ga quyidagi funksiyani qo'shing:

# allauth signal — login bo'lganda welcome sahifaga yo'naltirish
# config/settings.py ga qo'shing:
# LOGIN_REDIRECT_URL = '/welcome/'

# views.py ga qo'shish:

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required(login_url='/accounts/login/')
def welcome_page(request):
    """Login bo'lgandan keyin ko'rinadigan tabiat rasmi sahifasi"""
    from .models import ChiqindiXabar
    jami_xabarlar = ChiqindiXabar.objects.filter(
        holati__in=['tasdiqlandi', 'tozalandi']
    ).count()
    tozalangan = ChiqindiXabar.objects.filter(holati='tozalandi').count()
    return render(request, 'welcome.html', {
        'jami_xabarlar': jami_xabarlar,
        'tozalangan': tozalangan,
    })
