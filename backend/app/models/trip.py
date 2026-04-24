from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    destination = Column(String)
    # 新增：AI 规划相关首选项（可直接持久化）
    days = Column(Integer, nullable=True)
    interests = Column(JSON, nullable=True)  # 存数组
    avoids = Column(JSON, nullable=True)     # 存数组
    status = Column(String, default="planning")  # planning, ongoing, completed
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    members = relationship("TripMember", back_populates="trip")
    # expenses = relationship("Expense", back_populates="trip")  # 暂时注释，等Expense模型实现
    # memories = relationship("Memory", back_populates="trip")   # 暂时注释，等Memory模型实现
    plans = relationship("TripPlan", back_populates="trip")

class TripMember(Base):
    __tablename__ = "trip_members"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="member")  # owner, admin, member
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    trip = relationship("Trip", back_populates="members")
    user = relationship("User")  # 添加与User的关系
