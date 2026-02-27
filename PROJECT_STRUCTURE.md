# Cheetah Express - Project Structure

```
CheetahExpress/
├── agents/                          # Multi-Agent System
│   ├── __init__.py
│   ├── orchestrator_agent.py       # GPT-4o coordinator
│   ├── driver_context_agent.py     # Yutori API integration
│   ├── compliance_agent.py         # Neo4j compliance checks
│   ├── routing_agent.py            # Google Maps routing
│   ├── ranking_agent.py            # Driver scoring engine
│   └── voice_dispatch_agent.py     # Modulate voice calls
│
├── database/                        # Database Layer
│   ├── __init__.py
│   └── neo4j_client.py             # Neo4j graph operations
│
├── scripts/                         # Utility Scripts
│   ├── __init__.py
│   ├── seed_drivers.py             # Populate sample drivers
│   └── test_order.py               # Test order creation
│
├── tests/                           # Test Suite
│   ├── __init__.py
│   └── test_api.py                 # API endpoint tests
│
├── main.py                          # FastAPI application
├── models.py                        # Pydantic data models
├── config.py                        # Configuration management
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
│
├── Dockerfile                       # Docker image definition
├── docker-compose.yml              # Multi-container setup
├── Procfile                        # Render deployment
├── render.yaml                     # Render configuration
├── runtime.txt                     # Python version
│
├── README.md                        # Main documentation
├── ARCHITECTURE.md                 # System design details
├── DEPLOYMENT.md                   # Deployment guide
├── QUICKSTART.md                   # 5-minute setup
├── PROJECT_STRUCTURE.md            # This file
└── LICENSE                         # MIT License
```

---

## File Descriptions

### Core Application

**`main.py`** (350 lines)
- FastAPI application entry point
- REST API endpoints for order management
- Health checks and monitoring
- Background task processing
- Lifespan management for Neo4j connection

**`models.py`** (120 lines)
- Pydantic models for type safety
- OrderRequest, DispatchResult, DriverInfo
- Enums for VehicleType, OrderStatus, CallOutcome
- Validation schemas

**`config.py`** (25 lines)
- Environment variable management
- Settings class with Pydantic
- API key configuration
- Database connection strings

---

### Agents (Multi-Agent System)

**`agents/orchestrator_agent.py`** (200 lines)
- Main coordinator using GPT-4o
- Orchestrates all sub-agents
- Error handling and recovery
- Order analysis and insights

**`agents/driver_context_agent.py`** (80 lines)
- Yutori API integration
- Fetch active drivers with GPS
- Driver profile retrieval
- Availability checking

**`agents/compliance_agent.py`** (90 lines)
- Neo4j compliance validation
- License expiry checks
- Vehicle type matching
- Workload budget verification
- Shift window validation

**`agents/routing_agent.py`** (120 lines)
- Google Maps Distance Matrix API
- ETA calculations (driver→pickup→dropoff)
- SLA time window validation
- Route feasibility filtering

**`agents/ranking_agent.py`** (100 lines)
- Multi-factor scoring algorithm
- Driver prioritization
- Workload optimization
- License expiry buffer consideration

**`agents/voice_dispatch_agent.py`** (130 lines)
- Modulate AI voice integration
- Sequential driver calling
- Sentiment analysis
- Accept/decline capture

---

### Database

**`database/neo4j_client.py`** (280 lines)
- Neo4j driver management
- Schema initialization
- Compliance queries
- Audit trail logging
- Workload tracking
- Graph relationship management

---

### Scripts

**`scripts/seed_drivers.py`** (100 lines)
- Populate Neo4j with sample drivers
- 8 diverse driver profiles
- Varied vehicle types and shifts
- License expiry dates

**`scripts/test_order.py`** (60 lines)
- Create test delivery orders
- Sample order generation
- API testing helper

---

### Tests

**`tests/test_api.py`** (80 lines)
- FastAPI endpoint tests
- Order validation tests
- Health check tests
- Async order processing tests

---

### Configuration Files

**`requirements.txt`**
- FastAPI, Uvicorn
- OpenAI, Neo4j drivers
- httpx, pydantic
- structlog, pytest

**`.env.example`**
- Template for environment variables
- API key placeholders
- Database configuration

**`Dockerfile`**
- Python 3.11 slim base image
- Production-ready container

**`docker-compose.yml`**
- Neo4j + Application stack
- Network configuration
- Volume management

**`render.yaml`**
- Render deployment config
- Environment variables
- Build/start commands

---

## Data Flow Through Files

1. **Order Intake**: `main.py` → receives webhook
2. **Orchestration**: `orchestrator_agent.py` → coordinates flow
3. **Driver Fetch**: `driver_context_agent.py` → Yutori API
4. **Compliance**: `compliance_agent.py` + `neo4j_client.py` → validate
5. **Routing**: `routing_agent.py` → Google Maps API
6. **Ranking**: `ranking_agent.py` → score drivers
7. **Dispatch**: `voice_dispatch_agent.py` → Modulate API
8. **Audit**: `neo4j_client.py` → log decisions
9. **Response**: `main.py` → return DispatchResult

---

## Key Design Patterns

### Agent Pattern
Each agent is a self-contained module with:
- Single responsibility
- Async operations
- Error handling
- Structured logging

### Repository Pattern
`neo4j_client.py` abstracts database operations:
- Connection management
- Query encapsulation
- Transaction handling

### Dependency Injection
Settings injected via `config.py`:
- Environment-based configuration
- Easy testing with mocks
- Secure credential management

### API Gateway Pattern
`main.py` serves as single entry point:
- Request validation
- Response formatting
- Error standardization

---

## Technology Stack by File

| File | Technologies |
|------|-------------|
| `main.py` | FastAPI, Uvicorn, structlog |
| `orchestrator_agent.py` | OpenAI GPT-4o |
| `driver_context_agent.py` | httpx, Yutori API |
| `compliance_agent.py` | Neo4j Python driver |
| `routing_agent.py` | Google Maps API |
| `voice_dispatch_agent.py` | Modulate API |
| `neo4j_client.py` | Neo4j 5.x, Cypher |
| `models.py` | Pydantic v2 |
| `tests/` | pytest, pytest-asyncio |

---

## Lines of Code Summary

| Component | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| Agents | 6 | ~820 | Multi-agent orchestration |
| Database | 1 | ~280 | Neo4j operations |
| API | 1 | ~350 | FastAPI endpoints |
| Models | 1 | ~120 | Data validation |
| Scripts | 2 | ~160 | Utilities |
| Tests | 1 | ~80 | Quality assurance |
| Config | 3 | ~100 | Deployment |
| **Total** | **15** | **~1,910** | **Production system** |

---

## Extension Points

### Adding New Agents
1. Create `agents/new_agent.py`
2. Implement async methods
3. Add to orchestrator workflow
4. Update tests

### Adding New Compliance Rules
1. Update `compliance_agent.py`
2. Add Neo4j queries in `neo4j_client.py`
3. Update `ComplianceResult` model
4. Document in ARCHITECTURE.md

### Adding New API Endpoints
1. Add route in `main.py`
2. Create request/response models in `models.py`
3. Add tests in `tests/test_api.py`
4. Update API documentation

---

**Project Structure Version**: 1.0  
**Total Files**: 22  
**Total Lines of Code**: ~1,910  
**Language**: Python 3.11  
**Framework**: FastAPI  
**Database**: Neo4j 5.x
