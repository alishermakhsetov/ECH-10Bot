# bot/utils/transliterate.py

def normalize_text(text: str) -> str:
    """Matnni qidiruv uchun tayyorlash"""
    # Kirill-Lotin moslik jadvali
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

    # Transliteratsiya
    result = ''
    for char in text:
        result += trans_dict.get(char, char)

    # Kichik harfga o'tkazish va bo'sh joylarni tozalash
    return result.lower().strip()