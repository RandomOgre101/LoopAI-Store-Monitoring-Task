from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from typing_extensions import Annotated


class TriggerReport(BaseModel):
    sid: int

class ReportIdOut(BaseModel):
    report_id: int