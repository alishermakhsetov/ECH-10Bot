
from bot.utils.transliterate import normalize_text


def format_full_name(text: str) -> str:
    """
    Ism-familyani to'g'ri formatlash:
    - Kirill bo'lsa lotinga o'tkazish
    - Har bir so'zning birinchi harfini katta qilish
    - Ortiqcha bo'sh joylarni tozalash
    """
    # 1. Kirill -> Lotin (agar kerak bo'lsa)
    # normalize_text kichik harfga o'tkazadi, shuning uchun boshqa funksiya kerak
    latin_text = cyrillic_to_latin_preserve_case(text)

    # 2. Ortiqcha bo'sh joylarni tozalash va so'zlarga ajratish
    words = latin_text.strip().split()

    # 3. Har bir so'zning birinchi harfini katta qilish
    formatted_words = [word.capitalize() for word in words]

    # 4. Qayta birlashtirish
    return ' '.join(formatted_words)


def cyrillic_to_latin_preserve_case(text: str) -> str:
    """Kirill -> Lotin, katta-kichik harflarni saqlagan holda"""
    trans_dict = {
        # Kichik harflar
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'i', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',

        # Katta harflar
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch',
        'Ш': 'Sh', 'Щ': 'Sh', 'Ъ': '', 'Ы': 'I', 'Ь': '',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',

        # O'zbek kirill harflari
        'ў': "o'", 'Ў': "O'",
        'қ': 'q', 'Қ': 'Q',
        'ғ': "g'", 'Ғ': "G'",
        'ҳ': 'h', 'Ҳ': 'H'
    }

    result = ''
    for char in text:
        result += trans_dict.get(char, char)

    return result


def validate_full_name(text: str) -> bool:
    """
    Ism-familyani tekshirish
    Returns: is_valid (bool)
    """
    # Bo'sh joylarni tozalash
    cleaned = text.strip()

    # Bo'sh tekshirish
    if not cleaned:
        return False

    # So'zlarga ajratish
    words = cleaned.split()

    # Kamida 2 ta so'z bo'lishi kerak
    if len(words) < 2:
        return False

    # Har bir so'z kamida 2 ta harfdan iborat bo'lishi kerak
    for word in words:
        if len(word) < 2:
            return False

    # Faqat harflar va ba'zi belgilar ruxsat etilgan
    allowed_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'-абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЎҚҒҲ ")

    for char in cleaned:
        if char not in allowed_chars:
            return False

    return True