from typing import Tuple


def get_exam_status(days_left: int) -> Tuple[str, str]:
    """Imtihon statusini aniqlash"""
    from bot.utils.texts import (
        exam_status_overdue_text, exam_status_urgent_text,
        exam_status_warning_text, exam_status_normal_text,
        exam_status_safe_text
    )

    if days_left < 0:
        return "⛔", exam_status_overdue_text(abs(days_left))
    elif days_left <= 5:
        return "🔴", exam_status_urgent_text(days_left)
    elif days_left <= 10:
        return "🟡", exam_status_warning_text(days_left)
    elif days_left <= 30:
        return "🟢", exam_status_normal_text(days_left)
    return "🔵", exam_status_safe_text(days_left)