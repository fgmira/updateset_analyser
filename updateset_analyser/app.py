import logging
from datetime import datetime
from fastapi import FastAPI

from models import (
    UpdateSetAnalyserPostRequest,
    UpdateSetAnlyserPostResponse,
)
from tasks import analyse_updateset

app = FastAPI()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

logger.info("Starting Update Set Analyser API")


@app.post(path="/webhook", response_model=UpdateSetAnlyserPostResponse)
def webhook(data: UpdateSetAnalyserPostRequest):
    logger.info(f"Received request to analyse update set {data.update_set_sys_id}")
    task_id = analyse_updateset.delay(data.update_set_sys_id)
    logger.info(
        f"Task {task_id} to analyse update set {data.update_set_sys_id} has been scheduled"
    )
    return UpdateSetAnlyserPostResponse(task_id=str(task_id), start_time=datetime.now())
