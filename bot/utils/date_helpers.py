# bot/utils/date_helpers.py

from datetime import datetime, timedelta


def get_previous_friday(date: datetime) -> datetime:
    """
    Berilgan sanadan oldingi yoki shu haftaning juma kunini qaytaradi.

    Mantiq:
    - Agar 1,2,3,4-kunlar (Du-Pa) bo'lsa → oldingi haftaning jumasi
    - Agar 5,6,7-kunlar (Ju-Ya) bo'lsa → shu haftaning jumasi
    """
    # weekday(): 0=Monday, 1=Tuesday, ..., 4=Friday, 5=Saturday, 6=Sunday
    weekday = date.weekday()

    if weekday < 4:  # 0,1,2,3 (Monday-Thursday)
        # Oldingi haftaning jumasi
        days_to_subtract = weekday + 3  # 3,4,5,6
        return date - timedelta(days=days_to_subtract)
    else:  # 4,5,6 (Friday-Sunday)
        # Shu haftaning jumasi
        days_to_subtract = weekday - 4  # 0,1,2
        return date - timedelta(days=days_to_subtract)


def get_next_exam_friday(last_exam_date: datetime) -> datetime:
    """
    Oxirgi imtihon sanasidan keyingi yilning juma kunini hisoblaydi.

    Mantiq:
    1. Oxirgi imtihon + 365 kun
    2. Bu sana haftaning qaysi kuniga to'g'ri kelsa:
       - 1,2,3,4 (Du-Pa) → oldingi haftaning jumasi
       - 5,6,7 (Ju-Ya) → shu haftaning jumasi
    """
    # 365 kun qo'shish
    next_year_date = last_exam_date + timedelta(days=365)

    # Haftaning qaysi kuni ekanligini aniqlash
    weekday = next_year_date.weekday()  # 0=Monday, 4=Friday, 6=Sunday

    if weekday < 4:  # 0,1,2,3 (Monday-Thursday)
        # Oldingi haftaning jumasi
        days_to_subtract = weekday + 3
        return next_year_date - timedelta(days=days_to_subtract)
    else:  # 4,5,6 (Friday-Sunday)
        # Shu haftaning jumasi
        days_to_subtract = weekday - 4
        return next_year_date - timedelta(days=days_to_subtract)


def get_next_friday(date: datetime) -> datetime:
    """
    Berilgan sanadan keyingi juma kunini qaytaradi.
    """
    weekday = date.weekday()
    days_to_add = (4 - weekday) % 7

    if days_to_add == 0 and date.weekday() == 4:
        # Agar bugun juma bo'lsa, keyingi juma
        days_to_add = 7

    return date + timedelta(days=days_to_add)


def get_days_until_friday(target_date: datetime) -> int:
    """
    Bugundan berilgan sana (juma)gacha qancha kun qolganini hisoblaydi.
    """
    today = datetime.now().date()
    target = target_date.date()
    return (target - today).days


# Test funksiyalari (ixtiyoriy)
if __name__ == "__main__":
    # Test oxirgi imtihon sanasi
    last_exam = datetime(2024, 6, 24)  # Dushanba

    print(f"Oxirgi imtihon: {last_exam.strftime('%A %d.%m.%Y')}")

    # 365 kun qo'shish
    next_year = last_exam + timedelta(days=365)
    print(f"365 kun keyin: {next_year.strftime('%A %d.%m.%Y')}")

    # Juma kuniga to'g'irlash
    next_exam = get_next_exam_friday(last_exam)
    print(f"Keyingi imtihon: {next_exam.strftime('%A %d.%m.%Y')}")

    # Test boshqa sanalar uchun
    test_dates = [
        datetime(2024, 3, 18),  # Dushanba
        datetime(2024, 3, 19),  # Seshanba
        datetime(2024, 3, 20),  # Chorshanba
        datetime(2024, 3, 21),  # Payshanba
        datetime(2024, 3, 22),  # Juma
        datetime(2024, 3, 23),  # Shanba
        datetime(2024, 3, 24),  # Yakshanba
    ]

    print("\n--- Test natijalar ---")
    for date in test_dates:
        next_exam = get_next_exam_friday(date)
        days = (next_exam - date).days
        print(f"{date.strftime('%A %d.%m.%Y')} → "
              f"Keyingi imtihon: {next_exam.strftime('%A %d.%m.%Y')} "
              f"({days} kun keyin)")