from aiogram.utils.i18n import gettext as _
from datetime import datetime, timezone
from typing import List, Tuple
import re
import random

# ============================ start_handler ============================


def full_name_example() -> str:
    return _("📝 Ism va Familyangizni to'liq kiriting.\n {example}").format(
        example=_("👉 Masalan : ") + "<i>Alisher Maxsetov</i>"
    )

def full_name_error() -> str:
    return _("❌ Iltimos, Ism va Familyangizni to'liq kiriting.\n {example}").format(
        example=_("👉 Masalan : ") + "<i>Alisher Maxsetov</i>"
    )

def phone_number_prompt() -> str:
    return _("📱 Telefon raqamingizni yuborish uchun, iltimos, pastdagi tugmani bosing.")

def phone_number_error() -> str:
    return _("❌ Iltimos, '📱 Raqamni yuborish' tugmasidan foydalaning.")

def get_main_menu_text_once(name: str) -> str:
    return f"{_('✋ Assalomu alaykum, Xush kelibsiz!')}\n<b>👤 {name}</b>"

def get_main_text() -> str:
    return _("🏠 <b>Asosiy Menyu</b>")

def phone_number_prompt_with_name(name: str) -> str:
    return _(
        "✅ Rahmat, <b>{name}</b>!\n\n"
        "📱 Telefon raqamingizni yuborish uchun, iltimos, pastdagi tugmani bosing."
    ).format(name=name)


# --------------------- /help ---------------------

def get_help_text(admin_link="@admin"):
    """Help komandasi uchun matn"""
    return _(
    f"""🤖 <b>BOT IMKONIYATLARI:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 <b>Test Bo'limi</b>
    • Malaka darajasi bo'yicha bilim sinovlari

🦺 <b>Himoya Vositalari Bo'limi</b>
    • Himoya vositalarining holati    
      va sinov muddatlari

⚠️ <b>Baxtsiz Hodisalar Bo'limi</b>
    • Sodir bo'lgan baxtsiz hodisalar 
      va ularning tahlili

📅 <b>Davriy Imtixon Vaqti Bo'limi</b>
    • Yillik imtihon muddati

🤖 <b>AI Yordamchi Bo'limi</b>
    • Suniy intelekt bilan o'zbek tilida 
      savol-javob

📚 <b>Kutubxona Bo'limi</b>
    • Elektron kitoblar,hujjatlar va qo'llanmalar

🎥 <b>Video Materiallar Bo'limi</b>
    • Foydali ta'limiy video materiallar

🚆 <b>Poezdlar Harakat Xavfsizligi Bo'limi</b>
    • Harakat havsizligini taminlash 
      va oldini olish 

🏢 <b>Biz Haqimizda Bo'lim</b>
    • Korxona haqida toliq malumot
      va admin bilan bog'lanish 
       
🌐 <b>Tilni O'zgartirish</b>
    • Interfeys tilini tanlash imkoniyati
━━━━━━━━━━━━━━━━━━━━━━━━━
💬 <b>Murojaat uchun:</b> <a href="{admin_link}"><b>Admin bilan bog'lanish</b></a>""")


# ============================ language_handler ============================


def language_prompt_text() -> str:
    return _("👇 Iltimos, tilni tanlang")

def language_invalid_text() -> str:
    return _("❗️ Iltimos, tugmalardan birini tanlang")

def language_updated_text() -> str:
    return _("✅ Til muvaffaqiyatli o'zgartirildi")

def language_error_text() -> str:
    return _("❌ Tilni o'zgartirishda xatolik yuz berdi")


# ============================ test_handler ============================

def test_no_categories_text() -> str:
    return _("📂 <b>Hozircha hech qanday Test Bo'limi mavjud emas.</b>\n"
            "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
            "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>")

def test_categories_prompt() -> str:
    return _(
        "🧠 <b>TEST BO'LIMI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "👇 <b>Test Bo'limini tanlang:</b>\n\n"
    )

def test_category_empty() -> str:
    return _("❌ <b>Bu Bo'limda Testlar mavjud emas</b>\n\n")

def test_starting_text(total_questions: int) -> str:
    return _(
        "🎯 <b>Test boshlanmoqda!</b>\n\n"
        "🔢 Jami savollar: <b>{total}</b> ta\n"
        "⏱ Har bir savolga: <b>60 soniya</b>\n\n"
        "💡 <i>Tayyor bo'lsangiz, boshlaymiz...</i>"
    ).format(total=total_questions)

def test_question_header(current: int, total: int) -> str:
    return _("📝 Savol - {current}/{total}").format(current=current, total=total)

def test_time_remaining(seconds: int) -> str:
    return _("⏳ <i>Qolgan vaqt: <b>{seconds}</b> soniya</i>").format(seconds=seconds)

def test_time_up_result() -> str:
    return _("⏰ <b>Vaqt tugadi!</b>\n\n")

def test_answer_variants_header() -> str:
    return _("📝 <b>Javob variantlari:</b>\n")

def test_correct_response() -> str:
    return _("✅ <b>To'g'ri javob!</b>\n\n")

def test_incorrect_response() -> str:
    return _("❌ <b>Noto'g'ri javob!</b>\n\n")

def test_finished_header() -> str:
    return _("🏁 <b>TEST YAKUNLANDI!</b>\n")

def test_participant_label(name: str) -> str:
    return _("👤 <b>Ishtirokchi: {name}</b>\n\n").format(name=name)

def test_result_label(correct: int, total: int) -> str:
    return _("📊 <b>Natija:</b> {correct}/{total}\n\n").format(correct=correct, total=total)

def test_percentage_label(percentage: float) -> str:
    return _("📈 <b>Foiz:</b> <i>{percentage}%</i>\n\n").format(percentage=percentage)

def test_grade_label(grade_text: str) -> str:
    return _("<b>Baho: {grade}</b>\n\n").format(grade=grade_text)

def test_correct_answers_count(correct: int) -> str:
    return _("✅ To'g'ri javoblar: {correct}\n\n").format(correct=correct)

def test_incorrect_answers_count(incorrect: int) -> str:
    return _("❌ Noto'g'ri javoblar: {incorrect}\n\n").format(incorrect=incorrect)

# Baholar
def test_grade_excellent() -> str:
    return _("A'lo darajada!")

def test_grade_good() -> str:
    return _("Yaxshi!")

def test_grade_satisfactory() -> str:
    return _("Qoniqarli!")

def test_grade_average() -> str:
    return _("O'rtacha!")

def test_grade_unsatisfactory() -> str:
    return _("Qoniqarsiz!")

# Tabriklar
def test_congratulation_excellent() -> str:
    return _("🎊 Ajoyib natija! Siz haqiqiy bilimdon ekansiz!")

def test_congratulation_good() -> str:
    return _("👏 Yaxshi natija! Biroz ko'proq mashq qilsangiz a'lo bo'ladi!")

def test_congratulation_satisfactory() -> str:
    return _("💪 Yaxshi harakat! Davom eting!")

def test_congratulation_average() -> str:
    return _("📖 Yaxshi boshlanish! Ko'proq o'qish kerak!")

def test_congratulation_unsatisfactory() -> str:
    return _("💡 Bilimlaringizni oshirish uchun ko'proq harakat qiling!")

# Xatoliklar
def test_invalid_format_text() -> str:
    return _("❌ Noto'g'ri format!")

def test_answer_not_found_text() -> str:
    return _("❌ Javob yoki savol topilmadi!")

def test_time_expired_text() -> str:
    return _("⏰ Kechikdingiz, vaqt tugagan!")

def test_error_occurred() -> str:
    return _(
        "❌ <b>Xatolik yuz berdi</b>\n\n"
        "🔄 Iltimos, qaytadan urinib ko'ring."
    )

def test_default_user_name() -> str:
    return _("Foydalanuvchi")

# YANGI FUNKSIYALAR - Qisqa natija matnlari tugma uchun
def test_correct_response_short() -> str:
    return _("✅ To'g'ri!")

def test_incorrect_response_short() -> str:
    return _("❌ Noto'g'ri!")

def test_time_up_short() -> str:
    return _("⏰ Vaqt tugadi!")


# ============================ equipment_handler ============================

def safety_equipment_count_text(count: int) -> str:
    """Equipment soni haqida ma'lumot"""
    return _("🧰 <b>Jami Himoya vositalar soni: <i>{count}</i> ta</b>").format(count=count)

def safety_equipment_count_with_dash_text(count: int) -> str:
    """Equipment soni haqida ma'lumot (dash bilan)"""
    return _("🧰 <b>Jami Himoya vositalar soni: <i>{count}</i> ta</b>").format(count=count)

def safety_equipment_page_info_text(count: int, page: int, total_pages: int) -> str:
    """Sahifa ma'lumoti"""
    return _("🧰 <b>Jami: {count} ta</b> ┃ 📄 <b>Sahifa: {page}/{total_pages}</b>").format(
        count=count, page=page, total_pages=total_pages
    )

def safety_no_equipment_in_department_text() -> str:
    """Department'da equipment yo'q"""
    return _("📊 Bu bo'limda hozircha Himoya vositalari yo'q")


# Handler ichidagi string'lar uchun
def safety_department_statistics_header_text(department_name: str) -> str:
    """Statistika header"""
    return _(
        "📈 <b>{department_name}: Statistika</b>\n\n"
        "🔢 <b>Himoya vositalari soni:</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
    ).format(department_name=department_name)

def safety_department_statistics_item_text(name: str, count: int) -> str:
    """Statistika elementi"""
    return _("🔸 <b>{name}: {count} ta</b>").format(name=name, count=count)

def safety_department_statistics_total_text(total: int) -> str:
    """Jami statistika"""
    return _(
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "🧰 <b>Jami: <i>{total}</i> ta</b>"
    ).format(total=total)

def safety_no_departments_text() -> str:
    """Department'lar topilmaganda"""
    return _(
        "❌ <b>Hozircha hech qanday Bo'lim topilmadi.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    )


def safety_departments_prompt() -> str:
    """Department tanlash uchun"""
    return _(
        "🦺 <b>HIMOY VOSTALAR BO'LIMI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "📋 Quyidagi Bo'limlardan birini tanlang:\n"
    )


def safety_no_areas_text(department_name: str) -> str:
    """Area'lar topilmaganda"""
    return _(
        "❌ <b>{department_name}</b> Bo'limida hozircha\n"
        "hech qanday <b>Hudud</b> topilmadi.\n\n"
        "🙏 <i>Iltimos, boshqa bo'limni tanlang yoki keyinroq qayta urinib ko'ring</i>"
    ).format(department_name=department_name)


def safety_areas_prompt(department_name: str) -> str:
    """Area tanlash uchun"""
    return _(
        "🏢 <b>Bo'lim: {department_name}</b>\n\n"
        "📍 Quyidagi Hududlardan birini tanlang:\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖"
    ).format(department_name=department_name)


def safety_area_with_image_caption(department_name: str, area_name: str) -> str:
    """Area rasmi uchun caption"""
    return _(
        "🏢 <b>Bo'lim: {department_name}</b>\n\n"
        "📍 <b>Hudud: {area_name}</b>\n\n"
        "🏛️ Quyidagi Inshootlardan birini tanlang:\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖"
    ).format(department_name=department_name, area_name=area_name)


def safety_no_facilities_text(area_name: str) -> str:
    """Facility'lar topilmaganda"""
    return _(
        "❌ <b>{area_name}</b> - hududida hozircha\n"
        "hech qanday <b>Inshoot</b> topilmadi.\n\n"
        "🙏 <i>Iltimos, boshqa hududni tanlang yoki keyinroq qayta urinib ko'ring.</i>"
    ).format(area_name=area_name)


def safety_facility_with_image_caption(department_name: str, area_name: str, facility_name: str) -> str:
    """Facility rasmi uchun caption"""
    return _(
        "🏢 <b>Bo'lim: {department_name}</b>\n"
        "📍 <b>Hudud: {area_name}</b>\n"
        "🏛️ <b>Inshoot: {facility_name}</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "⚠️ <b>Himoya vositalari holati:</b>\n\n"
        "🔵 Muddati xavfsiz (30 kundan ko'p)\n"
        "🟢 Muddati kamaymoqda (30 kundan kam)\n"
        "🟡 Muddati yaqinlashdi (14 kundan kam)\n"
        "🔴 Muddati juda yaqin (5 kundan kam)\n"
        "⛔️ Muddati tugagan\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖"
    ).format(
        department_name=department_name,
        area_name=area_name,
        facility_name=facility_name
    )

def safety_no_equipment_text(facility_name: str) -> str:
    """Equipment'lar topilmaganda"""
    return _(
        "❌ <b>{facility_name}</b> - inshootida hozircha\n"
        "faol <b>Himoya vositalari</b> topilmadi.\n\n"
        "🙏 <i>Iltimos, boshqa inshootni tanlang yoki keyinroq qayta urinib ko'ring.</i>"
    ).format(facility_name=facility_name)


def safety_equipment_detail_text(
        department_name: str,
        area_name: str,
        facility_name: str,
        catalog_name: str,
        catalog_description: str,
        serial_number: str,
        expire_date: datetime
) -> str:
    """Equipment haqida batafsil ma'lumot"""

    # Muddatgacha qolgan kunlar
    days_left = (expire_date - datetime.now(timezone.utc)).days

    # Status belgisi va matni
    if days_left < 0:
        status_emoji = "⛔️"
        status_text = _("MUDDATI TUGAGAN!")
        days_text = _("Muddati {days} kun oldin tugagan").format(days=abs(days_left))
    elif days_left <= 5:
        status_emoji = "🔴"
        status_text = _("Muddati juda yaqin!")
        days_text = _("{days} kun qoldi").format(days=days_left)
    elif days_left <= 14:
        status_emoji = "🟡"
        status_text = _("Muddati yaqinlashdi!")
        days_text = _("{days} kun qoldi").format(days=days_left)
    elif days_left <= 30:
        status_emoji = "🟢"
        status_text = _("Muddati kamaymoqda")
        days_text = _("{days} kun qoldi").format(days=days_left)
    else:
        status_emoji = "🔵"
        status_text = _("Muddati xavfsiz")
        days_text = _("{days} kun qoldi").format(days=days_left)

    # Muddat sanasi formati
    expire_date_str = expire_date.strftime("%d.%m.%Y")

    return _(
        "🏢 <b>Bo'lim: {department_name}</b>\n"
        "📍 <b>Hudud: {area_name}</b>\n"
        "🏛️ <b>Inshoot: {facility_name}</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "🦺  <b>HIMOYA VOSITASI</b>\n\n"
        "📌 <b>Nomi:</b> {catalog_name}\n"
        "🔢 <b>Seriya raqami:</b> №{serial_number}\n"
        "📝 <b>Tavsifi:</b> {catalog_description}\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "📅 <b>MUDDAT MA'LUMOTLARI</b>\n\n"
        "⏰ <b>Tugash sanasi:</b> {expire_date}\n"
        "⌛ <b>Qolgan muddat:</b> {days_text}\n\n"
        "{status_emoji} <b>HOLAT: {status_text}</b>"
    ).format(
        department_name=department_name,
        area_name=area_name,
        facility_name=facility_name,
        catalog_name=catalog_name,
        catalog_description=catalog_description,
        serial_number=serial_number,
        expire_date=expire_date_str,
        days_text=days_text,
        status_emoji=status_emoji,
        status_text=status_text
    )

def safety_statistics_text(department_name: str, statistics: list) -> str:
    """Department statistikasi"""
    text = _(
        "📈 <b>{department_name}: Statistika</b>\n\n"
        "🔢 <b>Himoya vositalari soni:</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
    ).format(department_name=department_name)

    # Umumiy soni
    total = sum(stat.count for stat in statistics)

    # Har bir tur bo'yicha
    for stat in statistics:
        text += f"🔸 <b>{stat.name}: {stat.count} ta</b>\n"

    text += f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
    text += f"🧰 <b>Jami: <i>{total}</i> ta</b>"

    return text


def safety_error_text() -> str:
    """Xatolik yuz berganda"""
    return _("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


# ============================ exam_schedule_handler ============================


def exam_user_not_found_text() -> str:
    return _("❌ Foydalanuvchi topilmadi!")


def exam_no_data_text(full_name: str, phone_number: str) -> str:
    return _(
        "👤 <b>To'liq Ism:  <i>{full_name}</i></b>\n"
        "📞 <b>Telefon:  <i>{phone_number}</i></b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "📅 <b>Oxirgi imtihon:</b> Ma'lumot yo'q\n"
        "⏰ <b>Keyingi imtihon:</b> Ma'lumot yo'q\n\n"
        "❓ <b>Imtihon ma'lumotlari kiritilmagan</b>"
    ).format(full_name=full_name, phone_number=phone_number)


def exam_user_info_text(full_name: str, phone_number: str, last_exam: str, next_exam: str, status_icon: str,
                        status_text: str) -> str:
    return _(
        "👤 <b>To'liq Ism:  <i>{full_name}</i></b>\n"
        "📞 <b>Telefon:  <i>{phone_number}</i></b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        "📅 <b>Oxirgi imtihon:</b> {last_exam}\n"
        "⏰ <b>Keyingi imtihon:</b> {next_exam}\n\n"
        "{status_icon} <b>{status_text}</b>"
    ).format(
        full_name=full_name,
        phone_number=phone_number,
        last_exam=last_exam,
        next_exam=next_exam,
        status_icon=status_icon,
        status_text=status_text
    )


def exam_no_users_found_text() -> str:
    return _("❌ Hech qanday Xodim topilmadi!")


def exam_all_users_header_text() -> str:
    return _(
        "📊 <b>BARCHA XODIMLAR IMTIHON JADVALI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
    )


def exam_statistics_text(total: int, overdue: int, urgent: int, warning: int, normal: int, safe: int,
                         no_data: int) -> str:
    return _(
        "📈 <b>STATISTIKA:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👥 <b>Jami Xodimlar soni:  <i>{total}</i></b>\n"
        "⛔ <b>Muddati o'tgan:  <i>{overdue}</i></b>\n"
        "🔴 <b>Juda yaqin (5 kundan kam):  <i>{urgent}</i></b>\n"
        "🟡 <b>Yaqinlashdi (10 kundan kam):  <i>{warning}</i></b>\n"
        "🟢 <b>Kamaymoqda (30 kundan kam):  <i>{normal}</i></b>\n"
        "🔵 <b>Xavfsiz (30 kundan ortiq):  <i>{safe}</i></b>\n"
        "❓ <b>Ma'lumot qoshilmagan:  <i>{no_data}</i></b>"
    ).format(total=total, overdue=overdue, urgent=urgent, warning=warning, normal=normal, safe=safe, no_data=no_data)


# Status matnlari
def exam_status_overdue_text(days: int) -> str:
    return _("Imtihon muddati <b>{days}</b> kun oldin o'tgan").format(days=days)


def exam_status_urgent_text(days: int) -> str:
    return _("Imtihongacha: <b>{days}</b> kun qoldi").format(days=days)


def exam_status_warning_text(days: int) -> str:
    return _("Imtihongacha: <b>{days}</b> kun qoldi").format(days=days)


def exam_status_normal_text(days: int) -> str:
    return _("Imtihongacha: <b>{days}</b> kun qoldi").format(days=days)


def exam_status_safe_text(days: int) -> str:
    return _("Imtihongacha: <b>{days}</b> kun qoldi").format(days=days)


# Kategoriya funksiyalari
def get_category_header_text(category: str, total_items: int, page: int, total_pages: int) -> str:
    """Kategoriya header matni"""
    category_names = {
        'overdue': '⛔ <b>MUDDATI O\'TGANLAR</b>',
        'urgent': '🔴 <b>MUDDATI JUDA YAQIN\n(5 kun va undan kam)</b>',
        'warning': '🟡 <b>MUDDATI YAQINLASHDI\n(10 kun va undan kam)</b>',
        'normal': '🟢 <b>MUDDATI KAMAYMOQDA\n(30 kun va undan kam)</b>',
        'safe': '🔵 <b>MUDDATI XAVFSIZ\n(30 kundan ortiq)</b>',
        'no_data': '❓ <b>MA\'LUMOT YO\'Q</b>'
    }

    header = category_names.get(category, category.upper())

    return _(
        "{header}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👥 <b>Jami: <i>{total}</i> ta</b> ┃ 📄 <b>Sahifa: <i>{page}/{total_pages}</i></b>\n\n"
    ).format(header=header, total=total_items, page=page, total_pages=total_pages)


def exam_search_footer_text(count: int) -> str:
    """Qidiruv natijalarining pastki qismi uchun matn"""
    return _(
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Topildi: <i>{count}</i> ta</b>  ┃  ").format(count=count)


def get_category_empty_text(category: str) -> str:
    """Bo'sh kategoriya matni"""
    category_names = {
        'overdue': 'muddati o\'tgan',
        'urgent': 'muddati juda yaqin',
        'warning': 'muddati yaqinlashgan',
        'normal': 'muddati kamaygan',
        'safe': 'muddati xavfsiz',
        'no_data': 'ma\'lumoti yo\'q'
    }

    name = category_names.get(category, category)
    return _("❌ Hozircha {name} xodimlar yo'q").format(name=name)


def format_users_list(users_list, category: str) -> str:
    """Userlar ro'yxatini formatlash"""
    text = ""

    for i, user_info in enumerate(users_list, 1):
        user = user_info['user']
        days_left = user_info['days_left']

        if category == "no_data":
            text += _("<b>{i}. {name}</b>\n   📞 <i>+{phone}</i>\n   ❓ Ma'lumot kiritilmagan\n\n").format(
                i=i, name=user.full_name, phone=user.phone_number
            )
        elif category == "overdue":
            days_overdue = abs(days_left)
            text += _("<b>{i}. {name}</b>\n   📞 <i>+{phone}</i>\n   ⛔ {days} kun kechikkan\n\n").format(
                i=i, name=user.full_name, phone=user.phone_number, days=days_overdue
            )
        else:
            emoji_map = {
                'urgent': '🔴',
                'warning': '🟡',
                'normal': '🟢',
                'safe': '🔵'
            }
            emoji = emoji_map.get(category, '📅')

            text += _("<b>{i}. {name}</b>\n   📞 <i>+{phone}</i>\n   {emoji} {days} kun qoldi\n\n").format(
                i=i, name=user.full_name, phone=user.phone_number, emoji=emoji, days=days_left
            )

    return text


# ------------------------- Qidiruv funksiyalari uchun matnlar -------------------------

def exam_search_prompt_text() -> str:
    """Qidiruv uchun prompt text"""
    return _(
        "🔍 <b>Foydalanuvchini qidirish</b>\n\n"
        "📌 Qidirish uchun foydalanuvchining Ismini yoki Familyasini kiriting.\n"
        "👉 Masalan: <code>Alisher</code> yoki <code>Maxsetov</code>\n\n"
        "<b><i>Kamida 2 ta harf kiriting.</i></b>"
    )


def exam_search_too_short_text() -> str:
    """Qidiruv so'zi juda qisqa bo'lganda"""
    return _(
        "❌ <b>Xatolik. Qidiruv so'zi juda qisqa!</b>\n\n"
        "<b><i>Kamida 2 ta harf kiriting.</i></b>"
    )


def exam_search_no_results_text(query: str) -> str:
    """Qidiruv natijasi topilmaganda"""
    return _(
        "❌ <b>Hech narsa topilmadi!</b>\n\n"
        "☹️ <code>{query}</code> - bo'yicha hech qanday foydalanuvchi topilmadi.\n\n"
        "🔁 <b><i>Boshqa nom bilan qidirib ko'ring.</i></b>"
    ).format(query=query)


def exam_search_results_header_text(query: str, count: int) -> str:
    """Qidiruv natijalari header"""
    return _(
        "🔍 <b>Qidiruv natijalari:</b> <code>{query}</code>\n\n"
        "📋 <b>Topildi: <i>{count}</i> ta</b>  ┃  "
    ).format(query=query, count=count)


def exam_search_pagination_text(page: int, total_pages: int) -> str:
    """Qidiruv sahifa ko'rsatkichi"""
    if total_pages > 1:
        return _("📄 <b>Sahifa: <i>{page}/{total_pages}</i></b>\n").format(page=page, total_pages=total_pages)
    return ""


def exam_search_divider() -> str:
    """Qidiruv uchun ajratuvchi chiziq"""
    return "━━━━━━━━━━━━━━━━━━━━\n"


def format_search_user_result(index: int, user, exam_schedule, today) -> str:
    """Search natijasida bitta userning ma'lumotini formatlash"""
    from bot.utils.date_helpers import get_next_exam_friday
    from bot.utils.exam_helpers import get_exam_status

    if exam_schedule:
        next_exam = get_next_exam_friday(exam_schedule.last_exam)
        days_left = (next_exam.date() - today).days
        status_icon, status_text = get_exam_status(days_left)

        return _(
            "<b>{index}.</b> {status_icon} <b>{full_name}</b>\n"
            "    📞 <i>+{phone_number}</i>\n"
            "    📅 <b>Imtihon:</b> {next_exam_date} "
            "({days_count} kun {status})\n\n"
        ).format(
            index=index,
            status_icon=status_icon,
            full_name=user.full_name,
            phone_number=user.phone_number,
            next_exam_date=next_exam.strftime('%d.%m.%Y'),
            days_count=abs(days_left),
            status='qoldi' if days_left >= 0 else 'o\'tdi'
        )
    else:
        return _(
            "{index}. ❓ <b>{full_name}</b>\n"
            "    📞 <i>+{phone_number}</i>\n"
            "   📅 Ma'lumot yo'q\n\n"
        ).format(
            index=index,
            full_name=user.full_name,
            phone_number=user.phone_number
        )


# ============================ accident_handler ============================

def accident_loading_text() -> str:
    """Loading text"""
    return "..."


def accident_error_text() -> str:
    """General error text"""
    return _(
        "❌ <b>Hozircha hech qanday Ma'lumot topilmadi.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    )


def accident_file_error_text() -> str:
    """File sending error"""
    return _(
        "❌ <b>Faylni yuborishda xatolik yuz berdi.</b>\n"
        "🙏 <i>Iltimos, Admin bilan bog'laning.</i>"
    )


def accident_main_text() -> str:
    """Baxtsiz hodisalar asosiy menyu"""
    return _(
        "⚠️ <b>BAXTSIZ HODISALAR BO'LIMI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "📆 <b>Quyidagi yillardan birini tanlang:</b>\n"
        "ℹ️ <i>(qavsda shu yildagi malumotlar soni)</i>\n"
    )


def accident_no_years_text() -> str:
    """Yillar yo'q"""
    return _(
        "❌ <b>Hozircha hech qanday Baxtsiz Hodisa ma'lumotlari mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    )


def accident_year_header_text(year_name: str, total: int, page: int, total_pages: int) -> str:
    """Yil bo'yicha hodisalar header"""
    text = _(
        "📆 <b>{year_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔢 <b>Jami malumotlar soni:</b> <i>{total}</i> <b>ta</b>"
    ).format(year_name=year_name.upper(), total=total)

    if total_pages > 1:
        text += _(" ┃ 📄 <b>Sahifa:</b> <i>{page}/{total_pages}</i>").format(
            page=page,
            total_pages=total_pages
        )

    text += _("\n\n📋 Batafsil ma'lumot uchun tanlang:")

    return text


def accident_no_accidents_text(year_name: str) -> str:
    """Yilda hodisa yo'q"""
    return _(
        "📆 <b>{year_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ <b>Hozircha bu bo'limdagi baxtsiz hodisalar ma'lumotlari mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    ).format(year_name=year_name.upper())


def accident_detail_text(title: str, year: str, category: str, description: str = None) -> str:
    """Accident detail text (separate message)"""
    text = _(
        "📋 <b>{title}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📆 <b>Yil:</b> {year}\n"
        "📂 <b>Kategoriya:</b> {category}"
    ).format(title=title, year=year, category=category)

    if description:
        text += _("\n📝 <b>Tavsif:</b> {description}").format(description=description)

    return text


def accident_statistics_main_text(category_stats: List[Tuple], year_stats: List[Tuple]) -> str:
    """Umumiy statistika teksti (Xisobat kategoriyasi chiqarilgan)"""
    text = _(
        "📊 <b>UMUMIY STATISTIKA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # Jami hodisalar (Xisobat kategoriyasiz)
    total = sum(stat.count for stat in category_stats)
    text += _("📈 <b>Jami Baxtsiz Hodisalar:</b> <i>{total}</i> <b>ta</b>\n").format(total=total)
    text += _("ℹ️ <i>(Xisobat hujjatlari hisobga olinmagan)</i>\n\n")

    # Yillar bo'yicha trend (oxirgi 5 yil)
    if year_stats and len(year_stats) >= 1:
        text += _("📅 <b>Yillik dinamika:</b>\n")
        text += "━━━━━━━━━━━━━━━━━━━━\n"

        # Sort years by year number for proper comparison
        sorted_years = sorted(year_stats, key=lambda x: _extract_year_number(x.name), reverse=True)

        for i, stat in enumerate(sorted_years[:5]):  # Show only last 5 years
            current_year_num = _extract_year_number(stat.name)

            # Display current year
            text += _("🔹 <b>{name} - Baxtsiz hodisalar soni:</b> <i>{count}</i> <b>ta</b>").format(
                name=stat.name,
                count=stat.count
            )

            # Find previous year for comparison (year before current)
            prev_year_data = None
            for prev_stat in sorted_years:
                prev_year_num = _extract_year_number(prev_stat.name)
                if prev_year_num == current_year_num - 1:  # Previous year
                    prev_year_data = prev_stat
                    break

            if prev_year_data and prev_year_data.count > 0:
                # Calculate change (current - previous)
                change_abs = stat.count - prev_year_data.count
                change_percent = (change_abs / prev_year_data.count * 100)

                prev_year_short = str(current_year_num - 1) + " yil"

                if change_abs > 0:
                    emoji = "📈"
                    text += _(
                        "\n{emoji} <b>{prev_year} ga Nisbatan:</b>\n"
                        "      <i>+{change_abs}</i> <b>taga yani</b> <i>(+{change_percent:.1f}%)</i> <b>ga oshgan</b>"
                    ).format(
                        emoji=emoji,
                        prev_year=prev_year_short,
                        change_abs=change_abs,
                        change_percent=change_percent
                    )
                elif change_abs < 0:
                    emoji = "📉"
                    text += _(
                        "\n{emoji} <b>{prev_year} ga Nisbatan:</b>\n"
                        "      <i>{change_abs}</i> <b>taga yani</b> <i>({change_percent:.1f}%)</i> <b>ga kamaygan</b>"
                    ).format(
                        emoji=emoji,
                        prev_year=prev_year_short,
                        change_abs=change_abs,
                        change_percent=change_percent
                    )
                else:
                    emoji = "➡️"
                    text += _("\n{emoji} <b>{prev_year} ga Nisbatan o'zgarmagan</b>").format(
                        emoji=emoji,
                        prev_year=prev_year_short
                    )

            # Add separator line after each year (except last)
            if i < len(sorted_years[:5]) - 1:
                text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            else:
                text += "\n"

    return text


def accident_statistics_year_text(year_name: str, total: int, category_stats: List[Tuple]) -> str:
    """Yil bo'yicha statistika (Xisobat kategoriyasiz)"""
    text = _(
        "📊 <b>{year_name} STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📈 <b>Jami Baxtsiz Hodisalar soni:</b> <i>{total}</i> <b>ta</b>\n"
        "ℹ️ <i>(Xisobat hujjatlari hisobga olinmagan)</i>\n\n"
    ).format(year_name=year_name.upper(), total=total)

    if category_stats and total > 0:
        text += _("📂 <b>Kategoriyalar bo'yicha taqsimot:</b>\n")
        text += "━━━━━━━━━━━━━━━━━━━━\n"

        for stat in category_stats:
            percentage = (stat.count / total * 100) if total > 0 else 0

            # Progress bar
            filled = int(percentage / 5)
            empty = 20 - filled
            progress_bar = "█" * filled + "░" * empty

            text += _(
                "🔹 <b>{name}</b>\n"
                "      {progress} {percentage:.1f}%\n"
                "      Baxtsiz hodisalar soni: <b>{count} ta</b>\n\n"
            ).format(
                name=stat.name,
                progress=progress_bar,
                percentage=percentage,
                count=stat.count
            )
    else:
        text += _("❌ <i>Bu yilda baxtsiz hodisalar qayd etilmagan</i>")

    return text


def accident_no_statistics_text() -> str:
    """Ma'lumot yo'q statistika"""
    return _(
        "📊 <b>UMUMIY STATISTIKA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ <b>Hozircha statistika ma'lumotlari mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi"
    )


def _extract_year_number(year_name: str) -> int:
    """Extract year number from year name for sorting"""
    match = re.search(r'(\d{4})', year_name)
    return int(match.group(1)) if match else 0


# ============================ ai_assistant_handler ============================
# bot/utils/texts.py - AI Assistant yangilangan qismi

def ai_timeout_text() -> str:
    """AI timeout text"""
    return _(
        "⏰ <b>AI xizmati javob bermadi</b>\n\n"
        "🔄 <i>Qayta urinib ko'ring</i>\n"
        "⚡ <i>Yoki boshqa savol bering</i>\n\n"
        "💡 <i>Ba'zan murakkab savollar ko'proq vaqt talab qiladi</i>"
    )


def ai_processing_long_text() -> str:
    """Long processing text"""
    return _(
        "🤖 <b>Murakkab savol...</b>\n\n"
        "⏳ <i>Bir oz ko'proq vaqt ketishi mumkin</i>\n"
        "🧠 <i>AI chuqur o'ylayapti</i>\n\n"
        "⌛ <i>Iltimos, sabr qiling...</i>"
    )


def ai_welcome_text(user=None) -> str:
    """AI assistant welcome text"""
    user_info = ""
    if user:
        user_info = (
            f"👤 <b>Foydalanuvchi: </b> <i>{user.full_name}\n</i>"
            f"📞 <b>Telefon: </b> <i>{user.phone_number}\n\n</i>"
        )

    return _(
        "🤖 <b>AI YORDAMCHI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "{user_info}"
        "💬 <b>Savollaringizni Matn shaklida yuboring!</b>\n"
        "🤖 <b>Sun'iy intellekt sizga javob beradi</b>\n\n"
        "💭 <b>Menga istalgan savolingizni bering:</b>\n"
        "• 🚆 Transport va turizm\n"
        "• 📚 Ta'lim va fan\n"
        "• 💼 Ish va biznes\n"
        "• 🏥 Sog'liq va tibbiyot\n"
        "• 💻 Texnologiya\n"
        "• 🎨 San'at va madaniyat\n"
        "• 🌍 Sayohat va geografiya\n"
        "• ⚡ Va boshqa mavzular...\n\n"
        "🔄 <b>AI xizmatlari:</b> \nGoogle Gemini + Groq + Together\n\n"
        "💬 <i>Savolingizni yuboring ⬇️</i>"
    ).format(user_info=user_info)


def ai_waiting_text() -> str:
    """AI processing text"""
    return _(
        "🤖 <b>AI javob tayyorlamoqda...</b>\n\n"
        "⏳ <i>Iltimos, bir oz sabr qiling</i>\n"
        "🔄 <i>Eng yaxshi javobni izlamoqdamiz</i>"
    )


def ai_response_text(ai_response: str, service_used: str = None) -> str:
    """Format AI response"""
    text = (f"🤖 <b>AI Javobi:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{ai_response}"
            )

    text += "\n\n💡 <i>Qo'shimcha ma'lumot kerakmi? Batafsil so'rang!</i>"

    if service_used:
        text += f"\n<i>📡 {service_used} orqali</i>"

    text += "\n\n💬 <b>Yana savol bering!</b>"

    return text


def ai_error_text() -> str:
    """AI error text"""
    return _(
        "❌ <b>Xatolik yuz berdi</b>\n\n"
        "🔄 <i>Iltimos, qayta urinib ko'ring</i>\n"
        "⏰ <i>Yoki bir oz kuting va qayta yuboring</i>\n\n"
        "💡 <b>Agar muammo davom etsa:</b>\n"
        "• Internetni tekshiring\n"
        "• Botni qayta ishga tushiring"
    )


def ai_limit_text(limit_message: str) -> str:
    """AI rate limit text"""
    return _(
        "⏰ <b>Limit tugadi</b>\n\n"
        "📊 <b>{limit_message}</b>\n\n"
        "🕐 <b>Nima qilish kerak:</b>\n"
        "• Biroz kuting va qayta urinib ko'ring\n"
        "• Limitlar har soat yangilanadi\n"
        "• Ertaga yangi limitlar beriladi\n\n"
        "💡 <i>Bu sizning xavfsizligingiz uchun</i>"
    ).format(limit_message=limit_message)


def ai_no_services_text() -> str:
    """No AI services available"""
    return _(
        "❌ <b>Barcha AI xizmatlar band</b>\n\n"
        "⏰ <i>Hozirda barcha AI xizmatlar limitga yetdi</i>\n\n"
        "🕐 <b>Nima qilish kerak:</b>\n"
        "• 1 soat kuting\n"
        "• Qayta urinib ko'ring\n"
        "• Ertaga yangi limitlar beriladi\n\n"
        "💡 <i>Bu vaqtinchalik holat</i>"
    )


def ai_limits_status_text(user_hour: int, user_day: int, google_hour: int, google_day: int,
                         groq_hour: int, groq_day: int, together_hour: int, together_day: int,
                         max_hour: int, max_day: int) -> str:
    """Show AI limits status with Together.ai"""
    return _(
        "📊 <b>SIZNING LIMITLARINGIZ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 <b>Shaxsiy limitlar:</b>\n"
        "🕐 Soatlik: <b>{user_hour}/{max_hour}</b> ta so'rov\n"
        "📆 Kunlik: <b>{user_day}/{max_day}</b> ta so'rov\n\n"
        "🤖 <b>AI xizmatlar holati:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🟢 <b>Google Gemini:</b> (Tekin)\n"
        "   🕐 Soatlik: <b>{google_hour}/100</b> ta\n"
        "   📆 Kunlik: <b>{google_day}/1000</b> ta\n\n"
        "🟠 <b>Groq AI:</b> (Tekin)\n"
        "   🕐 Soatlik: <b>{groq_hour}/200</b> ta\n"
        "   📆 Kunlik: <b>{groq_day}/2000</b> ta\n\n"
        "🔵 <b>Together:</b>\n"
        "   🕐 Soatlik: <b>{together_hour}/30</b> ta\n"
        "   📆 Kunlik: <b>{together_day}/300</b> ta\n\n"
        "⚡ <b>Prioritet:</b> Google → Groq → Together\n"
        "🔄 <i>Limitlar har soat yangilanadi</i>\n"
        "⏰ <i>Kunlik limitlar yarim tunda yangilanadi</i>"
    ).format(
        user_hour=user_hour,
        user_day=user_day,
        max_hour=max_hour,
        max_day=max_day,
        google_hour=google_hour,
        google_day=google_day,
        groq_hour=groq_hour,
        groq_day=groq_day,
        together_hour=together_hour,
        together_day=together_day
    )


def ai_back_to_chat_text() -> str:
    """Back to chat text"""
    return _(
        "💬 <b>Suhbatga qaytdik</b>\n\n"
        "✅ <i>Endi savolingizni yuboring!</i>\n"
        "🤖 <i>AI sizga javob berishga tayyor</i>"
    )


def ai_other_messages_text() -> str:
    """Handle other message types"""
    return _(
        "❓ <b>Faqat Matn xabar yuboring</b>\n\n"
        "💬 <i>Audio, rasm va boshqa formatlar hozircha qo'llab-quvvatlanmaydi</i>\n"
        "✍️ <i>Savolingizni matn shaklida yozing</i>"
    )


# -------------- INPUT VALIDATION TEXTS --------------

def ai_input_too_long_text() -> str:
    """Input too long error text"""
    return _(
        "❌ <b>Xabar juda uzun!</b>\n\n"
        "📝 <i>Maksimal 1000 belgi ruxsat etiladi</i>\n"
        "✂️ <i>Qisqaroq qilib yuboring</i>"
    )


def ai_input_empty_text() -> str:
    """Empty input error text"""
    return _(
        "❓ <b>Bo'sh xabar!</b>\n\n"
        "💬 <i>Savolingizni yozing</i>"
    )


def ai_input_invalid_text() -> str:
    """Invalid input error text"""
    return _(
        "🤔 <b>To'liq savol yuboring!</b>\n\n"
        "💭 <i>Masalan: \"Python dasturlash nima?\"</i>"
    )


def ai_input_duplicate_text() -> str:
    """Duplicate input error text"""
    return _(
        "🔄 <b>Bu savolni yaqinda berdingiz!</b>\n\n"
        "💡 <i>Boshqa savol bering yoki batafsil so'rang</i>"
    )

# ============================ library_handler ============================

def library_loading_text() -> str:
    """Loading text"""
    return "..."


def library_error_text() -> str:
    """General error text"""
    return _(
        "❌ <b>Xatolik yuz berdi.</b>\n"
        "🙏 <i>Iltimos, qayta urinib ko'ring</i>"
    )


def library_file_error_text() -> str:
    """File sending error"""
    return _(
        "❌ <b>Faylni yuborishda xatolik yuz berdi.</b>\n"
        "🙏 <i>Iltimos, Admin bilan bog'laning.</i>"
    )


def library_main_text() -> str:
    """Kutubxona asosiy menyu"""
    return _(
        "📚 <b>KUTUBXONA BO'LIMI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "📂 <b>Quyidagi bo'limlardan birini tanlang:</b>\n\n"
        "💭 <i>{quote}</i>"
    ).format(quote=get_random_book_quote())


def get_random_book_quote() -> str:
    """Kitoblar haqida buyuk insonlarning aqlli so'zlari"""
    quotes = [
        _("Kitob - eng yaxshi do'st, u hech qachon xiyonat qilmaydi.\n🎓 <b>(Konfutsiy)</b>"),
        _("Kitobsiz hayot - qushsiz osmon kabi.\n🎓 <b>(Ahmad Yugnakiy)</b>"),
        _("Kitob o'qish - ruhni oziqlantirishdir.\n🎓 <b>(Voltaire)</b>"),
        _("Yaxshi kitob mingta do'stdan qimmatroqdir.\n🎓 <b>(Abu Nasr Forobiy)</b>"),
        _("Kitob - bilimning kalidi, bilim esa baxtning siridir.\n🎓 <b>(Alisher Navoiy)</b>"),
        _("O'qish miyani kuchaytiradi, sport tanani.\n🎓 <b>(Jozef Addison)</b>"),
        _("Kitob - dunyo bo'ylab arzon sayohat.\n🎓 <b>(Meri Xart)</b>"),
        _("Bilim - o'g'irlab bo'lmaydigan boylik.\n🎓 <b>(Aristotel)</b>"),
        _("Kitob o'qimagan kishi - ko'r kabi.\n🎓 <b>(Mark Tven)</b>"),
        _("Har bir buyuk inson ortida o'qilgan minglab kitoblar turadi.\n🎓 <b>(Napoleon Bonapart)</b>"),
    ]
    return random.choice(quotes)


def library_no_categories_text() -> str:
    """Kategoriyalar yo'q"""
    return _(
        "❌ <b>Hozircha hech qanday kitob bo'limi mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    )


def library_categories_text(page: int, total_pages: int) -> str:
    """Categories pagination header"""
    text = _(
        "📚 <b>KUTUBXONA KATEGORIYALARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    if total_pages > 1:
        text += _(" 📄 <b>Sahifa:</b> <i>{page}/{total_pages}</i>\n\n").format(
            page=page,
            total_pages=total_pages
        )

    text += _("📂 <b>Kategoriyani tanlang:</b>")

    return text


def library_books_text(category_name: str, total: int, page: int, total_pages: int) -> str:
    """Books list header"""
    text = _(
        "📂 <b>{category_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📚 <b>Jami kitoblar:</b> <i>{total} ta</i>"
    ).format(category_name=category_name.upper(), total=total)

    if total_pages > 1:
        text += _(" ┃ 📄 <b>Sahifa:</b> <i>{page}/{total_pages}</i>").format(
            page=page,
            total_pages=total_pages
        )

    text += _("\n\n📖 <b>Batafsil ma'lumot uchun bitta Kitobni tanlang:</b>")

    return text


def library_no_books_text(category_name: str) -> str:
    """Kategoriyada kitob yo'q"""
    return _(
        "📂 <b>{category_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ <b>Hozircha bu bo'limda Kitoblar mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    ).format(category_name=category_name.upper())


def library_book_detail_text(title: str, category: str, description: str = None) -> str:
    """Book detail text"""
    text = _(
        "📖 <b>{title}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📂 <b>Kategoriya:</b> {category}"
    ).format(title=title, category=category)

    if description:
        text += _("\n\n📝 <b>Tavsif:</b> {description}").format(description=description)

    text += _("\n\n✅ <i>Yuqoridagi faylni ko'rishingiz mumkin</i>")

    return text


def library_statistics_text(total_books: int, category_stats: List[Tuple]) -> str:
    """Kutubxona statistika teksti"""
    text = _(
        "📊 <b>KUTUBXONA STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📚 <b>Jami kitoblar soni:</b> <i>{total} ta</i>\n"
    ).format(total=total_books)

    if category_stats and total_books > 0:
        text += _("📂 <b>Bo'limlar bo'yicha taqsimot:</b>\n")
        text += "━━━━━━━━━━━━━━━━━━━━\n"

        for stat in category_stats:
            if stat.count > 0:  # Only show categories with books
                percentage = (stat.count / total_books * 100) if total_books > 0 else 0

                # Progress bar
                filled = int(percentage / 5)
                empty = 20 - filled
                progress_bar = "█" * filled + "░" * empty

                text += _(
                    "\n🔹 <b>{name}</b>\n"
                    "      {progress} {percentage:.1f}%\n"
                    "      <i>Kitoblar soni: {count} ta</i>\n"
                ).format(
                    name=stat.name,
                    progress=progress_bar,
                    percentage=percentage,
                    count=stat.count
                )

    return text


def library_no_statistics_text() -> str:
    """Ma'lumot yo'q statistika"""
    return _(
        "📊 <b>KUTUBXONA STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ <b>Hozircha Statistika ma'lumotlari mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi"
    )


def main_menu_text() -> str:
    """Asosiy menyu texti"""
    return _("🏠 <b>Asosiy Menyu</b>")



# ============================ video_handler ============================

def video_main_text() -> str:
    """Video roliklar asosiy menyu"""
    return _(
        "🎥 <b>VIDEO MATERIALLAR BO'LIMI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "📂 <b>Quyidagi bo'limlardan birini tanlang:</b>"
    )


def video_no_categories_text() -> str:
    """Kategoriyalar yo'q"""
    return _(
        "❌ <b>Hozircha hech qanday Video bo'limi mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    )


def video_categories_text(page: int, total_pages: int) -> str:
    """Categories pagination header"""
    text = _(
        "🎥 <b>VIDEO KATEGORIYALARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    if total_pages > 1:
        text += _(" 📄 <b>Sahifa:</b> <i>{page}/{total_pages}</i>\n\n").format(
            page=page,
            total_pages=total_pages
        )

    text += _("📂 <b>Kategoriyani tanlang:</b>")

    return text


def video_list_text(category_name: str, total: int, page: int, total_pages: int) -> str:
    """Videos list header"""
    text = _(
        "📂 <b>{category_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎬 <b>Jami videolar:</b> <i>{total} ta</i>"
    ).format(category_name=category_name.upper(), total=total)

    if total_pages > 1:
        text += _(" ┃ 📄 <b>Sahifa:</b> <i>{page}/{total_pages}</i>").format(
            page=page,
            total_pages=total_pages
        )

    text += _("\n\n🎥 <b>Ko'rish uchun Videoni tanlang:</b>")

    return text


def video_no_videos_text(category_name: str) -> str:
    """Kategoriyada video yo'q"""
    return _(
        "📂 <b>{category_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ <b>Hozircha bu bo'limda Videolar mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi\n\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    ).format(category_name=category_name.upper())


def video_detail_text(title: str, category: str, description: str = None) -> str:
    """Video detail text"""
    text = _(
        "🎬 <b>{title}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📂 <b>Kategoriya:</b> {category}"
    ).format(title=title, category=category)

    if description:
        text += _("\n\n📝 <b>Tavsif:</b> {description}").format(description=description)

    text += _("\n\n✅ <i>Yuqorida Videoni ko'rishingiz mumkin</i>")

    return text


def video_statistics_text(total_videos: int, category_stats: List[Tuple]) -> str:
    """Video statistika teksti"""
    text = _(
        "📊 <b>VIDEO MATERIALLAR STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎬 <b>Jami videolar soni:</b> <i>{total} ta</i>\n"
    ).format(total=total_videos)

    if category_stats and total_videos > 0:
        text += _("📂 <b>Bo'limlar bo'yicha taqsimot:</b>\n")
        text += "━━━━━━━━━━━━━━━━━━━━\n"

        for stat in category_stats:
            if stat.count > 0:  # Only show categories with videos
                percentage = (stat.count / total_videos * 100) if total_videos > 0 else 0

                # Progress bar
                filled = int(percentage / 5)
                empty = 20 - filled
                progress_bar = "█" * filled + "░" * empty

                text += _(
                    "\n🔹 <b>{name}</b>\n"
                    "      {progress} {percentage:.1f}%\n"
                    "      <i>Videolar soni: {count} ta</i>\n"
                ).format(
                    name=stat.name,
                    progress=progress_bar,
                    percentage=percentage,
                    count=stat.count
                )

    return text


def video_no_statistics_text() -> str:
    """Ma'lumot yo'q statistika"""
    return _(
        "📊 <b>VIDEO MATERIALLAR STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ <b>Hozircha statistika ma'lumotlari mavjud emas.</b>\n"
        "📥 Tez orada ma'lumotlar qo'shiladi"
    )


def video_error_text() -> str:
    """General error text"""
    return _(
        "❌ <b>Xatolik yuz berdi.</b>\n"
        "🙏 <i>Iltimos, qayta urinib ko'ring</i>"
    )


def video_file_error_text() -> str:
    """Video file sending error"""
    return _(
        "❌ <b>Videoni yuborishda xatolik yuz berdi.</b>\n"
        "🙏 <i>Iltimos, Admin bilan bog'laning.</i>"
    )


# ============================ company_handler ============================

def company_info_text(name: str, description: str) -> str:
    """Kompaniya asosiy ma'lumoti (tugmalarsiz)"""
    return (
        f"🏢 <b>{name.upper()}</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        f"📝 {description}\n"
    )


def company_presentation_with_contact_text() -> str:
    """Prezentatsiya fayli + kontakt ma'lumoti"""
    return _(
        "👆 <b>Ko'proq ma'lumot olish uchun</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 <b>Savol yoki takliflaringiz bo'lsa murojat qiling:</b>"
    )


def company_no_data_text() -> str:
    """Ma'lumot yo'q holati"""
    return _(
        "❌ <b>Hozircha Korxona ma'lumotlari kiritilmagan</b>\n\n"
        "📥 <i>Tez orada ma'lumotlar qo'shiladi</i>\n"
        "🙏 <i>Iltimos, keyinroq qayta urinib ko'ring</i>"
    )


def company_no_contact_text() -> str:
    """Prezentatsiya yo'q, faqat kontakt"""
    return _("📞 <b>Savol yoki takliflaringiz bo'lsa admin bilan bog'laning:</b>")


def company_presentation_error_with_contact_text() -> str:
    """Prezentatsiya xatolik + kontakt"""
    return _(
        "⚠️ <b>Prezentatsiya faylini yuborishda xatolik yuz berdi</b>\n\n"
        "🔄 <i>Iltimos, keyinroq qayta urinib ko'ring</i>\n\n"
        "📞 <b>Savol yoki takliflaringiz bo'lsa admin bilan bog'laning:</b>"
    )


# ============================ train_handler ============================

# bot/utils/texts.py da qo'shish
def train_safety_main_text() -> str:
    """Poezdlar harakat xavfsizligi asosiy sahifa"""
    return _(
        "🚆 <b>POEZDLAR HARAKAT XAVFSIZLIGI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "📂 <i>Kerakli bo'limni tanlang:</i>"
    )

def train_safety_no_folders_text() -> str:
    """Papkalar mavjud emas"""
    return _(
        "🚆 <b>POEZDLAR HARAKAT XAVFSIZLIGI</b>\n"
        "➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        "❌ <b>Hozircha bo'limlar mavjud emas</b>\n"
        "📥 <i>Tez orada ma'lumotlar qo'shiladi</i>\n"
        "🔄 <i>Keyinroq qayta urinib ko'ring</i>"
    )

def train_safety_folder_files_text(folder_name: str, description: str = None, files_count: int = 0) -> str:
    """Papka ichidagi fayllar"""
    desc_text = f"📝 {description}\n\n" if description else ""

    if files_count == 0:
        return _(
            "📂 <b>{folder_name}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "{description}"
            "❌ <b>Bu bo'limda hozircha hujjatlar mavjud emas</b>\n"
            "📥 <i>Tez orada ma'lumotlar qo'shiladi</i>"
        ).format(
            folder_name=folder_name.upper(),
            description=desc_text
        )

    return _(
        "📂 <b>{folder_name}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📄 <b>Jami hujjatlar:</b> <i>{files_count} ta</i>\n\n"
        "{description}"
        "📄 <b>Kerakli hujjatni tanlang:</b>"
    ).format(
        folder_name=folder_name.upper(),
        files_count=files_count,
        description=desc_text
    )

def train_safety_file_info_text(folder_name: str, file_name: str, description: str = None) -> str:
    """Fayl haqida ma'lumot"""
    desc_text = f"📝 <b>Tavsif:</b> {description}\n\n" if description else ""

    return _(
        "📂 <b>Bo'lim:</b> {folder_name}\n"
        "📄 <b>Hujjat:</b> {file_name}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "{description}\n"
        "✅ <i>Yuqoridagi hujjatni ko'rishingiz mumkin</i>"
    ).format(
        folder_name=folder_name,
        file_name=file_name,
        description=desc_text
    )

def train_safety_file_error_text(file_name: str, folder_name: str) -> str:
    """Fayl yuborishda xatolik"""
    return _(
        "⚠️ <b>Hujjatni yuborishda xatolik!</b>\n\n"
        "📄 <b>Hujjat:</b> {file_name}\n"
        "📂 <b>Bo'lim:</b> {folder_name}\n\n"
        "🔄 <i>Keyinroq qayta urinib ko'ring yoki admin bilan bog'laning</i>"
    ).format(
        file_name=file_name,
        folder_name=folder_name
    )

def train_safety_error_text() -> str:
    """General error text"""
    return _(
        "❌ <b>Xatolik yuz berdi.</b>\n"
        "🙏 <i>Iltimos, qayta urinib ko'ring</i>"
    )