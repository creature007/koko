from sqlalchemy.orm import Session
from models import User, Student
from security import get_password_hash

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, role: str, branch: str = None, group_name: str = None):
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        password=hashed_password,
        role=role,
        branch=branch,
        group_name=group_name
    )
    db.add(new_user)
    db.commit()
    return new_user

def get_students_by_teacher(db: Session, branch: str, group_name: str):
    return db.query(Student).filter(
        Student.branch == branch,
        Student.group_name == group_name
    ).all()

def get_teachers_by_branch(db: Session, branch: str):
    return db.query(User).filter(
        User.role == "teacher",
        User.branch == branch
    ).all()

def get_branch_students(db: Session, branch: str):
    return db.query(Student).filter(Student.branch == branch).all()

def add_student(db: Session, name: str, branch: str, group_name: str, teacher_id: int = None):
    new_student = Student(
        name=name,
        branch=branch,
        group_name=group_name,
        teacher_id=teacher_id
    )
    db.add(new_student)
    db.commit()
    return new_student

def delete_student(db: Session, student_id: int):
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        db.delete(student)
        db.commit()
        return True
    return False