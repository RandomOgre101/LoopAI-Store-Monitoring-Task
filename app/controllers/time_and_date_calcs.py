import pytz
from datetime import datetime


def convert_timestamp_timezone(timestamp, current_timezone, target_timezone):
    current_tz = pytz.timezone(current_timezone)
    target_tz = pytz.timezone(target_timezone)
    
    localized_timestamp = current_tz.localize(timestamp)
    
    converted_timestamp = localized_timestamp.astimezone(target_tz)
    
    return converted_timestamp.strftime("%H:%M:%S")


def calculate_uptime_downtime(start_hour, start_minute, end_hour, end_minute, 
                                hour_1, hour_2, minute_1, minute_2, status_1, status_2, 
                                is_start):
    uptime: int = 0
    downtime: int = 0

    if hour_1 == hour_2:
        if ((status_1 == 'active' and status_2 == 'active') or
            (status_1 == 'inactive' and status_2 == 'inactive')
            ):
            return uptime, downtime
        
        elif (status_1 == 'inactive' and status_2 == 'active'
              ):
            return uptime, downtime + minute_2
        
        elif (status_1 == 'active' and status_2 == 'inactive' 
              ):
            return uptime + minute_2, downtime

    if is_start:
        if status_1 == 'active':
            uptime += 60
        else:
            downtime += 60 * (hour_1 - start_hour)
    
    else:
        if hour_2 - hour_1 > 1:
            downtime += 60 * (hour_2 - hour_1)
        
        else:
            if minute_1 < minute_2:
                if ((status_1 == 'active' and status_2 == 'active') or
                    (status_1 == 'active' and status_2 == 'inactive')
                    ):
                    uptime += 60
                
                else:
                    downtime += 60
                
            else:
                if (status_1 == 'active' and status_2 == 'active'):
                    uptime += 60
                
                elif (status_1 == 'active' and status_2 == 'inactive'):
                    uptime += 60 - (minute_1 - minute_2)
                    downtime += 60 - uptime
                
                else:
                    downtime += 60

    return uptime, downtime




def get_day_from_date(date):
    day_of_week = date.weekday()

    return day_of_week