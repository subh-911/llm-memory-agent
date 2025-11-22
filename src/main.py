from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

from .config import settings
from .agent import SimpleMemoryAgent
from .llm_client import get_llm_client
from .memory_store import get_memory_store

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
llm_client = None
memory_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global llm_client, memory_store
    
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    try:
        llm_client = get_llm_client()
        memory_store = get_memory_store()
        logger.info(f"LLM Provider: {settings.llm_provider}")
        logger.info(f"Memory Store: {'Redis' if settings.use_redis else 'In-Memory'}")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down gracefully")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready LLM Agent with Memory",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message", min_length=1, max_length=10000)
    session_id: Optional[str] = Field(default="default", description="Session identifier")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    session_id: str
    usage: Dict[str, int]
    context_used: bool
    memories_count: Dict[str, int]


class MemoryRequest(BaseModel):
    key: str = Field(..., description="Memory key")
    value: Any = Field(..., description="Memory value")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    session_id: Optional[str] = Field(default="default")


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    session_id: Optional[str] = Field(default="default")
    limit: int = Field(default=5, ge=1, le=20)


class SessionRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")


# Dependency: API Key Authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if authentication is enabled"""
    if not settings.api_keys:
        # No authentication required
        return True
    
    if not x_api_key or x_api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True


# Dependency: Get Agent Instance
async def get_agent(session_id: str = "default") -> SimpleMemoryAgent:
    """Get or create agent instance for session"""
    agent = SimpleMemoryAgent(
        llm_client=llm_client,
        memory_store=memory_store,
        session_id=session_id
    )
    await agent.initialize()
    return agent


# Health Check Endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check LLM client
        llm_status = "healthy" if llm_client else "unavailable"
        
        # Check memory store
        store_status = "healthy" if memory_store else "unavailable"
        
        overall_healthy = llm_status == "healthy" and store_status == "healthy"
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "version": settings.app_version,
            "checks": {
                "llm_client": llm_status,
                "memory_store": store_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(
    request: ChatRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Send a message to the agent and get a response.
    
    The agent maintains conversation history and can remember information
    from previous messages in the same session.
    """
    try:
        agent = await get_agent(request.session_id)
        result = await agent.process(request.message)
        
        return ChatResponse(
            response=result["response"],
            session_id=request.session_id,
            usage=result["usage"],
            context_used=result["context_used"],
            memories_count=result["memories_count"]
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


# Memory Management Endpoints
@app.post("/memory/store", tags=["Memory"])
async def store_memory(
    request: MemoryRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """Manually store information in agent memory"""
    try:
        agent = await get_agent(request.session_id)
        agent.remember(
            key=request.key,
            value=request.value,
            importance=request.importance
        )
        await agent.save()
        
        return {
            "status": "success",
            "message": f"Memory '{request.key}' stored successfully"
        }
    except Exception as e:
        logger.error(f"Store memory error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/memory/recall/{key}", tags=["Memory"])
async def recall_memory(
    key: str,
    session_id: str = "default",
    authenticated: bool = Depends(verify_api_key)
):
    """Retrieve specific memory by key"""
    try:
        agent = await get_agent(session_id)
        value = agent.recall(key)
        
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Memory '{key}' not found"
            )
        
        return {
            "key": key,
            "value": value,
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recall memory error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/memory/search", tags=["Memory"])
async def search_memories(
    request: MemorySearchRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """Search memories by query"""
    try:
        agent = await get_agent(request.session_id)
        results = agent.search_memories(request.query, limit=request.limit)
        
        return {
            "query": request.query,
            "results": [
                {
                    "key": memory.key,
                    "value": memory.value,
                    "type": memory.memory_type,
                    "relevance": memory.calculate_relevance(),
                    "timestamp": memory.timestamp.isoformat()
                }
                for memory in results
            ],
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search memories error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/memory/summary", tags=["Memory"])
async def get_memory_summary(
    session_id: str = "default",
    authenticated: bool = Depends(verify_api_key)
):
    """Get summary of agent's current memory state"""
    try:
        agent = await get_agent(session_id)
        summary = agent.get_memory_summary()
        return summary
    except Exception as e:
        logger.error(f"Memory summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/memory/clear", tags=["Memory"])
async def clear_memory(
    request: SessionRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """Clear all memories and conversation history for a session"""
    try:
        agent = await get_agent(request.session_id)
        await agent.clear_memory()
        
        return {
            "status": "success",
            "message": f"Memory cleared for session '{request.session_id}'"
        }
    except Exception as e:
        logger.error(f"Clear memory error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Session Management
@app.get("/sessions", tags=["Sessions"])
async def list_sessions(authenticated: bool = Depends(verify_api_key)):
    """List all active sessions"""
    try:
        sessions = await memory_store.list_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(
    session_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Delete a session and all its data"""
    try:
        await memory_store.delete(session_id)
        return {
            "status": "success",
            "message": f"Session '{session_id}' deleted"
        }
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Production-ready LLM Agent with Memory",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
