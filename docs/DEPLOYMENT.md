# Deployment & Operations Guide

## Quick Start (Development)

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run server
python main.py
```

Visit: http://localhost:8000/docs

### 2. Test
```bash
# Run tests
pytest test_agent.py -v

# Run demo
python demo.py
```

## Docker Deployment

### Single Container
```bash
# Build
docker build -t llm-memory-agent .

# Run
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  llm-memory-agent
```

### With Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Deployment

### Prerequisites
- Python 3.11+
- Redis (for persistence)
- LLM API key (OpenAI or Anthropic)
- SSL certificate (for HTTPS)

### Using Systemd (Linux)

1. Create service file: `/etc/systemd/system/llm-agent.service`
```ini
[Unit]
Description=LLM Memory Agent
After=network.target redis.service

[Service]
Type=simple
User=agent
WorkingDirectory=/opt/llm-agent
Environment="PATH=/opt/llm-agent/venv/bin"
EnvironmentFile=/opt/llm-agent/.env
ExecStart=/opt/llm-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable llm-agent
sudo systemctl start llm-agent
sudo systemctl status llm-agent
```

### Using Gunicorn (Production WSGI)

```bash
# Install gunicorn
pip install gunicorn

# Run with workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name agent.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name agent.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/agent.crt;
    ssl_certificate_key /etc/ssl/private/agent.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Kubernetes Deployment

### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-memory-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-memory-agent
  template:
    metadata:
      labels:
        app: llm-memory-agent
    spec:
      containers:
      - name: agent
        image: llm-memory-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: openai-api-key
        - name: USE_REDIS
          value: "true"
        - name: REDIS_HOST
          value: redis-service
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llm-memory-agent-service
spec:
  selector:
    app: llm-memory-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-memory-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-memory-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```

## Monitoring & Observability

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Session count
curl http://localhost:8000/sessions
```

### Prometheus Metrics (Future Enhancement)

Add to `main.py`:
```python
from prometheus_client import Counter, Histogram, make_asgi_app

request_count = Counter('agent_requests_total', 'Total requests')
request_duration = Histogram('agent_request_duration_seconds', 'Request duration')

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Logging

Configure structured logging:
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        return json.dumps(log_obj)
```

### Alerting

Key metrics to monitor:
- Response time (p95, p99)
- Error rate
- Token usage
- Memory usage per session
- Active sessions

## Performance Tuning

### Worker Configuration
```bash
# CPU-bound: workers = (2 x CPU cores) + 1
# For 4 cores:
uvicorn main:app --workers 9

# Memory-bound: Reduce workers
uvicorn main:app --workers 4
```

### Redis Optimization
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Connection Pooling
```python
# For high traffic
import redis.asyncio as redis

redis_pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    max_connections=50
)
```

## Security Hardening

### API Key Authentication
```env
# .env
API_KEYS=["key1_prod_xyz", "key2_prod_abc"]
```

Usage:
```bash
curl -H "X-API-Key: key1_prod_xyz" \
  http://localhost:8000/chat \
  -d '{"message": "Hello"}'
```

### Rate Limiting

Add middleware:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, ...):
    ...
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

## Backup & Recovery

### Redis Backup
```bash
# Manual backup
redis-cli BGSAVE

# Automated backup (cron)
0 2 * * * redis-cli BGSAVE && \
  cp /var/lib/redis/dump.rdb /backups/redis-$(date +\%Y\%m\%d).rdb
```

### Session Export
```python
# Export all sessions
sessions = await memory_store.list_sessions()
for session_id in sessions:
    snapshot = await memory_store.load(session_id)
    with open(f"backup_{session_id}.json", "w") as f:
        f.write(snapshot.model_dump_json())
```

## Troubleshooting

### High Memory Usage
```bash
# Check per-session memory
curl http://localhost:8000/memory/summary?session_id=X

# Clear old sessions
curl -X DELETE http://localhost:8000/sessions/old_session_id
```

### Slow Response Times
- Check token limits (LLM_MAX_TOKENS)
- Reduce conversation history (MAX_CONVERSATION_HISTORY)
- Enable Redis caching
- Add more workers

### Redis Connection Issues
```bash
# Test Redis
redis-cli ping

# Check connections
redis-cli INFO clients

# Restart Redis
docker-compose restart redis
```

### LLM API Errors
- Verify API key is valid
- Check rate limits
- Monitor token usage
- Implement retry logic

## Cost Optimization

### Token Usage Reduction
1. Limit conversation history to 5-10 messages
2. Reduce LLM_MAX_TOKENS
3. Use cheaper models for simple queries
4. Cache frequent responses

### Monitoring Costs
```python
# Track token usage
total_tokens = sum(msg.tokens_used for msg in conversation.messages)
cost = total_tokens * 0.00001  # Adjust per model

# Log to monitoring system
logger.info(f"Session cost: ${cost:.4f}")
```

## Scaling Guidelines

### Vertical Scaling
- 2 GB RAM per worker
- 1 CPU core per 2 workers
- Redis: 4 GB RAM for 10K sessions

### Horizontal Scaling
- Use Redis for shared state
- Deploy multiple instances
- Add load balancer
- Session affinity not required

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f load_test.py --host=http://localhost:8000
```

## Maintenance

### Regular Tasks
- [ ] Weekly: Review error logs
- [ ] Weekly: Check memory usage trends
- [ ] Monthly: Update dependencies
- [ ] Monthly: Review and clean old sessions
- [ ] Quarterly: Security audit
- [ ] Quarterly: Performance review

### Update Procedure
```bash
# 1. Backup
docker-compose exec redis redis-cli BGSAVE

# 2. Pull updates
git pull

# 3. Test
pytest test_agent.py

# 4. Deploy
docker-compose up -d --build

# 5. Verify
curl http://localhost:8000/health
```

## Support

For production issues:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl /health`
3. Check Redis: `redis-cli ping`
4. Review metrics: `curl /metrics`

## Checklist: Production Ready

- [ ] Environment variables configured
- [ ] Redis configured and running
- [ ] SSL certificates installed
- [ ] API authentication enabled
- [ ] Rate limiting configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Health checks passing
- [ ] Load tested
- [ ] Documentation reviewed
