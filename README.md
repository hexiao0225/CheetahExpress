# Cheetah Express 🐆

**Production-Level AI-Powered Delivery Dispatch System**

Cheetah Express is an intelligent, multi-agent delivery dispatch system that automates driver assignment through real-time compliance checking, route optimization, and AI-powered voice dispatch.

<img width="544" height="503" alt="Screenshot 2026-02-27 at 3 45 21 PM" src="https://github.com/user-attachments/assets/6b466412-a883-4bf5-b32d-d3d9733c8e6d" />
<img width="526" height="505" alt="Screenshot 2026-02-27 at 3 46 05 PM" src="https://github.com/user-attachments/assets/f8e91a9f-9421-4f8c-9266-59ce9d5f2e2e" />

## Team

- hexiao0225
- Luxin

---

## 🏗️ System Architecture

```
Order Intake (Webhook)
        ↓
Orchestrator Agent (GPT-4o)
        ↓
    ┌───┴───┐
    ↓       ↓
Driver    Compliance
Context   Check Agent
Agent     (Neo4j)
(Mock Pool)   ↓
    ↓         ↓
    └────┬────┘
         ↓
    Routing Agent
    (Google Maps)
         ↓
    Ranking Engine
         ↓
    Voice Dispatch
    (Modulate)
         ↓
    Neo4j Audit Graph
```

## 🚀 Key Features

### Multi-Agent Orchestration

- **Orchestrator Agent (GPT-4o)**: Coordinates all sub-agents and analyzes order complexity
- **Driver Context Agent**: Loads local mock driver data (GPS, availability, profiles)
- **Compliance Agent**: Validates drivers against Neo4j rules (license, vehicle type, workload limits)
- **Routing Agent**: Calculates real-time ETAs via Google Maps Distance Matrix API
- **Ranking Engine**: Scores drivers based on ETA, compliance, and workload optimization
- **Voice Dispatch Agent**: Calls drivers via Modulate AI with sentiment analysis

### Neo4j Dual-Role System

1. **Pre-Dispatch Compliance Gate**: Blocks non-compliant drivers before routing
2. **Post-Dispatch Audit Trail**: Full decision graph for explainability

### Production-Ready Features

- ✅ RESTful API with FastAPI
- ✅ Async order processing
- ✅ Comprehensive audit logging
- ✅ Health checks and monitoring
- ✅ Structured logging with structlog
- ✅ Full test coverage
- ✅ Render deployment configuration

---

## 📋 Prerequisites

- Python 3.11+
- Neo4j 5.x (local or cloud instance)
- API Keys:
  - OpenAI (GPT-4o)
  - Google Maps API
  - Modulate Voice API

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/hexiao0225/CheetahExpress.git
cd CheetahExpress
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
MODULATE_API_KEY=your-modulate-api-key
MODULATE_BASE_URL=https://api.modulate.ai/v1
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
PORT=8000
LOG_LEVEL=INFO
```

### 5. Start Neo4j Database

```bash
# Using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5.16.0

# Or use Neo4j Desktop / Aura
```

### 6. Seed Sample Drivers

```bash
# Start the server first
python main.py

# In another terminal, seed drivers
curl -X POST http://localhost:8000/api/v1/drivers/seed
```

---

## 🚀 Running the Application

### Development Mode

```bash
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Health & Status

- `GET /` - Service information
- `GET /health` - Health check with database connectivity

### Order Management

- `POST /api/v1/orders` - Create order (synchronous)
- `POST /api/v1/orders/async` - Create order (background processing)
- `GET /api/v1/orders/{order_id}` - Get order status
- `GET /api/v1/orders/{order_id}/audit` - Get full audit trail

### Driver Management

- `POST /api/v1/drivers/seed` - Seed sample drivers

---

## 📝 Example Usage

### Create a Delivery Order

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD12345",
    "pickup": {
      "address": "123 Main St, San Francisco, CA",
      "latitude": 37.7749,
      "longitude": -122.4194
    },
    "dropoff": {
      "address": "456 Market St, San Francisco, CA",
      "latitude": 37.7849,
      "longitude": -122.4094
    },
    "time_window": {
      "start": "2026-02-27T14:00:00",
      "end": "2026-02-27T16:00:00"
    },
    "vehicle_type": "sedan",
    "customer_info": {
      "name": "John Doe",
      "phone": "+1-555-1234",
      "email": "john@example.com"
    },
    "special_instructions": "Handle with care",
    "priority": 8
  }'
```

### Get Audit Trail

```bash
curl http://localhost:8000/api/v1/orders/ORD12345/audit
```

Response includes:

- All compliance checks per driver
- Ranking decisions with scores
- Voice call outcomes with sentiment
- Assignment details

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

## 🌐 Deployment (Render)

### Automatic Deployment

1. Push to GitHub
2. Connect repository to Render
3. Render will use `render.yaml` for configuration
4. Set environment variables in Render dashboard
5. Deploy!

### Manual Deployment

```bash
# Render will automatically run:
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 🏛️ Neo4j Graph Schema

### Nodes

- `Driver`: Driver profiles with license, vehicle, shift data
- `Order`: Delivery orders with pickup/dropoff details

### Relationships

- `COMPLIANCE_CHECK`: Order → Driver (compliance validation results)
- `RANKED`: Order → Driver (ranking score and reasoning)
- `CALLED`: Order → Driver (voice call outcome + sentiment)
- `ASSIGNED_TO`: Driver → Order (final assignment)

### Example Cypher Queries

**View all compliance checks for an order:**

```cypher
MATCH (o:Order {order_id: 'ORD12345'})-[r:COMPLIANCE_CHECK]->(d:Driver)
RETURN d.name, r.is_compliant, r.reasons
```

**View ranking decisions:**

```cypher
MATCH (o:Order {order_id: 'ORD12345'})-[r:RANKED]->(d:Driver)
RETURN d.name, r.rank, r.score, r.reasoning
ORDER BY r.rank
```

**Full audit trail:**

```cypher
MATCH (o:Order {order_id: 'ORD12345'})
OPTIONAL MATCH (o)-[cc:COMPLIANCE_CHECK]->(d1:Driver)
OPTIONAL MATCH (o)-[r:RANKED]->(d2:Driver)
OPTIONAL MATCH (o)-[c:CALLED]->(d3:Driver)
OPTIONAL MATCH (d4:Driver)-[a:ASSIGNED_TO]->(o)
RETURN o, cc, r, c, a, d1, d2, d3, d4
```

---

## 🔍 System Flow

1. **Order Intake**: Webhook receives delivery order
2. **GPT-4o Analysis**: Orchestrator analyzes order complexity
3. **Driver Fetch**: Local mock pool returns active drivers with SF GPS
4. **Compliance Check**: Neo4j validates each driver against rules:
   - License valid (>14 days until expiry)
   - Vehicle type matches order
   - Daily km/hour budget available
   - Shift window covers delivery time
5. **Routing**: Google Maps calculates ETA for compliant drivers
6. **Ranking**: Score drivers by ETA, vehicle match, license buffer, workload
7. **Voice Dispatch**: Modulate calls drivers in ranked order
8. **Assignment**: First driver to accept gets the order
9. **Audit Logging**: All decisions written to Neo4j graph

---

## 📊 Monitoring & Observability

- **Structured Logging**: JSON logs with correlation IDs
- **Health Checks**: `/health` endpoint for uptime monitoring
- **Audit Trail**: Full decision graph in Neo4j
- **Sentiment Analysis**: Voice call emotional metadata

---

## 🛡️ Compliance Rules

| Rule               | Check                      | Threshold   |
| ------------------ | -------------------------- | ----------- |
| License Validity   | Days until expiry          | > 14 days   |
| Vehicle Type       | Matches order requirement  | Exact match |
| Daily KM Budget    | Remaining km today         | > 20 km     |
| Daily Hours Budget | Remaining hours today      | > 1 hour    |
| Shift Coverage     | Delivery time within shift | Must fit    |

---

## 🎯 Ranking Algorithm

```
Score = 100
  - (ETA to pickup × 0.5)
  - (Total trip time × 0.2)
  + (Vehicle match ? 20 : -10)
  + (License expiry buffer bonus: 0-10)
  + (Remaining km budget bonus: 0-15)
```

---

## 🔧 Technology Stack

| Component      | Technology            |
| -------------- | --------------------- |
| Backend        | FastAPI (Python 3.11) |
| Orchestration  | OpenAI GPT-4o         |
| Database       | Neo4j 5.x             |
| Driver Data    | Local mock pool       |
| Routing        | Google Maps API       |
| Voice Dispatch | Modulate AI           |
| Logging        | structlog             |
| Testing        | pytest                |
| Deployment     | Render                |

---

## 📈 Future Enhancements

- [ ] Real-time driver tracking dashboard
- [ ] Predictive ETA adjustments based on traffic
- [ ] Multi-order batching optimization
- [ ] Driver performance analytics
- [ ] Customer notification system
- [ ] Mobile app for drivers
- [ ] Machine learning for ranking optimization

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📞 Support

For issues or questions, please open a GitHub issue or contact the team.

**Built with ❤️ by hexiao0225 & Luxin**
