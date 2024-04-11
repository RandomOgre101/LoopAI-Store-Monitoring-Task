from fastapi import APIRouter, Depends, status, HTTPException
from ..DB.db_connection import get_db
from sqlalchemy.orm import Session
from ..DB import models
from ..schemas import schemas
from ..controllers.report_gen import ReportGen
from fastapi.responses import StreamingResponse
import csv
import io
from fastapi import BackgroundTasks
from datetime import datetime



router = APIRouter(
    prefix = "/api/v1",
    tags = ['Reports']
)


report_status = {}
import time
def get_data(sid, db, rid):
    time.sleep(10)
    rg = ReportGen(sid, db)
    last_hour_uptime, last_hour_downtime = rg.get_last_hour_data()
    last_day_uptime, last_day_downtime = rg.get_last_day_data()
    last_week_uptime, last_week_downtime = rg.get_last_week_data()
    report_status[rid] = [
        {
            'store_id': sid,
            'last_hour_uptime': last_hour_uptime,
            'last_hour_downtime': last_hour_downtime,
            'last_day_uptime': last_day_uptime,
            'last_day_downtime': last_day_downtime,
            'last_week_uptime': last_week_uptime,
            'last_week_downtime': last_week_downtime

        }, 'complete'
    ]



@router.get("/trigger_report/{sid}", response_model=schemas.ReportIdOut, status_code=status.HTTP_200_OK)
async def trigger_creation_of_report(background_tasks: BackgroundTasks, sid: int, db: Session = Depends(get_db)):
    
    store_ids_query = db.query(models.StoreStatus.store_id).distinct().all()
    list_of_store_ids = {stid[0] for stid in store_ids_query}

    if sid in list_of_store_ids:
        report_id = int( str(sid) + 
                        str(datetime.now().date().day) + str(datetime.now().date().month) + str(datetime.now().date().year) + 
                        str(datetime.now().time().hour) 
                        )

        if report_id in report_status:
            return {'report_id': report_id}
        
        else:
            report_status[report_id] = [None, 'running']
            background_tasks.add_task(get_data, sid, db, report_id)

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"store with id: {sid} does not exist")
    
    return {'report_id': report_id}
    # return {
    #     'store_id': sid,
    #     'last_hour_uptime': last_hour_uptime, 'last_hour_downtime': last_hour_downtime,
    #     'last_day_uptime': last_day_uptime, 'last_day_downtime': last_day_downtime,
    #     'last_week_uptime': last_week_uptime, 'last_week_downtime': last_week_downtime
    #     }



@router.get("/get_report/{report_id}", status_code=status.HTTP_200_OK)
async def excel_test(report_id: int):

    if report_id in report_status:

        if report_status[report_id][1] == 'running':
            return {'status': 'Running'}
        
        else:
            r = report_status[report_id][0]
            buffer = io.StringIO()

            headers = [
                "store_id",
                "uptime_last_hour(in minutes)",
                "uptime_last_day(in hours)",
                "uptime_last_week(in hours)",
                "downtime_last_hour(in minutes)",
                "downtime_last_day(in hours)",
                "downtime_last_week(in hours)",
            ]

            writer = csv.writer(buffer)
            writer.writerow(headers)

            writer.writerow(
                [
                    r['store_id'],
                    r['last_hour_uptime'],
                    r['last_day_uptime'],
                    r['last_week_uptime'],
                    r['last_hour_downtime'],
                    r['last_day_downtime'],
                    r['last_week_downtime']
                ]
            )

            buffer.seek(0)

            return StreamingResponse(
                io.BytesIO(buffer.getvalue().encode()),
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=test.csv"
                },
            )
    
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"report with id: {report_id} does not exist")