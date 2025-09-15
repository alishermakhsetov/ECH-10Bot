from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Video
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from typing import List

from bot.utils.constants import ANSWER_LETTERS
from db.models import CategoryTest, AnswerTest, DepartmentSafety, AreaSafety, FacilitySafety, EquipmentSafety, \
    CategoryBook, Book, CategoryVideo, Channel
from datetime import datetime, timezone
from db.models import AccidentYear, Accident


def channel_join_keyboard(channels: List[Channel]) -> InlineKeyboardMarkup:
    """Guruh/kanallarga qo'shilish uchun inline tugmalar"""
    builder = InlineKeyboardBuilder()

    for channel in channels:
        if channel.link:  # Link mavjud bo'lsa
            # Emoji tanlash
            emoji = "🏢" if "guruh" in channel.title.lower() else "📢"

            builder.button(
                text=f"{emoji} {channel.title or 'Guruh/Kanal'}",
                url=channel.link
            )

    builder.adjust(1)  # Har qatorda 1 tadan tugma
    return builder.as_markup()

# -------------------- 🧠 Test keyboards --------------------

def test_category_keyboard(categories: List[CategoryTest]) -> InlineKeyboardMarkup:
    """
    Test kategoriyalari uchun tugmalarni yaratadi.
    """
    builder = InlineKeyboardBuilder()

    # Kategoriyalar (2 tadan har qatorda)
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"test_category:{category.id}"
        )

    builder.adjust(2)  # har qatorda 2 tadan tugma

    # Asosiy menyu tugmasini alohida qator qilish
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="main_menu"
        )
    )

    return builder.as_markup()


def answer_keyboard(answers: List[AnswerTest], question_id: int) -> InlineKeyboardMarkup:
    """
    Test savoli uchun javob variantlari tugmalari.
    Faqat A, B, C, D harflarni ko'rsatadi.
    """
    buttons = []
    row = []

    for i in range(min(len(answers), 4)):  # Maksimum 4 ta javob
        button = InlineKeyboardButton(
            text=ANSWER_LETTERS[i],
            callback_data=f"answer:{question_id}:{answers[i].id}"
        )
        row.append(button)

    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def disable_answer_keyboard(answers: List[AnswerTest], question_id: int, selected_id: int,
                            correct_id: int) -> InlineKeyboardMarkup:
    """
    Javob tanlangandan yoki vaqt tugagandan keyin — tugmalarni faolligini o'chiradi.
    """
    buttons = []
    row = []

    for i in range(min(len(answers), 4)):  # Maksimum 4 ta javob
        letter = ANSWER_LETTERS[i]

        if answers[i].id == correct_id:
            text = f"✅ {letter}"
        elif answers[i].id == selected_id and selected_id != correct_id:
            text = f"❌ {letter}"
        else:
            text = letter

        button = InlineKeyboardButton(
            text=text,
            callback_data="disabled"
        )
        row.append(button)

    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def result_with_next_question_keyboard(answers: List[AnswerTest], question_id: int,
                                       selected_id: int, correct_id: int,
                                       result_text: str) -> InlineKeyboardMarkup:
    """
    Rasmli savollar uchun: Natija + javob tugmalari (3 soniya kutishdan keyin keyingi savol).
    """
    buttons = []

    # Tepada natija tugmasi
    buttons.append([
        InlineKeyboardButton(text=result_text, callback_data="disabled")
    ])

    # O'rtada javob tugmalari (3 soniyadan keyin bu o'rnida "Keyingi savol" chiqadi)
    answer_row = []
    for i in range(min(len(answers), 4)):
        letter = ANSWER_LETTERS[i]

        if answers[i].id == correct_id:
            text = f"✅ {letter}"
        elif answers[i].id == selected_id and selected_id != correct_id:
            text = f"❌ {letter}"
        else:
            text = letter

        button = InlineKeyboardButton(text=text, callback_data="disabled")
        answer_row.append(button)

    buttons.append(answer_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def result_with_only_next_question_keyboard(result_text: str) -> InlineKeyboardMarkup:
    """
    Rasmli savollar uchun: Natija + keyingi savol tugmasi (javoblar o'rnida).
    """
    buttons = []

    # Tepada natija tugmasi
    buttons.append([
        InlineKeyboardButton(text=result_text, callback_data="disabled")
    ])

    # O'rtada keyingi savol tugmasi (A,B,C,D o'rnida)
    buttons.append([
        InlineKeyboardButton(text=_("👉 Keyingi savol"), callback_data="next_question")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timeout_result_keyboard(answers: List[AnswerTest], question_id: int,
                            selected_id: int, correct_id: int) -> InlineKeyboardMarkup:
    """
    Rasmli savollar uchun vaqt tugaganda: Vaqt tugadi + to'g'ri javob ko'rsatish.
    """
    buttons = []

    # Tepada "Vaqt tugadi!" tugmasi
    buttons.append([
        InlineKeyboardButton(text=_("⏰ Vaqt tugadi!"), callback_data="disabled")
    ])

    # O'rtada javob tugmalari (faqat to'g'ri javob belgilanadi)
    answer_row = []
    for i in range(min(len(answers), 4)):
        letter = ANSWER_LETTERS[i]

        if answers[i].id == correct_id:
            text = f"✅ {letter}"
        else:
            text = letter

        button = InlineKeyboardButton(text=text, callback_data="disabled")
        answer_row.append(button)

    buttons.append(answer_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timeout_with_next_question_keyboard() -> InlineKeyboardMarkup:
    """
    Rasmli savollar uchun vaqt tugaganda keyingi savol tugmasi.
    """
    buttons = []

    # Tepada "Vaqt tugadi!" tugmasi
    buttons.append([
        InlineKeyboardButton(text=_("⏰ Vaqt tugadi!"), callback_data="disabled")
    ])

    # O'rtada keyingi savol tugmasi
    buttons.append([
        InlineKeyboardButton(text=_("👉 Keyingi savol"), callback_data="next_question")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

    buttons = []

    # Tepada natija tugmasi
    buttons.append([
        InlineKeyboardButton(text=result_text, callback_data="disabled")
    ])

    # O'rtada keyingi savol tugmasi (A,B,C,D o'rnida)
    buttons.append([
        InlineKeyboardButton(text=_("👉 Keyingi savol"), callback_data="next_question")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def next_question_keyboard() -> InlineKeyboardMarkup:
    """
    "Keyingisi" tugmasi — foydalanuvchi keyingi savolga o'tishi uchun.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("👉 Keyingi savol"), callback_data="next_question")]
    ])


def back_to_categories_keyboard() -> InlineKeyboardMarkup:
    """
    "Orqaga" va "Asosiy menyu" tugmalari yonma-yon chiqadi.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=_("↩️ Orqaga"), callback_data="back_to_categories"),
            InlineKeyboardButton(text=_("🏠 Asosiy Menyu"), callback_data="main_menu")
        ]
    ])


def test_result_keyboard(score: int, total: int) -> InlineKeyboardMarkup:
    """
    Test yakunlangandan keyin natijalar tugmalari.
    """
    percentage = round((score / total) * 100, 1) if total > 0 else 0
    buttons = []

    if percentage >= 70:
        # Tarjima qilingan ulashish matni
        share_text = _(
            "📢 Men Test topshirdim:\n"
            "✅ Natija: {score}/{total}\n"
            "📈 Foiz: {percentage}%\n\n"
            "🎯 Siz ham bilim darajangizni tekshirib ko'ring:"
        ).format(score=score, total=total, percentage=percentage)

        buttons.append([
            InlineKeyboardButton(
                text=_("📤 Natijani ulashish"),
                switch_inline_query=share_text
            )
        ])

    buttons.append([
        InlineKeyboardButton(text=_("🔄 Qayta Test"), callback_data="back_to_categories")
    ])
    buttons.append([
        InlineKeyboardButton(text=_("🏠 Asosiy Menyu"), callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# -------------------- 🦺 Safety Equipment keyboards --------------------

def safety_department_keyboard(departments: List[DepartmentSafety]) -> InlineKeyboardMarkup:
    """Himoya vositalari department'lari uchun tugmalar."""
    builder = InlineKeyboardBuilder()

    # Department'lar (2 tadan har qatorda)
    for dept in departments:
        builder.button(
            text=f"🏢 {dept.name}",
            callback_data=f"safety_dept:{dept.id}"
        )

    builder.adjust(2)  # har qatorda 2 ta tugma

    # Asosiy menyu tugmasi
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="safety_main_menu"
        )
    )

    return builder.as_markup()



def safety_area_keyboard(areas: List[AreaSafety], department_id: int) -> InlineKeyboardMarkup:
    """Department ichidagi area'lar uchun tugmalar."""
    builder = InlineKeyboardBuilder()

    for area in areas:
        builder.button(
            text=f"📍 {area.name}",
            callback_data=f"safety_area:{department_id}:{area.id}"
        )

    builder.adjust(2)  # Har bir qatorga 2 ta tugma

    # Statistika tugmasi alohida qatorda
    builder.row(
        InlineKeyboardButton(
            text=_("📊 Statistika"),
            callback_data=f"safety_statistics:{department_id}"
        )
    )

    # Orqaga va asosiy menyu tugmalari
    builder.row(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="back_to_departments"
        ),
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="safety_main_menu"
        )
    )

    return builder.as_markup()


def safety_facility_keyboard(
        facilities: List[FacilitySafety],
        department_id: int,
        area_id: int
) -> InlineKeyboardMarkup:
    """Area ichidagi facility'lar uchun tugmalar."""
    builder = InlineKeyboardBuilder()

    # Facility'lar (1 tadan har qatorda - to'liq nom ko'rinishi uchun)
    for facility in facilities:
        emoji = "🏛️"
        builder.button(
            text=f"{emoji} {facility.name}",
            callback_data=f"safety_facility:{department_id}:{area_id}:{facility.id}"
        )

    builder.adjust(2)

    # Orqaga va asosiy menyu tugmalari HAR DOIM ko'rsatiladi
    builder.row(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data=f"back_to_areas:{department_id}"
        ),
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="safety_main_menu"
        )
    )

    return builder.as_markup()


def safety_equipment_keyboard(
        equipment_items: List[EquipmentSafety],
        department_id: int,
        area_id: int,
        facility_id: int,
        page: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Sahifa sozlamalari
    items_per_page = 10
    total_items = len(equipment_items)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    # Hozirgi sahifa uchun equipment'larni olish
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_items = equipment_items[start_idx:end_idx]

    MAX_LENGTH = 28  # Emoji + space uchun joy qoldiramiz

    for item in current_items:
        # Muddatgacha qolgan kunlar
        days_left = (item.expire_at - datetime.now(timezone.utc)).days

        # Status emoji
        if days_left < 0:
            emoji = "⛔️"
        elif days_left <= 5:
            emoji = "🔴"
        elif days_left <= 14:
            emoji = "🟡"
        elif days_left <= 30:
            emoji = "🟢"
        else:
            emoji = "🔵"

        # Matnni yaratish
        raw_text = f"{item.catalog.name} №{item.serial_number}"
        if len(raw_text) > MAX_LENGTH:
            raw_text = raw_text[:MAX_LENGTH - 1] + "…"  # Uzun matnni qisqartiramiz

        aligned_text = raw_text.ljust(MAX_LENGTH)  # Qisqa matnlarni tekislaymiz
        button_text = f"{emoji} {aligned_text}"

        builder.button(
            text=button_text,
            callback_data=f"safety_equipment:{department_id}:{area_id}:{facility_id}:{item.id}"
        )

    builder.adjust(2)

    # Navigatsiya tugmalari
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"equipment_page:{department_id}:{area_id}:{facility_id}:{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data=f"back_to_facilities:{department_id}:{area_id}"
        )
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"equipment_page:{department_id}:{area_id}:{facility_id}:{page + 1}"
            )
        )

    builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="safety_main_menu"
        )
    )

    return builder.as_markup()


def safety_equipment_detail_keyboard(
        equipment_id: int,
        department_id: int,
        area_id: int,
        facility_id: int
) -> InlineKeyboardMarkup:
    """Equipment detail ko'rish uchun tugmalar."""
    # Faqat orqaga va asosiy menyu tugmalari
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"back_to_equipment:{department_id}:{area_id}:{facility_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="safety_main_menu"
            )
        ]
    ])


def back_to_departments_keyboard() -> InlineKeyboardMarkup:
    """Departments ro'yxatiga qaytish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="back_to_departments"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="safety_main_menu"
            )
        ]
    ])


def back_to_areas_keyboard(department_id: int) -> InlineKeyboardMarkup:
    """Areas ro'yxatiga qaytish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"back_to_areas:{department_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="safety_main_menu"
            )
        ]
    ])


def back_to_facilities_keyboard(department_id: int, area_id: int) -> InlineKeyboardMarkup:
    """Facilities ro'yxatiga qaytish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"back_to_facilities:{department_id}:{area_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="safety_main_menu"
            )
        ]
    ])


def department_statistics_keyboard(department_id: int) -> InlineKeyboardMarkup:
    """Statistika sahifasi uchun tugmalar."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"back_to_areas:{department_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="safety_main_menu"
            )
        ]
    ])


# -------------------- 📅 Exam Schedule keyboards --------------------

def exam_schedule_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Imtihon jadvali uchun asosiy menyu tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("🏠 Asosiy Menyu"), callback_data="main_menu")]
    ])


def exam_viewer_categories_keyboard(overdue: int, urgent: int, warning: int, normal: int, safe: int,
                                    no_data: int) -> InlineKeyboardMarkup:
    """Viewer uchun kategoriya tugmalari"""
    builder = InlineKeyboardBuilder()

    # Faqat 0 dan katta bo'lgan kategoriyalarni ko'rsatish
    if overdue > 0:
        builder.button(
            text=f"⛔ Muddati o'tgan ({overdue})",
            callback_data="exam_category:overdue:1"
        )

    if urgent > 0:
        builder.button(
            text=f"🔴 Juda yaqin ({urgent})",
            callback_data="exam_category:urgent:1"
        )

    if warning > 0:
        builder.button(
            text=f"🟡 Yaqinlashdi ({warning})",
            callback_data="exam_category:warning:1"
        )

    if normal > 0:
        builder.button(
            text=f"🟢 Kamaymoqda ({normal})",
            callback_data="exam_category:normal:1"
        )

    if safe > 0:
        builder.button(
            text=f"🔵 Xavfsiz ({safe})",
            callback_data="exam_category:safe:1"
        )

    if no_data > 0:
        builder.button(
            text=f"❓ Ma'lumot yo'q ({no_data})",
            callback_data="exam_category:no_data:1"
        )

    builder.adjust(2)  # 2 tadan har qatorda

    # Qidiruv tugmasi
    builder.row(
        InlineKeyboardButton(
            text=_("🔍 Foydalanuvchi qidirish"),
            callback_data="exam_search"
        )
    )

    # Asosiy menyu tugmasi
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="main_menu"
        )
    )

    return builder.as_markup()


def exam_search_keyboard() -> InlineKeyboardMarkup:
    """Qidiruv sahifasi uchun keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="back_to_exam_categories"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="main_menu"
            )
        ]
    ])


def exam_category_pagination_keyboard(category: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Kategoriya ichida pagination uchun keyboard"""
    buttons = []

    # Pagination tugmalari (faqat kerakli bo'lsa)
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"exam_category:{category}:{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="back_to_exam_categories"
        )
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"exam_category:{category}:{page + 1}"
            )
        )

    # Birinchi qator - navigation
    buttons.append(nav_buttons)

    # Ikkinchi qator - asosiy menyu
    buttons.append([
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)



def exam_search_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Qidiruv natijalari uchun pagination keyboard"""
    buttons = []

    # Pagination tugmalari
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"exam_search_page:{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=_("🔍 Qidiruv"),
            callback_data="exam_search"
        )
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"exam_search_page:{page + 1}"
            )
        )

    # Birinchi qator - navigation
    buttons.append(nav_buttons)

    # Ikkinchi qator - orqaga va asosiy menyu bir qatorda
    buttons.append([
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="back_to_exam_categories"
        ),
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def exam_back_to_categories_keyboard() -> InlineKeyboardMarkup:
    """Kategoriyalarga qaytish uchun keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="back_to_exam_categories"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="main_menu"
            )
        ]
    ])

# -------------------- ⚠️ accident_handler --------------------

def accident_years_keyboard(years: List[AccidentYear]) -> InlineKeyboardMarkup:
    """Years list keyboard with accident counts"""
    builder = InlineKeyboardBuilder()

    if years:
        # Year buttons (2 per row)
        for year in years:
            count = len(year.accidents)  # Barcha hodisalar soni (Xisobat ham kiradi)
            builder.button(
                text=f"📆 {year.name} ({count})",
                callback_data=f"accident_year:{year.id}:1"
            )

        builder.adjust(2)

        # Statistics button
        builder.row(
            InlineKeyboardButton(
                text=_("📊 Umumiy Statistika"),
                callback_data="accident_statistics_main"
            )
        )

    # Main menu
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="main_menu"
        )
    )

    return builder.as_markup()


def accident_empty_year_keyboard() -> InlineKeyboardMarkup:
    """Empty year keyboard with back button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="accident_back_to_years"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="main_menu"
            )
        ]
    ])


def accident_list_keyboard(
        accidents: List[Accident],
        year_id: int,
        current_page: int,
        total_pages: int
) -> InlineKeyboardMarkup:
    """Accidents list keyboard with pagination"""
    builder = InlineKeyboardBuilder()

    # Accident buttons (3 per row)
    for accident in accidents:
        builder.button(
            text=f"📋 {accident.title}",
            callback_data=f"accident_detail:{accident.id}"
        )

    builder.adjust(3)

    # Navigation buttons row
    nav_buttons = []

    # Previous page button
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"accident_year:{year_id}:{current_page - 1}"
            )
        )

    # Back to years button (always present)
    nav_buttons.append(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="accident_back_to_years"
        )
    )

    # Next page button
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"accident_year:{year_id}:{current_page + 1}"
            )
        )

    # Add navigation row
    if nav_buttons:
        builder.row(*nav_buttons)

    # Statistics for this year
    builder.row(
        InlineKeyboardButton(
            text=_("📊 Yil Statistikasi"),
            callback_data=f"accident_statistics_year:{year_id}"
        )
    )

    # Main menu separately
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="main_menu"
        )
    )

    return builder.as_markup()


def accident_detail_keyboard(year_id: int) -> InlineKeyboardMarkup:
    """Accident detail keyboard with back navigation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"accident_year:{year_id}:1"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="main_menu"
            )
        ]
    ])


def accident_statistics_main_keyboard() -> InlineKeyboardMarkup:
    """Main statistics keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="accident_back_from_stats"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="main_menu"
            )
        ]
    ])


def accident_statistics_year_keyboard(year_id: int) -> InlineKeyboardMarkup:
    """Year statistics keyboard with enhanced navigation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"accident_year:{year_id}:1"
            ),
            InlineKeyboardButton(
                text=_("📊 Umumiy Statistika"),
                callback_data="accident_statistics_main"
            )
        ],
        [
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="main_menu"
            )
        ]
    ])



def ai_limits_keyboard() -> InlineKeyboardMarkup:
    """Limits view keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="ai_back_to_chat"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="ai_main_menu"
            )
        ]
    ])


# -------------------- 📚 library_handler --------------------

def library_categories_keyboard(categories: List[CategoryBook], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Categories list keyboard with pagination (2x2 grid)"""
    builder = InlineKeyboardBuilder()

    # Category buttons (2 per row)
    for category in categories:
        builder.button(
            text=f"📂 {category.name}",
            callback_data=f"library_category:{category.id}:1"
        )

    builder.adjust(2)  # 2 buttons per row

    # Pagination buttons if needed
    if total_pages > 1:
        nav_buttons = []

        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=_("⬅️ Oldingi"),
                    callback_data=f"library_categories_page:{page - 1}"
                )
            )

        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=_("Keyingi ➡️"),
                    callback_data=f"library_categories_page:{page + 1}"
                )
            )

        if nav_buttons:
            builder.row(*nav_buttons)

    # Statistics button
    builder.row(
        InlineKeyboardButton(
            text=_("📊 Statistika"),
            callback_data="library_statistics"
        )
    )

    # Main menu
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="library_main_menu"
        )
    )

    return builder.as_markup()


def library_books_keyboard(
        books: List[Book],
        category_id: int,
        current_page: int,
        total_pages: int
) -> InlineKeyboardMarkup:
    """Books list keyboard with pagination (1 per row)"""
    builder = InlineKeyboardBuilder()

    # Book buttons (1 per row)
    for book in books:
        builder.button(
            text=f"📖 {book.name}",
            callback_data=f"library_book:{book.id}"
        )

    builder.adjust(1)  # 1 button per row

    # Navigation buttons row
    nav_buttons = []

    # Previous page button
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"library_category:{category_id}:{current_page - 1}"
            )
        )

    # Back to categories button (always present)
    nav_buttons.append(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="library_back_to_categories"
        )
    )

    # Next page button
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"library_category:{category_id}:{current_page + 1}"
            )
        )

    # Add navigation row
    if nav_buttons:
        builder.row(*nav_buttons)

    # Main menu separately
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="library_main_menu"
        )
    )

    return builder.as_markup()


def library_book_detail_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Book detail keyboard with back navigation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"library_back_from_detail:{category_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="library_main_menu"
            )
        ]
    ])


def library_statistics_keyboard() -> InlineKeyboardMarkup:
    """Library statistics keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="library_back_from_stats"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="library_main_menu"
            )
        ]
    ])


def library_empty_category_keyboard() -> InlineKeyboardMarkup:
    """Empty category keyboard with back button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="library_back_to_categories"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="library_main_menu"
            )
        ]
    ])

# -------------------- 🎥 video_handler --------------------

def video_categories_keyboard(categories: List[CategoryVideo], page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Categories list keyboard with pagination (2x2 grid)"""
    builder = InlineKeyboardBuilder()

    # Category buttons (2 per row)
    for category in categories:
        builder.button(
            text=f"📂 {category.name}",
            callback_data=f"video_category:{category.id}:1"
        )

    builder.adjust(2)  # 2 buttons per row

    # Pagination buttons if needed
    if total_pages > 1:
        nav_buttons = []

        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=_("⬅️ Oldingi"),
                    callback_data=f"video_categories_page:{page - 1}"
                )
            )

        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=_("Keyingi ➡️"),
                    callback_data=f"video_categories_page:{page + 1}"
                )
            )

        if nav_buttons:
            builder.row(*nav_buttons)

    # Statistics button
    builder.row(
        InlineKeyboardButton(
            text=_("📊 Statistika"),
            callback_data="video_statistics"
        )
    )

    # Main menu
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="video_main_menu"
        )
    )

    return builder.as_markup()


def video_list_keyboard(
        videos: List[Video],
        category_id: int,
        current_page: int,
        total_pages: int
) -> InlineKeyboardMarkup:
    """Videos list keyboard with pagination (1 per row)"""
    builder = InlineKeyboardBuilder()

    # Video buttons (1 per row)
    for video in videos:
        builder.button(
            text=f"🎬 {video.name}",
            callback_data=f"video_detail:{video.id}"
        )

    builder.adjust(1)  # 1 button per row

    # Navigation buttons row
    nav_buttons = []

    # Previous page button
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"video_category:{category_id}:{current_page - 1}"
            )
        )

    # Back to categories button (always present)
    nav_buttons.append(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="video_back_to_categories"
        )
    )

    # Next page button
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"video_category:{category_id}:{current_page + 1}"
            )
        )

    # Add navigation row
    if nav_buttons:
        builder.row(*nav_buttons)

    # Main menu separately
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="video_main_menu"
        )
    )

    return builder.as_markup()


def video_detail_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Video detail keyboard with back navigation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"video_back_from_detail:{category_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="video_main_menu"
            )
        ]
    ])


def video_statistics_keyboard() -> InlineKeyboardMarkup:
    """Video statistics keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="video_back_from_stats"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="video_main_menu"
            )
        ]
    ])


def video_empty_category_keyboard() -> InlineKeyboardMarkup:
    """Empty category keyboard with back button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="video_back_to_categories"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="video_main_menu"
            )
        ]
    ])


# -------------------- 🏢 company_handler --------------------


def company_contact_keyboard(admin_link: str = None) -> InlineKeyboardMarkup:
    """Faqat admin kontakt tugmasi"""
    builder = InlineKeyboardBuilder()

    # Admin button
    if admin_link:
        # Check if it's a link or ID
        if admin_link.startswith('http') or admin_link.startswith('@'):
            # Normal link
            url = admin_link if admin_link.startswith('http') else f"https://t.me/{admin_link.lstrip('@')}"
            builder.row(
                InlineKeyboardButton(
                    text=_("👤 Admin bilan bog'lanish"),
                    url=url
                )
            )
        else:
            # Telegram User ID
            builder.row(
                InlineKeyboardButton(
                    text=_("👤 Admin bilan bog'lanish"),
                    url=f"tg://user?id={admin_link}"
                )
            )

    # Main menu button (alohida qatorda)
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="company_main_menu"
        )
    )

    return builder.as_markup()


def company_main_keyboard() -> InlineKeyboardMarkup:
    """Asosiy menyu tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="company_main_menu")]
    ])


# -------------------- 🚆 train_handler --------------------

def train_safety_folders_keyboard(folders, page: int = 1, per_page: int = 10):
    """Papkalar klaviaturasi (pagination bilan)"""
    builder = InlineKeyboardBuilder()

    # Sahifa sozlamalari
    total_items = len(folders)
    total_pages = (total_items + per_page - 1) // per_page

    # Hozirgi sahifa uchun papkalarni olish
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    current_folders = folders[start_idx:end_idx]

    # Papka tugmalari (2 tadan har qatorda)
    for folder in current_folders:
        builder.button(
            text=f"📂 {folder.name}",
            callback_data=f"train_safety_folder_{folder.id}"
        )

    builder.adjust(2)  # 2 tadan har qatorda

    # Pagination tugmalari (agar kerak bo'lsa)
    if total_pages > 1:
        nav_buttons = []

        # Oldingi sahifa
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=_("⬅️ Oldingi"),
                    callback_data=f"train_safety_folders_page_{page - 1}"
                )
            )

        # Keyingi sahifa
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=_("Keyingi ➡️"),
                    callback_data=f"train_safety_folders_page_{page + 1}"
                )
            )

        # Navigation tugmalarini qo'shish
        if nav_buttons:
            builder.row(*nav_buttons)

    # Asosiy menyu tugmasi
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="train_safety_main_menu"
        )
    )

    return builder.as_markup()


def train_safety_files_keyboard(files, folder_id: int, page: int = 1, per_page: int = 10):
    """Papka ichidagi fayllar klaviaturasi (pagination bilan)"""
    builder = InlineKeyboardBuilder()

    # Sahifa sozlamalari
    total_items = len(files)
    total_pages = (total_items + per_page - 1) // per_page

    # Hozirgi sahifa uchun fayllarni olish
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    current_files = files[start_idx:end_idx]

    # Fayllar ro'yxati (1 tadan har qatorda)
    for file in current_files:
        builder.button(
            text=f"📄 {file.name}",
            callback_data=f"train_safety_file_{file.id}"
        )

    builder.adjust(1)  # 1 tadan har qatorda

    # Navigation tugmalari
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("⬅️ Oldingi"),
                callback_data=f"train_safety_files_page_{folder_id}_{page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=_("↩️ Orqaga"),
            callback_data="train_safety_back_to_folders"
        )
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text=_("Keyingi ➡️"),
                callback_data=f"train_safety_files_page_{folder_id}_{page + 1}"
            )
        )

    builder.row(*nav_buttons)

    # Asosiy menyu tugmasi
    builder.row(
        InlineKeyboardButton(
            text=_("🏠 Asosiy Menyu"),
            callback_data="train_safety_main_menu"
        )
    )

    return builder.as_markup()


def train_safety_empty_folder_keyboard():
    """Bo'sh papka uchun keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data="train_safety_back_to_folders"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="train_safety_main_menu"
            )
        ]
    ])


def train_safety_file_detail_keyboard(folder_id: int):
    """Fayl ko'rish uchun keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("↩️ Orqaga"),
                callback_data=f"train_safety_back_from_detail:{folder_id}"
            ),
            InlineKeyboardButton(
                text=_("🏠 Asosiy Menyu"),
                callback_data="train_safety_main_menu"
            )
        ]
    ])