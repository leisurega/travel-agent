"""
基于Qwen模型的mem0记忆功能API接口
提供RESTful API接口用于记忆管理
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .qwen_mem0_service import QwenMem0Service, create_qwen_mem0_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/memory", tags=["memory"])

# 请求模型
class MemoryAddRequest(BaseModel):
    content: str = Field(..., description="记忆内容")
    user_id: str = Field(..., description="用户ID")
    memory_type: str = Field(default="conversation", description="记忆类型")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    user_id: str = Field(..., description="用户ID")
    limit: int = Field(default=5, ge=1, le=50, description="返回结果数量限制")
    memory_type: Optional[str] = Field(default=None, description="记忆类型过滤")

class MemoryUpdateRequest(BaseModel):
    memory_id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="新的记忆内容")
    user_id: str = Field(..., description="用户ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="新的元数据")

class MemoryDeleteRequest(BaseModel):
    memory_id: str = Field(..., description="记忆ID")
    user_id: str = Field(..., description="用户ID")

class MemoryClearRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    memory_type: Optional[str] = Field(default=None, description="记忆类型过滤")

class MemoryExportRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    file_path: Optional[str] = Field(default=None, description="导出文件路径")

class MemoryImportRequest(BaseModel):
    file_path: str = Field(..., description="导入文件路径")
    user_id: Optional[str] = Field(default=None, description="目标用户ID")

# 响应模型
class MemoryResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MemoryListResponse(BaseModel):
    success: bool
    total: int
    memories: List[Dict[str, Any]]
    error: Optional[str] = None

class MemoryStatsResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    error: Optional[str] = None

# 依赖注入
def get_memory_service() -> QwenMem0Service:
    """获取记忆服务实例"""
    try:
        return create_qwen_mem0_service()
    except Exception as e:
        logger.error(f"创建记忆服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"记忆服务初始化失败: {str(e)}")

# API端点
@router.post("/add", response_model=MemoryResponse)
async def add_memory(
    request: MemoryAddRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """添加记忆"""
    try:
        result = service.add_memory(
            content=request.content,
            user_id=request.user_id,
            metadata=request.metadata,
            memory_type=request.memory_type
        )
        
        if result.get("success"):
            return MemoryResponse(
                success=True,
                message="记忆添加成功",
                data=result
            )
        else:
            return MemoryResponse(
                success=False,
                error=result.get("error", "添加记忆失败")
            )
            
    except Exception as e:
        logger.error(f"添加记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=MemoryListResponse)
async def search_memories(
    request: MemorySearchRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """搜索记忆"""
    try:
        results = service.search_memories(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit,
            memory_type=request.memory_type
        )
        
        return MemoryListResponse(
            success=True,
            total=len(results),
            memories=results
        )
        
    except Exception as e:
        logger.error(f"搜索记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=MemoryListResponse)
async def get_user_memories(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    memory_type: Optional[str] = Query(default=None),
    service: QwenMem0Service = Depends(get_memory_service)
):
    """获取用户记忆"""
    try:
        results = service.get_user_memories(
            user_id=user_id,
            limit=limit,
            memory_type=memory_type
        )
        
        return MemoryListResponse(
            success=True,
            total=len(results),
            memories=results
        )
        
    except Exception as e:
        logger.error(f"获取用户记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", response_model=MemoryResponse)
async def update_memory(
    request: MemoryUpdateRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """更新记忆"""
    try:
        result = service.update_memory(
            memory_id=request.memory_id,
            content=request.content,
            user_id=request.user_id,
            metadata=request.metadata
        )
        
        if result.get("success"):
            return MemoryResponse(
                success=True,
                message="记忆更新成功",
                data=result
            )
        else:
            return MemoryResponse(
                success=False,
                error=result.get("error", "更新记忆失败")
            )
            
    except Exception as e:
        logger.error(f"更新记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete", response_model=MemoryResponse)
async def delete_memory(
    request: MemoryDeleteRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """删除记忆"""
    try:
        result = service.delete_memory(
            memory_id=request.memory_id,
            user_id=request.user_id
        )
        
        if result.get("success"):
            return MemoryResponse(
                success=True,
                message="记忆删除成功",
                data=result
            )
        else:
            return MemoryResponse(
                success=False,
                error=result.get("error", "删除记忆失败")
            )
            
    except Exception as e:
        logger.error(f"删除记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{user_id}", response_model=MemoryResponse)
async def get_memory_summary(
    user_id: str,
    memory_type: Optional[str] = Query(default=None),
    service: QwenMem0Service = Depends(get_memory_service)
):
    """获取记忆摘要"""
    try:
        summary = service.generate_memory_summary(
            user_id=user_id,
            memory_type=memory_type
        )
        
        return MemoryResponse(
            success=True,
            message="记忆摘要生成成功",
            data={"summary": summary}
        )
        
    except Exception as e:
        logger.error(f"获取记忆摘要API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{user_id}", response_model=MemoryStatsResponse)
async def get_memory_stats(
    user_id: str,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """获取记忆统计"""
    try:
        stats = service.get_memory_stats(user_id=user_id)
        
        return MemoryStatsResponse(
            success=True,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"获取记忆统计API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear", response_model=MemoryResponse)
async def clear_memories(
    request: MemoryClearRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """清空记忆"""
    try:
        result = service.clear_user_memories(
            user_id=request.user_id,
            memory_type=request.memory_type
        )
        
        if result.get("success"):
            return MemoryResponse(
                success=True,
                message=result.get("message", "记忆清空成功"),
                data=result
            )
        else:
            return MemoryResponse(
                success=False,
                error=result.get("error", "清空记忆失败")
            )
            
    except Exception as e:
        logger.error(f"清空记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export", response_model=MemoryResponse)
async def export_memories(
    request: MemoryExportRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """导出记忆"""
    try:
        result = service.export_memories(
            user_id=request.user_id,
            file_path=request.file_path
        )
        
        if result.get("success"):
            return MemoryResponse(
                success=True,
                message="记忆导出成功",
                data=result
            )
        else:
            return MemoryResponse(
                success=False,
                error=result.get("error", "导出记忆失败")
            )
            
    except Exception as e:
        logger.error(f"导出记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import", response_model=MemoryResponse)
async def import_memories(
    request: MemoryImportRequest,
    service: QwenMem0Service = Depends(get_memory_service)
):
    """导入记忆"""
    try:
        result = service.import_memories(
            file_path=request.file_path,
            user_id=request.user_id
        )
        
        if result.get("success"):
            return MemoryResponse(
                success=True,
                message="记忆导入成功",
                data=result
            )
        else:
            return MemoryResponse(
                success=False,
                error=result.get("error", "导入记忆失败")
            )
            
    except Exception as e:
        logger.error(f"导入记忆API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查端点
@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "qwen-mem0-memory",
        "timestamp": datetime.now().isoformat()
    }

# 获取API文档信息
@router.get("/info")
async def get_api_info():
    """获取API信息"""
    return {
        "service": "Qwen Mem0 Memory Service",
        "version": "1.0.0",
        "description": "基于Qwen模型的mem0记忆功能服务",
        "endpoints": [
            "POST /add - 添加记忆",
            "POST /search - 搜索记忆",
            "GET /user/{user_id} - 获取用户记忆",
            "PUT /update - 更新记忆",
            "DELETE /delete - 删除记忆",
            "GET /summary/{user_id} - 获取记忆摘要",
            "GET /stats/{user_id} - 获取记忆统计",
            "POST /clear - 清空记忆",
            "POST /export - 导出记忆",
            "POST /import - 导入记忆",
            "GET /health - 健康检查",
            "GET /info - API信息"
        ]
    }

