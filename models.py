from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)

class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String(50))
    student_name = Column(String(50))
    student_father_name = Column(String(50))
    student_mother_name = Column(String(50))
    gender = Column(String(50))
    day = Column(String(5))
    month = Column(String(5))
    year = Column(String(5))
    category = Column(String(10))
    occupation = Column(String(50))
    organization_name = Column(String(50))
    school_college_name = Column(String(50))
    others_detail = Column(String(50))
    student_phone = Column(String(50))
    student_mobile = Column(String(50))
    email = Column(String(50))
    address = Column(String(100))
    village = Column(String(50))
    block = Column(String(50))
    sub_division = Column(String(50))
    district = Column(String(50))
    state = Column(String(50))
    pincode = Column(String(50))


