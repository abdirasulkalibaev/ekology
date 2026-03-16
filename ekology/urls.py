# mainapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('',          views.landing_page, name='landing_page'),
    path('welcome/',  views.welcome_page, name='welcome_page'),
    path('home/',     views.home_page,    name='home_page'),
    path('yuklash/',  views.yuklash_page, name='yuklash_page'),
    path('xarita/',   views.xarita_page,  name='xarita_page'),
    path('profil/',   views.profil_page,  name='profil_page'),
    path('logout/',   views.logout_page,  name='logout_page'),

    # Admin panel
    path('admin-panel/',                        views.admin_panel,     name='admin_panel'),
    path('admin-panel/tasdiqlash/<int:xabar_id>/', views.xabar_tasdiqlash, name='xabar_tasdiqlash'),
    path('admin-panel/rad/<int:xabar_id>/',        views.xabar_rad_etish,  name='xabar_rad_etish'),
    path('admin-panel/tozalandi/<int:xabar_id>/',  views.xabar_tozalandi,  name='xabar_tozalandi'),
]
