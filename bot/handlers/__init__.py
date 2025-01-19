from bot.distpatchers import dp
from bot.handlers.main import main


dp.include_router(*[
    main
])


