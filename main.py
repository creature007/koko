from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import Base, User, Student
from database import SessionLocal, engine
from security import verify_password, create_access_token, decode_token
from crud import get_user_by_username, create_user, get_students_by_teacher, add_student, delete_student

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register endpoint
@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    branch: str = Form(None),
    group_name: str = Form(None),
    db: Session = Depends(get_db)
):
    if role not in ["teacher", "admin", "superadmin"]:
        raise HTTPException(status_code=400, detail="Noto'g'ri rol tanlandi")
    
    existing_user = get_user_by_username(db, username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu username allaqachon mavjud")
    
    new_user = create_user(db, username, password, role, branch, group_name)
    return {"message": f"Foydalanuvchi qo'shildi: {username}, Rol: {role}"}

# Login endpoint
@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Noto'g'ri username yoki password")
    
    access_token = create_access_token(data={
        "sub": user.username,
        "role": user.role,
        "branch": user.branch,
        "group": user.group_name
    })
    return {"access_token": access_token, "token_type": "bearer"}

# Get students endpoint
@app.get("/students")
async def get_students(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token yaroqsiz")
    
    user = get_user_by_username(db, payload.get("sub"))
    
    if user.role == "teacher":
        # Teacher faqat o'z guruhidagi studentlarni ko'radi
        students = get_students_by_teacher(db, user.branch, user.group_name)
    elif user.role == "admin":
        # Admin o'z branchidagi barcha studentlarni ko'radi
        students = db.query(Student).filter(Student.branch == user.branch).all()
    elif user.role == "superadmin":
        # Superadmin barcha studentlarni ko'radi
        students = db.query(Student).all()
    else:
        raise HTTPException(status_code=403, detail="Sizda ruxsat yo'q")
    
    return {"students": students}

# Add student endpoint
@app.post("/add_student")
async def add_new_student(
    name: str = Form(...),
    branch: str = Form(...),
    group_name: str = Form(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token yaroqsiz")
    
    user = get_user_by_username(db, payload.get("sub"))
    if user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Faqat admin va superadmin student qo'sha oladi")
    
    if user.role == "admin" and user.branch != branch:
        raise HTTPException(status_code=403, detail="Siz faqat o'z branchingizga student qo'sha olasiz")
    
    # Guruh uchun teacher ni topish
    teacher = db.query(User).filter(
        User.role == "teacher",
        User.branch == branch,
        User.group_name == group_name
    ).first()
    
    teacher_id = teacher.id if teacher else None
    
    new_student = add_student(db, name, branch, group_name, teacher_id)
    return {
        "message": f"Yangi student qo'shildi: {name}",
        "teacher_assigned": teacher.username if teacher else "Guruh uchun teacher topilmadi"
    }

# Delete student endpoint
@app.delete("/delete_student/{student_id}")
async def remove_student(
    student_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token yaroqsiz")
    
    user = get_user_by_username(db, payload.get("sub"))
    if user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Faqat admin va superadmin student o'chira oladi")
    
    # Admin faqat o'z branchidagi studentlarni o'chira oladi
    if user.role == "admin":
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or student.branch != user.branch:
            raise HTTPException(status_code=403, detail="Bu studentni o'chira olmaysiz")
    
    if delete_student(db, student_id):
        return {"message": "Student o'chirildi"}
    else:
        raise HTTPException(status_code=404, detail="Student topilmadi")

# Add admin endpoint (only for superadmin)
@app.post("/add_admin")
async def add_new_admin(
    username: str = Form(...),
    password: str = Form(...),
    branch: str = Form(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token yaroqsiz")
    
    user = get_user_by_username(db, payload.get("sub"))
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Faqat superadmin admin qo'sha oladi")
    
    existing_user = get_user_by_username(db, username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu username band")
    
    new_admin = create_user(db, username, password, "admin", branch)
    return {"message": f"Yangi admin qo'shildi: {username}, Branch: {branch}"}