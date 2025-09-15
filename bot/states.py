from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    """Start handler states"""
    full_name = State()
    phone_number = State()


class MenuState(StatesGroup):
    language = State()


class TestState(StatesGroup):
    """Test handler states"""
    choosing_category = State()
    answering_question = State()
    showing_answer = State()
    finished = State()


class AIStates(StatesGroup):
    """Ai_assistant handler states"""
    waiting_question = State()
    viewing_limits = State()


class EquipmentState(StatesGroup):
    """Equipment handler states"""
    choosing_department = State()
    choosing_area = State()
    choosing_facility = State()
    choosing_equipment = State()
    viewing_detail = State()

class ExamSearchState(StatesGroup):
    """Exam_schedule handler states"""
    waiting_for_name = State()


class LibraryStates(StatesGroup):
    """Library handler states"""
    viewing_categories = State()
    viewing_books = State()
    viewing_book_detail = State()
    viewing_statistics = State()


class VideoStates(StatesGroup):
    """Video handler states"""
    viewing_categories = State()
    viewing_videos = State()
    viewing_video_detail = State()
    viewing_statistics = State()


class CompanyStates(StatesGroup):
    """Company handler states"""
    viewing_info = State()
    viewing_slideshow = State()


class TrainSafetyStates(StatesGroup):
    """Train_safety handler states"""
    viewing_folders = State()
    viewing_files = State()


