# mainapp/views.py

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum

from .models import ChiqindiXabar, XabarRasm, FoydalanuvchiProfil
from .ai_service import kop_rasm_tahlil


# ─────────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────

def profil_olish_yoki_yaratish(user):
    profil, _ = FoydalanuvchiProfil.objects.get_or_create(foydalanuvchi=user)
    return profil


def admin_tekshirish(user):
    return user.is_staff or user.is_superuser


# ─────────────────────────────────────────────
# UMUMIY SAHIFALAR
# ─────────────────────────────────────────────

def landing_page(request):
    jami_xabarlar = ChiqindiXabar.objects.filter(
        holati__in=['tasdiqlandi', 'tozalandi']
    ).count()
    tozalangan = ChiqindiXabar.objects.filter(holati='tozalandi').count()
    return render(request, 'landing.html', {
        'jami_xabarlar': jami_xabarlar,
        'tozalangan': tozalangan,
    })


@login_required(login_url='/accounts/login/')
def welcome_page(request):
    """Login bo'lgandan keyin tabiat rasmi sahifasi"""
    jami_xabarlar = ChiqindiXabar.objects.filter(
        holati__in=['tasdiqlandi', 'tozalandi']
    ).count()
    tozalangan = ChiqindiXabar.objects.filter(holati='tozalandi').count()
    return render(request, 'welcome.html', {
        'jami_xabarlar': jami_xabarlar,
        'tozalangan': tozalangan,
    })


@login_required(login_url='/accounts/login/')
def home_page(request):
    profil = profil_olish_yoki_yaratish(request.user)
    oxirgi_xabarlar = ChiqindiXabar.objects.filter(
        foydalanuvchi=request.user
    ).prefetch_related('rasmlar')[:6]

    # Reyting — top 10
    top_users = FoydalanuvchiProfil.objects.select_related('foydalanuvchi').order_by('-jami_ball')[:10]

    return render(request, 'home.html', {
        'profil': profil,
        'oxirgi_xabarlar': oxirgi_xabarlar,
        'top_users': top_users,
    })


# ─────────────────────────────────────────────
# RASM YUKLASH
# ─────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def yuklash_page(request):
    if request.method == 'POST':
        rasm_fayllar = request.FILES.getlist('rasmlar')  # 5 tagacha

        # Validatsiya
        if not rasm_fayllar:
            return render(request, 'yuklash.html', {
                'xato': 'Kamida 1 ta rasm yuklang.'
            })
        if len(rasm_fayllar) > 5:
            return render(request, 'yuklash.html', {
                'xato': 'Maksimal 5 ta rasm yuklanadi.'
            })

        # Koordinatalar
        try:
            latitude  = float(request.POST.get('latitude', 41.2995))
            longitude = float(request.POST.get('longitude', 69.2401))
        except ValueError:
            latitude, longitude = 41.2995, 69.2401

        # AI tahlil
        ai_natija = kop_rasm_tahlil(rasm_fayllar)

        if not ai_natija['qabul']:
            return render(request, 'yuklash.html', {
                'xato': ai_natija.get('rad_sababi', 'Xabar qabul qilinmadi.'),
                'ai_tahlil': ai_natija.get('rasmlar_tahlil', []),
            })

        # Xabar saqlash
        xabar = ChiqindiXabar.objects.create(
            foydalanuvchi = request.user,
            turi          = ai_natija['turi'],
            xavflilik     = ai_natija['xavflilik'],
            hajm          = ai_natija['hajm'],
            tavsif        = ai_natija['tavsif'],
            latitude      = latitude,
            longitude     = longitude,
            holati        = 'kutilmoqda',  # admin tasdiqlashini kutadi
            ball          = ai_natija['ball'],
            ai_tahlil     = ai_natija['ai_tahlil'],
        )

        # Rasmlarni saqlash
        for i, fayl in enumerate(rasm_fayllar):
            fayl.seek(0)
            rasm_tahlil = ''
            if i < len(ai_natija.get('rasmlar_tahlil', [])):
                rasm_tahlil = json.dumps(
                    ai_natija['rasmlar_tahlil'][i],
                    ensure_ascii=False
                )
            XabarRasm.objects.create(
                xabar     = xabar,
                rasm      = fayl,
                ai_tahlil = rasm_tahlil,
                tartib    = i + 1,
            )

        messages.success(
            request,
            f'Xabar yuborildi! AI {ai_natija["ball"]} ball berdi. Admin tasdiqlagandan keyin ballingiz qo\'shiladi.'
        )
        return redirect('home_page')

    return render(request, 'yuklash.html')


# ─────────────────────────────────────────────
# XARITA
# ─────────────────────────────────────────────

def xarita_page(request):
    # Faqat tasdiqlangan va tozalangan — 7 kundan keyin o'chadi
    xabarlar_qs = ChiqindiXabar.objects.filter(
        holati__in=['tasdiqlandi', 'tozalandi']
    ).prefetch_related('rasmlar')

    xabarlar_list = []
    for x in xabarlar_qs:
        if not x.xaritada_korinsinmi():
            continue
        birinchi_rasm = x.rasmlar.first()
        xabarlar_list.append({
            'lat':       x.latitude,
            'lng':       x.longitude,
            'turi':      x.turi,
            'xavflilik': x.xavflilik,
            'hajm':      x.hajm,
            'holati':    x.holati,
            'tavsif':    x.tavsif,
            'sana':      x.sana.strftime('%d.%m.%Y'),
            'rasm':      birinchi_rasm.rasm.url if birinchi_rasm else '',
        })

    return render(request, 'xarita.html', {
        'xabarlar_json': json.dumps(xabarlar_list, ensure_ascii=False),
    })


# ─────────────────────────────────────────────
# PROFIL
# ─────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def profil_page(request):
    profil = profil_olish_yoki_yaratish(request.user)
    xabarlar = ChiqindiXabar.objects.filter(
        foydalanuvchi=request.user
    ).prefetch_related('rasmlar')

    # Reyting o'rni
    barcha_profiller = FoydalanuvchiProfil.objects.order_by('-jami_ball')
    reyting_orni = None
    for i, p in enumerate(barcha_profiller, 1):
        if p.foydalanuvchi == request.user:
            reyting_orni = i
            break

    return render(request, 'profil.html', {
        'profil':       profil,
        'xabarlar':     xabarlar,
        'reyting_orni': reyting_orni,
    })


# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────

@user_passes_test(admin_tekshirish, login_url='/accounts/login/')
def admin_panel(request):
    kutilmoqda = ChiqindiXabar.objects.filter(
        holati='kutilmoqda'
    ).prefetch_related('rasmlar').select_related('foydalanuvchi')

    tasdiqlangan = ChiqindiXabar.objects.filter(
        holati='tasdiqlandi'
    ).prefetch_related('rasmlar').select_related('foydalanuvchi')[:20]

    tozalangan = ChiqindiXabar.objects.filter(
        holati='tozalandi'
    ).prefetch_related('rasmlar').select_related('foydalanuvchi')[:20]

    # Statistika
    jami_foydalanuvchilar = FoydalanuvchiProfil.objects.count()
    jami_xabarlar = ChiqindiXabar.objects.count()

    return render(request, 'admin_panel.html', {
        'kutilmoqda':          kutilmoqda,
        'tasdiqlangan':        tasdiqlangan,
        'tozalangan':          tozalangan,
        'jami_foydalanuvchi':  jami_foydalanuvchilar,
        'jami_xabarlar':       jami_xabarlar,
    })


@user_passes_test(admin_tekshirish, login_url='/accounts/login/')
def xabar_tasdiqlash(request, xabar_id):
    """Admin xabarni tasdiqlaydi → foydalanuvchiga ball beriladi"""
    if request.method != 'POST':
        return redirect('admin_panel')

    xabar = get_object_or_404(ChiqindiXabar, id=xabar_id)

    if xabar.holati == 'kutilmoqda':
        xabar.holati = 'tasdiqlandi'
        xabar.save()

        # Foydalanuvchiga ball qo'shish
        profil = profil_olish_yoki_yaratish(xabar.foydalanuvchi)
        profil.jami_ball     += xabar.ball
        profil.xabarlar_soni += 1
        profil.save()

        messages.success(request, f'Xabar tasdiqlandi. +{xabar.ball} ball berildi.')
    return redirect('admin_panel')


@user_passes_test(admin_tekshirish, login_url='/accounts/login/')
def xabar_rad_etish(request, xabar_id):
    """Admin xabarni rad etadi"""
    if request.method != 'POST':
        return redirect('admin_panel')

    xabar = get_object_or_404(ChiqindiXabar, id=xabar_id)
    xabar.holati = 'rad'
    xabar.save()
    messages.success(request, 'Xabar rad etildi.')
    return redirect('admin_panel')


@user_passes_test(admin_tekshirish, login_url='/accounts/login/')
def xabar_tozalandi(request, xabar_id):
    """Admin: chiqindi tozalandi → +50 bonus ball, 7 kundan keyin xaritadan o'chadi"""
    if request.method != 'POST':
        return redirect('admin_panel')

    xabar = get_object_or_404(ChiqindiXabar, id=xabar_id)

    if xabar.holati == 'tasdiqlandi':
        xabar.holati         = 'tozalandi'
        xabar.tozalangan_sana = timezone.now()
        xabar.save()

        # +50 bonus ball
        profil = profil_olish_yoki_yaratish(xabar.foydalanuvchi)
        profil.jami_ball += 50
        profil.save()

        messages.success(request, 'Tozalandi deb belgilandi. +50 bonus ball berildi!')
    return redirect('admin_panel')


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

def logout_page(request):
    logout(request)
    return redirect('/accounts/login/')
