from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.types import Message
from aiolimiter import AsyncLimiter
import asyncio
from typing import Dict, Set
import time

media_router = Router()

# 🛡️ OQILONA LIMITLAR - Normal foydalanish uchun yetarli
photo_limiter = AsyncLimiter(max_rate=8, time_period=60)  # 8 rasm/daqiqa
video_limiter = AsyncLimiter(max_rate=4, time_period=60)  # 4 video/daqiqa
document_limiter = AsyncLimiter(max_rate=6, time_period=60)  # 6 hujjat/daqiqa
audio_limiter = AsyncLimiter(max_rate=8, time_period=60)  # 8 audio/daqiqa
test_limiter = AsyncLimiter(max_rate=3, time_period=60)  # 3 test/daqiqa

# FLOOD PROTECTION - 1000 ta fayl oldini olish
user_flood_protection: Dict[int, list] = {}
MAX_FILES_PER_MINUTE = 12  # Daqiqada maksimal 12 ta fayl
FLOOD_BAN_TIME = 300  # 5 daqiqa ban
MAX_FILES_PER_HOUR = 50  # Soatiga 50 ta
PROGRESSIVE_BAN_MULTIPLIER = 2  # Har safar 2 barobar ko'payadi

# User ban tarixi
user_ban_history: Dict[int, int] = {}
banned_users: Set[int] = set()
user_ban_until: Dict[int, float] = {}

# XAVFSIZ XABAR BOSHQARUVI - Race condition oldini olish
user_last_messages = {}
user_last_replies = {}
MAX_STORED = 2

# Video kengaytmalari
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.mts'}


async def check_flood_protection(user_id: int) -> bool:
    """Progressive flood protection"""
    current_time = time.time()

    # Ban holatini tekshirish
    if user_id in user_ban_until:
        if current_time < user_ban_until[user_id]:
            return False
        else:
            # Ban tugagan
            del user_ban_until[user_id]
            banned_users.discard(user_id)

    # Flood protection
    if user_id not in user_flood_protection:
        user_flood_protection[user_id] = []

    # Eski vaqtlarni tozalash (1 daqiqadan eski)
    user_flood_protection[user_id] = [
        t for t in user_flood_protection[user_id]
        if current_time - t < 60
    ]

    # Soatlik limit tekshirish
    hour_old_times = [
        t for t in user_flood_protection[user_id]
        if current_time - t < 3600
    ]

    if len(hour_old_times) >= MAX_FILES_PER_HOUR:
        # Soatlik limit oshgan - 24 soat ban
        banned_users.add(user_id)
        user_ban_until[user_id] = current_time + 86400  # 24 soat
        return False

    # Daqiqalik limit tekshirish
    if len(user_flood_protection[user_id]) >= MAX_FILES_PER_MINUTE:
        # Progressive ban
        ban_count = user_ban_history.get(user_id, 0) + 1
        user_ban_history[user_id] = ban_count

        # Progressive ban vaqti
        ban_duration = FLOOD_BAN_TIME * (PROGRESSIVE_BAN_MULTIPLIER ** (ban_count - 1))
        if ban_duration > 86400:  # Maksimal 24 soat
            ban_duration = 86400

        banned_users.add(user_id)
        user_ban_until[user_id] = current_time + ban_duration
        return False

    # Vaqtni qo'shish
    user_flood_protection[user_id].append(current_time)
    return True


async def safe_reply_then_clean(message: Message, text: str, user_id: int):
    """XAVFSIZ: Avval reply, keyin clean - Race condition yo'q"""
    try:
        # 1-qadam: REPLY (xabar mavjud bo'lganida)
        reply_msg = await message.reply(
            text,
            parse_mode="HTML",
            disable_notification=True
        )

        # 2-qadam: KICHIK PAUZA (race condition oldini olish)
        await asyncio.sleep(0.05)

        # 3-qadam: CLEAN (reply tugagandan keyin)
        await safe_clean_messages(user_id, message.message_id, reply_msg.message_id, message.bot)

        return True

    except Exception as e:
        # Agar reply ishlamasa, hech narsa qilmaslik
        try:
            # Faqat user xabarini tozalash
            await safe_clean_user_only(user_id, message.message_id, message.bot)
        except:
            pass
        return False


async def safe_clean_messages(user_id: int, user_msg_id: int, reply_msg_id: int, bot):
    """XAVFSIZ xabar tozalash - race condition yo'q"""
    try:
        # User xabarini saqlash
        if user_id not in user_last_messages:
            user_last_messages[user_id] = []
        user_last_messages[user_id].append(user_msg_id)

        # Bot javobini saqlash
        if user_id not in user_last_replies:
            user_last_replies[user_id] = []
        user_last_replies[user_id].append(reply_msg_id)

        # Agar 2 tadan ko'p bo'lsa - eskisini o'chirish
        if len(user_last_messages[user_id]) > MAX_STORED:
            old_msg = user_last_messages[user_id].pop(0)
            try:
                await bot.delete_message(chat_id=user_id, message_id=old_msg)
            except:
                pass

        if len(user_last_replies[user_id]) > MAX_STORED:
            old_reply = user_last_replies[user_id].pop(0)
            try:
                await bot.delete_message(chat_id=user_id, message_id=old_reply)
            except:
                pass

    except Exception:
        pass


async def safe_clean_user_only(user_id: int, user_msg_id: int, bot):
    """Faqat user xabarini tozalash"""
    try:
        if user_id not in user_last_messages:
            user_last_messages[user_id] = []
        user_last_messages[user_id].append(user_msg_id)

        if len(user_last_messages[user_id]) > MAX_STORED:
            old_msg = user_last_messages[user_id].pop(0)
            try:
                await bot.delete_message(chat_id=user_id, message_id=old_msg)
            except:
                pass
    except:
        pass


async def send_flood_warning(message: Message):
    """Progressive flood warning"""
    user_id = message.from_user.id

    # Qolgan vaqtni hisoblash
    current_time = time.time()
    if user_id in user_ban_until:
        remaining_seconds = int(user_ban_until[user_id] - current_time)
        remaining_minutes = remaining_seconds // 60
        remaining_secs = remaining_seconds % 60
        if remaining_minutes >= 60:
            remaining_hours = remaining_minutes // 60
            remaining_minutes = remaining_minutes % 60
            time_left = f"{remaining_hours}:{remaining_minutes:02d}:{remaining_secs:02d}"
        else:
            time_left = f"{remaining_minutes}:{remaining_secs:02d}"
    else:
        time_left = "5:00"

    # Ban history
    ban_count = user_ban_history.get(user_id, 0)
    if ban_count == 0:
        ban_status = "Birinchi ogohlantirish"
    elif ban_count == 1:
        ban_status = "Ikkinchi ogohlantirish"
    elif ban_count >= 2:
        ban_status = "Ko'p marta buzish"

    warning_text = (
        "🚫 <b>Juda ko'p fayl yubormoqdasiz!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <b>Qolgan vaqt: {time_left}</b>\n"
        f"⚠️ <b>Holat: {ban_status}</b>\n\n"
        "📊 <b>Fayl yuborish limitlari:</b>\n"
        f"🖼️ Rasm: <b>8</b> ta / daqiqa\n"
        f"🎞️ Video: <b>4</b> ta / daqiqa\n"
        f"📄 Hujjat: <b>6</b> ta / daqiqa\n"
        f"🔢 Umumiy: <b>{MAX_FILES_PER_MINUTE}</b> ta / daqiqa\n"
        f"⏰ Soatlik: <b>{MAX_FILES_PER_HOUR}</b> ta / soat\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ <i>Progressive spam himoyasi</i>"
    )

    try:
        warning_msg = await message.reply(
            warning_text,
            parse_mode="HTML",
            disable_notification=True
        )
        # Warning ham clean qilish
        await asyncio.sleep(0.05)
        await safe_clean_messages(user_id, message.message_id, warning_msg.message_id, message.bot)
    except:
        pass


def format_file_size(file_size: int) -> str:
    """Fayl hajmini formatlash"""
    if file_size < 1024:
        return f"{file_size} B"
    elif file_size < 1024 * 1024:
        return f"{round(file_size / 1024, 2)} KB"
    else:
        return f"{round(file_size / (1024 * 1024), 2)} MB"


def is_video_file(file_name: str) -> bool:
    """Fayl video ekanligini tekshirish"""
    if not file_name:
        return False
    return any(file_name.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)


# 🖼️ Rasm handler - File ID olish
@media_router.message(F.content_type == ContentType.PHOTO)
async def photo_handler(message: Message):
    """Rasm yuklanganda file_id ni ko'rsatish"""
    user_id = message.from_user.id

    # Flood protection
    if not await check_flood_protection(user_id):
        await send_flood_warning(message)
        return

    async with photo_limiter:
        photo = message.photo[-1]
        file_id = photo.file_id
        width = photo.width
        height = photo.height
        file_size = photo.file_size or 0

        # Rasm nomi (agar bor bo'lsa)
        photo_name = getattr(message, 'caption', None) or "rasm_nomi"

        # Chiroyli dizayn
        text = (
            f"✅ <b>Rasm muvaffaqiyatli qabul qilindi!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>File ID:</b>\n"
            f"<code>{file_id}</code>\n"
            f"🛠️ <b>Rasm ma'lumotlar:</b>\n"
            f"📝 Nomi:  <b>{photo_name}</b>\n"
            f"💾 Hajmi:  <b>{format_file_size(file_size)}</b>\n"
            f"📐 O'lchami:  <b>{width} × {height}</b> px\n"
            f"🖼️ Turi:  <b>Photo</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # XAVFSIZ reply va clean
        await safe_reply_then_clean(message, text, user_id)


# 📹 Video handler - File ID olish
@media_router.message(F.content_type == ContentType.VIDEO)
async def video_handler(message: Message):
    """Video yuklanganda file_id ni ko'rsatish"""
    user_id = message.from_user.id

    # Flood protection
    if not await check_flood_protection(user_id):
        await send_flood_warning(message)
        return

    async with video_limiter:
        video = message.video
        file_id = video.file_id
        file_name = video.file_name or "Nomsiz video"
        file_size = video.file_size or 0
        duration = video.duration or 0
        width = video.width or 0
        height = video.height or 0

        # Davomiylikni formatlash
        minutes = duration // 60
        seconds = duration % 60
        duration_text = f"{minutes}:{seconds:02d}" if duration > 0 else "0:00"

        # Chiroyli dizayn
        text = (
            f"✅ <b>Video muvaffaqiyatli qabul qilindi!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>File ID:</b>\n"
            f"<code>{file_id}</code>\n"
            f"🛠️ <b>Video ma'lumotlari:</b>\n"
            f"📝 Nomi:  <b>{file_name}</b>\n"
            f"💾 Hajmi:  <b>{format_file_size(file_size)}</b>\n"
            f"⏱️ Vaqti:  <b>{duration_text}</b>\n"
            f"🎞️ Sifati:  <b>{width} × {height}</b>\n"
            f"📹 Turi:  <b>Video</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # XAVFSIZ reply va clean
        await safe_reply_then_clean(message, text, user_id)


# 📄 Document handler - File ID olish
@media_router.message(F.content_type == ContentType.DOCUMENT)
async def document_handler(message: Message):
    """Hujjat yuklanganda file_id ni ko'rsatish"""
    user_id = message.from_user.id

    # Flood protection
    if not await check_flood_protection(user_id):
        await send_flood_warning(message)
        return

    async with document_limiter:
        document = message.document
        file_id = document.file_id
        file_name = document.file_name or "Nomsiz fayl"
        file_size = document.file_size or 0

        # Video fayl ekanligini tekshirish
        is_video = is_video_file(file_name)

        if is_video:
            title = "Video (Hujjat formatida) muvaffaqiyatli yuklandi!"
        else:
            title = "Hujjat muvaffaqiyatli qabul qilindi!"

        # Chiroyli dizayn
        text = (
            f"✅ <b>{title}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>File ID:</b>\n"
            f"<code>{file_id}</code>\n\n"
            f"🛠️ <b>Fayl ma'lumotlari:</b>\n"
            f"📝 Nomi:  <b>{file_name}</b>\n"
            f"💾 Hajmi:  <b>{format_file_size(file_size)}</b>\n"
            f"📄 Turi:  <b>Document</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # XAVFSIZ reply va clean
        await safe_reply_then_clean(message, text, user_id)


# 🎵 Audio handler - File ID olish
@media_router.message(F.content_type == ContentType.AUDIO)
async def audio_handler(message: Message):
    """Audio yuklanganda file_id ni ko'rsatish"""
    user_id = message.from_user.id

    # Flood protection
    if not await check_flood_protection(user_id):
        await send_flood_warning(message)
        return

    async with audio_limiter:
        audio = message.audio
        file_id = audio.file_id
        file_name = audio.file_name or audio.title or "Nomsiz audio"
        file_size = audio.file_size or 0
        duration = audio.duration or 0

        # Davomiylikni formatlash
        minutes = duration // 60
        seconds = duration % 60
        duration_text = f"{minutes}:{seconds:02d}" if duration > 0 else "0:00"

        text = (
            f"✅ <b>Audio muvaffaqiyatli qabul qilindi!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>File ID:</b>\n"
            f"<code>{file_id}</code>\n\n"
            f"🛠️ <b>Audio ma'lumotlari:</b>\n"
            f"🎼 Nomi:  <b>{file_name}</b>\n"
            f"💾 Hajmi:  <b>{format_file_size(file_size)}</b>\n"
            f"⏱️ Vaqti:  <b>{duration_text}</b>\n"
            f"🎵 Turi:  <b>Audio</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # XAVFSIZ reply va clean
        await safe_reply_then_clean(message, text, user_id)


# # 🎤 Voice handler - File ID olish
# @media_router.message(F.content_type == ContentType.VOICE)
# async def voice_handler(message: Message):
#     """Ovozli xabar yuklanganda file_id ni ko'rsatish"""
#     user_id = message.from_user.id
#
#     # Flood protection
#     if not await check_flood_protection(user_id):
#         await send_flood_warning(message)
#         return
#
#     # Voice uchun audio limiter ishlatamiz
#     async with audio_limiter:
#         voice = message.voice
#         file_id = voice.file_id
#         file_size = voice.file_size or 0
#         duration = voice.duration or 0
#
#         # Davomiylikni formatlash
#         minutes = duration // 60
#         seconds = duration % 60
#         duration_text = f"{minutes}:{seconds:02d}" if duration > 0 else "0:00"
#
#         text = (
#             f"✅ <b>Ovozli xabar muvaffaqiyatli qabul qilindi!</b>\n"
#             "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
#             f"🆔 <b>File ID:</b>\n"
#             f"<code>{file_id}</code>\n\n"
#             f"🛠️ <b>Voice ma'lumotlari:</b>\n"
#             f"🔊 <b>Ovozli xabar</b>\n"
#             f"💾 Hajmi:  <b>{format_file_size(file_size)}</b>\n"
#             f"⏱️ Vaqti:  <b>{duration_text}</b>\n"
#             f"🎙️ Turi:  <b>Voice</b>\n"
#             "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
#         )
#
#         # XAVFSIZ reply va clean
#         await safe_reply_then_clean(message, text, user_id)


# 🔍 Test uchun - File ID tekshirish
@media_router.message(F.text.startswith("/test_file"))
async def test_file_id(message: Message):
    """File ID ni test qilish: /test_file FILE_ID"""
    user_id = message.from_user.id

    # Flood protection
    if not await check_flood_protection(user_id):
        await send_flood_warning(message)
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        error_text = (
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "To'g'ri: <code>/test_file FILE_ID</code>"
        )
        await safe_reply_then_clean(message, error_text, user_id)
        return

    file_id = parts[1].strip()

    # Test limiter
    async with test_limiter:
        # Loading xabari
        loading_text = "🔄 <b>File ID tekshirilmoqda...</b>"
        loading_success = await safe_reply_then_clean(message, loading_text, user_id)

        if not loading_success:
            return

        # Kichik pauza
        await asyncio.sleep(0.1)

        # Test qilish - timeout bilan
        try:
            # Rasm sifatida sinash
            await asyncio.wait_for(
                message.reply_photo(
                    photo=file_id,
                    caption="✅ <b>File ID ishlaydi!</b>\n📸 <i>Rasm</i>",
                    parse_mode="HTML"
                ),
                timeout=10.0
            )
            return
        except (Exception, asyncio.TimeoutError):
            pass

        try:
            # Video sifatida sinash
            await asyncio.wait_for(
                message.reply_video(
                    video=file_id,
                    caption="✅ <b>File ID ishlaydi!</b>\n📹 <i>Video</i>",
                    parse_mode="HTML"
                ),
                timeout=10.0
            )
            return
        except (Exception, asyncio.TimeoutError):
            pass

        try:
            # Hujjat sifatida sinash
            await asyncio.wait_for(
                message.reply_document(
                    document=file_id,
                    caption="✅ <b>File ID ishlaydi!</b>\n📄 <i>Hujjat</i>",
                    parse_mode="HTML"
                ),
                timeout=10.0
            )
            return
        except (Exception, asyncio.TimeoutError):
            # Barcha urinishlar muvaffaqiyatsiz
            error_text = (
                f"❌ <b>File ID ishlamaydi!</b>\n\n"
                f"💡 <i>Eskirgan yoki noto'g'ri File ID</i>"
            )
            await safe_reply_then_clean(message, error_text, user_id)