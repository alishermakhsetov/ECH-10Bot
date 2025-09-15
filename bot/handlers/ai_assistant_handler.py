# bot/handlers/ai_assistant_handler.py

import os
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.i18n import lazy_gettext as __
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# AI Libraries
import google.generativeai as genai
from groq import Groq

from db.models import User
from bot.states import AIStates  # Import qilindi
from bot.buttons.inline import ai_limits_keyboard
from bot.buttons.reply import ai_menu_keyboard, get_main_menu_keyboard
from bot.utils.texts import (
    ai_welcome_text,
    ai_waiting_text,
    ai_error_text,
    ai_limit_text,
    ai_no_services_text,
    ai_back_to_chat_text,
    ai_limits_status_text,
    ai_response_text,
    ai_other_messages_text,
    get_main_text,
    # Input validation texts
    ai_input_too_long_text,
    ai_input_empty_text,
    ai_input_invalid_text,
    ai_input_duplicate_text,
    # Timeout texts
    ai_timeout_text,
    ai_processing_long_text
)

ai_router = Router()

# Configure AI services
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# 🎯 CONSTANTS
MAX_MESSAGES_PER_USER = 50
CLEANUP_INTERVAL = 3600
MAX_RETRIES = 3
RETRY_DELAY = 0.1
DELETE_CHUNK_SIZE = 20

# AI Timeout constants
AI_REQUEST_TIMEOUT = 35  # sekund
GROQ_REQUEST_TIMEOUT = 30  # sekund (Groq tezroq)
MAX_RETRIES_ON_TIMEOUT = 2
LONG_PROCESSING_WARNING_TIME = 20  # sekund

# Rate limiting
user_requests: Dict[int, List[float]] = {}
user_conversations: Dict[int, List[Dict[str, str]]] = {}

# Per user limits
MAX_USER_REQUESTS_HOUR = 10
MAX_USER_REQUESTS_DAY = 30

# Service usage tracking
service_usage = {
    "google": {"requests": [], "max_hour": 500, "max_day": 1000},
    "groq": {"requests": [], "max_hour": 2000, "max_day": 4000}
}


# 🚀 OPTIMIZED MESSAGE STORE
class OptimizedMessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "ai"):
        """Xabarni saqlash"""
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "ai") -> list[int]:
        """User xabarlarini olish"""
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "ai"):
        """User xabarlarini tozalash"""
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
        """Har soatda bir marta eski userlarni tozalash"""
        current_time = time.time()
        if current_time - self.last_cleanup > CLEANUP_INTERVAL:
            empty_users = [
                user_id for user_id, categories in self.user_messages.items()
                if not any(messages for messages in categories.values())
            ]
            for user_id in empty_users:
                del self.user_messages[user_id]
            self.last_cleanup = current_time

    def start_periodic_cleanup(self):
        """Davriy tozalashni boshlash"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup())

    async def _auto_cleanup(self):
        """Avtomatik tozalash"""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            self._periodic_cleanup()


# Global instance
message_store = OptimizedMessageStore()


# 🎯 MESSAGE FUNCTIONS
async def store_message(user_id: int, category: str, message_id: int):
    """Xabar saqlash"""
    try:
        message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot: Bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    """Xabarlarni tez parallel o'chirish"""
    msg_ids = message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    if not msg_ids:
        return

    # Parallel o'chirish
    tasks = []
    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        chunk_tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        tasks.extend(chunk_tasks)

    await asyncio.gather(*tasks, return_exceptions=True)

    # Store tozalash
    if not exclude_ids:
        message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot: Bot, chat_id: int, msg_id: int):
    """Xavfsiz xabar o'chirish"""
    try:
        await bot.delete_message(chat_id, msg_id)
        return True
    except:
        return False


# 🛡️ INPUT VALIDATION FUNCTION
async def validate_user_input(message: Message, user_id: int) -> bool:
    """Validate user input, return True if error occurred"""

    # 1. Xabar uzunligini tekshirish
    if len(message.text) > 1000:
        error_msg = await message.answer(
            ai_input_too_long_text(),
            parse_mode="HTML"
        )
        await store_message(user_id, "ai", error_msg.message_id)
        return True

    # 2. Bo'sh xabarni tekshirish
    if not message.text.strip():
        error_msg = await message.answer(
            ai_input_empty_text(),
            parse_mode="HTML"
        )
        await store_message(user_id, "ai", error_msg.message_id)
        return True

    # 3. Faqat raqam yoki belgilarni tekshirish
    if message.text.isdigit() or not any(c.isalpha() for c in message.text):
        error_msg = await message.answer(
            ai_input_invalid_text(),
            parse_mode="HTML"
        )
        await store_message(user_id, "ai", error_msg.message_id)
        return True

    # 4. Takroriy xabarni tekshirish (oxirgi 5 daqiqada)
    now = time.time()
    if user_id in user_conversations:
        recent_messages = [
            msg for msg in user_conversations[user_id]
            if msg.get("timestamp", now) > now - 300  # 5 daqiqa
        ]
        if any(msg.get("content") == message.text for msg in recent_messages):
            error_msg = await message.answer(
                ai_input_duplicate_text(),
                parse_mode="HTML"
            )
            await store_message(user_id, "ai", error_msg.message_id)
            return True

    return False  # No error


# Helper functions
def clean_old_requests() -> None:
    """Clean old requests from tracking"""
    now = time.time()
    day_ago = now - 86400

    # Clean user requests
    for user_id in list(user_requests.keys()):
        user_requests[user_id] = [req for req in user_requests[user_id] if req > day_ago]
        if not user_requests[user_id]:
            del user_requests[user_id]

    # Clean service usage
    for service in service_usage.values():
        service["requests"] = [req for req in service["requests"] if req > day_ago]


def check_user_limit(user_id: int) -> Tuple[bool, str]:
    """Check user's personal limits"""
    clean_old_requests()
    now = time.time()
    hour_ago = now - 3600

    if user_id not in user_requests:
        user_requests[user_id] = []

    recent_requests = [req for req in user_requests[user_id] if req > hour_ago]

    if len(recent_requests) >= MAX_USER_REQUESTS_HOUR:
        minutes_until_reset = 60 - int((now - min(recent_requests)) / 60)
        return False, f"Soatlik limitingiz tugadi ({MAX_USER_REQUESTS_HOUR} ta). {minutes_until_reset} daqiqadan so'ng yangilanadi"

    if len(user_requests[user_id]) >= MAX_USER_REQUESTS_DAY:
        return False, f"Kunlik limitingiz tugadi ({MAX_USER_REQUESTS_DAY} ta)"

    return True, ""


def can_use_service(service_name: str) -> bool:
    """Check if service can be used"""
    now = time.time()
    hour_ago = now - 3600

    service = service_usage[service_name]
    recent_requests = [req for req in service["requests"] if req > hour_ago]

    return len(recent_requests) < service["max_hour"] and len(service["requests"]) < service["max_day"]


def get_conversation_context(user_id: int) -> str:
    """Get last 5 messages for context"""
    if user_id not in user_conversations:
        return ""

    recent_messages = user_conversations[user_id][-10:]
    context = "Oldingi suhbat:\n"
    for msg in recent_messages:
        if msg["role"] == "user":
            context += f"Savol: {msg['content']}\n"
        else:
            context += f"Javob: {msg['content'][:100]}...\n"

    return context + "\n"


async def call_google_gemini(question: str, user_name: str, user_id: int) -> Tuple[bool, str]:
    """Call Google Gemini API with context and timeout protection"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        context = get_conversation_context(user_id)

        prompt = f"""Sen yordamchi AI assistantsiz. O'zbek tilida javob ber.

{context}

Foydalanuvchi: {user_name}
Yangi savol: {question}

To'liq, batafsil va foydali javob ber. Agar kerak bo'lsa, misollar keltir. 
Javobni formatlashda markdown ishlatma. Oddiy matn formatida javob ber.
Agar savol murakkab bo'lsa, bosqichma-bosqich tushuntir.
Agar qo'shimcha ma'lumot kerak bo'lsa, qisqa va foydali internet manbalarini taklif qil."""

        # ⏰ TIMEOUT PROTECTION
        def generate_content():
            return model.generate_content(prompt)

        response = await asyncio.wait_for(
            asyncio.to_thread(generate_content),
            timeout=AI_REQUEST_TIMEOUT
        )

        if response.text:
            service_usage["google"]["requests"].append(time.time())

            if user_id not in user_conversations:
                user_conversations[user_id] = []

            user_conversations[user_id].append({"role": "user", "content": question, "timestamp": time.time()})
            user_conversations[user_id].append(
                {"role": "assistant", "content": response.text.strip(), "timestamp": time.time()})

            if len(user_conversations[user_id]) > 20:
                user_conversations[user_id] = user_conversations[user_id][-20:]

            return True, response.text.strip()
        else:
            return False, "Google Gemini javob bermadi"

    except asyncio.TimeoutError:
        print(f"Google Gemini timeout for user {user_id}")
        return False, "AI xizmati javob bermadi (timeout)"
    except Exception as e:
        print(f"Google Gemini Error: {e}")
        return False, str(e)


async def call_groq_api(question: str, user_name: str, user_id: int) -> Tuple[bool, str]:
    """Call Groq API with context and timeout protection"""
    try:
        messages = [
            {
                "role": "system",
                "content": """Siz yordamchi AI assistantsiz. O'zbek tilida javob bering. 
To'liq, batafsil va foydali javoblar bering. Oldingi suhbatni yodda tuting.
Javoblarni oddiy matn formatida bering, markdown ishlatmang.
Murakkab savollarni bosqichma-bosqich tushuntiring.
Qo'shimcha ma'lumot kerak bo'lsa, foydali manbalarni taklif qiling."""
            }
        ]

        if user_id in user_conversations:
            for msg in user_conversations[user_id][-10:]:
                if msg["role"] == "user":
                    messages.append({"role": "user", "content": msg["content"]})
                else:
                    messages.append({"role": "assistant", "content": msg["content"]})

        messages.append({
            "role": "user",
            "content": f"Foydalanuvchi: {user_name}\nSavol: {question}"
        })

        # ⏰ TIMEOUT PROTECTION
        def create_completion():
            return groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

        response = await asyncio.wait_for(
            asyncio.to_thread(create_completion),
            timeout=GROQ_REQUEST_TIMEOUT
        )

        if response.choices and response.choices[0].message:
            service_usage["groq"]["requests"].append(time.time())

            if user_id not in user_conversations:
                user_conversations[user_id] = []

            user_conversations[user_id].append({"role": "user", "content": question, "timestamp": time.time()})
            user_conversations[user_id].append(
                {"role": "assistant", "content": response.choices[0].message.content.strip(), "timestamp": time.time()})

            if len(user_conversations[user_id]) > 20:
                user_conversations[user_id] = user_conversations[user_id][-20:]

            return True, response.choices[0].message.content.strip()
        else:
            return False, "Groq javob bermadi"

    except asyncio.TimeoutError:
        print(f"Groq timeout for user {user_id}")
        return False, "AI xizmati javob bermadi (timeout)"
    except Exception as e:
        print(f"Groq API Error: {e}")
        return False, str(e)


async def get_ai_response_with_retry(question: str, user_name: str, user_id: int) -> Tuple[bool, str, str]:
    """Get AI response with retry mechanism and timeout protection"""

    for attempt in range(MAX_RETRIES_ON_TIMEOUT):
        try:
            # Try Google Gemini first
            if can_use_service("google"):
                success, response = await call_google_gemini(question, user_name, user_id)
                if success:
                    return True, response, "Google Gemini"

            # Fallback to Groq
            if can_use_service("groq"):
                success, response = await call_groq_api(question, user_name, user_id)
                if success:
                    return True, response, "Groq"

        except Exception as e:
            print(f"AI request attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES_ON_TIMEOUT - 1:
                await asyncio.sleep(2)  # 2 sekund kutish

    return False, "Barcha AI xizmatlar javob bermadi", ""


# 🤖 HANDLERS

@ai_router.message(F.text == __("🤖 AI Yordamchi"))
async def start_ai_assistant(message: Message, state: FSMContext, session: AsyncSession):
    """Start AI assistant"""
    user_id = message.from_user.id

    # User xabarini saqlash
    await store_message(user_id, "ai", message.message_id)

    # Oldingi barcha xabarlarni o'chirish
    await delete_user_messages(message.bot, user_id, "ai")
    await delete_user_messages(message.bot, user_id, "menu")

    # Conversation tozalash
    if user_id in user_conversations:
        del user_conversations[user_id]

    # State o'rnatish
    await state.clear()
    await state.set_state(AIStates.waiting_question)

    # Get user info
    try:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
    except Exception as e:
        print(f"User fetch error: {e}")
        user = None

    # Welcome message yuborish
    welcome_msg = await message.answer(
        ai_welcome_text(user),
        reply_markup=ai_menu_keyboard(),
        parse_mode="HTML"
    )
    await store_message(user_id, "ai", welcome_msg.message_id)
    await state.update_data(welcome_msg_id=welcome_msg.message_id)


@ai_router.message(
    AIStates.waiting_question,
    lambda msg: msg.text not in [
        __("📊 Limitni ko'rish"),
        __("🏠 Asosiy Menyu"),
        __("🗑 Chatni tozalash")
    ]
)
async def process_text_question(message: Message, state: FSMContext):
    """Process text question with timeout protection"""
    user_id = message.from_user.id

    # 🛡️ Input validation
    validation_error = await validate_user_input(message, user_id)
    if validation_error:
        return

    await store_message(user_id, "ai", message.message_id)

    # Check user limits
    can_proceed, limit_msg = check_user_limit(user_id)
    if not can_proceed:
        limit_msg_obj = await message.answer(
            ai_limit_text(limit_msg),
            parse_mode="HTML"
        )
        await store_message(user_id, "ai", limit_msg_obj.message_id)
        return

    # Add to user tracking
    user_requests[user_id].append(time.time())

    # ⌨️ Typing action
    await message.bot.send_chat_action(chat_id=user_id, action="typing")

    # Show waiting message
    waiting_msg = await message.answer(
        ai_waiting_text(),
        parse_mode="HTML"
    )
    await store_message(user_id, "ai", waiting_msg.message_id)

    # 📊 Long processing warning task
    async def long_processing_warning():
        await asyncio.sleep(LONG_PROCESSING_WARNING_TIME)
        try:
            await waiting_msg.edit_text(
                ai_processing_long_text(),
                parse_mode="HTML"
            )
        except:
            pass

    warning_task = asyncio.create_task(long_processing_warning())

    try:
        user_name = message.from_user.full_name or "Foydalanuvchi"

        # ⌨️ Typing action before AI call
        await message.bot.send_chat_action(chat_id=user_id, action="typing")

        # 🚀 Get AI response with retry and timeout protection
        success, ai_response, service_used = await get_ai_response_with_retry(message.text, user_name, user_id)

        # Cancel warning task
        warning_task.cancel()

        if success:
            response_text = ai_response_text(ai_response, service_used)
        else:
            # Check if it's a timeout error
            if "timeout" in ai_response.lower():
                response_text = ai_timeout_text()
            else:
                response_text = ai_no_services_text()

        await waiting_msg.edit_text(
            response_text,
            parse_mode="HTML"
        )

    except Exception as e:
        # Cancel warning task
        warning_task.cancel()

        await waiting_msg.edit_text(
            ai_error_text(),
            parse_mode="HTML"
        )
        print(f"AI Error: {e}")


@ai_router.message(AIStates.waiting_question, F.text == __("📊 Limitni ko'rish"))
async def view_limits_handler(message: Message, state: FSMContext):
    """Show limits with inline keyboard"""
    user_id = message.from_user.id

    await store_message(user_id, "ai", message.message_id)

    # Reply keyboard'ni o'chirish
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    await state.set_state(AIStates.viewing_limits)

    now = time.time()
    hour_ago = now - 3600
    day_ago = now - 86400

    # User stats
    user_reqs = user_requests.get(user_id, [])
    user_hour = len([req for req in user_reqs if req > hour_ago])
    user_day = len([req for req in user_reqs if req > day_ago])

    # Service stats
    google_reqs = service_usage["google"]["requests"]
    groq_reqs = service_usage["groq"]["requests"]

    google_hour = len([req for req in google_reqs if req > hour_ago])
    groq_hour = len([req for req in groq_reqs if req > hour_ago])

    text = ai_limits_status_text(
        user_hour, user_day,
        google_hour, len(google_reqs),
        groq_hour, len(groq_reqs),
        MAX_USER_REQUESTS_HOUR,
        MAX_USER_REQUESTS_DAY
    )

    limits_msg = await message.answer(
        text,
        reply_markup=ai_limits_keyboard(),
        parse_mode="HTML"
    )
    await store_message(user_id, "ai", limits_msg.message_id)
    await state.update_data(limit_msg_id=limits_msg.message_id)


@ai_router.message(AIStates.waiting_question, F.text == __("🗑 Chatni tozalash"))
async def clear_chat_handler(message: Message, state: FSMContext, session: AsyncSession):
    """Clear all chat messages and resend welcome"""
    user_id = message.from_user.id

    # User xabarini ham saqlash
    await store_message(user_id, "ai", message.message_id)

    # Barcha AI xabarlarni o'chirish (user xabari ham)
    await delete_user_messages(message.bot, user_id, "ai")

    # Conversation history tozalash
    if user_id in user_conversations:
        del user_conversations[user_id]

    # Get user info
    try:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
    except:
        user = None

    # Yangi welcome message
    welcome_msg = await message.answer(
        ai_welcome_text(user),
        reply_markup=ai_menu_keyboard(),
        parse_mode="HTML"
    )
    await store_message(user_id, "ai", welcome_msg.message_id)
    await state.update_data(welcome_msg_id=welcome_msg.message_id)


@ai_router.message(AIStates.waiting_question, F.text == __("🏠 Asosiy Menyu"))
async def main_menu_from_ai(message: Message, state: FSMContext):
    """Return to main menu"""
    user_id = message.from_user.id

    await store_message(user_id, "ai", message.message_id)

    # 📱 Klaviaturani yopish
    temp_remove = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await temp_remove.delete()
    await asyncio.sleep(0.1)

    # Conversation history tozalash
    if user_id in user_conversations:
        del user_conversations[user_id]

    # Barcha xabarlarni o'chirish
    await asyncio.gather(
        delete_user_messages(message.bot, user_id, "ai"),
        delete_user_messages(message.bot, user_id, "menu"),
        return_exceptions=True
    )

    # State tozalash
    await state.clear()

    # Send main menu
    kb = await get_main_menu_keyboard()
    sent = await message.answer(
        get_main_text(),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await store_message(user_id, "menu", sent.message_id)


@ai_router.message(AIStates.waiting_question)
async def handle_other_messages(message: Message):
    """Handle other message types (not text)"""
    user_id = message.from_user.id

    await store_message(user_id, "ai", message.message_id)

    error_msg = await message.answer(
        ai_other_messages_text(),
        parse_mode="HTML"
    )
    await store_message(user_id, "ai", error_msg.message_id)


# 🔙 Callback handlers
@ai_router.callback_query(F.data == "ai_back_to_chat")
async def back_to_chat_handler(callback: CallbackQuery, state: FSMContext):
    """Back to chat from limits view"""
    await callback.answer()
    await state.set_state(AIStates.waiting_question)

    # Limitlar xabarini o'chirish
    try:
        await callback.message.delete()
    except:
        pass

    # Suhbatga qaytish xabari
    back_msg = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=ai_back_to_chat_text(),
        reply_markup=ai_menu_keyboard(),
        parse_mode="HTML"
    )
    await store_message(callback.from_user.id, "ai", back_msg.message_id)


@ai_router.callback_query(F.data == "ai_main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Return to main menu via callback"""
    await callback.answer()

    user_id = callback.from_user.id

    # 📱 Klaviaturani yopish
    temp_remove = await callback.bot.send_message(
        chat_id=user_id,
        text="...",
        reply_markup=ReplyKeyboardRemove()
    )
    await temp_remove.delete()
    await asyncio.sleep(0.1)

    # Conversation history tozalash
    if user_id in user_conversations:
        del user_conversations[user_id]

    # Callback message'ni o'chirish
    try:
        await callback.message.delete()
    except:
        pass

    # Barcha xabarlarni o'chirish
    await asyncio.gather(
        delete_user_messages(callback.bot, user_id, "ai"),
        delete_user_messages(callback.bot, user_id, "menu"),
        return_exceptions=True
    )

    # State tozalash
    await state.clear()

    # Send main menu
    kb = await get_main_menu_keyboard()
    sent = await callback.bot.send_message(
        chat_id=user_id,
        text=get_main_text(),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await store_message(user_id, "menu", sent.message_id)


# 🚀 Bot ishga tushganda cleanup'ni boshlash
async def start_ai_message_store_cleanup():
    """Bot start bo'lganda cleanup'ni ishga tushirish"""
    message_store.start_periodic_cleanup()