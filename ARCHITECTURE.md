# 🏗️ Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER (User)                           │
│                      frontend/index.html                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTP Requests (JSON)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO REST API                               │
│                  http://localhost:8000                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Endpoints (tasks/views.py)                           │  │
│  │  • POST /api/tasks/analyze/   - Analyze & sort tasks     │  │
│  │  • POST /api/tasks/suggest/   - Get top 3 tasks          │  │
│  │  • GET  /api/strategies/      - Get strategy configs     │  │
│  └──────────────┬────────────────────────────────────────────┘  │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Validation (tasks/serializers.py)                   │  │
│  │  • TaskSerializer         - Validate individual tasks     │  │
│  │  • AnalyzeRequestSerializer - Validate full request       │  │
│  └──────────────┬────────────────────────────────────────────┘  │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Algorithm (tasks/scoring.py)                        │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  1. Detect Circular Dependencies (DFS)             │  │  │
│  │  │  2. Build Dependency Map                           │  │  │
│  │  │  3. Calculate Component Scores:                    │  │  │
│  │  │     • Urgency (due date)                           │  │  │
│  │  │     • Importance (user rating)                     │  │  │
│  │  │     • Effort (estimated hours)                     │  │  │
│  │  │     • Dependencies (blocking tasks)                │  │  │
│  │  │  4. Apply Strategy Weights                         │  │  │
│  │  │  5. Sort & Rank Tasks                              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────┬────────────────────────────────────────────┘  │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  JSON Response                                            │  │
│  │  {                                                        │  │
│  │    "analyzed": [...],  // Sorted tasks with scores       │  │
│  │    "warnings": [...],  // Edge case warnings             │  │
│  │    "strategy": "...",  // Used strategy                  │  │
│  │    "weights": {...}    // Applied weights                │  │
│  │  }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                 │
                 │ JSON Response
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               FRONTEND (frontend/app.js)                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  UI Components                                            │  │
│  │  • Task Input Form                                        │  │
│  │  • Bulk JSON Loader                                       │  │
│  │  • Task List Manager                                      │  │
│  │  • Strategy Selector                                      │  │
│  │  • Results Display (color-coded cards)                    │  │
│  │  • Top 3 Suggestions                                      │  │
│  │  • Warnings Display                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Task Input Flow
```
User Input (Form/JSON)
    ↓
Validate on frontend (basic checks)
    ↓
Store in local array (tasks[])
    ↓
Display in task list
```

### 2. Analysis Flow
```
User clicks "Analyze Tasks"
    ↓
Frontend: POST /api/tasks/analyze/
    {
      "strategy": "smart_balance",
      "tasks": [...]
    }
    ↓
Backend: Validate request (serializers.py)
    ↓
Backend: Run scoring algorithm (scoring.py)
    • Detect cycles
    • Build dependency map
    • Calculate scores
    • Sort tasks
    ↓
Backend: Return JSON response
    {
      "analyzed": [
        {
          "id": "t1",
          "score": 78.5,
          "priority_label": "High",
          "explanation": "...",
          ...
        }
      ],
      "warnings": [...]
    }
    ↓
Frontend: Display results
    • Create result cards
    • Apply color coding
    • Show warnings
```

## Algorithm Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    analyze_tasks()                           │
│                   (Main Entry Point)                         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Validate & Clean Tasks                              │
│  • Check required fields (id, title)                         │
│  • Set defaults (importance=5, hours=1)                      │
│  • Clamp values to valid ranges                              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Detect Circular Dependencies                        │
│  • Build dependency graph                                    │
│  • Run DFS with color marking                                │
│  • Collect cycles and affected tasks                         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Build Dependency Map                                │
│  • Count how many tasks depend on each task                  │
│  • Find max_dependents                                       │
│  • Identify missing dependency IDs                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Score Each Task                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  For each task:                                         │ │
│  │                                                         │ │
│  │  Calculate U (urgency):                                │ │
│  │    if overdue: U = 1.0 + min(late_days/7, 1.0)        │ │
│  │    else: U = max(0, 1 - days_left/30)                 │ │
│  │                                                         │ │
│  │  Calculate I (importance):                             │ │
│  │    I = (importance - 1) / 9                            │ │
│  │                                                         │ │
│  │  Calculate E (effort):                                 │ │
│  │    E = 1 - log(hours+1) / log(max_hours+1)            │ │
│  │                                                         │ │
│  │  Calculate D (dependencies):                           │ │
│  │    D = num_dependents / max_dependents                 │ │
│  │                                                         │ │
│  │  Final Score:                                          │ │
│  │    score = (w_u*U + w_i*I + w_e*E + w_d*D) * 100      │ │
│  │                                                         │ │
│  │  Determine Priority Label:                             │ │
│  │    >= 75: High                                         │ │
│  │    >= 50: Medium                                       │ │
│  │    <  50: Low                                          │ │
│  │                                                         │ │
│  │  Build Explanation String                              │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Sort Tasks                                          │
│  Primary: Score (descending)                                 │
│  Secondary: Dependency count (descending)                    │
│  Tertiary: Effort hours (ascending)                          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Return Result                                       │
│  • Sorted task array                                         │
│  • Warnings array                                            │
│  • Strategy & weights used                                   │
└─────────────────────────────────────────────────────────────┘
```

## Strategy Weight Matrix

```
┌─────────────────┬─────────┬────────────┬────────┬──────────────┐
│   Strategy      │ Urgency │ Importance │ Effort │ Dependencies │
├─────────────────┼─────────┼────────────┼────────┼──────────────┤
│ Smart Balance   │  0.35   │    0.35    │  0.15  │     0.15     │
│ (Recommended)   │  ███    │    ███     │  █     │     █        │
├─────────────────┼─────────┼────────────┼────────┼──────────────┤
│ Fastest Wins    │  0.15   │    0.20    │  0.50  │     0.15     │
│ (Quick Tasks)   │  █      │    ██      │  █████ │     █        │
├─────────────────┼─────────┼────────────┼────────┼──────────────┤
│ High Impact     │  0.15   │    0.60    │  0.10  │     0.15     │
│ (Important)     │  █      │    ██████  │  █     │     █        │
├─────────────────┼─────────┼────────────┼────────┼──────────────┤
│ Deadline Driven │  0.60   │    0.25    │  0.05  │     0.10     │
│ (Urgent)        │  ██████ │    ██      │  ▓     │     █        │
└─────────────────┴─────────┴────────────┴────────┴──────────────┘
```

## File Dependencies

```
frontend/index.html
    ├── imports: frontend/styles.css
    └── imports: frontend/app.js
            │
            └── calls API: http://localhost:8000/api/

backend/manage.py
    └── loads: smart_analyzer.settings
            │
            └── includes: tasks (app)
                    │
                    ├── tasks/views.py
                    │      ├── uses: tasks/serializers.py
                    │      └── uses: tasks/scoring.py (core algorithm)
                    │
                    └── tasks/urls.py
                           └── routes to: tasks/views.py
```

## Technology Stack

### Backend
```
Python 3.8+
    ├── Django 4.2+ (Web framework)
    ├── Django REST Framework 3.14+ (API framework)
    ├── django-cors-headers 4.3+ (CORS handling)
    └── python-dateutil 2.8+ (Date parsing)
```

### Frontend
```
HTML5
CSS3 (with CSS Grid & Flexbox)
Vanilla JavaScript (ES6+)
    └── Fetch API for HTTP requests
```

### Development Tools
```
Git (Version control)
pip (Python package manager)
venv (Virtual environment)
```

## Key Design Patterns

### 1. **Separation of Concerns**
- `scoring.py` → Pure algorithm logic (no Django dependencies)
- `serializers.py` → Data validation
- `views.py` → Request/response handling (thin layer)

### 2. **Strategy Pattern**
- Multiple scoring strategies encapsulated in `STRATEGIES` dict
- Easy to add new strategies without changing algorithm code

### 3. **Single Responsibility Principle**
- Each function does ONE thing:
  - `calculate_urgency_score()` → only urgency
  - `detect_circular_dependencies()` → only cycle detection
  - `analyze_tasks()` → orchestrates, doesn't compute

### 4. **Fail-Safe Defaults**
- Missing data → use sensible defaults
- Invalid data → clamp to valid ranges
- All issues reported in `warnings` array

### 5. **Stateless API**
- No server-side task storage
- Each request is independent
- Easy to scale horizontally

## Performance Considerations

### Time Complexity
- **Validation**: O(n) - linear scan of tasks
- **Cycle Detection**: O(V + E) - DFS on dependency graph
- **Dependency Map**: O(n × d) - n tasks, d dependencies per task
- **Scoring**: O(n) - score each task once
- **Sorting**: O(n log n) - Python's Timsort
- **Overall**: O(n log n + V + E) - dominated by sorting and cycle detection

### Space Complexity
- **Task Storage**: O(n) - input tasks
- **Dependency Graph**: O(V + E) - adjacency list
- **Results**: O(n) - scored tasks
- **Overall**: O(n + V + E) - linear in input size

### Optimizations
- Single-pass validation
- In-place sorting where possible
- Lazy evaluation of explanations
- No unnecessary data copying

## Security Considerations

### Current Implementation (Development)
- `DEBUG = True` → **MUST CHANGE FOR PRODUCTION**
- `CORS_ALLOW_ALL_ORIGINS = True` → **MUST RESTRICT FOR PRODUCTION**
- No authentication → Fine for assessment, add for production
- No rate limiting → Add for production

### Production Recommendations
```python
# settings.py (for production)
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']
# Add authentication (JWT, OAuth, etc.)
# Add rate limiting (django-ratelimit)
# Add input sanitization (already partially handled)
```

## Testing Strategy

### Unit Tests (Recommended to Add)
```python
# tests/test_scoring.py
def test_urgency_overdue():
    score, meta = calculate_urgency_score("2025-11-01", datetime(2025, 11, 30))
    assert score > 1.0
    assert meta['status'] == 'overdue'

def test_circular_dependency_detection():
    tasks = [
        {"id": "t1", "dependencies": ["t2"]},
        {"id": "t2", "dependencies": ["t1"]}
    ]
    cycles, _ = detect_circular_dependencies(tasks)
    assert len(cycles) > 0
```

### Integration Tests
```python
# tests/test_api.py (using DRF test client)
def test_analyze_endpoint():
    response = client.post('/api/tasks/analyze/', data={...})
    assert response.status_code == 200
    assert 'analyzed' in response.json()
```

## Deployment Options

### Local Development
```
Current setup - works out of the box
```

### Production Deployment

**Option 1: Traditional Server (VPS)**
```
- Gunicorn (WSGI server)
- Nginx (reverse proxy)
- PostgreSQL (if adding database)
- Supervisor (process management)
```

**Option 2: Platform-as-a-Service**
```
- Heroku (easy Django deployment)
- PythonAnywhere
- Railway.app
```

**Option 3: Containerized**
```
- Docker + Docker Compose
- Kubernetes (for scale)
```

**Option 4: Serverless**
```
- AWS Lambda + API Gateway
- Google Cloud Run
- Vercel (frontend) + AWS Lambda (backend)
```

## Extension Points

### Easy to Add
- New strategy presets (just add to `STRATEGIES` dict)
- New validation rules (add to serializers)
- New API endpoints (add to `urls.py` and `views.py`)

### Medium Effort
- Database persistence (add Django models)
- User accounts (Django authentication)
- Task history tracking
- Email notifications for overdue tasks

### Advanced Features
- Machine learning weight optimization
- Collaborative task lists
- Real-time updates (WebSockets)
- Mobile app (React Native + same API)

---

**This architecture is designed for:**
- ✅ Easy understanding (clear separation)
- ✅ Easy testing (pure functions)
- ✅ Easy extension (well-defined interfaces)
- ✅ Production-ready with minimal changes

