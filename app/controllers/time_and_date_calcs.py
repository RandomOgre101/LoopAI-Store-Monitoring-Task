import pytz
from datetime import datetime


def convert_timestamp_timezone(timestamp, current_timezone, target_timezone):
    current_tz = pytz.timezone(current_timezone)
    target_tz = pytz.timezone(target_timezone)
    
    localized_timestamp = current_tz.localize(timestamp)
    
    converted_timestamp = localized_timestamp.astimezone(target_tz)
    
    return converted_timestamp.strftime("%H:%M:%S")



# def check_if_in_timezone(timestamp, current_timezone, target_timezone, start_time, end_time):
#     converted_time = convert_timestamp_timezone(timestamp, current_timezone, target_timezone)

#     return start_time <= str(converted_time) <= end_time



def get_day_from_date(date):
    day_of_week = date.weekday()

    return day_of_week