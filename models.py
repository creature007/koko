from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # "superadmin", "admin", "teacher"
    branch = Column(String, nullable=True)
    group_name = Column(String, nullable=True)
    
    # Relationship
    students = relationship("Student", back_populates="teacher")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    branch = Column(String)
    group_name = Column(String)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship
    teacher = relationship("User", back_populates="students")