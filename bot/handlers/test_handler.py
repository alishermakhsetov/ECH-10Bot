from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from random import sample, shuffle
from typing import List, Optional
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
import asyncio
import time
from collections import defaultdict, deque
from aiogram.types import ReplyKeyboardRemove

from bot.states import TestState
from bot.buttons.inline import (
    test_category_keyboard,
    answer_keyboard,
    next_question_keyboard,
    back_to_categories_keyboard,
    test_result_keyboard,
    disable_answer_keyboard,
    result_with_next_question_keyboard,
    result_with_only_next_question_keyboard,
    timeout_result_keyboard,
    timeout_with_next_question_keyboard
)
from bot.utils.constants import QUESTION_TIME_LIMIT, UPDATE_INTERVAL, MAX_QUESTIONS, ANSWER_LETTERS
from bot.utils.texts import (
    get_main_text, test_no_categories_text, test_categories_prompt,
    test_category_empty, test_starting_text, test_question_header,
    test_time_remaining, test_time_up_result, test_correct_response,
    test_incorrect_response, test_finished_header, test_participant_label,
    test_result_label, test_percentage_label, test_grade_label,
    test_correct_answers_count, test_incorrect_answers_count,
    test_grade_excellent, test_grade_good, test_grade_satisfactory,
    test_grade_average, test_grade_unsatisfactory, test_congratulation_excellent,
    test_congratulation_good, test_congratulation_satisfactory,
    test_congratulation_average, test_congratulation_unsatisfactory,
    test_invalid_format_text, test_answer_not_found_text, test_time_expired_text,
    test_error_occurred, test_default_user_name, test_answer_variants_header,
    test_correct_response_short, test_incorrect_response_short
)
from db.models import CategoryTest, Test, AnswerTest, User

test_router = Router()

# Constants
MAX_MESSAGES_PER_USER = 5
CLEANUP_INTERVAL = 3600
TIMER_UPDATE_INTERVAL = 5
MAX_RETRIES = 3
RETRY_DELAY = 0.5
ANSWER_DISPLAY_TIME = 3
TEST_START_DELAY = 4
DELETE_CHUNK_SIZE = 10


class OptimizedMessageStore:
    def __init__(self):
        self.user_messages = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_USER))
        )
        self.last_cleanup = time.time()
        self._cleanup_task = None

    def store_message(self, user_id: int, message_id: int, category: str = "test"):
        self.user_messages[user_id][category].append(message_id)
        self._periodic_cleanup()

    def get_messages(self, user_id: int, category: str = "test") -> list[int]:
        return list(self.user_messages[user_id][category])

    def clear_user_messages(self, user_id: int, category: str = "test"):
        self.user_messages[user_id][category].clear()

    def _periodic_cleanup(self):
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
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup())

    async def _auto_cleanup(self):
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            self._periodic_cleanup()


message_store = OptimizedMessageStore()


async def store_message(user_id: int, category: str, message_id: int):
    try:
        message_store.store_message(user_id, message_id, category)
    except Exception:
        pass


async def delete_user_messages(bot, user_id: int, category: str, exclude_ids: Optional[list[int]] = None):
    msg_ids = message_store.get_messages(user_id, category)

    if exclude_ids:
        msg_ids = [msg_id for msg_id in msg_ids if msg_id not in exclude_ids]

    for i in range(0, len(msg_ids), DELETE_CHUNK_SIZE):
        chunk = msg_ids[i:i + DELETE_CHUNK_SIZE]
        tasks = [_safe_delete(bot, user_id, msg_id) for msg_id in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)

    if not exclude_ids:
        message_store.clear_user_messages(user_id, category)


async def _safe_delete(bot, chat_id: int, msg_id: int):
    for attempt in range(MAX_RETRIES):
        try:
            await bot.delete_message(chat_id, msg_id)
            return True
        except Exception:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False


async def send_clean_message(message: Message, text: str, reply_markup=None, category="test"):
    await delete_user_messages(message.bot, message.chat.id, category)
    sent = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await store_message(message.chat.id, category, sent.message_id)
    return sent


async def cleanup_timer(state: FSMContext):
    data = await state.get_data()
    timer_task = data.get("current_timer_task")

    if timer_task and not timer_task.done():
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass


def format_question_text(question: Test, answers: List[AnswerTest], current_num: int, total_num: int) -> str:
    """Savol matnini formatlash"""
    header = test_question_header(current_num, total_num)
    separator1 = "➖" * 15
    separator2 = "━" * 25

    text = f"<b>{header}</b>\n{separator1}\n"
    text += f"<b>{question.text}</b>\n{separator2}\n"

    # Javob variantlari
    text += test_answer_variants_header()
    text += "\n"  # Qo'shimcha enter
    for i, ans in enumerate(answers):
        if i < len(ANSWER_LETTERS):
            letter = ANSWER_LETTERS[i]
            text += f"<b>{letter})</b> {ans.text}\n"

    return text


def format_result_text_for_text_message(question: Test, selected_answer: AnswerTest,
                                        answers: List[AnswerTest], current_num: int, total_num: int) -> str:
    """Rasmsiz savollar uchun javob natijasini formatlash"""
    header = test_question_header(current_num, total_num)
    separator1 = "➖" * 15
    separator2 = "━" * 25

    text = f"<b>{header}</b>\n{separator1}\n"
    text += f"<b>{question.text}</b>\n{separator2}\n"

    # Natija
    if selected_answer.is_correct:
        text += test_correct_response()
    else:
        text += test_incorrect_response()

    # Javoblar
    text += test_answer_variants_header()
    text += "\n"  # Qo'shimcha enter
    for i, ans in enumerate(answers):
        if i < len(ANSWER_LETTERS):
            letter = ANSWER_LETTERS[i]

            if ans.id == selected_answer.id and selected_answer.is_correct:
                emoji = "✅"
            elif ans.id == selected_answer.id and not selected_answer.is_correct:
                emoji = "❌"
            elif ans.is_correct:
                emoji = "✅"
            else:
                emoji = ""

            text += f"{emoji} <b>{letter})</b> {ans.text}\n"

    return text


def format_timeout_text_for_text_message(question: Test, answers: List[AnswerTest],
                                         current_num: int, total_num: int) -> str:
    """Rasmsiz savollar uchun vaqt tugaganda ko'rsatiladigan matn"""
    header = test_question_header(current_num, total_num)
    separator1 = "➖" * 15
    separator2 = "━" * 25

    text = f"<b>{header}</b>\n{separator1}\n"
    text += f"<b>{question.text}</b>\n{separator2}\n"

    text += test_time_up_result()
    text += test_answer_variants_header()
    text += "\n"  # Qo'shimcha enter

    for i, ans in enumerate(answers):
        if i < len(ANSWER_LETTERS):
            letter = ANSWER_LETTERS[i]
            emoji = "✅" if ans.is_correct else ""
            text += f"{emoji} <b>{letter})</b> {ans.text}\n"

    return text


@test_router.message(F.text == __("🧠 Test"))
async def show_test_categories(message: Message, state: FSMContext, session: AsyncSession):
    await store_message(message.from_user.id, "test", message.message_id)

    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(0.1)
    await temp_msg.delete()

    await state.clear()
    await state.update_data(user_telegram_id=message.from_user.id)

    result = await session.execute(select(CategoryTest))
    categories = result.scalars().all()

    if not categories:
        text = test_no_categories_text()
        reply_markup = None
    else:
        text = test_categories_prompt()
        reply_markup = test_category_keyboard(categories)

    sent = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await store_message(message.chat.id, "test", sent.message_id)

    await asyncio.gather(
        delete_user_messages(message.bot, message.from_user.id, "menu"),
        delete_user_messages(message.bot, message.from_user.id, "test", exclude_ids=[sent.message_id])
    )

    await state.set_state(TestState.choosing_category)


@test_router.callback_query(F.data.startswith("test_category:"))
async def start_test(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        category_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(test_invalid_format_text())
        return

    result = await session.execute(select(Test).where(Test.category_test_id == category_id))
    questions = result.scalars().all()

    if not questions:
        return await callback.message.edit_text(
            test_category_empty(),
            reply_markup=back_to_categories_keyboard()
        )

    selected_questions = sample(questions, min(MAX_QUESTIONS, len(questions)))

    await state.update_data(
        questions=[q.id for q in selected_questions],
        index=0,
        correct=0,
        category_id=category_id,
        timer_active=True,
        current_timer_task=None,
        user_telegram_id=callback.from_user.id
    )

    await state.set_state(TestState.answering_question)
    await callback.message.delete()

    start_msg = await callback.message.answer(test_starting_text(len(selected_questions)))
    await asyncio.sleep(TEST_START_DELAY)
    await start_msg.delete()

    await send_question(callback.message, state, session)


async def send_question(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    index = data["index"]
    question_ids: List[int] = data["questions"]

    if index >= len(question_ids):
        return await show_result(message, state, session)

    question_id = question_ids[index]
    question = await session.get(Test, question_id)

    if not question:
        await state.update_data(index=index + 1)
        return await send_question(message, state, session)

    result = await session.execute(select(AnswerTest).where(AnswerTest.test_id == question.id))
    answers = result.scalars().all()
    answers_list = list(answers)
    shuffle(answers_list)

    markup = answer_keyboard(answers_list, question.id)
    countdown = QUESTION_TIME_LIMIT

    question_text = format_question_text(question, answers_list, index + 1, len(question_ids))
    timer_text = lambda s: f"{question_text}\n\n{test_time_remaining(s)}"

    await state.update_data(timer_active=True, current_answers=answers_list)

    try:
        if question.image:
            sent_msg = await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=question.image,
                caption=timer_text(countdown),
                reply_markup=markup,
                parse_mode="HTML"
            )
        else:
            sent_msg = await message.answer(timer_text(countdown), reply_markup=markup, parse_mode="HTML")

        await store_message(message.chat.id, "test", sent_msg.message_id)
    except Exception:
        await state.update_data(index=index + 1)
        return await send_question(message, state, session)

    # Timer
    async def countdown_timer():
        for sec in range(countdown - TIMER_UPDATE_INTERVAL, 0, -TIMER_UPDATE_INTERVAL):
            await asyncio.sleep(TIMER_UPDATE_INTERVAL)
            current_data = await state.get_data()
            if not current_data.get("timer_active", False):
                return

            try:
                updated_text = timer_text(sec)
                if question.image:
                    await sent_msg.edit_caption(caption=updated_text, reply_markup=markup, parse_mode="HTML")
                else:
                    await sent_msg.edit_text(updated_text, reply_markup=markup, parse_mode="HTML")
            except Exception:
                break

        # Vaqt tugadi
        current_data = await state.get_data()
        if current_data.get("timer_active", False):
            await state.update_data(index=index + 1, timer_active=False)
            correct_answer = next((a for a in answers_list if a.is_correct), None)

            try:
                if question.image:
                    # Rasmli savollar uchun - caption yangilash (timer matni olib tashlanadi)
                    clean_caption = format_question_text(question, answers_list, index + 1, len(question_ids))
                    await sent_msg.edit_caption(
                        clean_caption,
                        reply_markup=timeout_result_keyboard(answers_list, question.id, -1,
                                                           correct_answer.id if correct_answer else -1),
                        parse_mode="HTML"
                    )
                else:
                    # Rasmsiz savollar uchun - matnni o'zgartirish
                    timeout_text = format_timeout_text_for_text_message(question, answers_list, index + 1,
                                                                        len(question_ids))
                    await sent_msg.edit_text(
                        timeout_text,
                        reply_markup=disable_answer_keyboard(answers_list, question.id, -1,
                                                             correct_answer.id if correct_answer else -1),
                        parse_mode="HTML"
                    )
            except Exception:
                pass

            await asyncio.sleep(ANSWER_DISPLAY_TIME)

            if index + 1 >= len(question_ids):
                await show_result(message, state, session)
            else:
                await state.set_state(TestState.showing_answer)
                try:
                    if question.image:
                        # Rasmli savollar uchun - vaqt tugadi + keyingi savol
                        clean_caption = format_question_text(question, answers_list, index + 1, len(question_ids))
                        await sent_msg.edit_caption(
                            clean_caption,
                            reply_markup=timeout_with_next_question_keyboard(),
                            parse_mode="HTML"
                        )
                    else:
                        # Rasmsiz savollar uchun - keyingi savol tugmasi
                        await sent_msg.edit_reply_markup(reply_markup=next_question_keyboard())
                except Exception:
                    pass

    timer_task = asyncio.create_task(countdown_timer())
    await state.update_data(current_timer_task=timer_task)


@test_router.callback_query(F.data.startswith("answer:"))
async def handle_answer(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        parts = callback.data.split(":")
        if len(parts) != 3:
            return await callback.answer(test_invalid_format_text())

        _, question_id, answer_id = parts
        answer = await session.get(AnswerTest, int(answer_id))
        question = await session.get(Test, int(question_id))
    except Exception:
        return await callback.answer(test_invalid_format_text())

    if not answer or not question:
        return await callback.answer(test_answer_not_found_text())

    data = await state.get_data()
    if not data.get("timer_active", False):
        return await callback.answer(test_time_expired_text())

    await cleanup_timer(state)

    current_answers = data.get("current_answers", [])
    correct_answer = next((a for a in current_answers if a.is_correct), None)

    correct = data["correct"] + (1 if answer.is_correct else 0)
    index = data["index"] + 1
    current_num = data["index"] + 1
    total_num = len(data["questions"])

    await state.update_data(correct=correct, index=index, timer_active=False)

    try:
        if question.image:
            # Rasmli savollar uchun - birinchi bosqich: natija + javob tugmalari
            result_text = test_correct_response_short() if answer.is_correct else test_incorrect_response_short()
            await callback.message.edit_reply_markup(
                reply_markup=result_with_next_question_keyboard(
                    current_answers, question.id, answer.id,
                    correct_answer.id if correct_answer else -1,
                    result_text
                )
            )
        else:
            # Rasmsiz savollar uchun - matnni o'zgartirish
            result_text = format_result_text_for_text_message(question, answer, current_answers, current_num, total_num)
            await callback.message.edit_text(
                result_text,
                reply_markup=disable_answer_keyboard(current_answers, question.id, answer.id,
                                                     correct_answer.id if correct_answer else -1),
                parse_mode="HTML"
            )
    except Exception:
        pass

    await asyncio.sleep(ANSWER_DISPLAY_TIME)

    if index >= len(data["questions"]):
        await show_result(callback.message, state, session)
        return

    try:
        if question.image:
            # Rasmli savollar uchun - ikkinchi bosqich: natija + keyingi savol (A,B,C,D o'rnida)
            result_text = test_correct_response_short() if answer.is_correct else test_incorrect_response_short()
            await callback.message.edit_reply_markup(
                reply_markup=result_with_only_next_question_keyboard(result_text)
            )
        else:
            # Rasmsiz savollar uchun keyingi savol tugmasini ko'rsatish
            await callback.message.edit_reply_markup(reply_markup=next_question_keyboard())
    except Exception:
        pass

    await state.set_state(TestState.showing_answer)


@test_router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    await callback.message.delete()
    await send_question(callback.message, state, session)
    await state.set_state(TestState.answering_question)


@test_router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await cleanup_timer(state)
    await callback.answer()
    await callback.message.delete()
    await show_test_categories(callback.message, state, session)


@test_router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    from bot.buttons.reply import get_main_menu_keyboard

    await cleanup_timer(state)
    await callback.answer()
    await callback.message.delete()

    await asyncio.gather(
        delete_user_messages(callback.bot, callback.from_user.id, "test"),
        delete_user_messages(callback.bot, callback.from_user.id, "menu")
    )

    await state.clear()

    kb = await get_main_menu_keyboard()
    sent = await callback.message.answer(get_main_text(), reply_markup=kb, parse_mode="HTML")
    await store_message(callback.from_user.id, "menu", sent.message_id)


async def show_result(message: Message, state: FSMContext, session: AsyncSession):
    try:
        data = await state.get_data()
        correct = data.get("correct", 0)
        total = len(data.get("questions", []))
        percentage = round((correct / total) * 100, 1) if total > 0 else 0

        user_telegram_id = data.get("user_telegram_id")
        if not user_telegram_id:
            user_telegram_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id

        result = await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )
        user = result.scalar_one_or_none()
        name = user.full_name if user and user.full_name else test_default_user_name()

        # Baholash
        if percentage >= 90:
            grade_emoji = "🏆"
            grade_text = test_grade_excellent()
            congrats = test_congratulation_excellent()
        elif percentage >= 80:
            grade_emoji = "🥇"
            grade_text = test_grade_good()
            congrats = test_congratulation_good()
        elif percentage >= 70:
            grade_emoji = "🥈"
            grade_text = test_grade_satisfactory()
            congrats = test_congratulation_satisfactory()
        elif percentage >= 60:
            grade_emoji = "🥉"
            grade_text = test_grade_average()
            congrats = test_congratulation_average()
        else:
            grade_emoji = "📚"
            grade_text = test_grade_unsatisfactory()
            congrats = test_congratulation_unsatisfactory()

        header = test_finished_header()
        separator = "▬" * 18 + "\n\n"

        result_text = (
            f"{header}{separator}"
            f"{test_participant_label(name)}"
            f"{test_result_label(correct, total)}"
            f"{test_percentage_label(percentage)}"
            f"{grade_emoji} {test_grade_label(grade_text)}"
            f"{test_correct_answers_count(correct)}"
            f"{test_incorrect_answers_count(total - correct)}"
            f"{separator}"
            f"{congrats}"
        )

        await send_clean_message(
            message,
            result_text,
            reply_markup=test_result_keyboard(correct, total),
            category="test"
        )
        await state.set_state(TestState.finished)

    except Exception:
        try:
            await send_clean_message(message, test_error_occurred(), category="test")
        except Exception:
            pass


async def start_message_store_cleanup():
    message_store.start_periodic_cleanup()