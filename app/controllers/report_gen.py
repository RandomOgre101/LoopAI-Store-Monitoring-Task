from sqlalchemy.orm import Session
from ..DB import models 
from . import time_and_date_calcs as tdc
from sqlalchemy import func


class ReportGen:
    def __init__(self, sid: int, db: Session):
        self.sid = sid
        self.db = db

        store_timezone_query: models.Timezone = self.db.query(models.Timezone).filter(models.Timezone.store_id == sid).first()
        if store_timezone_query:
            self.store_timezone = self.serialize_data(store_timezone_query)['timezone_str']
        else:
            self.store_timezone = 'America/Chicago'

    def serialize_data(self, objects):
        return [{c.name: getattr(obj, c.name) for c in obj.__table__.columns} for obj in objects] if type(objects) == list else {c.name: getattr(objects, c.name) for c in objects.__table__.columns}


    def get_last_hour_data(self):
        i: int = 0

        latest_time_query: list = self.db.query(models.StoreStatus).\
                            order_by(models.StoreStatus.timestamp_utc.desc()).\
                            filter(models.StoreStatus.store_id == self.sid).all()
        
        latest_time_data: list = self.serialize_data(latest_time_query)
        time_in_range: bool = True

        # edge case: prev record might not be same day - handled
        while time_in_range or i >= len(latest_time_data):
            
            day_of_week = tdc.get_day_from_date(latest_time_data[i]['timestamp_utc'])

            start_end_time_query = self.db.query(models.WorkHours).filter(models.WorkHours.store_id == self.sid, 
                                                                    (models.WorkHours.day == day_of_week) 
                                                                    ).first()
            if start_end_time_query:
                query_data = self.serialize_data(start_end_time_query)

                local_start_time, local_end_time = query_data['start_time_local'], query_data['end_time_local']
            else:
                local_start_time, local_end_time = '00:00:00', "23:59:57"

            converted_time = tdc.convert_timestamp_timezone(latest_time_data[i]['timestamp_utc'], 'UTC', self.store_timezone)
            
            if ( 
                str(local_start_time) <= str(converted_time) <= str(local_end_time) ):
                hour_data = [converted_time, latest_time_data[i]['status']]
                time_in_range = False
            else:
                i += 1
        
        if ((i+1) < len(latest_time_data) and 
            latest_time_data[i+1]['timestamp_utc'].day == latest_time_data[i]['timestamp_utc'].day and
            latest_time_data[i+1]['timestamp_utc'].hour == latest_time_data[i]['timestamp_utc'].hour - 1):
            prev_hour_data: list = [tdc.convert_timestamp_timezone(latest_time_data[i+1]['timestamp_utc'], 'UTC', self.store_timezone), latest_time_data[i+1]['status']]
        else:
            prev_hour_data = None


        uptime: int = 0
        downtime: int = 0

        # if (prev_hour_data and 
        #     prev_hour_data[0].split(":")[1] < hour_data[0].split(":")[1]
        #     ):

        #     hour_min: int = int(hour_data[0].split(":")[1])
        #     prev_min: int = int(prev_hour_data[0].split(":")[1])

        #     if (prev_hour_data[1] == 'active' and
        #         hour_data[1] == 'active'
        #         ):
        #         uptime += 60
            
        #     elif (prev_hour_data[1] == 'active' and
        #         hour_data[1] == 'inactive'
        #         ):         
        #         uptime += 60
            
        #     elif (prev_hour_data[1] == 'inactive' and
        #         hour_data[1] == 'active'
        #         ):
        #         downtime += 60
            
        #     elif (prev_hour_data[1] == 'inactive' and
        #         hour_data[1] == 'inactive'):
        #         downtime += 60
        

        # elif (prev_hour_data and 
        #     prev_hour_data[0].split(":")[1] >= hour_data[0].split(":")[1]
        #     ):
        #     hour_min: int = int(hour_data[0].split(":")[1])
        #     prev_min: int = int(prev_hour_data[0].split(":")[1])

        #     if (prev_hour_data[1] == 'active' and
        #         hour_data[1] == 'active'
        #         ):
        #         uptime += 60
            
        #     elif (prev_hour_data[1] == 'active' and
        #         hour_data[1] == 'inactive'
        #         ):         
        #         uptime += 60 - (prev_min - hour_min)
        #         downtime += 60 - uptime
            
        #     elif (prev_hour_data[1] == 'inactive' and
        #         hour_data[1] == 'active'
        #         ):
        #         downtime += 60
            
        #     elif (prev_hour_data[1] == 'inactive' and
        #         hour_data[1] == 'inactive'):
        #         downtime += 60
        
        if prev_hour_data is None:
            downtime += 60
        else:
            hour_1 = int(prev_hour_data[0].split(":")[0])
            hour_2 = int(hour_data[0].split(":")[0])

            minute_1 = int(prev_hour_data[0].split(":")[1])
            minute_2 = int(hour_data[0].split(":")[1])

            status_1 = prev_hour_data[1]
            status_2 = hour_data[1]

            up, dwn = tdc.calculate_uptime_downtime(None, None, None, None, hour_1, hour_2, minute_1, minute_2, status_1, status_2, False)
            uptime += up
            downtime += dwn

        return uptime, downtime


    def get_last_day_data(self):

        latest_date_query = self.db.query(func.max(models.StoreStatus.timestamp_utc)).\
                            filter(models.StoreStatus.store_id == self.sid).first()[0]
        latest_date = latest_date_query.day
        latest_month = str(latest_date_query.month) if len(str(latest_date_query.month)) > 1 else "0" + str(latest_date_query.month)
        latest_year = latest_date_query.year

        on_latest_date_query = self.db.query(models.StoreStatus).\
                                filter(models.StoreStatus.store_id == self.sid, 
                                    func.to_char(models.StoreStatus.timestamp_utc, 'YYYY-MM-DD HH24:MI:SS').\
                                    like(f'{latest_year}-{latest_month}-{latest_date}%')).\
                                order_by(models.StoreStatus.timestamp_utc).all()

        on_latest_date_data = self.serialize_data(on_latest_date_query)
        

        day_of_week = tdc.get_day_from_date(latest_date_query)

        start_end_time_query = self.db.query(models.WorkHours).\
                                filter(models.WorkHours.store_id == self.sid, 
                                    (models.WorkHours.day == day_of_week)).first()
        if start_end_time_query:
            query_data = self.serialize_data(start_end_time_query)
            local_start_time, local_end_time = str(query_data['start_time_local']), str(query_data['end_time_local'])
        else:
            local_start_time, local_end_time = '00:00:00', "23:59:57"

        valid_timestamps_on_latest_day = []

        for data in on_latest_date_data:
            converted_time = str(tdc.convert_timestamp_timezone(data['timestamp_utc'], 'UTC', self.store_timezone))

            if local_start_time <= converted_time <= local_end_time:
                valid_timestamps_on_latest_day.append([converted_time, data['status']])
        
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

        
        if (uptime + downtime)/60 == (end_hour - start_hour) or int((uptime + downtime)/60) == 24:
            return int(uptime/60), int(downtime/60)
        elif end_hour - start_hour == 23:
            return int(uptime/60), int(downtime + int(( 24 - (uptime + downtime)/60 )*60)) / 60
        else:
            return int(uptime/60), int(int(downtime + int(( (end_hour - start_hour) - (uptime + downtime)/60 )*60)) /60)
    

    def get_last_week_data(self):

        latest_date_query = self.db.query(func.max(models.StoreStatus.timestamp_utc)).\
                            filter(models.StoreStatus.store_id == self.sid).first()[0]
        latest_date = latest_date_query.day
        latest_month = str(latest_date_query.month) if len(str(latest_date_query.month)) > 1 else "0" + str(latest_date_query.month)
        latest_year = latest_date_query.year

        data_for_past_week_query = self.db.query(models.StoreStatus).\
                                filter(models.StoreStatus.store_id == self.sid,
                                       models.StoreStatus.timestamp_utc.\
                                        between(f'{latest_year}-{latest_month}-{latest_date-6}', f'{latest_year}-{latest_month}-{latest_date+1}')).\
                                order_by(models.StoreStatus.timestamp_utc).all()

        week_data = self.serialize_data(data_for_past_week_query)

                                    #  timestamp, status, start_time, end_time
        valid_timestamps_for_week = [ [ [], None, None ] for i in range(7) ]
        first_date_of_data = current_day = week_data[0]['timestamp_utc'].day
        day_of_week = tdc.get_day_from_date(week_data[0]['timestamp_utc'])
        start_end_time_query = self.db.query(models.WorkHours).\
                                filter(models.WorkHours.store_id == self.sid, 
                                    (models.WorkHours.day == day_of_week)).first()
        if start_end_time_query:
            query_data = self.serialize_data(start_end_time_query)
            local_start_time, local_end_time = str(query_data['start_time_local']), str(query_data['end_time_local'])
            start_end_exists = True
        else:
            local_start_time, local_end_time = '00:00:00', "23:59:59"
            start_end_exists = False


        for data in week_data:
            if data['timestamp_utc'].day != current_day:
                day_of_week = tdc.get_day_from_date(data['timestamp_utc'])
                current_day = data['timestamp_utc'].day

                if start_end_exists:
                    start_end_time_query = self.db.query(models.WorkHours).\
                                filter(models.WorkHours.store_id == self.sid, 
                                    (models.WorkHours.day == day_of_week)).first()
                    if not start_end_time_query:
                        valid_timestamps_for_week[day_of_week][1] = 0
                        valid_timestamps_for_week[day_of_week][2] = 0
                    else:
                        query_data = self.serialize_data(start_end_time_query)
                        local_start_time, local_end_time = str(query_data['start_time_local']), str(query_data['end_time_local'])


            else:
                converted_time = str(tdc.convert_timestamp_timezone(data['timestamp_utc'], 'UTC', self.store_timezone))
                valid_timestamps_for_week[day_of_week][1] = local_start_time
                valid_timestamps_for_week[day_of_week][2] = local_end_time
                if local_start_time <= converted_time <= local_end_time:
                    valid_timestamps_for_week[day_of_week][0].append([converted_time, data['status']])
            
        for i in range(len(valid_timestamps_for_week)):
            if (not valid_timestamps_for_week[i][1] and 
                not valid_timestamps_for_week[i][2]
                ):
                if start_end_exists:
                    start_end_query = self.db.query(models.WorkHours).\
                                            filter(models.WorkHours.store_id == self.sid, 
                                                (models.WorkHours.day == i)).first()
                    if not start_end_query:
                        valid_timestamps_for_week[i][1] = 0
                        valid_timestamps_for_week[i][2] = 0
                    else:
                        start_end_query_data = self.serialize_data(start_end_query)
                        valid_timestamps_for_week[i][1] = str(start_end_query_data['start_time_local'])
                        valid_timestamps_for_week[i][2] = str(start_end_query_data['end_time_local'])
                else:
                    valid_timestamps_for_week[i][1] = '00:00:00'
                    valid_timestamps_for_week[i][2] = "23:59:57"
                    
        
        final_uptime = 0
        final_downtime = 0

        for day_data in valid_timestamps_for_week:
            index = 0
            uptime = 0
            downtime = 0
            if day_data[1] == 0 and day_data[2] == 0:
                continue

            if not day_data[0]:
                downtime += ( int(day_data[2].split(":")[0]) - int(day_data[1].split(":")[0]) ) * 60
            
            else:
                start_hour = int(day_data[1].split(":")[0])
                end_hour = int(day_data[2].split(":")[0])

                start_minute = int(day_data[1].split(":")[1])
                end_minute = int(day_data[2].split(":")[1])
                while index < ( len(day_data[0]) -1 ):

                    hour_1 = int(day_data[0][index][0].split(":")[0])
                    hour_2 = int(day_data[0][index+1][0].split(":")[0])

                    minute_1 = int(day_data[0][index][0].split(":")[1])
                    minute_2 = int(day_data[0][index+1][0].split(":")[1])

                    status_1 = day_data[0][index][1]
                    status_2 = day_data[0][index+1][1]

                    if index == 0:
                        is_start = True
                    else:
                        is_start = False

                    up, dwn = tdc.calculate_uptime_downtime(start_hour, start_minute, end_hour, end_minute, hour_1, hour_2, minute_1, minute_2, status_1, status_2, is_start)
                    uptime += up
                    downtime += dwn

                    index += 1

                if (uptime + downtime)/60 == (end_hour - start_hour) or int((uptime + downtime)/60) == 24:
                    uptime = uptime
                    downtime = downtime
                elif end_hour - start_hour == 23:
                    uptime = uptime
                    downtime = downtime + int(( 24 - (uptime + downtime)/60 )*60)
                else:
                    uptime = uptime
                    downtime = downtime + int(( (end_hour - start_hour) - (uptime + downtime)/60 )*60)
                
            final_uptime += uptime
            final_downtime += downtime

        return int(final_uptime/60), int(final_downtime/60)
        
    
