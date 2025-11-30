# 🚀 Quick Start Guide

## Step-by-Step Instructions to Run the Project

### ✅ Step 1: Verify You're in the Right Directory
```bash
# You should see these folders:
# - backend/
# - frontend/
# - samples/
ls
```

### ✅ Step 2: Set Up Python Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### ✅ Step 3: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

Expected output:
```
Successfully installed Django-4.2.x djangorestframework-3.14.x django-cors-headers-4.3.x
```

### ✅ Step 4: Start Django Server
```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

**Leave this terminal running!** Open a new terminal for the next steps.

### ✅ Step 5: Open the Frontend

**Option A: Direct File Open (Easiest)**
- Navigate to the `frontend/` folder
- Double-click `index.html`
- It should open in your default browser

**Option B: Using Python HTTP Server (Better CORS handling)**
```bash
# In a new terminal
cd frontend
python -m http.server 3000
```
Then visit: http://localhost:3000

### ✅ Step 6: Test the Application

1. **Add Sample Tasks**:
   - Copy the content from `samples/tasks.json`
   - Paste it into the "Bulk JSON Input" textarea
   - Click "Load JSON Tasks"
   - You should see 8 tasks appear

2. **Analyze Tasks**:
   - Select a strategy (try "Smart Balance" first)
   - Click "Analyze Tasks"
   - Scroll down to see results with scores and priorities

3. **Get Suggestions**:
   - Click "Get Top 3 Suggestions"
   - See the recommended tasks to work on

4. **Try Different Strategies**:
   - Switch to "Fastest Wins" → See low-effort tasks rise
   - Switch to "Deadline Driven" → See urgent tasks prioritized
   - Switch to "High Impact" → See important tasks on top

### ✅ Step 7: Test Edge Cases

**Test Circular Dependencies**:
- Load `samples/circular_dependency_example.json`
- Analyze → Should see warning about cycle

**Test Overdue Tasks**:
- Load `samples/overdue_example.json`
- Analyze → Should see OVERDUE badges and high scores

## 🔧 Troubleshooting

### Issue: "Module not found" error
**Solution**: Make sure you installed requirements:
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Port already in use"
**Solution**: Use a different port:
```bash
python manage.py runserver 8080
```
Then update `API_BASE_URL` in `frontend/app.js` to `http://localhost:8080/api`

### Issue: API requests fail (CORS error)
**Solution**: 
1. Make sure Django server is running
2. Check that `django-cors-headers` is installed
3. Verify `CORS_ALLOW_ALL_ORIGINS = True` in `backend/smart_analyzer/settings.py`

### Issue: Frontend doesn't load tasks
**Solution**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify API URL in `frontend/app.js` matches your Django server

## 📝 API Testing with curl

Test the API directly:

```bash
curl -X POST http://localhost:8000/api/tasks/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "smart_balance",
    "tasks": [
      {
        "id": "t1",
        "title": "Test task",
        "due_date": "2025-12-05",
        "estimated_hours": 2,
        "importance": 7,
        "dependencies": []
      }
    ]
  }'
```

Expected response: JSON with analyzed tasks and scores.

## 🎯 What to Check

- ✅ Django server running on http://localhost:8000
- ✅ Frontend accessible (via file:// or http://localhost:3000)
- ✅ Can add tasks via form
- ✅ Can load JSON tasks
- ✅ Analyze button works and shows results
- ✅ Different strategies change task order
- ✅ Warnings appear for circular dependencies
- ✅ Overdue tasks show with special badges

## 📚 Next Steps

Once everything works:
1. Read the algorithm documentation in `README.md`
2. Explore the code in `backend/tasks/scoring.py`
3. Try creating your own task scenarios
4. Experiment with custom weight configurations

---

**Need Help?** Check the main README.md for detailed documentation.

