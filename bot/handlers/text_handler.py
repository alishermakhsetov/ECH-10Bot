from aiogram import Router, F
from aiogram.enums import ParseMode, ChatType, ContentType
from aiogram.types import Message

text_router = Router()

MAX_STORED_MESSAGES = 1
user_text_messages = {}

# Shaxsiy chatdagi FAQAT MATNLAR uchun
@text_router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type == ContentType.TEXT,  # Faqat matn
    ~F.text.startswith("/")  # Komanda emas
)
async def handle_private_texts(message: Message):
    user_id = message.from_user.id

    # Xabar ID'ni saqlash
    user_text_messages.setdefault(user_id, []).append(message.message_id)

    # Eski xabarlarni o'chirish
    if len(user_text_messages[user_id]) > MAX_STORED_MESSAGES:
        old_msg_id = user_text_messages[user_id].pop(0)
        try:
            await message.bot.delete_message(chat_id=user_id, message_id=old_msg_id)
        except Exception as e:
            print(f"[ERROR] delete_message: {e}")


# Guruh yoki kanal ichida /id komandasi ishlaydi
@text_router.message(F.text == "/id")
async def send_chat_id(message: Message):
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
        chat = message.chat
        chat_title = chat.title or "Noma'lum"
        chat_id = chat.id

        await message.answer(
            f"📢 Nomi : <b>{chat_title}</b>\n"
            f"🆔 Chat ID : <code>{chat_id}</code>",
            parse_mode=ParseMode.HTML
        )
    # Shaxsiy chatda /id ishlamaydi
