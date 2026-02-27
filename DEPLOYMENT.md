# Cheetah Express Deployment Guide

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Docker Desktop (for Neo4j)
- API Keys (OpenAI, Yutori, Google Maps, Modulate)

### Step 1: Clone and Setup
```bash
git clone https://github.com/hexiao0225/CheetahExpress.git
cd CheetahExpress
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Step 3: Start Neo4j
```bash
docker run -d \
  --name cheetah-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/cheetahexpress \
  neo4j:5.16.0
```

### Step 4: Seed Drivers
```bash
python scripts/seed_drivers.py
```

### Step 5: Run Application
```bash
python main.py
```

Visit: http://localhost:8000/docs

---

## Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

This starts:
- Neo4j on ports 7474 (HTTP) and 7687 (Bolt)
- Cheetah Express API on port 8000

### Stop Services
```bash
docker-compose down
```

---

## Production Deployment (Render)

### Prerequisites
- GitHub account
- Render account (free tier available)
- Neo4j Aura account (free tier available)

### Step 1: Setup Neo4j Aura
1. Go to https://neo4j.com/cloud/aura/
2. Create free instance
3. Save connection URI and password
4. Example URI: `neo4j+s://xxxxx.databases.neo4j.io`

### Step 2: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/hexiao0225/CheetahExpress.git
git push -u origin main
```

### Step 3: Deploy to Render
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render auto-detects `render.yaml`
5. Set environment variables:
   - `OPENAI_API_KEY`
   - `YUTORI_API_KEY`
   - `GOOGLE_MAPS_API_KEY`
   - `MODULATE_API_KEY`
   - `NEO4J_URI` (from Aura)
   - `NEO4J_USER` (usually `neo4j`)
   - `NEO4J_PASSWORD` (from Aura)
6. Click "Create Web Service"

### Step 4: Seed Production Database
```bash
# Get your Render URL (e.g., https://cheetah-express.onrender.com)
curl -X POST https://your-app.onrender.com/api/v1/drivers/seed
```

### Step 5: Test Production
```bash
curl https://your-app.onrender.com/health
```

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT-4o | `sk-...` |
| `YUTORI_API_KEY` | Yes | Yutori API key for driver data | `yut_...` |
| `YUTORI_BASE_URL` | No | Yutori API base URL | `https://api.yutori.com/v1` |
| `GOOGLE_MAPS_API_KEY` | Yes | Google Maps API key | `AIza...` |
| `MODULATE_API_KEY` | Yes | Modulate Voice API key | `mod_...` |
| `MODULATE_BASE_URL` | No | Modulate API base URL | `https://api.modulate.ai/v1` |
| `NEO4J_URI` | Yes | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Yes | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Yes | Neo4j password | `your-password` |
| `PORT` | No | Server port | `8000` |
| `LOG_LEVEL` | No | Logging level | `INFO` |

---

## Health Checks

### Local
```bash
curl http://localhost:8000/health
```

### Production
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "operational"
}
```

---

## Monitoring

### Logs (Render)
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab
4. View real-time structured JSON logs

### Neo4j Monitoring
```cypher
// View all orders
MATCH (o:Order) RETURN o ORDER BY o.created_at DESC LIMIT 10

// View driver workload
MATCH (d:Driver)-[a:ASSIGNED_TO]->(o:Order)
WHERE date(o.created_at) = date()
RETURN d.name, count(a) as orders_today, sum(a.distance_km) as km_today

// View compliance failures
MATCH (o:Order)-[cc:COMPLIANCE_CHECK]->(d:Driver)
WHERE cc.is_compliant = false
RETURN o.order_id, d.name, cc.reasons
```

---

## Troubleshooting

### Issue: "Failed to connect to Neo4j"
**Solution**: 
- Check Neo4j is running: `docker ps`
- Verify `NEO4J_URI` in `.env`
- Test connection: `neo4j://localhost:7687`

### Issue: "OpenAI API error"
**Solution**:
- Verify `OPENAI_API_KEY` is valid
- Check API quota/billing
- Ensure GPT-4o access enabled

### Issue: "No active drivers available"
**Solution**:
- Run seed script: `python scripts/seed_drivers.py`
- Or call: `POST /api/v1/drivers/seed`

### Issue: "Google Maps API error"
**Solution**:
- Enable Distance Matrix API in Google Cloud Console
- Check API key restrictions
- Verify billing enabled

### Issue: Render deployment fails
**Solution**:
- Check build logs in Render dashboard
- Verify `requirements.txt` is complete
- Ensure Python version matches `runtime.txt`

---

## Scaling Considerations

### Vertical Scaling (Render)
- Upgrade to paid plan for more resources
- Increase worker count in `Procfile`

### Horizontal Scaling
- Use Render's auto-scaling
- Add Redis for caching driver data
- Implement rate limiting

### Database Optimization
- Add indexes on frequently queried fields
- Use Neo4j Enterprise for clustering
- Implement connection pooling

---

## Security Checklist

- [ ] All API keys in environment variables (not code)
- [ ] `.env` file in `.gitignore`
- [ ] Neo4j authentication enabled
- [ ] HTTPS enabled (automatic on Render)
- [ ] CORS configured for production domains
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Structured logging (no PII)

---

## Backup & Recovery

### Neo4j Backup (Local)
```bash
docker exec cheetah-neo4j neo4j-admin database dump neo4j --to-path=/backups
```

### Neo4j Backup (Aura)
- Automatic daily backups
- Point-in-time recovery available
- Export via Neo4j Browser

### Application State
- All state in Neo4j (stateless API)
- Easy to redeploy from scratch
- Seed drivers as needed

---

## Performance Benchmarks

### Expected Latencies
- Order intake: < 100ms
- Compliance check: < 500ms per driver
- Route calculation: < 1s per driver
- Voice dispatch: 10-30s per driver
- Total order processing: 30-120s (depends on driver count)

### Optimization Tips
- Cache driver data (Redis)
- Parallel compliance checks
- Batch route calculations
- Async voice dispatch

---

## API Rate Limits

### External APIs
- **OpenAI**: 3,500 RPM (tier 1)
- **Google Maps**: 1,000 requests/day (free tier)
- **Yutori**: Check your plan
- **Modulate**: Check your plan

### Mitigation
- Implement request queuing
- Add retry logic with exponential backoff
- Cache responses where appropriate

---

## Cost Estimation (Monthly)

### Free Tier
- Render: Free (with limitations)
- Neo4j Aura: Free (up to 50k nodes)
- OpenAI: Pay-per-use (~$0.01/order)
- Google Maps: Free (1,000 requests/day)

### Production Tier
- Render: $7-25/month
- Neo4j Aura: $65+/month
- OpenAI: ~$100/month (1000 orders)
- Google Maps: $5-20/month

---

## Support & Maintenance

### Regular Tasks
- Monitor error logs daily
- Review audit trails weekly
- Update dependencies monthly
- Rotate API keys quarterly

### Alerts
- Set up Render alerts for downtime
- Monitor Neo4j disk usage
- Track API quota usage
- Watch for compliance failures

---

**Deployment Guide Version**: 1.0  
**Last Updated**: February 27, 2026  
**Maintained By**: hexiao0225 & Luxin
