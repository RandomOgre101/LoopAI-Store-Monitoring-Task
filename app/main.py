from fastapi import FastAPI
from .routers import report
from .DB import models
from .DB.db_connection import engine


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(report.router)


# @app.get("/")
# async def test():
#     return {"Hello": "World"}