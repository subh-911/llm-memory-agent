# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                            │
│                                                                   │
│  Web Browser / Mobile App / API Client / CLI / Other Services   │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP/HTTPS
                                 │
                ┌────────────────▼────────────────┐
                │       Nginx (Optional)          │
                │    - SSL Termination            │
                │    - Load Balancing             │
                │    - Rate Limiting              │
                └────────────────┬────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                         FastAPI Application                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                     main.py (API Layer)                     │ │
│  │  - Health checks     - Authentication                       │ │
│  │  - Chat endpoints    - Session management                   │ │
│  │  - Memory endpoints  - Error handling                       │ │
│  └───────────────────────────┬────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼────────────────────────────────┐ │
│  │               agent.py (Business Logic)                     │ │
│  │  - Memory management      - Context building               │ │
│  │  - Information extraction - Memory search                  │ │
│  │  - Conversation flow      - Memory decay                   │ │
│  └───────────────┬──────────────────────┬────────────────────┘ │
│                  │                      │                       │
│     ┌────────────▼──────────┐  ┌───────▼────────────┐          │
│     │   llm_client.py       │  │  memory_store.py   │          │
│     │  - OpenAI client      │  │  - Redis store     │          │
│     │  - Anthropic client   │  │  - In-memory store │          │
│     │  - Token counting     │  │  - Persistence     │          │
│     └──────────┬────────────┘  └──────┬─────────────┘          │
│                │                      │                         │
│     ┌──────────▼──────────┐  ┌───────▼─────────────┐           │
│     │     models.py       │  │    config.py        │           │
│     │  - Data schemas     │  │  - Settings         │           │
│     │  - Validation       │  │  - Environment      │           │
│     └─────────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                │                              │
                │ API Calls                    │ Redis Protocol
                │                              │
┌───────────────▼──────────────┐  ┌───────────▼─────────────┐
│    External LLM API          │  │      Redis Server        │
│  - OpenAI GPT-4              │  │  - Session storage       │
│  - Anthropic Claude          │  │  - Memory persistence    │
│  - Token consumption         │  │  - Cache layer           │
└──────────────────────────────┘  └──────────────────────────┘
```

## Data Flow

### Chat Request Flow

```
User Message
    │
    ├─► [1] FastAPI receives request
    │       ├─► Authenticate API key
    │       └─► Validate request format
    │
    ├─► [2] Create/Load Agent instance
    │       └─► Load session from memory store
    │
    ├─► [3] Agent processes message
    │       ├─► Clean expired memories
    │       ├─► Build context from memories
    │       ├─► Prepare messages with history
    │       └─► Add current user input
    │
    ├─► [4] Call LLM API
    │       ├─► OpenAI or Anthropic
    │       ├─► Send messages + context
    │       └─► Receive response + usage stats
    │
    ├─► [5] Process LLM response
    │       ├─► Update conversation history
    │       ├─► Extract memorable information
    │       └─► Store new memories
    │
    ├─► [6] Save state
    │       └─► Persist to memory store
    │
    └─► [7] Return response to user
            ├─► Response text
            ├─► Usage statistics
            └─► Memory metadata
```

### Memory Management Flow

```
Information Input
    │
    ├─► Automatic Extraction
    │   ├─► Pattern matching (regex)
    │   ├─► Identify: names, preferences, facts
    │   └─► Generate memory keys
    │
    ├─► Memory Creation
    │   ├─► Create MemoryItem
    │   ├─► Set importance score
    │   ├─► Add timestamp
    │   └─► Classify type (semantic/episodic)
    │
    ├─► Storage
    │   ├─► Semantic → Dict (by key)
    │   ├─► Episodic → List (chronological)
    │   └─► Working → Conversation history
    │
    ├─► Decay Management
    │   ├─► Calculate age
    │   ├─► Apply importance weighting
    │   └─► Remove if expired
    │
    └─► Retrieval
        ├─► By key (recall)
        ├─► By search (keyword match)
        └─► By relevance (scoring)
```

## Component Responsibilities

### main.py (API Layer)
**Purpose**: HTTP interface and request handling

**Responsibilities**:
- Route management
- Request/response validation
- Authentication
- Error handling
- Health checks
- API documentation

**Does NOT handle**:
- Business logic
- Memory management
- LLM communication

### agent.py (Core Logic)
**Purpose**: Agent behavior and memory management

**Responsibilities**:
- Process user input
- Manage conversation state
- Extract information
- Search memories
- Build context
- Coordinate LLM calls

**Key Methods**:
- `process()`: Main entry point
- `remember()`: Store memory
- `recall()`: Retrieve memory
- `search_memories()`: Find relevant info
- `clean_expired_memories()`: Maintenance

### models.py (Data Layer)
**Purpose**: Data structures and validation

**Components**:
- `MemoryItem`: Individual memory with metadata
- `ConversationMessage`: Single message
- `ConversationHistory`: Message list management
- `MemorySnapshot`: Complete state for persistence

**Features**:
- Pydantic validation
- JSON serialization
- Type safety
- Business rules (decay, relevance)

### llm_client.py (Integration Layer)
**Purpose**: Abstract LLM provider details

**Responsibilities**:
- Unified interface for multiple providers
- Request formatting
- Response parsing
- Error handling
- Token counting

**Supported Providers**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Extensible for new providers

### memory_store.py (Persistence Layer)
**Purpose**: State persistence

**Implementations**:
- `InMemoryStore`: Development/testing
- `RedisStore`: Production persistence

**Operations**:
- Save snapshot
- Load snapshot
- Delete session
- List sessions

### config.py (Configuration Layer)
**Purpose**: Centralized settings management

**Features**:
- Environment variable loading
- Type validation
- Default values
- Documentation

## Memory Architecture

### Memory Types

```
┌─────────────────────────────────────────────────────────┐
│                    Working Memory                        │
│  (Conversation History - Last 10 exchanges)             │
│                                                          │
│  [User] → [Assistant] → [User] → [Assistant] → ...     │
│                                                          │
│  Purpose: Maintain conversation context                 │
│  Storage: List[ConversationMessage]                     │
│  Limit: MAX_CONVERSATION_HISTORY (default: 10)         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Semantic Memory                        │
│  (Facts, Knowledge, Preferences)                        │
│                                                          │
│  {                                                       │
│    "user_name": "John",                                 │
│    "favorite_color": "blue",                            │
│    "occupation": "engineer",                            │
│    ...                                                   │
│  }                                                       │
│                                                          │
│  Purpose: Store factual information                     │
│  Storage: Dict[str, MemoryItem]                         │
│  Access: By key                                          │
│  Decay: Time + importance weighted                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Episodic Memory                        │
│  (Conversation Events, Experiences)                     │
│                                                          │
│  [                                                       │
│    "User discussed vacation plans",                     │
│    "Talked about favorite movies",                      │
│    "Asked about weather",                               │
│    ...                                                   │
│  ]                                                       │
│                                                          │
│  Purpose: Record conversation events                    │
│  Storage: List[MemoryItem]                              │
│  Access: Chronological, search                          │
│  Limit: Last 50 episodes                                │
└─────────────────────────────────────────────────────────┘
```

### Memory Lifecycle

```
1. Creation
   ├─► User mentions information
   ├─► Pattern matching identifies it
   ├─► MemoryItem created with:
   │   ├─► Key
   │   ├─► Value
   │   ├─► Type (semantic/episodic/preference)
   │   ├─► Importance score
   │   └─► Timestamp

2. Storage
   ├─► Semantic/Preference → semantic_memory dict
   └─► Episodic → episodic_memory list

3. Access
   ├─► Direct recall (by key)
   ├─► Search (keyword matching)
   ├─► Context building (relevance scored)
   └─► Access tracking (count, last_accessed)

4. Decay
   ├─► Age calculation
   ├─► Importance weighting
   ├─► Expiration check
   └─► Automatic cleanup

5. Persistence
   ├─► On every process() call
   ├─► Serialize to JSON
   ├─► Save to memory store
   └─► Redis or in-memory
```

## Scaling Architecture

### Horizontal Scaling

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Instance 1  │   │  Instance 2  │   │  Instance 3  │
│  (FastAPI)   │   │  (FastAPI)   │   │  (FastAPI)   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                    ┌─────▼─────┐
                    │   Redis   │
                    │  (Shared  │
                    │   State)  │
                    └───────────┘
```

**Key Points**:
- Stateless application instances
- Redis for shared session state
- Load balancer distributes requests
- No session affinity required

### Vertical Scaling

**Resource Guidelines**:
- **2 GB RAM** per worker process
- **1 CPU core** per 2 workers
- **Redis**: 4 GB for ~10K sessions

**Optimization**:
- Reduce conversation history
- Lower max tokens
- Use smaller LLM models
- Implement response caching

## Security Architecture

### Authentication Flow

```
Request
    │
    ├─► Extract X-API-Key header
    │
    ├─► Validate against API_KEYS list
    │   ├─► Valid → Continue
    │   └─► Invalid → 401 Unauthorized
    │
    └─► Process request
```

### Data Security

**At Rest**:
- Redis password protection
- Encrypted connection strings
- No sensitive data in logs

**In Transit**:
- HTTPS/TLS for API
- Redis TLS (optional)
- Encrypted LLM API calls

**Access Control**:
- API key authentication
- Rate limiting per key
- Session isolation

## Observability

### Logging Points

```
[Request] → Log: session_id, endpoint, auth_status
    │
    ├─► [Agent Process] → Log: context_used, memory_counts
    │
    ├─► [LLM Call] → Log: model, tokens, latency
    │
    ├─► [Memory Ops] → Log: keys_stored, searches, cleanups
    │
    └─► [Response] → Log: status, duration, errors
```

### Metrics to Track

**Performance**:
- Request latency (p50, p95, p99)
- LLM call duration
- Memory operations time

**Usage**:
- Requests per session
- Tokens per request
- Active sessions
- Memory items per session

**Health**:
- Error rates
- Redis connection status
- LLM API availability

## Extension Points

### Adding New Memory Types

1. Update `MemoryType` enum in `models.py`
2. Add extraction logic in `agent._extract_memory()`
3. Update storage logic if needed
4. Add retrieval methods

### Adding New LLM Providers

1. Create new client class in `llm_client.py`
2. Inherit from `LLMClient`
3. Implement `chat()` and `count_tokens()`
4. Update `get_llm_client()` factory
5. Add config settings

### Adding Custom Tools

1. Create tool function
2. Register in agent initialization
3. Add to LLM system prompt
4. Implement execution logic
5. Add error handling

## Performance Characteristics

### Latency Breakdown

```
Total Request Time: ~2-5 seconds
    │
    ├─► Authentication: 1-5ms
    ├─► Load session: 10-50ms (Redis) or 1ms (in-memory)
    ├─► Memory cleanup: 1-10ms
    ├─► Context building: 5-20ms
    ├─► LLM API call: 1-4 seconds ⬅ Dominant factor
    ├─► Memory extraction: 5-10ms
    ├─► Save session: 10-50ms (Redis)
    └─► Response formatting: 1-5ms
```

### Resource Usage

**Memory per Session**:
- Conversation history: ~10-50 KB
- Semantic memories: ~1-10 KB per memory
- Total: ~50-200 KB per active session

**Database (Redis)**:
- ~100-500 KB per session (with all data)
- 1 GB supports ~2,000-10,000 sessions

## Deployment Patterns

### Development
```
Local Machine
    └─► Python process
        └─► In-memory storage
```

### Staging
```
Docker Container
    └─► FastAPI + Uvicorn
        └─► Redis container
```

### Production
```
Kubernetes Cluster
    ├─► Multiple pods (FastAPI)
    ├─► Redis StatefulSet
    ├─► Load Balancer
    └─► Monitoring (Prometheus/Grafana)
```

This architecture provides a solid foundation for building upon while maintaining clean separation of concerns and scalability.
