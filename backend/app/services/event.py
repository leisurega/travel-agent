from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.memory import Memory
from ..models.trip import TripMember
from typing import List, Optional
from datetime import datetime

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_memory(self, trip_id: int, user_id: int, memory_data: dict) -> Memory:
        """创建新的时光记录"""
        memory = Memory(
            trip_id=trip_id,
            user_id=user_id,
            title=memory_data.get('title', ''),
            content=memory_data.get('content', ''),
            location=memory_data.get('location'),
            images=memory_data.get('images', []),
            tags=memory_data.get('tags', []),
            date=memory_data.get('date', datetime.utcnow())
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory
    
    def get_memories_by_trip(self, trip_id: int, user_id: int) -> List[Memory]:
        """获取旅行的所有时光记录"""
        # 验证用户权限
        trip_member = self.db.query(TripMember).filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id
        ).first()
        
        if not trip_member:
            return []
        
        return self.db.query(Memory).filter(
            Memory.trip_id == trip_id
        ).order_by(desc(Memory.date)).all()
    
    def get_memory_by_id(self, memory_id: int, user_id: int) -> Optional[Memory]:
        """根据ID获取时光记录"""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return None
        
        # 验证用户权限
        trip_member = self.db.query(TripMember).filter(
            TripMember.trip_id == memory.trip_id,
            TripMember.user_id == user_id
        ).first()
        
        if not trip_member:
            return None
        
        return memory
    
    def update_memory(self, memory_id: int, user_id: int, memory_data: dict) -> Optional[Memory]:
        """更新时光记录"""
        memory = self.get_memory_by_id(memory_id, user_id)
        if not memory:
            return None
        
        # 更新字段
        if 'title' in memory_data:
            memory.title = memory_data['title']
        if 'content' in memory_data:
            memory.content = memory_data['content']
        if 'location' in memory_data:
            memory.location = memory_data['location']
        if 'images' in memory_data:
            memory.images = memory_data['images']
        if 'tags' in memory_data:
            memory.tags = memory_data['tags']
        if 'date' in memory_data:
            memory.date = memory_data['date']
        
        memory.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(memory)
        return memory
    
    def delete_memory(self, memory_id: int, user_id: int) -> bool:
        """删除时光记录"""
        memory = self.get_memory_by_id(memory_id, user_id)
        if not memory:
            return False
        
        # 只有创建者可以删除
        if memory.user_id != user_id:
            return False
        
        self.db.delete(memory)
        self.db.commit()
        return True
    
    def get_memories_by_user(self, user_id: int, trip_id: Optional[int] = None) -> List[Memory]:
        """获取用户的时光记录"""
        query = self.db.query(Memory).filter(Memory.user_id == user_id)
        if trip_id:
            query = query.filter(Memory.trip_id == trip_id)
        
        return query.order_by(desc(Memory.date)).all()
