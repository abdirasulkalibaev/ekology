# mainapp/ai_service.py
# Gemini AI bilan barcha ishlar shu faylda

import json
import google.generativeai as genai
from PIL import Image
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def _rasm_ochish(rasm_fayl):
    """Faylni PIL Image ga aylantirish"""
    try:
        rasm_fayl.seek(0)
        return Image.open(rasm_fayl)
    except Exception:
        return None


def bitta_rasm_tahlil(rasm_fayl):
    """
    Bitta rasmni AI tahlil qiladi.
    Qaytaradi: dict yoki None
    """
    rasm = _rasm_ochish(rasm_fayl)
    if not rasm:
        return None

    prompt = """
Ushbu rasmni ekologiya nuqtai nazaridan DIQQAT BILAN tahlil qil.

Faqat JSON formatida javob ber, boshqa hech narsa yozma:
{
    "chiqindi_bormi": true yoki false,
    "turi": "plastik" YOKI "qurilish" YOKI "maishiy" YOKI "kimyoviy" YOKI "noaniq",
    "hajm": "kichik" YOKI "orta" YOKI "katta",
    "xavflilik": "past" YOKI "orta" YOKI "yuqori",
    "tavsif": "o'zbek tilida qisqacha tavsif (1-2 gap)",
    "ishonch": 0 dan 100 gacha son (AI ning ishonch darajasi)
}

Hajm mezonlari:
- kichik: bir qo'lda ko'tarsa bo'ladigan miqdor (1-2 paket, oz chiqindi)
- orta: bir kishi tozalashi mumkin bo'lgan miqdor
- katta: bir nechta kishi yoki texnika kerak bo'ladigan miqdor
"""
    try:
        response = model.generate_content([prompt, rasm])
        text = response.text.strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            return None
        return json.loads(text[start:end])
    except Exception as e:
        print(f"AI xato: {e}")
        return None


def kop_rasm_tahlil(rasm_fayllar):
    """
    5 tagacha rasmni tahlil qilib, UMUMIY qaror chiqaradi.
    Qaytaradi: {
        'qabul': True/False,
        'rad_sababi': str yoki None,
        'turi': str,
        'hajm': str,
        'xavflilik': str,
        'tavsif': str,
        'ball': int,
        'rasmlar_tahlil': list,
        'ai_tahlil': str  (batafsil)
    }
    """
    if not rasm_fayllar:
        return {'qabul': False, 'rad_sababi': 'Rasm yuklanmadi'}

    rasmlar_tahlil = []
    chiqindi_topilgan = 0

    for i, fayl in enumerate(rasm_fayllar[:5]):
        natija = bitta_rasm_tahlil(fayl)
        if natija:
            natija['rasm_tartib'] = i + 1
            rasmlar_tahlil.append(natija)
            if natija.get('chiqindi_bormi'):
                chiqindi_topilgan += 1

    # Hech bir rasmda chiqindi yo'q
    if chiqindi_topilgan == 0:
        return {
            'qabul': False,
            'rad_sababi': 'Rasmlarda chiqindi aniqlanmadi. Aniqroq rasm yuboring.',
            'rasmlar_tahlil': rasmlar_tahlil,
            'ai_tahlil': json.dumps(rasmlar_tahlil, ensure_ascii=False)
        }

    # Eng ko'p uchrayotgan turni aniqlash
    turlar = [r['turi'] for r in rasmlar_tahlil if r.get('chiqindi_bormi')]
    turi = max(set(turlar), key=turlar.count) if turlar else 'noaniq'

    # Eng yuqori xavflilikni olish
    xavf_daraja = {'past': 1, 'orta': 2, 'yuqori': 3}
    xavfliliklar = [r.get('xavflilik', 'past') for r in rasmlar_tahlil if r.get('chiqindi_bormi')]
    xavflilik = max(xavfliliklar, key=lambda x: xavf_daraja.get(x, 0)) if xavfliliklar else 'past'

    # Eng katta hajmni olish
    hajm_daraja = {'kichik': 1, 'orta': 2, 'katta': 3}
    hajmlar = [r.get('hajm', 'kichik') for r in rasmlar_tahlil if r.get('chiqindi_bormi')]
    hajm = max(hajmlar, key=lambda x: hajm_daraja.get(x, 0)) if hajmlar else 'kichik'

    # Kichik chiqindi — rad etish
    if hajm == 'kichik':
        return {
            'qabul': False,
            'rad_sababi': (
                'Chiqindi hajmi juda kichik (bir qo\'lda ko\'tarsa bo\'ladigan miqdor). '
                'Katta hajmdagi chiqindilar haqida xabar bering.'
            ),
            'rasmlar_tahlil': rasmlar_tahlil,
            'ai_tahlil': json.dumps(rasmlar_tahlil, ensure_ascii=False)
        }

    # Ball hisoblash (AI tomonidan)
    ball = _ball_hisoblash(hajm, xavflilik, chiqindi_topilgan, len(rasm_fayllar))

    tavsiflar = [r.get('tavsif', '') for r in rasmlar_tahlil if r.get('tavsif')]
    tavsif = tavsiflar[0] if tavsiflar else ''

    return {
        'qabul': True,
        'rad_sababi': None,
        'turi': turi,
        'hajm': hajm,
        'xavflilik': xavflilik,
        'tavsif': tavsif,
        'ball': ball,
        'rasmlar_tahlil': rasmlar_tahlil,
        'ai_tahlil': json.dumps(rasmlar_tahlil, ensure_ascii=False, indent=2)
    }


def _ball_hisoblash(hajm, xavflilik, topilgan_rasmlar, jami_rasmlar):
    """
    AI tomonidan ball hisoblash.
    Hajm, xavflilik va rasm soni asosida.
    """
    # Asosiy ball
    hajm_ball = {'kichik': 0, 'orta': 15, 'katta': 30}
    xavf_ball = {'past': 5, 'orta': 10, 'yuqori': 20}

    ball = hajm_ball.get(hajm, 15) + xavf_ball.get(xavflilik, 5)

    # Ko'p rasm = ko'proq ball (aniqroq xabar)
    if jami_rasmlar >= 3:
        ball += 5
    if jami_rasmlar >= 5:
        ball += 5

    return ball
