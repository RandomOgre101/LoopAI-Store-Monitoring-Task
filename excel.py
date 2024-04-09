import csv

# with open(r"C:\Users\Rishi\Downloads\timezones.csv") as csvfile:
#     spamreader = csv.reader(csvfile, delimiter=',')
#     for row in spamreader:
#         # print(row)


# from pytz import timezone
from datetime import datetime

# now = datetime.now().strftime('%H:%m:%s')
# print(now)

# t = 'America/Toronto'
# canada = datetime.now(timezone(t))
# print(canada)


# print(datetime.now())

# datetime('2024-04-07 12:51:43.053911')
d = datetime(2024, 4, 7, 12, 51, 43)

print('12:00:00' <= str(d.time()) <= '23:59:59')

'''
 # Getting all the DISTINCT store ids and storing them in a list
    result_store_ids = db.query(models.StoreStatus.store_id).distinct().all()
    list_of_store_ids = [item[0] for item in result_store_ids]
    
    # latest_times_query = db.query(models.StoreStatus.store_id,
    #                           func.max(models.StoreStatus.timestamp_utc).label('latest_time')).\
    #                           group_by(models.StoreStatus.store_id).\
    #                           subquery()

    # # Fetch all latest timestamps for all store IDs in one query
    # latest_times = db.query(latest_times_query.c.store_id,
    #                         latest_times_query.c.latest_time).all()
    
    # times = {(sid, timestamp) for sid, timestamp in latest_times}

    times = set()

    for i, sid in enumerate(list_of_store_ids):
        latest_time = db.query(func.max(models.StoreStatus.timestamp_utc)).filter(models.StoreStatus.store_id == sid).all()
        times.add((sid, latest_time[0][0]))
        print(f'Iteration {i}: DONE')
    
    print(times)
'''

    # latest_times_query = db.query(models.StoreStatus.store_id,
    #                           func.max(models.StoreStatus.timestamp_utc)).\
    #                           group_by(models.StoreStatus.store_id).all()

    # # Convert the result into a set
    # times = {(sid, timestamp) for sid, timestamp in latest_times_query}
    
    # print(len(times))