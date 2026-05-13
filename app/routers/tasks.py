from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, cache
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    obj = models.Task(**task.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    cache.flush_tasks()
    return obj

@router.get("/", response_model=List[schemas.TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    cached = cache.get_cached("task:all")
    if cached:
        return cached
    tasks = db.query(models.Task).all()
    result = [schemas.TaskResponse.model_validate(t).model_dump() for t in tasks]
    cache.set_cached("task:all", result)
    return result

@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    cached = cache.get_cached(f"task:{task_id}")
    if cached:
        return cached
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    cache.set_cached(f"task:{task_id}", schemas.TaskResponse.model_validate(task).model_dump())
    return task

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    cache.delete_cached(f"task:{task_id}")
    cache.flush_tasks()
    return task

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    cache.delete_cached(f"task:{task_id}")
    cache.flush_tasks()
