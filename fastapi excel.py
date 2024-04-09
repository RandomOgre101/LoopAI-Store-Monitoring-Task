from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import csv
import io

app = FastAPI()


@app.get("/")
async def download_csv():
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
            "Content-Disposition": "attachment; filename=uptime_downtime_report.csv"
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


# uvicorn fastapi:app --reload
