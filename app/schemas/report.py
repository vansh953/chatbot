from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    original_filename: str
    content_type: Optional[str] = None
    ai_summary: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ReportDetailOut(ReportOut):
    extracted_text: Optional[str] = None
