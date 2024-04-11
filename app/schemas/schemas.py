from pydantic import BaseModel



class TriggerReport(BaseModel):
    sid: int

class ReportIdOut(BaseModel):
    report_id: int