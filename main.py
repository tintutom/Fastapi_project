from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import models
from database import *
from typing import List 
import crud
from crud import *
import schemas
from schemas import *

models.Base.metadata.create_all(bind=engine)


app = FastAPI()

# Project Endpoints

@app.post("/register/", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.email)
    db_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if db_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, phonenumber=user.phonenumber, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(email: str, password: str, db: Session = Depends(get_db)):
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/projects/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    db_project = models.Project(**project.dict(), owner_id=current_user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse])
def read_projects(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()

@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, project: ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    db_project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.dict().items():
        setattr(db_project, key, value)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.delete("/projects/{project_id}", response_model=ProjectResponse)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(db_project)
    db.commit()
    return db_project


# milestone Endpoints
@app.post("/projects/{project_id}/milestones/", response_model=schemas.MilestoneResponse)
def create_milestone_for_project(
    project_id: int,
    milestone: schemas.MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    milestone.project_id = project_id
    return crud.create_milestone(db, milestone)

@app.get("/projects/{project_id}/milestones/", response_model=List[schemas.MilestoneResponse])
def read_milestones_for_project(
    project_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    return crud.get_milestones_by_project(db, project_id, skip=skip, limit=limit)

@app.get("/projects/{project_id}/milestones/{milestone_id}", response_model=schemas.MilestoneResponse)
def read_milestone_for_project(
    project_id: int, milestone_id: int, db: Session = Depends(get_db)
):
    milestone = crud.get_milestone(db, milestone_id)
    if not milestone or milestone.project_id != project_id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone

@app.put("/projects/{project_id}/milestones/{milestone_id}", response_model=schemas.MilestoneResponse)
def update_milestone(
    project_id: int,
    milestone_id: int,
    milestone: schemas.MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_milestone = crud.get_milestone(db, milestone_id)
    if not db_milestone or db_milestone.project_id != project_id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return crud.update_milestone(db, db_milestone, milestone)


@app.delete("/projects/{project_id}/milestones/{milestone_id}", response_model=schemas.MilestoneResponse)
def delete_milestone(
    project_id: int, milestone_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    milestone = crud.get_milestone(db, milestone_id)
    if not milestone or milestone.project_id != project_id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return crud.delete_milestone(db, milestone_id)


# TaskList Endpoints
@app.post("/projects/{project_id}/tasklists/", response_model=schemas.TaskListResponse)
def create_tasklist_for_project(
    project_id: int,
    tasklist: schemas.TaskListCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tasklist.project_id = project_id
    return crud.create_tasklist(db, tasklist)

@app.get("/projects/{project_id}/tasklists/", response_model=List[schemas.TaskListResponse])
def read_tasklists_for_project(
    project_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    return crud.get_tasklists_by_project(db, project_id, skip=skip, limit=limit)

@app.get("/projects/{project_id}/tasklists/{tasklist_id}", response_model=schemas.TaskListResponse)
def read_tasklist_for_project(
    project_id: int, tasklist_id: int, db: Session = Depends(get_db)
):
    tasklist = crud.get_tasklist(db, tasklist_id)
    if not tasklist or tasklist.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task list not found")
    return tasklist

@app.delete("/projects/{project_id}/tasklists/{tasklist_id}", response_model=schemas.TaskListResponse)
def delete_tasklist(
    project_id: int, tasklist_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    tasklist = crud.get_tasklist(db, tasklist_id)
    if not tasklist or tasklist.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task list not found")
    return crud.delete_tasklist(db, tasklist_id)


@app.post("/projects/{project_id}/tasks/", response_model=TaskResponse)
def create_task_api(project_id: int, task: TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return create_task(db, task.task_name, task.task_details, project_id, task.root_task_id)


@app.put("/projects/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def update_task_api(project_id: int, task_id: int, task: TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return update_task(db, project_id, task_id, task.task_name, task.task_details, task.root_task_id)


@app.get("/projects/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def read_task(project_id: int, task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = get_task(db, project_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/projects/{project_id}/tasks/{task_id}")
def delete_task_api(project_id: int, task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return delete_task(db, project_id, task_id)

@app.get("/projects/{project_id}/tasks/{task_id}/comments", response_model=List[CommentResponse])
def get_comments(task_id:int, db: Session = Depends(get_db)):
    get_comments=get_task_comments(db,task_id)
    if get_comments is None:
        raise HTTPException(status_code=404,detail="no task")
    return get_comments

@app.post("/projects/{project_id}/tasks/{task_id}/comments", response_model=CommentResponse)
def create_task_comment(task_id:int,commentcreate:str, db: Session = Depends(get_db)):
    return create_comment(db, commentcreate,type_id=task_id,type_name="task")
