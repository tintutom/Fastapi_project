from pydantic import BaseModel
from datetime import date
from typing import List, Optional, ForwardRef
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    phonenumber: str
    username: str
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    phonenumber: str
    username: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    
class ProjectCreate(BaseModel):
    projectname: str
    description: str
    due_date: datetime

class ProjectResponse(BaseModel):
    id: int
    projectname: str
    description: str
    due_date: datetime
    owner_id: int

    class Config:
        orm_mode = True
        
class MilestoneBase(BaseModel):
    milestone_name: str
    start_date: date
    end_date: date
    project_id: int

class MilestoneCreate(MilestoneBase):
    pass
class MilestoneUpdate(MilestoneBase):
    pass

class MilestoneResponse(MilestoneBase):
    id: int
    project: Optional[ProjectResponse]

    class Config:
        orm_mode = True

class TaskListBase(BaseModel):
    task_name: str
    milestone_id: int
    project_id: int

class TaskListCreate(TaskListBase):
    pass

class TaskListResponse(TaskListBase):
    id: int
    milestone: Optional[MilestoneResponse]
    project: Optional[ProjectResponse]

    class Config:
        orm_mode = True



class TaskBase(BaseModel):
    task_name: str
    task_details: str

class TaskCreate(TaskBase):
    root_task_id: Optional[int] = None

class TaskUpdate(TaskBase):
    root_task_id: Optional[int] = None

# class TaskResponse(TaskBase):
#     id: int
#     project_id: int
#     root_task_id: Optional[int] = None
#     subtasks: List['TaskResponse'] = []

#     class Config:
#         orm_mode = True
TaskResponse = ForwardRef('TaskResponse')

class TaskResponse(BaseModel):
    id: int
    task_name: str
    task_details: str
    project_id: int
    root_task_id: Optional[int] = None
    subtasks: List[TaskResponse] = []

    class Config:
        orm_mode = True

TaskResponse.update_forward_refs()


class ProjectBase(BaseModel):
    projectname: str
    description: str
    due_date: date

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    tasks: List[TaskResponse] = []

    class Config:
        orm_mode = True

class CommentResponse(BaseModel):
    type_name:str
    type_id:int
    comment:str
    
    class Config:
        orm_mode = True