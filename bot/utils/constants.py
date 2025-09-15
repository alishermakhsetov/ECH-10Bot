# ============ TEST CONSTANTS ============
QUESTION_TIME_LIMIT = 60  # Har bir savol uchun vaqt (soniya)
UPDATE_INTERVAL = 5       # Timer yangilanish intervali (soniya)
MAX_QUESTIONS = 10        # Maksimal savol soni
MIN_SHARE_PERCENTAGE = 70 # Ulashish uchun minimal foiz

# ============ MESSAGE CONSTANTS ============
MAX_STORED_MESSAGES = 2   # Saqlanadigan xabarlar soni

# ============ LANGUAGE CONSTANTS ============
DEFAULT_LANGUAGE = "uz"   # Asosiy til
SUPPORTED_LANGUAGES = ["uz", "ru", "en"]  # Qo'llab-quvvatlanadigan tillar

# ============ GRADE CONSTANTS ============
GRADE_EXCELLENT = 90      # A'lo baho uchun minimal foiz
GRADE_GOOD = 80          # Yaxshi baho uchun minimal foiz
GRADE_SATISFACTORY = 70  # Qoniqarli baho uchun minimal foiz
GRADE_AVERAGE = 60       # O'rtacha baho uchun minimal foiz

# ============ EMOJI CONSTANTS ============
GRADE_EMOJIS = {
    "excellent": "🏆",
    "good": "🥇",
    "satisfactory": "🥈",
    "average": "🥉",
    "poor": "📚"
}

GRADE_TEXTS = {
    "excellent": "A'lo!",
    "good": "Yaxshi!",
    "satisfactory": "Qoniqarli!",
    "average": "O'rtacha!",
    "poor": "Ko'proq o'qish kerak!"
}

# ============ ANSWER LETTERS ============
ANSWER_LETTERS = ['A', 'B', 'C', 'D']

# -------------------------------------------------------------------------
# exam_schedule_handler
import random

# Exam schedule uchun rasmlar (haqiqiy file_id'lar bilan almashtiring)
EXAM_SCHEDULE_IMAGES = [
    "AgACAgIAAxkBAAIfqGhqlLoFJWv7SotFjFWbSii8ByNIAALF_jEbX0JYSw4h4uJG-42yAQADAgADeAADNgQ",  # Haqiqiy file_id 1
    "AgACAgIAAxkBAAIfrGhqlMYuwYYjf6SvPX5s-Alq620vAALH_jEbX0JYSynXqTsbVFz9AQADAgADeQADNgQ",  # Haqiqiy file_id 2
    "AgACAgIAAxkBAAIfrmhqlM0T8I7PKgtEhrh-P6_7bf22AALI_jEbX0JYS_ZyBizu0FCqAQADAgADeQADNgQ",  # Haqiqiy file_id 3
    "AgACAgIAAxkBAAIfsmhqlN0hluAM4XrOhn0mH35CWmqTAAL0_DEbEP9YSxFZWUJ_b16UAQADAgADeQADNgQ",  # Haqiqiy file_id 4
    "AgACAgIAAxkBAAIftGhqlOW2cZ6eWGWEqSCNfZBTPwABfgACyf4xG19CWEvGtNhWpiW1_gEAAwIAA3gAAzYE",  # Haqiqiy file_id 5
    "AgACAgIAAxkBAAIfuGhqleSeJzspqhPjDfW-fCOM-6TJAALT_jEbX0JYS9H-tGJsqHtQAQADAgADeAADNgQ",  # Haqiqiy file_id 5
]

def get_random_exam_image():
    """Random exam rasmi qaytaradi"""
    if not EXAM_SCHEDULE_IMAGES:
        return None  # Agar rasmlar yo'q bo'lsa None qaytarish
    return random.choice(EXAM_SCHEDULE_IMAGES)
