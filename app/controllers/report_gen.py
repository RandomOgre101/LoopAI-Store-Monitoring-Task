from sqlalchemy.orm import Session
from ..DB.db_connection import SessionLocal, Base, engine
from ..DB import models 
from . import time_and_date_calcs as tdc
from sqlalchemy.inspection import inspect
from sqlalchemy import func

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def serialize_data(objects):
    return [{c.name: getattr(obj, c.name) for c in obj.__table__.columns} for obj in objects] if type(objects) == list else {c.name: getattr(objects, c.name) for c in objects.__table__.columns}



def get_last_hour_data(db: Session, sid: int):
    i: int = 0

    store_timezone_query: models.Timezone = db.query(models.Timezone).filter(models.Timezone.store_id == sid).first()
    if store_timezone_query:
        store_timezone = serialize_data(store_timezone_query)['timezone_str']
    else:
        store_timezone = 'America/Chicago'
    

    latest_time_query: list = db.query(models.StoreStatus).\
                        order_by(models.StoreStatus.timestamp_utc.desc()).\
                        filter(models.StoreStatus.store_id == sid).all()
    
    latest_time_data: list = serialize_data(latest_time_query)
    time_in_range: bool = True

    # edge case: prev record might not be same day - handled
    while time_in_range or i >= len(latest_time_data):
        
        day_of_week = tdc.get_day_from_date(latest_time_data[i]['timestamp_utc'])

        start_end_time_query = db.query(models.WorkHours).filter(models.WorkHours.store_id == sid, 
                                                                 (models.WorkHours.day == day_of_week) 
                                                                 ).first()
        if start_end_time_query:
            query_data = serialize_data(start_end_time_query)

            local_start_time, local_end_time = query_data['start_time_local'], query_data['end_time_local']
        else:
            local_start_time, local_end_time = '00:00:00', "23:59:57"

        converted_time = tdc.convert_timestamp_timezone(latest_time_data[i]['timestamp_utc'], 'UTC', store_timezone)
        
        if ( 
            str(local_start_time) <= str(converted_time) <= str(local_end_time) ):
            hour_data = [converted_time, latest_time_data[i]['status']]
            time_in_range = False
        else:
            i += 1
    
    if ((i+1) < len(latest_time_data) and 
        latest_time_data[i+1]['timestamp_utc'].day == latest_time_data[i]['timestamp_utc'].day and
        latest_time_data[i+1]['timestamp_utc'].hour == latest_time_data[i]['timestamp_utc'].hour - 1):
        prev_hour_data: list = [tdc.convert_timestamp_timezone(latest_time_data[i+1]['timestamp_utc'], 'UTC', store_timezone), latest_time_data[i+1]['status']]
    else:
        prev_hour_data = None


    uptime: int = 0
    downtime: int = 0

    if (prev_hour_data and 
        prev_hour_data[0].split(":")[1] < hour_data[0].split(":")[1]
        ):

        hour_min: int = int(hour_data[0].split(":")[1])
        prev_min: int = int(prev_hour_data[0].split(":")[1])

        if (prev_hour_data[1] == 'active' and
            hour_data[1] == 'active'
            ):
            uptime += 60
        
        elif (prev_hour_data[1] == 'active' and
              hour_data[1] == 'inactive'
              ):         
            uptime += 60
        
        elif (prev_hour_data[1] == 'inactive' and
              hour_data[1] == 'active'
              ):
            downtime += 60
        
        elif (prev_hour_data[1] == 'inactive' and
              hour_data[1] == 'inactive'):
            downtime += 60
    

    elif (prev_hour_data and 
          prev_hour_data[0].split(":")[1] >= hour_data[0].split(":")[1]
          ):
        hour_min: int = int(hour_data[0].split(":")[1])
        prev_min: int = int(prev_hour_data[0].split(":")[1])

        if (prev_hour_data[1] == 'active' and
            hour_data[1] == 'active'
            ):
            uptime += 60
        
        elif (prev_hour_data[1] == 'active' and
              hour_data[1] == 'inactive'
              ):         
            uptime += 60 - (prev_min - hour_min)
            downtime += 60 - uptime
        
        elif (prev_hour_data[1] == 'inactive' and
              hour_data[1] == 'active'
              ):
            downtime += 60
        
        elif (prev_hour_data[1] == 'inactive' and
              hour_data[1] == 'inactive'):
            downtime += 60
    

    elif prev_hour_data is None:
        downtime += 60

    return uptime, downtime



def get_last_day_data(db: Session, sid: int):

    store_timezone_query: models.Timezone = db.query(models.Timezone).filter(models.Timezone.store_id == sid).first()
    if store_timezone_query:
        store_timezone = serialize_data(store_timezone_query)['timezone_str']
    else:
        store_timezone = 'America/Chicago'


    latest_date_query = db.query(func.max(models.StoreStatus.timestamp_utc)).\
                        filter(models.StoreStatus.store_id == sid).first()[0]
    latest_date = latest_date_query.day
    latest_month = str(latest_date_query.month) if len(str(latest_date_query.month)) > 1 else "0"+str(latest_date_query.month)
    latest_year = latest_date_query.year

    on_latest_date_query = db.query(models.StoreStatus).\
                            filter(models.StoreStatus.store_id == sid, 
                                   func.to_char(models.StoreStatus.timestamp_utc, 'YYYY-MM-DD HH24:MI:SS').\
                                   like(f'{latest_year}-{latest_month}-{latest_date}%')).\
                            order_by(models.StoreStatus.timestamp_utc).all()

    on_latest_date_data = serialize_data(on_latest_date_query)
    
    
    
    day_of_week = tdc.get_day_from_date(latest_date_query)

    start_end_time_query = db.query(models.WorkHours).\
                            filter(models.WorkHours.store_id == sid, 
                                (models.WorkHours.day == day_of_week)).first()
    if start_end_time_query:
        query_data = serialize_data(start_end_time_query)
        local_start_time, local_end_time = str(query_data['start_time_local']), str(query_data['end_time_local'])
    else:
        local_start_time, local_end_time = '00:00:00', "23:59:57"

    valid_timestamps_on_latest_day = []

    for data in on_latest_date_data:
        converted_time = str(tdc.convert_timestamp_timezone(data['timestamp_utc'], 'UTC', store_timezone))

        if local_start_time <= converted_time <= local_end_time:
            valid_timestamps_on_latest_day.append([converted_time, data['status']])
    
    print(len(valid_timestamps_on_latest_day))
    index = 0
    start_hour, start_minute = int(local_start_time.split(":")[0]), int(local_start_time.split(":")[1])
    end_hour, end_minute = int(local_end_time.split(":")[0]), int(local_end_time.split(":")[1])
    uptime, downtime = 0, 0

    while index < ( len(valid_timestamps_on_latest_day) -1 ):

        hour_1 = int(valid_timestamps_on_latest_day[index][0].split(":")[0])
        hour_2 = int(valid_timestamps_on_latest_day[index+1][0].split(":")[0])

        minute_1 = int(valid_timestamps_on_latest_day[index][0].split(":")[1])
        minute_2 = int(valid_timestamps_on_latest_day[index+1][0].split(":")[1])

        status_1 = valid_timestamps_on_latest_day[index][1]
        status_2 = valid_timestamps_on_latest_day[index+1][1]

        if index == 0:
            is_start = True
        else:
            is_start = False

        up, dwn = tdc.calculate_uptime_downtime(start_hour, start_minute, end_hour, end_minute, hour_1, hour_2, minute_1, minute_2, status_1, status_2, is_start)
        uptime += up
        downtime += dwn

        index += 1

    print(uptime, downtime)
    
    if (uptime + downtime)/60 == (end_hour - start_hour) or int((uptime + downtime)/60) == 24:
        return uptime, downtime
    elif end_hour - start_hour == 23:
        return uptime, downtime + int(( 24 - (uptime + downtime)/60 )*60)
    else:
        return uptime, downtime + int(( (end_hour - start_hour) - (uptime + downtime)/60 )*60)
