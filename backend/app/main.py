from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

from .database import get_db, engine, Base
from .models import User
from .models.trip import Trip, TripMember
from .models.trip_plan import TripPlan
from .models.expense import Expense, ExpenseShare
from .services.ai_router import TravelPlanner
from .services.expense_splitter import calculate_settlements
from .services.event import MemoryService
from .services.ai_chatbot import TravelChatbot
from .models.memory import Memory
import asyncio
from pathlib import Path
from .services.weather_mcp import WeatherMCP
from .services.mcp_tool_router import MCPToolRouter
from .services.smithery_selector import SmitheryServerSelector
from .services.mcp_bike_client import MCPBikePlannerClient
from .services.mcp_weather_client import MCPWeatherClient

# 创建数据库表
Base.metadata.create_all(bind=engine)
# from .models import User, Trip, TripMember, Expense, ExpenseShare, Memory, TripPlan
# from .services.ai_service import AIService
# from .services.rag_service import RAGService

app = FastAPI(title="Travel Agent API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖注入
# ai_service = AIService()
# rag_service = RAGService()

# JWT配置
SECRET_KEY = "travel-agent-secret-key-2023"  # 在生产环境中应该从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# HTTP Bearer认证
security = HTTPBearer()

# Pydantic模型
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TripCreate(BaseModel):
    name: str
    description: Optional[str] = None
    destination: str
    # 不再强制要求开始/结束日期
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    # 新增：AI 规划偏好（作为必需字段）
    days: int
    interests: List[str]
    avoids: List[str]

class TripPlanData(BaseModel):
    time: str
    activity: str
    location: str
    description: str = None

# JWT工具函数
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Weather MCP service
weather_mcp = WeatherMCP()
tool_router = MCPToolRouter()
smithery_selector = SmitheryServerSelector()

# Load MCP weather client configuration
def get_mcp_weather_client():
    config_path = Path(__file__).parent / "data" / "mcp_smithery_servers.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    weather_config = config.get("mcpServers", {}).get("mcp_weather_server")
    if weather_config:
        return MCPWeatherClient(weather_config)
    return None

mcp_weather_client = get_mcp_weather_client()

# 认证相关API
@app.post("/auth/register/")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="用户名已存在")
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 生成token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return {
        "data": {
            "token": access_token,
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "avatar": db_user.avatar,
                "created_at": db_user.created_at.isoformat() if db_user.created_at else None
            }
        }
    }

@app.post("/auth/login/")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # 查找用户
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="账户已被禁用")
    
    # 生成token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "data": {
            "token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    }

@app.get("/users/me")
async def get_current_user(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }

# 用户相关API
@app.get("/users/")
async def get_users(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    """获取所有用户列表（用于邀请成员）"""
    users = db.query(User).filter(User.is_active == True).all()
    return {
        "data": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar
            }
            for user in users
        ]
    }

@app.post("/users/")
async def create_user(user: dict):
    # 用户创建逻辑
    return {"message": "用户创建成功"}

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # 获取用户信息逻辑
    return {"message": f"获取用户 {user_id} 信息"}

# 旅行相关API
@app.get("/trips/")
async def get_trips(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    # 获取用户参与的所有旅行
    trips = db.query(Trip).join(TripMember).filter(TripMember.user_id == user_id).all()
    
    trip_list = []
    for trip in trips:
        # 使用数据库中存储的days字段
        days = trip.days or 1  # 如果没有days字段，默认为1
        
        # 获取成员信息
        members = db.query(TripMember).join(User).filter(TripMember.trip_id == trip.id).all()
        
        trip_data = {
            "id": trip.id,
            "title": trip.name,  # 前端期望的字段名
            "name": trip.name,
            "description": trip.description,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat() if trip.start_date else None,
            "end_date": trip.end_date.isoformat() if trip.end_date else None,
            "status": trip.status,
            "days": days,
            "members": [{
                "id": m.id,
                "trip_id": m.trip_id,
                "user_id": m.user_id,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                "user": {
                    "id": m.user.id,
                    "username": m.user.username,
                    "email": m.user.email,
                    "avatar": m.user.avatar,
                    "created_at": m.user.created_at.isoformat() if m.user.created_at else None
                }
            } for m in members],
            "expenses": [],  # 暂时为空
            "memories": [],  # 暂时为空
            "created_at": trip.created_at.isoformat() if trip.created_at else None
        }
        trip_list.append(trip_data)
    
    return {"data": trip_list}

@app.post("/trips/")
async def create_trip(trip_data: TripCreate, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    # 创建新旅行
    # 若未提供日期，使用当前日期为开始，+1天为结束
    start_dt = trip_data.start_date or datetime.utcnow()
    end_dt = trip_data.end_date or (start_dt + timedelta(days=max(1, trip_data.days)))
    db_trip = Trip(
        name=trip_data.name,
        description=trip_data.description,
        destination=trip_data.destination,
        start_date=start_dt,
        end_date=end_dt,
        days=trip_data.days,
        interests=trip_data.interests,
        avoids=trip_data.avoids,
        created_by=user_id,
        status="planning"
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    
    # 添加创建者为旅行成员（角色为owner）
    trip_member = TripMember(
        trip_id=db_trip.id,
        user_id=user_id,
        role="owner"
    )
    db.add(trip_member)
    db.commit()
    
    # 计算天数并生成初始计划
    days = trip_data.days  # 直接使用传入的days字段
    
    # 为每一天创建空的计划
    for day in range(1, days + 1):
        trip_plan = TripPlan(
            trip_id=db_trip.id,
            day=day,
            plan_data={
                "day": day,
                "date": (start_dt + timedelta(days=day-1)).isoformat(),
                "activities": [
                    {
                        "time": "09:00",
                        "activity": "待规划",
                        "location": trip_data.destination,
                        "description": "点击编辑来添加活动安排"
                    }
                ]
            }
        )
        db.add(trip_plan)
    
    db.commit()
    
    # 返回完整的旅行信息
    members = [{"user_id": user_id, "role": "owner"}]
    
    return {
        "data": {
            "id": db_trip.id,
            "title": db_trip.name,
            "name": db_trip.name,
            "description": db_trip.description,
            "destination": db_trip.destination,
            "start_date": db_trip.start_date.isoformat(),
            "end_date": db_trip.end_date.isoformat(),
            "status": db_trip.status,
            "days": days,
            "members": members,
            "expenses": [],
            "memories": [],
            "created_at": db_trip.created_at.isoformat()
        }
    }

@app.get("/trips/{trip_id}")
async def get_trip(
    trip_id: int,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db),
    with_itinerary: bool = False,
    interests: str = "",
    avoid: str = "",
    route_mode: str = "walking"
):
    # 验证用户是否有权访问该旅行
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 获取旅行信息
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="旅行不存在")
    
    # 使用数据库中存储的days字段
    days = trip.days or 1  # 如果没有days字段，默认为1
    
    # 获取成员信息（包含用户详细信息）
    members = db.query(TripMember).join(User).filter(TripMember.trip_id == trip_id).all()
    
    # 获取旅行计划
    plans = db.query(TripPlan).filter(TripPlan.trip_id == trip_id).order_by(TripPlan.day).all()

    # 可选：动态生成AI行程
    itinerary = None
    if with_itinerary:
        try:
            planner = TravelPlanner()
            interests_list = [s for s in interests.split(',') if s.strip()] if interests else []
            avoid_list = [s for s in avoid.split(',') if s.strip()] if avoid else []
            itinerary = planner.generate_itinerary(
                destination=trip.destination,
                days=days,
                interests=interests_list,
                avoid=avoid_list,
                default_route_mode=route_mode if route_mode in ("walking", "driving") else "walking"
            )
        except Exception as e:
            itinerary = {"error": f"itinerary generation failed: {str(e)}"}
    
    return {
        "data": {
            "id": trip.id,
            "title": trip.name,
            "name": trip.name,
            "description": trip.description,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "status": trip.status,
            "days": days,
            "members": [{
                "id": m.id,
                "trip_id": m.trip_id,
                "user_id": m.user_id,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                "user": {
                    "id": m.user.id,
                    "username": m.user.username,
                    "email": m.user.email,
                    "avatar": m.user.avatar,
                    "created_at": m.user.created_at.isoformat() if m.user.created_at else None
                }
            } for m in members],
            "expenses": [],  # 暂时为空
            "memories": [],  # 暂时为空
            "plans": [{"day": p.day, "plan_data": p.plan_data} for p in plans],
            "itinerary": itinerary,
            "created_at": trip.created_at.isoformat() if trip.created_at else None
        }
    }

@app.post("/trips/{trip_id}/members/")
async def add_trip_member(trip_id: int, member_data: dict, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    """邀请用户加入旅行"""
    # 验证当前用户是否有权限邀请（必须是旅行成员）
    current_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    
    if not current_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 检查要邀请的用户是否存在
    invited_user = db.query(User).filter(User.id == member_data.get("user_id")).first()
    if not invited_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查用户是否已经是旅行成员
    existing_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == member_data.get("user_id")
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="用户已经是旅行成员")
    
    # 添加新成员
    new_member = TripMember(
        trip_id=trip_id,
        user_id=member_data.get("user_id"),
        role="member"
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    return {
        "data": {
            "id": new_member.id,
            "trip_id": new_member.trip_id,
            "user_id": new_member.user_id,
            "role": new_member.role,
            "joined_at": new_member.joined_at.isoformat() if new_member.joined_at else None,
            "user": {
                "id": invited_user.id,
                "username": invited_user.username,
                "email": invited_user.email,
                "avatar": invited_user.avatar
            }
        }
    }

# 记账分摊API
@app.post("/expenses/")
async def create_expense(expense: dict, db: Session = Depends(get_db)):
    # 创建支出逻辑
    return {"message": "支出创建成功"}

@app.post("/expenses/{expense_id}/split/")
async def split_expense(expense_id: int, split_data: dict, db: Session = Depends(get_db)):
    # 分摊支出逻辑
    return {"message": f"支出 {expense_id} 分摊成功"}

# 时光记录API
@app.post("/memories/")
async def create_memory(memory: dict, db: Session = Depends(get_db)):
    # 创建时光记录逻辑
    return {"message": "时光记录创建成功"}

@app.get("/trips/{trip_id}/memories/")
async def get_trip_memories(trip_id: int, db: Session = Depends(get_db)):
    # 获取旅行时光记录逻辑
    return {"message": f"获取旅行 {trip_id} 时光记录"}

# TripPlan相关API
@app.get("/trips/{trip_id}/plans/")
async def get_trip_plans(trip_id: int, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 获取所有计划
    plans = db.query(TripPlan).filter(TripPlan.trip_id == trip_id).order_by(TripPlan.day).all()
    
    return {
        "data": [
            {
                "id": p.id,
                "day": p.day,
                "plan_data": p.plan_data,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            } for p in plans
        ]
    }

@app.put("/trips/{trip_id}/plans/{day}")
async def update_trip_plan(
    trip_id: int, 
    day: int, 
    plan_data: dict,
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 查找或创建该天的计划
    trip_plan = db.query(TripPlan).filter(
        TripPlan.trip_id == trip_id,
        TripPlan.day == day
    ).first()
    
    if trip_plan:
        # 更新现有计划
        trip_plan.plan_data = plan_data
        trip_plan.updated_at = datetime.utcnow()
    else:
        # 创建新计划
        trip_plan = TripPlan(
            trip_id=trip_id,
            day=day,
            plan_data=plan_data
        )
        db.add(trip_plan)
    
    db.commit()
    db.refresh(trip_plan)
    
    return {
        "data": {
            "id": trip_plan.id,
            "day": trip_plan.day,
            "plan_data": trip_plan.plan_data,
            "created_at": trip_plan.created_at.isoformat(),
            "updated_at": trip_plan.updated_at.isoformat()
        }
    }

# AI旅行规划API（简化版本，不依赖AI服务）
@app.post("/trips/{trip_id}/plan/")
async def generate_trip_plan(trip_id: int, plan_request: dict, user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")

    # 获取旅行信息
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="旅行不存在")

    # 读取请求参数
    destination = plan_request.get("destination", trip.destination)
    days = (trip.end_date - trip.start_date).days + 1
    interests = plan_request.get("interests", [])
    avoid = plan_request.get("avoid", [])
    route_mode = plan_request.get("route_mode", "walking")  # walking/driving

    # 调用 AI 行程规划
    planner = TravelPlanner()
    itinerary = planner.generate_itinerary(
        destination=destination,
        days=days,
        interests=interests,
        avoid=avoid,
        default_route_mode=route_mode
    )

    # 可选：将结果落库为 TripPlan（此处先直接返回给前端）
    return {"data": itinerary}

# AI问答助手API（占位实现）
@app.post("/ai/ask/")
async def ask_ai(question: dict, context: str = ""):
    q = question.get("question", "")
    return {"answer": f"暂未实现AI问答。收到问题：{q}"}

# 仪表盘API
@app.get("/trips/{trip_id}/dashboard/")
async def get_trip_dashboard(trip_id: int, db: Session = Depends(get_db)):
    # 获取旅行仪表盘数据逻辑
    return {"message": f"获取旅行 {trip_id} 仪表盘数据"}

# WebSocket连接
@app.websocket("/ws/{trip_id}")
async def websocket_endpoint(websocket: WebSocket, trip_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理实时协作消息
            if message["type"] == "expense_update":
                await manager.broadcast(json.dumps(message))
            elif message["type"] == "memory_update":
                await manager.broadcast(json.dumps(message))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 记账分摊API
@app.post("/trips/{trip_id}/expenses/")
async def create_expense(
    trip_id: int, 
    expense_data: dict, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """创建支出记录"""
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 创建支出记录
    expense = Expense(
        trip_id=trip_id,
        user_id=user_id,  # 支付者
        amount=expense_data["amount"],
        currency=expense_data.get("currency", "CNY"),
        category=expense_data.get("category", "other"),
        description=expense_data.get("description", ""),
        location=expense_data.get("location"),
        status=expense_data.get("status", "pending"),
        date=datetime.utcnow()
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    # 创建分摊记录
    shares = expense_data.get("shares", [])
    
    # 计算分摊金额：总金额除以总人数（支出人 + 分摊人）
    total_people = 1 + len(shares)  # 支出人 + 分摊人
    share_amount = expense.amount / total_people
    
    # 为支出人创建分摊记录（支出人也要分摊）
    payer_share = ExpenseShare(
        expense_id=expense.id,
        user_id=expense.user_id,  # 支出人
        share_amount=share_amount
    )
    db.add(payer_share)
    
    # 为其他分摊人创建分摊记录
    for share_data in shares:
        share = ExpenseShare(
            expense_id=expense.id,
            user_id=share_data["user_id"],
            share_amount=share_amount
        )
        db.add(share)
    
    db.commit()
    
    return {
        "data": {
            "id": expense.id,
            "trip_id": expense.trip_id,
            "user_id": expense.user_id,
            "amount": expense.amount,
            "currency": expense.currency,
            "category": expense.category,
            "description": expense.description,
            "location": expense.location,
            "status": expense.status,
            "date": expense.date.isoformat(),
            "shares": shares,
            "created_at": expense.created_at.isoformat()
        }
    }

@app.get("/trips/{trip_id}/expenses/")
async def get_trip_expenses(
    trip_id: int, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """获取旅行的所有支出记录"""
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 获取所有支出记录
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    
    expense_list = []
    for expense in expenses:
        # 获取分摊信息
        shares = db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).all()
        share_list = []
        for share in shares:
            share_list.append({
                "user_id": share.user_id,
                "share_amount": share.share_amount,
                "is_paid": share.is_paid,
                "paid_at": share.paid_at.isoformat() if share.paid_at else None
            })
        
        expense_list.append({
            "id": expense.id,
            "trip_id": expense.trip_id,
            "user_id": expense.user_id,
            "amount": expense.amount,
            "currency": expense.currency,
            "category": expense.category,
            "description": expense.description,
            "location": expense.location,
            "status": expense.status,
            "date": expense.date.isoformat(),
            "shares": share_list,
            "created_at": expense.created_at.isoformat()
        })
    
    return {"data": expense_list}

@app.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: int, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """删除支出记录"""
    # 获取支出记录
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    
    # 验证用户权限（只有支出创建者或旅行成员可以删除）
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == expense.trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 删除相关的分摊记录
    db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense_id).delete()
    
    # 删除支出记录
    db.delete(expense)
    db.commit()
    
    return {"message": "删除成功"}

@app.put("/expenses/{expense_id}")
async def update_expense(
    expense_id: int, 
    expense_data: dict, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """更新支出记录"""
    # 获取支出记录
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    
    # 验证用户权限（只有支出创建者或旅行成员可以更新）
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == expense.trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 更新支出记录
    if "user_id" in expense_data:
        expense.user_id = expense_data["user_id"]
    if "amount" in expense_data:
        expense.amount = expense_data["amount"]
    if "currency" in expense_data:
        expense.currency = expense_data["currency"]
    if "category" in expense_data:
        expense.category = expense_data["category"]
    if "description" in expense_data:
        expense.description = expense_data["description"]
    if "status" in expense_data:
        expense.status = expense_data["status"]
    
    expense.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(expense)
    
    # 更新分摊记录
    if "shares" in expense_data:
        # 删除旧的分摊记录
        db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense_id).delete()
        
        # 计算分摊金额：总金额除以总人数（支出人 + 分摊人）
        shares = expense_data["shares"]
        total_people = 1 + len(shares)  # 支出人 + 分摊人
        share_amount = expense.amount / total_people
        
        # 为支出人创建分摊记录（支出人也要分摊）
        payer_share = ExpenseShare(
            expense_id=expense_id,
            user_id=expense.user_id,  # 支出人
            share_amount=share_amount
        )
        db.add(payer_share)
        
        # 为其他分摊人创建分摊记录
        for share_data in shares:
            share = ExpenseShare(
                expense_id=expense_id,
                user_id=share_data["user_id"],
                share_amount=share_amount
            )
            db.add(share)
        
        db.commit()
    
    return {
        "data": {
            "id": expense.id,
            "trip_id": expense.trip_id,
            "user_id": expense.user_id,
            "amount": expense.amount,
            "currency": expense.currency,
            "category": expense.category,
            "description": expense.description,
            "location": expense.location,
            "status": expense.status,
            "date": expense.date.isoformat(),
            "created_at": expense.created_at.isoformat(),
            "updated_at": expense.updated_at.isoformat()
        }
    }

@app.post("/trips/{trip_id}/expenses/{expense_id}/split/")
async def split_expense(
    trip_id: int, 
    expense_id: int, 
    split_data: dict, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """分摊支出"""
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 获取支出记录
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.trip_id == trip_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    
    # 删除旧的分摊记录
    db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense_id).delete()
    
    # 创建新的分摊记录
    shares = split_data.get("shares", [])
    total_share = sum(share["share_amount"] for share in shares)
    
    if abs(total_share - expense.amount) > 0.01:  # 允许0.01的误差
        raise HTTPException(status_code=400, detail="分摊金额总和必须等于支出金额")
    
    for share_data in shares:
        share = ExpenseShare(
            expense_id=expense_id,
            user_id=share_data["user_id"],
            share_amount=share_data["share_amount"]
        )
        db.add(share)
    
    db.commit()
    
    return {"message": "分摊成功"}

@app.get("/trips/{trip_id}/expenses/summary/")
async def get_expense_summary(
    trip_id: int, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """获取支出汇总和分摊计算"""
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 获取所有支出记录
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    
    # 准备数据给expense_splitter
    expenses_data = []
    user_payments = {}  # 用户支付的总金额
    user_shares = {}    # 用户分摊的总金额
    
    for expense in expenses:
        # 记录支付金额
        payer_id = expense.user_id
        user_payments[payer_id] = user_payments.get(payer_id, 0) + expense.amount
        
        # 获取分摊信息
        shares = db.query(ExpenseShare).filter(ExpenseShare.expense_id == expense.id).all()
        share_list = []
        for share in shares:
            user_shares[share.user_id] = user_shares.get(share.user_id, 0) + share.share_amount
            share_list.append({
                "user_id": share.user_id,
                "share_amount": share.share_amount
            })
        
        # 构建expense_splitter需要的数据格式
        expenses_data.append({
            "user_id": expense.user_id,
            "amount": expense.amount,
            "shares": share_list
        })
    
    # 获取用户名映射
    all_user_ids = set(user_payments.keys()) | set(user_shares.keys())
    users = db.query(User).filter(User.id.in_(all_user_ids)).all()
    user_map = {user.id: user.username for user in users}
    
    # 使用expense_splitter计算分摊方案
    settlements = calculate_settlements(expenses_data, user_map)
    
    # 计算净额（支付 - 分摊）
    user_net = {}
    for user_id in all_user_ids:
        payment = user_payments.get(user_id, 0)
        share = user_shares.get(user_id, 0)
        user_net[user_id] = payment - share
    
    return {
        "data": {
            "total_expenses": sum(user_payments.values()),
            "user_payments": user_payments,
            "user_shares": user_shares,
            "user_net": user_net,
            "settlements": settlements
        }
    }

@app.post("/trips/{trip_id}/expenses/{expense_id}/shares/{share_id}/pay/")
async def mark_share_as_paid(
    trip_id: int, 
    expense_id: int, 
    share_id: int, 
    user_id: int = Depends(verify_token), 
    db: Session = Depends(get_db)
):
    """标记分摊为已支付"""
    # 验证用户权限
    trip_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    if not trip_member:
        raise HTTPException(status_code=404, detail="旅行不存在或无权访问")
    
    # 获取分摊记录
    share = db.query(ExpenseShare).filter(
        ExpenseShare.id == share_id,
        ExpenseShare.expense_id == expense_id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分摊记录不存在")
    
    # 标记为已支付
    share.is_paid = True
    share.paid_at = datetime.utcnow()
    db.commit()
    
    return {"message": "标记支付成功"}

# 临时聊天API（不需要认证，用于测试）
@app.post("/chat/test/")
async def chat_with_ai_test(message: dict):
    """与AI聊天机器人对话（测试版本，无需认证）"""
    try:
        user_message = message.get("message", "")
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        # 使用固定的用户ID进行测试
        response = chatbot.chat_with_qwen(user_message, "test_user")
        
        print(f"[DEBUG] chat_with_qwen 返回类型: {type(response)}")
        print(f"[DEBUG] chat_with_qwen 返回值: {response}")
        
        # 确保response是字符串
        if isinstance(response, dict):
            # 如果返回的是字典，尝试提取文本
            if "output" in response and "text" in response["output"]:
                ai_response = response["output"]["text"]
            elif "text" in response:
                ai_response = response["text"]
            else:
                ai_response = str(response)
        else:
            ai_response = str(response)
        
        return {
            "success": True,
            "message": "对话成功",
            "data": {
                "user_message": user_message,
                "ai_response": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        print(f"[DEBUG] 聊天API异常: {e}")
        import traceback
        print(f"[DEBUG] 完整错误信息: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")

# 聊天机器人API
chatbot = TravelChatbot()

@app.post("/chat/")
async def chat_with_ai(
    message: dict,
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """与AI聊天机器人对话"""
    try:
        user_message = message.get("message", "")
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        # 使用user_id作为聊天机器人的用户标识
        response = chatbot.chat_with_qwen(user_message, str(user_id))
        
        return {
            "success": True,
            "message": "对话成功",
            "data": {
                "user_message": user_message,
                "ai_response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")

@app.get("/chat/memories/")
async def get_chat_memories(
    user_id: int = Depends(verify_token)
):
    """获取用户的聊天记忆"""
    try:
        memories = chatbot.get_user_memories(str(user_id))
        return {
            "message": "获取记忆成功",
            "data": memories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆失败: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Travel Agent API is running!"}

# Weather endpoints
@app.get("/weather/current")
async def weather_current(city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None):
    try:
        # Try MCP weather client first, fallback to local weather service
        if mcp_weather_client:
            try:
                data = await mcp_weather_client.get_current_weather(city=city, latitude=latitude, longitude=longitude)
                return {"data": data, "source": "mcp"}
            except Exception as mcp_error:
                print(f"MCP weather client failed: {mcp_error}, falling back to local service")
        
        # Fallback to local weather service
        data = weather_mcp.get_current_weather(city=city, latitude=latitude, longitude=longitude)
        return {"data": data, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SmitherySelectRequest(BaseModel):
    query: str


@app.post("/mcp/smithery/resolve")
async def smithery_resolve(req: SmitherySelectRequest):
    server = smithery_selector.resolve_by_intent(req.query)
    if not server:
        raise HTTPException(status_code=404, detail="No matching MCP server for query")
    return {"data": server}


class MCPIntentExecuteRequest(BaseModel):
    query: str
    params: Optional[dict] = None
    mode: Optional[str] = None  # optional hint: weather_current | weather_forecast


@app.post("/mcp/intent/execute")
async def mcp_intent_execute(req: MCPIntentExecuteRequest):
    print(f"[/mcp/intent/execute] Received request: query='{req.query}', params={req.params}")
    server = smithery_selector.resolve_by_intent(req.query)
    print(f"[/mcp/intent/execute] Resolved server: {server}")
    if not server:
        raise HTTPException(status_code=404, detail="No matching MCP server for query")

    # Weather intent: directly fulfill using internal WeatherMCP to execute the tool call
    server_name = None
    for name, cfg in json.loads(Path(Path(__file__).resolve().parent / "data" / "mcp_smithery_servers.json").read_text(encoding="utf-8")).get("mcpServers", {}).items():
        if cfg == server:
            server_name = name
            break

    if server_name == "mcp_weather_server":
        print(f"[/mcp/intent/execute] weather branch, params={req.params}")
        text = (req.query or "").lower()
        p = req.params or {}
        city = p.get("city")
        lat = p.get("latitude")
        lon = p.get("longitude")
        days = p.get("days")

        # naive extraction: prefer explicit params, else regex-like hints from query
        try:
            import re  # local import to avoid top pollution
            m = re.search(r"(\d+)[\s\u5929]", req.query)
            if not days and m:
                days = int(m.group(1))
        except Exception:
            pass

        is_forecast = req.mode == "weather_forecast" or ("forecast" in text or "预报" in req.query)
        try:
            if is_forecast or days:
                days = max(1, min(int(days or 7), 16))
                data = weather_mcp.get_daily_forecast(city=city, latitude=lat, longitude=lon, days=days)
                return {"server": server_name, "tool": "weather_forecast", "args": {"city": city, "latitude": lat, "longitude": lon, "days": days}, "data": data}
            else:
                data = weather_mcp.get_current_weather(city=city, latitude=lat, longitude=lon)
                return {"server": server_name, "tool": "weather_current", "args": {"city": city, "latitude": lat, "longitude": lon}, "data": data}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Weather execution failed: {str(e)}")

    # Bike route intent: return smithery server command for external execution
    if server_name == "bike-planner-mcp-v2":
        # Try to execute via Smithery + stdio
        try:
            print(f"[/mcp/intent/execute] bike branch, params={req.params}")
            city = (req.params or {}).get("city") if req.params else None
            # naive extraction for origin/destination from query if not provided
            origin = (req.params or {}).get("origin") if req.params else None
            destination = (req.params or {}).get("destination") if req.params else None
            if not origin or not destination:
                # simple heuristic: split by "到" or "to"
                q = req.query
                if "到" in q:
                    parts = q.split("到")
                    if len(parts) >= 2:
                        origin = origin or parts[0].strip()
                        destination = destination or parts[1].strip()
                elif " to " in q.lower():
                    parts = q.lower().split(" to ")
                    if len(parts) >= 2:
                        origin = origin or parts[0].strip()
                        destination = destination or parts[1].strip()
            print(f"[/mcp/intent/execute] bike parsed origin={origin}, destination={destination}, city={city}")
            if not origin or not destination:
                raise HTTPException(status_code=400, detail="Missing origin/destination. Provide params.origin/destination or phrase like 'A到B'.")

            client = MCPBikePlannerClient(server)
            result = await client.plan_route(origin=origin, destination=destination, city=city)
            print(f"[/mcp/intent/execute] bike result keys={list(result.keys()) if isinstance(result, dict) else type(result)}")
            return {"server": server_name, "tool": "plan_bike_route", "args": {"origin": origin, "destination": destination, "city": city}, "data": result}
        except HTTPException:
            raise
        except Exception as e:
            print(f"[/mcp/intent/execute] bike fallback error: {str(e)}")
            return {"server": server_name, "runner": server, "warning": f"Fallback to runner: {str(e)}"}

    # Fallback: return server info
    return {"server": server_name, "runner": server}

@app.get("/weather/forecast")
async def weather_forecast(city: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, days: int = 7):
    try:
        # Try MCP weather client first, fallback to local weather service
        if mcp_weather_client:
            try:
                data = await mcp_weather_client.get_weather_forecast(city=city, latitude=latitude, longitude=longitude, days=days)
                return {"data": data, "source": "mcp"}
            except Exception as mcp_error:
                print(f"MCP weather client failed: {mcp_error}, falling back to local service")
        
        # Fallback to local weather service
        data = weather_mcp.get_daily_forecast(city=city, latitude=latitude, longitude=longitude, days=days)
        return {"data": data, "source": "local"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ToolSelectRequest(BaseModel):
    query: str
    k: int = 20
    include_tags: Optional[List[str]] = None
    include_domains: Optional[List[str]] = None
    safety_levels: Optional[List[str]] = None


@app.post("/tools/select")
async def select_tools(req: ToolSelectRequest):
    try:
        tools = tool_router.select_top_k(
            query=req.query,
            k=req.k,
            include_tags=req.include_tags,
            include_domains=req.include_domains,
            safety_levels=req.safety_levels,
        )
        return {"data": tools}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tools/select/diagnose")
async def select_tools_diagnose(req: ToolSelectRequest):
    try:
        info = tool_router.diagnose_selection(
            query=req.query,
            k=req.k,
            include_tags=req.include_tags,
            include_domains=req.include_domains,
            safety_levels=req.safety_levels,
        )
        return {"data": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
