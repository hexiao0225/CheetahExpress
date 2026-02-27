# Cheetah Express Architecture Documentation

## System Overview

Cheetah Express is a production-level, AI-powered delivery dispatch system that uses multi-agent orchestration to automatically assign delivery orders to the most suitable drivers.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ORDER INTAKE EVENT                        │
│         (Direct Webhook / Your Own Order System)            │
│                                                              │
│   Payload: pickup, dropoff, time_window,                    │
│            vehicle_type, customer_info                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          ORCHESTRATOR AGENT (OpenAI GPT-4o)                 │
│          Cheetah Express Brain                              │
│   Parses order, coordinates all sub-agents                  │
└──────┬───────────────────────────┬──────────────────────────┘
       │                           │
       ▼                           ▼
┌─────────────────┐     ┌──────────────────────────┐
│  DRIVER CONTEXT │     │  COMPLIANCE CHECK AGENT  │
│  AGENT          │     │  (Neo4j)                 │
│                 │     │                          │
│  Yutori API:    │     │  2.1 License valid?      │
│  - Live GPS     │     │  2.2 Vehicle type match? │
│  - Driver info  │     │  2.3 Within allowed      │
│  - Phone number │     │       distance/time SLA? │
│  - Availability │     │  2.4 Shift hours OK?     │
│                 │     │                          │
│  Returns:       │     │  Returns:                │
│  Active driver  │     │  ELIGIBLE driver list    │
│  pool           │     │  + reason per driver     │
└──────┬──────────┘     └──────────┬───────────────┘
       │                           │
       └──────────────┬────────────┘
                      │ Active ∩ Compliant
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  ROUTING AGENT                               │
│              (Yutori → Google Maps)                         │
│                                                              │
│  For each eligible driver:                                  │
│  Yutori calls Google Maps Distance Matrix API               │
│  → Real-time ETA: driver GPS → pickup → dropoff             │
│  → Filter: total trip must fit within time_window           │
│                                                              │
│  Returns: ETA + feasibility per driver                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  RANKING ENGINE                              │
│                                                              │
│  Score = f(ETA, vehicle_match, SLA_fit,                     │
│             remaining_km_budget, license_expiry_buffer)     │
│                                                              │
│  Output: Ordered list [Driver_1, Driver_2, ... Driver_N]    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           VOICE DISPATCH AGENT (Modulate)                   │
│                                                              │
│  Loop: for each driver in ranked list                       │
│    → Call driver via Modulate Voice API                     │
│    → Inform: pickup, dropoff, time window                   │
│    → Capture: Accept / Decline + sentiment metadata         │
│    → If accepted → confirm assignment, break loop           │
│    → If declined → log reason → call next driver            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         DECISION LOGGING & AUDIT GRAPH (Neo4j)              │
│                                                              │
│  Compliance decisions → why each driver passed/failed       │
│  Ranking decisions → score + reasoning per driver           │
│  Call outcomes → accepted/declined + sentiment metadata     │
│  Full audit trail → explainable AI for ops managers         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Order Intake (FastAPI Webhook)
- **Technology**: FastAPI REST API
- **Endpoints**: 
  - `POST /api/v1/orders` (synchronous)
  - `POST /api/v1/orders/async` (background processing)
- **Input**: OrderRequest with pickup, dropoff, time window, vehicle type, customer info
- **Output**: Triggers orchestrator agent

### 2. Orchestrator Agent
- **Technology**: OpenAI GPT-4o
- **Responsibilities**:
  - Parse and analyze incoming orders
  - Coordinate all sub-agents in sequence
  - Handle error recovery and fallbacks
  - Return final dispatch result
- **File**: `agents/orchestrator_agent.py`

### 3. Driver Context Agent
- **Technology**: Yutori API integration
- **Responsibilities**:
  - Fetch active drivers with live GPS locations
  - Retrieve driver profiles (phone, license, vehicle type)
  - Filter available drivers
- **File**: `agents/driver_context_agent.py`
- **External Dependency**: Yutori API

### 4. Compliance Agent
- **Technology**: Neo4j graph database queries
- **Responsibilities**:
  - Validate license expiry (>14 days buffer)
  - Check vehicle type match
  - Verify daily km/hour budget remaining
  - Confirm shift window covers delivery time
  - Log all compliance decisions to Neo4j
- **File**: `agents/compliance_agent.py`
- **Database**: Neo4j

### 5. Routing Agent
- **Technology**: Google Maps Distance Matrix API
- **Responsibilities**:
  - Calculate ETA from driver location to pickup
  - Calculate ETA from pickup to dropoff
  - Determine if total trip fits within SLA time window
  - Filter out non-feasible routes
- **File**: `agents/routing_agent.py`
- **External Dependency**: Google Maps API

### 6. Ranking Engine
- **Technology**: Python scoring algorithm
- **Responsibilities**:
  - Score each eligible driver using multi-factor formula
  - Sort drivers by score (highest first)
  - Log ranking decisions to Neo4j
- **File**: `agents/ranking_agent.py`
- **Scoring Formula**:
  ```
  Score = 100
    - (ETA to pickup × 0.5)
    - (Total trip time × 0.2)
    + (Vehicle match ? 20 : -10)
    + (License expiry buffer bonus: 0-10)
    + (Remaining km budget bonus: 0-15)
  ```

### 7. Voice Dispatch Agent
- **Technology**: Modulate AI Voice API
- **Responsibilities**:
  - Call drivers in ranked order
  - Present order details via voice
  - Capture accept/decline response
  - Perform sentiment analysis
  - Log all call outcomes to Neo4j
- **File**: `agents/voice_dispatch_agent.py`
- **External Dependency**: Modulate API

### 8. Neo4j Audit Graph
- **Technology**: Neo4j 5.x graph database
- **Dual Role**:
  1. **Pre-Dispatch Compliance**: Store driver contracts, validate rules
  2. **Post-Dispatch Audit**: Log all decisions for explainability
- **File**: `database/neo4j_client.py`
- **Schema**:
  - Nodes: `Driver`, `Order`
  - Relationships: `COMPLIANCE_CHECK`, `RANKED`, `CALLED`, `ASSIGNED_TO`

---

## Data Flow

### Step-by-Step Process

1. **Order Received**
   - Webhook receives order via `POST /api/v1/orders`
   - Order validated against Pydantic schema
   - Orchestrator agent initiated

2. **GPT-4o Analysis**
   - Orchestrator sends order to GPT-4o for strategic analysis
   - Receives insights on urgency, challenges, risk factors

3. **Driver Fetch**
   - Driver Context Agent calls Yutori API
   - Retrieves all active drivers with live GPS
   - Returns list of available drivers

4. **Compliance Check**
   - For each driver, Compliance Agent queries Neo4j
   - Validates 5 compliance rules
   - Logs pass/fail + reasons to Neo4j
   - Returns only compliant drivers

5. **Route Calculation**
   - For each compliant driver, Routing Agent calls Google Maps
   - Calculates driver→pickup and pickup→dropoff ETAs
   - Filters drivers who can meet SLA time window

6. **Ranking**
   - Ranking Engine scores each eligible driver
   - Sorts by score (best first)
   - Logs ranking decisions to Neo4j

7. **Voice Dispatch**
   - Voice Dispatch Agent calls drivers in ranked order
   - First driver to accept gets the assignment
   - All call outcomes logged to Neo4j

8. **Assignment**
   - Winning driver assigned to order
   - Assignment relationship created in Neo4j
   - Driver's daily workload updated

9. **Response**
   - DispatchResult returned to client
   - Includes assigned driver, processing time, audit trail ID

---

## Database Schema (Neo4j)

### Driver Node
```cypher
(:Driver {
  driver_id: String,
  name: String,
  phone: String,
  license_number: String,
  license_expiry: DateTime,
  vehicle_type: String,
  max_km_per_day: Float,
  max_hours_per_day: Float,
  shift_start_hour: Int,
  shift_end_hour: Int,
  updated_at: DateTime
})
```

### Order Node
```cypher
(:Order {
  order_id: String,
  pickup_address: String,
  dropoff_address: String,
  vehicle_type: String,
  time_window_start: DateTime,
  time_window_end: DateTime,
  status: String,
  assigned_driver_id: String,
  created_at: DateTime,
  updated_at: DateTime
})
```

### Relationships

**COMPLIANCE_CHECK**
```cypher
(Order)-[:COMPLIANCE_CHECK {
  is_compliant: Boolean,
  reasons: [String],
  checks: String,
  timestamp: DateTime
}]->(Driver)
```

**RANKED**
```cypher
(Order)-[:RANKED {
  rank: Int,
  score: Float,
  eta_minutes: Float,
  reasoning: String,
  timestamp: DateTime
}]->(Driver)
```

**CALLED**
```cypher
(Order)-[:CALLED {
  outcome: String,
  sentiment_score: Float,
  decline_reason: String,
  call_duration_seconds: Float,
  timestamp: DateTime
}]->(Driver)
```

**ASSIGNED_TO**
```cypher
(Driver)-[:ASSIGNED_TO {
  distance_km: Float,
  duration_hours: Float,
  assigned_at: DateTime
}]->(Order)
```

---

## API Integration Points

### External APIs

1. **Yutori API**
   - Endpoint: `GET /drivers/active`
   - Purpose: Fetch active drivers with GPS
   - Auth: Bearer token

2. **Google Maps Distance Matrix API**
   - Endpoint: `GET /maps/api/distancematrix/json`
   - Purpose: Calculate real-time ETAs
   - Auth: API key

3. **Modulate Voice API**
   - Endpoint: `POST /voice/call`
   - Purpose: Make voice calls to drivers
   - Auth: Bearer token

4. **OpenAI API**
   - Model: GPT-4o
   - Purpose: Order analysis and orchestration
   - Auth: API key

---

## Error Handling

### Failure Scenarios

1. **No Active Drivers**
   - Status: `FAILED`
   - Message: "No active drivers available"

2. **No Compliant Drivers**
   - Status: `FAILED`
   - Message: "No compliant drivers found"

3. **No SLA-Compliant Routes**
   - Status: `FAILED`
   - Message: "No drivers can meet SLA time window"

4. **All Drivers Declined**
   - Status: `DECLINED`
   - Message: "All drivers declined the assignment"

5. **System Error**
   - Status: `FAILED`
   - Message: Detailed error message
   - All errors logged to Neo4j

---

## Scalability Considerations

### Current Architecture
- Synchronous processing per order
- Sequential agent execution
- Single-threaded voice dispatch

### Future Optimizations
- Parallel compliance checks
- Batch route calculations
- Concurrent voice calls (with priority queue)
- Redis caching for driver data
- Message queue (RabbitMQ/Kafka) for order intake
- Horizontal scaling with load balancer

---

## Security

### API Keys
- All API keys stored in environment variables
- Never committed to version control
- Rotated regularly

### Database
- Neo4j authentication required
- TLS encryption for production
- Role-based access control

### Logging
- No sensitive data in logs
- Structured JSON logging
- PII redaction in production

---

## Monitoring & Observability

### Metrics
- Order processing time
- Driver acceptance rate
- Compliance pass rate
- API response times
- Error rates

### Logging
- Structured JSON logs via structlog
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR

### Health Checks
- `/health` endpoint
- Database connectivity check
- API dependency checks

---

## Deployment

### Local Development
```bash
docker-compose up
```

### Production (Render)
- Automatic deployment from GitHub
- Environment variables via Render dashboard
- Neo4j Aura for managed database

---

## Testing Strategy

### Unit Tests
- Agent logic validation
- Scoring algorithm verification
- Database query testing

### Integration Tests
- End-to-end order flow
- API endpoint validation
- External API mocking

### Load Tests
- Concurrent order processing
- Database performance under load
- API rate limit handling

---

## Compliance Rules Detail

| Rule | Description | Threshold | Reason for Failure |
|------|-------------|-----------|-------------------|
| License Validity | Days until license expires | > 14 days | Safety buffer for renewal |
| Vehicle Type | Driver's vehicle matches order | Exact match | Cargo/passenger requirements |
| Daily KM Budget | Remaining km allowance today | > 20 km | Prevent driver fatigue |
| Daily Hours Budget | Remaining hours allowance today | > 1 hour | Labor law compliance |
| Shift Coverage | Delivery time within shift window | Must fit | Driver availability |

---

## Ranking Algorithm Detail

### Base Score: 100 points

### Penalties
- **ETA to Pickup**: -0.5 points per minute
- **Total Trip Time**: -0.2 points per minute

### Bonuses
- **Vehicle Match**: +20 points (exact match), -10 points (mismatch)
- **License Expiry Buffer**:
  - > 90 days: +10 points
  - > 30 days: +5 points
  - ≤ 30 days: 0 points
- **Remaining KM Budget**:
  - > 100 km: +15 points
  - > 50 km: +5 points
  - ≤ 50 km: 0 points

### Example Calculation
```
Driver A:
- ETA to pickup: 10 min → -5 points
- Total trip: 30 min → -6 points
- Vehicle match: Yes → +20 points
- License expiry: 120 days → +10 points
- Remaining km: 150 km → +15 points
Final Score: 100 - 5 - 6 + 20 + 10 + 15 = 134 points
```

---

## Future Architecture Enhancements

1. **Event-Driven Architecture**
   - Replace synchronous processing with event streams
   - Use Kafka/RabbitMQ for order intake
   - Enable real-time driver tracking

2. **Microservices**
   - Split agents into separate services
   - Independent scaling per component
   - Service mesh for communication

3. **Machine Learning**
   - Predictive ETA based on historical data
   - Driver acceptance probability modeling
   - Dynamic ranking weight optimization

4. **Real-Time Updates**
   - WebSocket connections for live tracking
   - Push notifications to drivers
   - Customer order status updates

5. **Multi-Region Support**
   - Geographic load balancing
   - Regional driver pools
   - Latency optimization

---

**Document Version**: 1.0  
**Last Updated**: February 27, 2026  
**Maintained By**: hexiao0225 & Luxin
