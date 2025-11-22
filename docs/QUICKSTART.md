# Quick Start Guide

## 🚀 Get Running in 3 Steps

### Step 1: Setup (1 minute)
```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
nano .env
```

### Step 2: Install & Run (1 minute)
```bash
# Option A: Use the start script (recommended)
chmod +x start.sh
./start.sh

# Option B: Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Step 3: Test (30 seconds)
```bash
# In a new terminal, run the demo
python demo.py

# Or test manually
curl http://localhost:8000/health
```

## 🎯 First API Call

Open your browser to http://localhost:8000/docs and try:

**Send a message:**
```json
POST /chat
{
  "message": "Hi, my name is Alice and I love pizza",
  "session_id": "test_123"
}
```

**Check what it remembers:**
```json
POST /chat
{
  "message": "What's my name and what do I like?",
  "session_id": "test_123"
}
```

**Response:**
```json
{
  "response": "Your name is Alice and you love pizza!",
  "session_id": "test_123",
  "usage": {
    "total_tokens": 150
  },
  "context_used": true,
  "memories_count": {
    "semantic": 2,
    "episodic": 2
  }
}
```

## 📚 Next Steps

1. **Read the README**: `README.md` - Complete documentation
2. **Try the demos**: `python demo.py` - 7 example scenarios
3. **Run tests**: `pytest test_agent.py -v` - Verify everything works
4. **Deploy**: See `DEPLOYMENT.md` for production setup

## 🐳 Docker Quick Start

Even faster with Docker:

```bash
# 1. Configure
cp .env.example .env
# Add your OpenAI key

# 2. Run everything
docker-compose up -d

# 3. Check it's working
curl http://localhost:8000/health

# 4. View logs
docker-compose logs -f

# 5. Stop when done
docker-compose down
```

## 🎓 Learning Path

1. **Try the basics** (5 min)
   - Start server
   - Send a chat message
   - Check memory summary

2. **Run the demo** (10 min)
   - `python demo.py`
   - See all features in action

3. **Explore the API** (10 min)
   - Visit http://localhost:8000/docs
   - Try different endpoints
   - Test memory search

4. **Read the code** (30 min)
   - Start with `agent.py`
   - See how memory works
   - Understand the flow

5. **Extend it** (1 hour)
   - Add custom extraction patterns
   - Try different LLM models
   - Implement new features

## 🔧 Common Issues

### "Cannot connect to server"
```bash
# Make sure server is running
python main.py

# Check it's listening
curl http://localhost:8000/health
```

### "OpenAI API error"
```bash
# Verify API key is set
cat .env | grep OPENAI_API_KEY

# Make sure it's exported
export $(cat .env | xargs)
```

### "Module not found"
```bash
# Install dependencies
pip install -r requirements.txt

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Redis connection failed"
```bash
# If USE_REDIS=true, start Redis:
docker run -d -p 6379:6379 redis:alpine

# Or set USE_REDIS=false in .env
```

## 📊 Features Overview

| Feature | Endpoint | Example |
|---------|----------|---------|
| Chat | `POST /chat` | Send messages |
| Memory | `GET /memory/summary` | View stored info |
| Search | `POST /memory/search` | Find memories |
| Store | `POST /memory/store` | Manual save |
| Clear | `DELETE /memory/clear` | Reset session |

## 💡 Pro Tips

1. **Use session IDs** to keep users separate
2. **Set importance** for critical memories (0.8-1.0)
3. **Search before storing** to avoid duplicates
4. **Monitor token usage** to control costs
5. **Clear old sessions** to save memory

## 🎮 Try These Examples

### Example 1: Personal Assistant
```python
import requests

# Tell it about yourself
requests.post("http://localhost:8000/chat", json={
    "message": "I prefer meeting in the mornings. My email is user@example.com",
    "session_id": "user_personal"
})

# Later, ask for scheduling help
requests.post("http://localhost:8000/chat", json={
    "message": "Schedule a meeting with John next week",
    "session_id": "user_personal"
})
# It remembers your morning preference!
```

### Example 2: Customer Support
```python
# First interaction
requests.post("http://localhost:8000/chat", json={
    "message": "I'm having trouble with order #12345",
    "session_id": "customer_789"
})

# Follow-up days later
requests.post("http://localhost:8000/chat", json={
    "message": "Any update on my order?",
    "session_id": "customer_789"
})
# It remembers the order number!
```

### Example 3: Learning Companion
```python
# Store important concepts
requests.post("http://localhost:8000/memory/store", json={
    "key": "python_basics",
    "value": "Variables, loops, functions, classes",
    "importance": 0.9,
    "session_id": "student_123"
})

# Search later
requests.post("http://localhost:8000/memory/search", json={
    "query": "python",
    "session_id": "student_123"
})
```

## 📖 Documentation Links

- **User Guide**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Summary**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **API Docs**: http://localhost:8000/docs (when running)

## 🆘 Need Help?

1. Check the troubleshooting section above
2. Review the test cases in `test_agent.py`
3. Run the demo: `python demo.py`
4. Check logs for error messages
5. Verify all environment variables are set

## ✅ Success Checklist

- [ ] Server starts without errors
- [ ] Health check returns 200
- [ ] Can send and receive messages
- [ ] Memory is persisted across requests
- [ ] Tests pass successfully
- [ ] Demo runs without errors

**If all checked, you're good to go! 🎉**

---

**Time to First Success: < 5 minutes**

Now explore the full documentation and start building!
