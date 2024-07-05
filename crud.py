from sqlalchemy.orm import Session,joinedload
import models
from models import Project, User, Task, Milestone, TaskList
from models import User, Project, Milestone, TaskList,Comment
from datetime import datetime, timedelta
from database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer,APIKeyHeader
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from schemas import *

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_scheme = APIKeyHeader(name='Authorization')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(api_key_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# CRUD for Milestone
def get_milestone(db: Session, milestone_id: int):
    return db.query(Milestone).filter(Milestone.id == milestone_id).first()

def get_milestones_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 10):
    return db.query(Milestone).filter(Milestone.project_id == project_id).offset(skip).limit(limit).all()

def create_milestone(db: Session, milestone: MilestoneCreate):
    db_milestone = Milestone(**milestone.dict())
    db.add(db_milestone)
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

def update_milestone(db: Session, db_milestone: Milestone, milestone_update: MilestoneUpdate):
    for key, value in milestone_update.dict(exclude_unset=True).items():
        setattr(db_milestone, key, value)
    db.commit()
    db.refresh(db_milestone)
    return db_milestone


def delete_milestone(db: Session, milestone_id: int):
    db_milestone = get_milestone(db, milestone_id)
    if db_milestone:
        db.delete(db_milestone)
        db.commit()
    return db_milestone

# CRUD for TaskList
def get_tasklist(db: Session, tasklist_id: int):
    return db.query(TaskList).filter(TaskList.id == tasklist_id).first()

def get_tasklists(db: Session, skip: int = 0, limit: int = 10):
    return db.query(TaskList).offset(skip).limit(limit).all()

def get_tasklists_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 10):
    return db.query(TaskList).filter(TaskList.project_id == project_id).offset(skip).limit(limit).all()

def create_tasklist(db: Session, tasklist: TaskListCreate):
    db_tasklist = TaskList(**tasklist.dict())
    db.add(db_tasklist)
    db.commit()
    db.refresh(db_tasklist)
    return db_tasklist

def delete_tasklist(db: Session, tasklist_id: int):
    db_tasklist = get_tasklist(db, tasklist_id)
    if db_tasklist:
        db.delete(db_tasklist)
        db.commit()
    return db_tasklist






def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()

def get_task(db: Session, project_id: int, task_id: int):
    return db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).options(joinedload(Task.subtasks)).first()

def create_task(db: Session, task_name: str, task_details: str, project_id: int, root_task_id: int = None):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if root_task_id is not None:
        root_task = get_task(db, project_id, root_task_id)
        if not root_task:
            raise HTTPException(status_code=400, detail="Invalid root task for the project")

        # Check if the root task is a valid parent (root_task should be null)
        parent_task = root_task
        while parent_task.root_task_id is not None:
            parent_task = get_task(db, project_id, parent_task.root_task_id)
            if not parent_task:
                raise HTTPException(status_code=400, detail="Invalid task hierarchy")

    new_task = Task(task_name=task_name, task_details=task_details, project_id=project_id, root_task_id=root_task_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def get_task(db: Session, project_id: int, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.project_id == project_id, Task.id == task_id).first()

def is_valid_root_task(db: Session, project_id: int, root_task_id: int) -> bool:
    ancestor = get_task(db, project_id, root_task_id)
    while ancestor is not None:
        if ancestor.root_task_id is None:
            return True
        ancestor = get_task(db, project_id, ancestor.root_task_id)
    return False

def check_cyclic_dependency(db: Session, project_id: int, task_id: int, root_task_id: int) -> bool:
    parent_task = get_task(db, project_id, root_task_id)
    while parent_task is not None:
        if parent_task.id == task_id:
            return True
        parent_task = get_task(db, project_id, parent_task.root_task_id)
    return False

def update_task(db: Session, project_id: int, task_id: int, task_name: Optional[str] = None, task_details: Optional[str] = None, root_task_id: Optional[int] = None):
    task = get_task(db, project_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if root_task_id is not None:
        root_task = get_task(db, project_id, root_task_id)
        if not root_task:
            raise HTTPException(status_code=400, detail="Invalid root task for the project")

        if check_cyclic_dependency(db, project_id, task_id, root_task_id):
            raise HTTPException(status_code=400, detail="Invalid new root task value is'nt contain a parent task. so not allow to update existing parent")

        if not is_valid_root_task(db, project_id, root_task_id):
            raise HTTPException(status_code=400, detail="The new root task must have an ancestor with root_task_id as null")

    if task.root_task_id is None and root_task_id is not None:
        if not is_valid_root_task(db, project_id, root_task_id):
            raise HTTPException(status_code=400, detail="The new root task must have an ancestor with root_task_id as null")

    if task_name is not None:
        task.task_name = task_name
    if task_details is not None:
        task.task_details = task_details
    task.root_task_id = root_task_id

    db.commit()
    db.refresh(task)
    return task


def delete_task_and_subtasks(db: Session, task: Task):
    for subtask in task.subtasks:
        delete_task_and_subtasks(db, subtask)
    db.delete(task)
    db.commit()

def delete_task(db: Session, project_id: int, task_id: int):
    task = get_task(db, project_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    delete_task_and_subtasks(db, task)
    return {"detail": "Task and its subtasks deleted"}


def get_task_comments(db:Session,task_id:int):
    # type_name="task"
    return db.query(Comment).filter(Comment.type_id == task_id, Comment.type_name=="task").all()

def create_comment(db: Session, comment_create: str,type_id:int,type_name:str):
    comment_create = Comment(comment=comment_create,type_id=type_id,type_name=type_name)
    db.add(comment_create)
    db.commit()
    db.refresh(comment_create)
    return comment_create