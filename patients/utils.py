from zoneinfo import ZoneInfo
from django.utils.timezone import now, localtime


def get_india_timezone():
    # india_timezone = ZoneInfo('Asia/Kolkata')
    # current_time = now().astimezone(india_timezone)
    current_time = localtime(now())
    current_date = current_time.date()
    current_time_obj = current_time.time()
    
    return current_date, current_time_obj

