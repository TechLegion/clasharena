from fastapi import APIRouter, HTTPException, status
from app.core.celery_app import celery_app
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Any = None
    error: str = None

@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status and result of a task"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return TaskStatus(
                task_id=task_id,
                status="pending",
                result=None
            )
        elif task_result.state == 'PROGRESS':
            return TaskStatus(
                task_id=task_id,
                status="progress",
                result=task_result.info
            )
        elif task_result.state == 'SUCCESS':
            return TaskStatus(
                task_id=task_id,
                status="success",
                result=task_result.result
            )
        elif task_result.state == 'FAILURE':
            return TaskStatus(
                task_id=task_id,
                status="failure",
                error=str(task_result.info)
            )
        else:
            return TaskStatus(
                task_id=task_id,
                status=task_result.state,
                result=task_result.result
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task status: {str(e)}"
        )

@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a pending task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {"message": f"Task {task_id} cancelled successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling task: {str(e)}"
        )

