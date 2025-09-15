from bot.distpatchers import dp
from bot.handlers.accident_handler import accident_router
from bot.handlers.ai_assistant_handler import ai_router
from bot.handlers.company_handler import company_router
from bot.handlers.equipment_handler import equipment_router
from bot.handlers.exam_schedule_handler import exam_schedule_router
from bot.handlers.group_events import group_router
from bot.handlers.language_handler import language_router
from bot.handlers.library_handler import library_router
from bot.handlers.media_handler import media_router
from bot.handlers.test_handler import test_router
from bot.handlers.text_handler import text_router
from bot.handlers.start_handler import main_router
from bot.handlers.train_safety_handler import train_safety_router
from bot.handlers.video_handler import video_router

dp.include_routers(
    group_router,
    accident_router,
    company_router,
    equipment_router,
    exam_schedule_router,
    language_router,
    library_router,
    media_router,
    main_router,
    test_router,
    video_router,
    train_safety_router,
    ai_router,
    text_router,
)


