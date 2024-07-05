from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phonenumber = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    projectname = Column(String, index=True)
    description = Column(String)
    due_date = Column(Date)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="projects")
    milestones = relationship("Milestone", back_populates="project")
    tasks = relationship("TaskList", back_populates="project")
    subtask = relationship("Task", back_populates="project")


class Milestone(Base):
    __tablename__ = 'milestones'

    id = Column(Integer, primary_key=True, index=True)
    milestone_name = Column(String, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    project_id = Column(Integer, ForeignKey('projects.id'))

    project = relationship("Project", back_populates="milestones")
    tasks = relationship("TaskList", back_populates="milestone")

class TaskList(Base):
    __tablename__ = 'task_lists'

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, index=True)
    milestone_id = Column(Integer, ForeignKey('milestones.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))

    milestone = relationship("Milestone", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    
    
class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, index=True)
    task_details = Column(Text)
    project_id = Column(Integer, ForeignKey('projects.id'))
    root_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)

    project = relationship("Project", back_populates="subtask")
    root_task = relationship("Task", remote_side=[id], back_populates="subtasks", uselist=False)
    subtasks = relationship("Task", back_populates="root_task")


class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer,primary_key=True, index=True)
    type_name = Column(String,index=True)
    type_id = Column(Integer)
    comment = Column(String, index=True)
    
