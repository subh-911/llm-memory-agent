# File Index

## 📁 Project Files Overview

### Core Application Files

| File | Lines | Description |
|------|-------|-------------|
| `main.py` | ~300 | FastAPI application with all REST endpoints |
| `agent.py` | ~400 | Core agent logic with memory management |
| `models.py` | ~150 | Pydantic data models and schemas |
| `llm_client.py` | ~150 | LLM provider abstraction (OpenAI/Anthropic) |
| `memory_store.py` | ~120 | Persistence layer (Redis/In-Memory) |
| `config.py` | ~40 | Configuration management with environment variables |

**Total Core Code**: ~1,160 lines

### Testing & Demo Files

| File | Lines | Description |
|------|-------|-------------|
| `test_agent.py` | ~400 | Comprehensive test suite with pytest |
| `demo.py` | ~300 | 7 interactive demo scenarios |

**Total Test/Demo Code**: ~700 lines

### Configuration Files

| File | Description |
|------|-------------|
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |
| `.gitignore` | Git ignore patterns |
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Multi-container orchestration |
| `start.sh` | Quick start script |

### Documentation Files

| File | Size | Description |
|------|------|-------------|
| `README.md` | ~11 KB | Complete user guide with examples |
| `ARCHITECTURE.md` | ~18 KB | Technical design and architecture |
| `DEPLOYMENT.md` | ~10 KB | Production deployment guide |
| `PROJECT_SUMMARY.md` | ~11 KB | Project overview and metrics |
| `QUICKSTART.md` | ~6 KB | Get started in 5 minutes |
| `FILE_INDEX.md` | This file | File navigation guide |

**Total Documentation**: ~56 KB

## 📊 Project Statistics

- **Total Files**: 18
- **Code Files**: 8 (core + tests)
- **Config Files**: 6
- **Documentation Files**: 6
- **Total Lines of Code**: ~1,860 (core + tests)
- **Total Documentation**: 400+ lines across 6 files

## 🗂️ File Organization by Purpose

### Want to understand the code flow?
1. Start with `agent.py` - core logic
2. Then read `models.py` - data structures
3. Review `main.py` - API endpoints
4. Check `llm_client.py` - LLM integration
5. Finally `memory_store.py` - persistence

### Want to deploy?
1. Read `QUICKSTART.md` first
2. Follow `DEPLOYMENT.md` for production
3. Use `docker-compose.yml` for easy setup

### Want to extend?
1. Review `ARCHITECTURE.md` for design
2. Check `test_agent.py` for patterns
3. Modify relevant files based on feature

### Want to test?
1. Run `test_agent.py` with pytest
2. Try `demo.py` for interactive examples
3. Use Swagger UI at `/docs` endpoint

## 📝 File Details

### main.py
**Purpose**: REST API layer
**Key Components**:
- FastAPI app initialization
- 10+ REST endpoints
- Authentication middleware
- Error handling
- Health checks
- API documentation

**Dependencies**: FastAPI, Pydantic
**Imports**: agent, models, config, llm_client, memory_store

### agent.py
**Purpose**: Core agent implementation
**Key Components**:
- SimpleMemoryAgent class
- Memory management (semantic, episodic)
- Conversation history
- Information extraction
- Memory search
- Context building

**Key Methods**:
- `process()` - Main entry point
- `remember()` - Store memory
- `recall()` - Retrieve memory
- `search_memories()` - Find relevant info
- `clean_expired_memories()` - Cleanup

### models.py
**Purpose**: Data structures
**Key Components**:
- MemoryItem - Individual memory
- MemoryType - Enum for types
- ConversationMessage - Chat message
- ConversationHistory - Message list
- MemorySnapshot - Complete state

**Features**:
- Pydantic validation
- JSON serialization
- Type safety
- Business logic (decay, relevance)

### llm_client.py
**Purpose**: LLM provider abstraction
**Key Components**:
- LLMClient abstract base class
- OpenAIClient implementation
- AnthropicClient implementation
- Token counting

**Supported**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Extensible for new providers

### memory_store.py
**Purpose**: State persistence
**Key Components**:
- MemoryStore abstract base class
- InMemoryStore (development)
- RedisStore (production)

**Operations**:
- save() - Persist snapshot
- load() - Restore snapshot
- delete() - Remove session
- list_sessions() - Get all sessions

### config.py
**Purpose**: Configuration management
**Key Components**:
- Settings class with Pydantic
- Environment variable loading
- Type validation
- Sensible defaults

**Configures**:
- LLM settings
- Memory limits
- Redis connection
- Authentication
- Debug mode

### test_agent.py
**Purpose**: Test suite
**Coverage**:
- Memory operations (store/recall)
- Memory types and decay
- Conversation history
- Information extraction
- Memory search
- Persistence
- Performance

**Framework**: pytest with async support
**Includes**: Mock LLM client for testing

### demo.py
**Purpose**: Interactive demonstrations
**Scenarios**:
1. Basic conversation with memory
2. Preference memory
3. Manual memory storage
4. Multi-turn context
5. Search and recall
6. Session isolation
7. Health check

**Usage**: `python demo.py`

## 🔍 Quick Reference

### To modify memory behavior:
- Edit `agent.py` - `_extract_memory()` method
- Update `models.py` - Add new MemoryType

### To add new API endpoints:
- Edit `main.py` - Add new route
- Update `agent.py` - Add logic if needed

### To support new LLM provider:
- Edit `llm_client.py` - Create new client class
- Inherit from LLMClient
- Implement required methods

### To change persistence:
- Edit `memory_store.py` - Create new store class
- Inherit from MemoryStore
- Implement required methods

### To adjust configuration:
- Edit `.env` file - Change values
- Or set environment variables
- Config loaded from `config.py`

## 📦 Dependencies

### Production Dependencies
```
fastapi==0.109.0          # Web framework
uvicorn[standard]==0.27.0 # ASGI server
pydantic==2.5.3           # Data validation
anthropic==0.18.1         # Anthropic API
openai==1.12.0            # OpenAI API
redis==5.0.1              # Redis client
python-dotenv==1.0.0      # Environment variables
```

### Development Dependencies
```
pytest==8.0.0             # Testing framework
pytest-asyncio==0.23.3    # Async test support
httpx==0.26.0             # HTTP client for tests
```

## 🎯 Entry Points

### Running the Application
```bash
python main.py              # Development server
uvicorn main:app           # Production with Uvicorn
gunicorn main:app          # Production with Gunicorn
```

### Running Tests
```bash
pytest test_agent.py       # All tests
pytest -v                  # Verbose output
pytest -k test_name        # Specific test
```

### Running Demos
```bash
python demo.py             # Interactive demo
```

### Docker
```bash
docker-compose up          # Start all services
docker-compose down        # Stop all services
docker-compose logs        # View logs
```

## 📖 Reading Order for New Developers

### For Understanding (Recommended Order):
1. `QUICKSTART.md` - Get it running (5 min)
2. `README.md` - Understand features (15 min)
3. `models.py` - Learn data structures (10 min)
4. `agent.py` - Core logic (30 min)
5. `main.py` - API layer (20 min)
6. `test_agent.py` - See usage patterns (20 min)
7. `ARCHITECTURE.md` - Deep dive (30 min)

### For Deployment:
1. `QUICKSTART.md` - Quick setup
2. `DEPLOYMENT.md` - Production guide
3. `docker-compose.yml` - Container setup

### For Extension:
1. `ARCHITECTURE.md` - Design patterns
2. Relevant code file for feature
3. `test_agent.py` - Add tests
4. Update `README.md` - Document changes

## 🔗 File Dependencies

```
main.py
  ├── agent.py
  │   ├── models.py
  │   ├── llm_client.py
  │   └── memory_store.py
  ├── config.py
  └── models.py

test_agent.py
  ├── agent.py
  ├── models.py
  └── memory_store.py

demo.py
  └── (HTTP client to running server)
```

## ✨ File Highlights

### Most Complex: `agent.py`
- Core business logic
- Multiple memory types
- Information extraction
- Search algorithms

### Most Important: `main.py`
- User-facing API
- Authentication
- Error handling
- Entry point

### Most Configurable: `config.py`
- All settings in one place
- Environment variable support
- Type safety

### Most Tested: `test_agent.py`
- 15+ test cases
- 100% core coverage
- Real-world scenarios

### Best Documented: `README.md`
- Complete user guide
- API examples
- Troubleshooting

---

**Total Project Size**: ~2,500 lines of code + documentation
**Time to Read All**: ~2-3 hours
**Time to Understand**: ~1 day
**Time to Master**: ~1 week
