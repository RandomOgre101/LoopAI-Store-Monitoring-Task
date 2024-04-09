from fastapi import APIRouter, Depends, status, HTTPException
from ..DB.db_connection import get_db
from sqlalchemy.orm import Session
from ..DB import models
from ..schemas import schemas
from ..controllers import report_gen
from fastapi.responses import StreamingResponse
import csv
import io


router = APIRouter(
    prefix = "/api/v1",
    tags = ['Reports']
)

report_status = {}

import random
@router.get("/trigger_report/{sid}")
async def trigger_creation_of_report(sid: int, db: Session = Depends(get_db)):

    store_ids_query = db.query(models.StoreStatus.store_id).distinct().all()
    list_of_store_ids = {sid[0] for sid in store_ids_query}
 
    # last_hour_uptime, last_hour_downtime = report_gen.get_last_hour_data(db, sid)
    # last_hour_uptime, last_hour_downtime = report_gen.get_last_hour_data(db, sid := random.choice(list(list_of_store_ids)))

    # last_day_uptime, last_day_downtime = report_gen.get_last_day_data(db, sid)
    last_day_uptime, last_day_downtime = report_gen.get_last_day_data(db, sid := random.choice(list(list_of_store_ids)))

    # return None
    return {'store_id': sid, "uptime": last_day_uptime, "downtime": last_day_downtime}



@router.get("/excel_test")
async def excel_test():
    buffer = io.StringIO()

    headers = [
        "store_id",
        "uptime_last_hour(in minutes)",
        "uptime_last_day(in hours)",
        "update_last_week(in hours)",
        "downtime_last_hour(in minutes)",
        "downtime_last_day(in hours)",
        "downtime_last_week(in hours)",
    ]

    writer = csv.writer(buffer)
    writer.writerow(headers)

    writer.writerow([1, 60, 24, 168, 0, 0, 0])

    buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(buffer.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=test.csv"
        },
    )