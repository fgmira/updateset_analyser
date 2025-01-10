from datetime import datetime
from pydantic import BaseModel, Field


class UpdateSetAnalyserPostRequest(BaseModel):
    update_set_sys_id: str = Field(
        ...,
        examples=[
            "c0595e94c3b61210907a9a2ed40131da",
            "c0595e94c3b61210907a9a2ed40131db",
        ],
        description="The sys_id of the update set to be analysed",
        max_length=32,
        min_length=32,
    )


class UpdateSetAnlyserPostResponse(BaseModel):
    task_id: str = Field(
        ...,
        description="The task id of the celery task that is running the update set analysis",
        max_length=36,
        min_length=36,
        examples=["c0595e94-c3b6-1210-907a-9a2ed40131da"],
    )
    start_time: datetime = Field(
        ...,
        description="The time the task started",
        examples=[datetime.now()],
    )
