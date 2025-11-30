# 🎯 Smart Task Analyzer

A mini-application that intelligently scores and prioritizes tasks based on multiple factors including urgency, importance, effort, and dependencies.

## 📋 Project Overview

This project is a technical assessment demonstrating:
- **Algorithm Design**: Intelligent task scoring based on multiple weighted factors
- **Clean Code**: Well-structured, maintainable Python/Django backend
- **Critical Thinking**: Comprehensive edge case handling (circular dependencies, missing data, overdue tasks)
- **Full-Stack Skills**: Django REST API + Vanilla JavaScript frontend

## 🏗️ Project Structure

```
smart-task-analyzer/
├── backend/                    # Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── smart_analyzer/        # Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── tasks/                 # Tasks app
│       ├── scoring.py         # Core algorithm
│       ├── serializers.py     # Data validation
│       ├── views.py           # API endpoints
│       └── urls.py
├── frontend/                  # Static frontend
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── samples/                   # Sample task data
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Modern web browser

### Installation & Setup

**Step 1: Clone/Navigate to Project**
```bash
cd smart-task-analyzer
```

**Step 2: Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

**Step 3: Run Django Development Server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

**Step 4: Open Frontend**

Open `frontend/index.html` in your web browser, or serve it:
```bash
# Option 1: Direct file open
# Just double-click frontend/index.html

# Option 2: Using Python's HTTP server
cd frontend
python -m http.server 3000
# Then visit http://localhost:3000
```

## 📊 Algorithm Design

### Priority Scoring Formula

The core algorithm computes a priority score (0-100) for each task using four weighted components:

```
Score = (w_u × U) + (w_i × I) + (w_e × E) + (w_d × D)
```

Where:
- **U** = Urgency Score (0-2 scale, >1 for overdue)
- **I** = Importance Score (0-1 scale)
- **E** = Effort Score (0-1 scale, higher for quick wins)
- **D** = Dependency Score (0-1 scale, higher if many tasks blocked)

### Component Details

#### 1. **Urgency (U)**
Calculated based on days until due date:

- **Overdue tasks**: `U = 1.0 + min(days_late / 7, 1.0)` (up to 2.0)
- **Due today**: `U = 1.0`
- **Due within 3 days**: `U = 0.9 - 1.0` (linear scale)
- **Future tasks**: `U = max(0, 1 - days_left / 30)` (30-day decay)
- **No due date**: `U = 0.5` (neutral)

**Design Decision**: Overdue tasks get a bonus score (>1.0) to ensure critical visibility. The 30-day decay prevents far-future tasks from being ignored completely.

#### 2. **Importance (I)**
User-provided rating on 1-10 scale, normalized:

```python
I = (importance - 1) / 9
```

**Design Decision**: Linear normalization preserves user intent while fitting the 0-1 scale.

#### 3. **Effort (E)**
Rewards "quick wins" using logarithmic scaling:

```python
E = 1 - (log(estimated_hours + 1) / log(max_hours + 1))
```

**Design Decision**: Logarithmic scale prevents extreme bias toward micro-tasks while still rewarding efficiency. A 1-hour task scores higher than an 8-hour task, but not 8× higher.

#### 4. **Dependencies (D)**
Measures how many other tasks are blocked:

```python
D = min(1.0, num_dependents / max_dependents)
```

**Design Decision**: Tasks blocking others get priority to unblock team progress. Normalized to 0-1 based on maximum dependents in the task set.

### Strategy Presets

Four predefined weight configurations:

| Strategy | Urgency | Importance | Effort | Dependencies | Use Case |
|----------|---------|------------|--------|--------------|----------|
| **Smart Balance** | 0.35 | 0.35 | 0.15 | 0.15 | Default, balanced approach |
| **Fastest Wins** | 0.15 | 0.20 | 0.50 | 0.15 | Maximize quick completions |
| **High Impact** | 0.15 | 0.60 | 0.10 | 0.15 | Focus on important work |
| **Deadline Driven** | 0.60 | 0.25 | 0.05 | 0.10 | Urgent/time-sensitive mode |

**Design Decision**: Customizable strategies allow users to adapt prioritization to their current work context (e.g., end-of-sprint = deadline driven).

### Tie-Breaking Rules

When tasks have equal scores, secondary sorting applies:

1. **More dependents first** (unblock others)
2. **Fewer hours first** (quick wins)
3. **Earlier due date** (urgency)

## 🛡️ Edge Case Handling

### 1. **Circular Dependencies**

**Detection**: Uses Depth-First Search (DFS) with color marking to detect cycles in the dependency graph.

```python
# White (0) = unvisited
# Gray (1) = in current path (cycle if revisited)
# Black (2) = fully processed
```

**Handling**:
- Cycles are detected and reported in warnings
- Tasks in cycles are flagged with `in_circular_dependency: true`
- Dependency scoring continues (doesn't break analysis)
- Warning message shows the cycle path

**Example**: Tasks A→B→C→A would trigger: "⚠️ Circular dependency detected: A -> B -> C -> A"

### 2. **Missing/Invalid Data**

| Issue | Handling | Default Value |
|-------|----------|---------------|
| Missing `id` | Skip task, add warning | N/A (required) |
| Missing `title` | Use default, warn | `"Task {id}"` |
| Missing `due_date` | Assign neutral urgency | `U = 0.5` |
| Missing `estimated_hours` | Default to 1 hour | `1` |
| Missing `importance` | Default to medium | `5` |
| Out-of-range `importance` | Clamp to 1-10 | `max(1, min(10, value))` |
| Negative `estimated_hours` | Clamp to 0 | `max(0, value)` |
| Invalid date format | Treat as missing, warn | `U = 0.5` |

**Design Decision**: Graceful degradation allows partial analysis rather than complete failure. All issues are reported in the `warnings` array.

### 3. **Missing Dependency IDs**

**Scenario**: Task A depends on non-existent task "Z"

**Handling**:
- Warning added: "Missing dependency IDs referenced: Z"
- Dependency score for A is not penalized
- Analysis continues normally

**Design Decision**: Missing dependencies might be tasks not yet created or external dependencies, so we don't penalize tasks for referencing them.

### 4. **Overdue Tasks**

**Special Treatment**:
- Urgency score exceeds 1.0 (bonus of up to +1.0)
- Explanation includes: "⚠️ OVERDUE by X days"
- Ensures critical visibility even with low importance

**Formula**:
```python
if days_late > 0:
    U = 1.0 + min(days_late / 7, 1.0)
```

**Design Decision**: Late tasks compound in urgency weekly (1 week late = +1.0 bonus). This prevents old tasks from becoming infinitely prioritized while ensuring they stay visible.

### 5. **Zero Effort Tasks**

**Handling**:
- `estimated_hours = 0` → Effort score = 1.0 (instant task)
- Avoids division by zero in logarithmic formula
- Treated as "ultimate quick win"

### 6. **No Dependencies**

**Handling**:
- Tasks with zero dependents → Dependency score = 0
- `max_dependents = 0` for entire set → All dependency scores = 0
- Analysis continues with other factors weighted proportionally

## 🔌 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Endpoints

#### 1. **POST /tasks/analyze/**

Analyze and sort tasks by priority.

**Request Body**:
```json
{
  "strategy": "smart_balance",
  "weights": {
    "u": 0.35,
    "i": 0.35,
    "e": 0.15,
    "d": 0.15
  },
  "tasks": [
    {
      "id": "t1",
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ]
}
```

**Parameters**:
- `strategy` (optional): `"smart_balance"` | `"fastest"` | `"high_impact"` | `"deadline"`
- `weights` (optional): Custom weights (overrides strategy)
- `tasks` (required): Array of task objects

**Response** (200):
```json
{
  "analyzed": [
    {
      "id": "t1",
      "title": "Fix login bug",
      "score": 78.5,
      "priority_label": "High",
      "explanation": "Due in 2 days. High importance (8/10). Blocks 1 task",
      "in_circular_dependency": false,
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ],
  "warnings": [],
  "strategy": "smart_balance",
  "weights": {"u": 0.35, "i": 0.35, "e": 0.15, "d": 0.15}
}
```

#### 2. **POST /tasks/suggest/**

Get top 3 recommended tasks with enhanced explanations.

**Request Body**: Same as `/analyze/`

**Response** (200):
```json
{
  "suggestions": [
    {
      "rank": 1,
      "id": "t1",
      "title": "Fix login bug",
      "score": 78.5,
      "confidence": "High",
      "recommendation": "Rank #1: Due in 2 days. High importance (8/10). Blocks 1 task"
    }
  ],
  "total_tasks": 5,
  "strategy": "smart_balance",
  "warnings": []
}
```

#### 3. **GET /strategies/**

Get available strategies and their configurations.

**Response** (200):
```json
{
  "strategies": {
    "smart_balance": {"u": 0.35, "i": 0.35, "e": 0.15, "d": 0.15},
    "fastest": {"u": 0.15, "i": 0.20, "e": 0.50, "d": 0.15},
    "high_impact": {"u": 0.15, "i": 0.60, "e": 0.10, "d": 0.15},
    "deadline": {"u": 0.60, "i": 0.25, "e": 0.05, "d": 0.10}
  },
  "descriptions": {
    "smart_balance": "Balanced approach considering all factors equally",
    "fastest": "Prioritizes quick wins - tasks that take less time",
    "high_impact": "Prioritizes importance over other factors",
    "deadline": "Prioritizes urgent tasks based on due dates"
  }
}
```

## 🎨 Frontend Features

### Input Options
1. **Single Task Form**: Add tasks one at a time with validation
2. **Bulk JSON Input**: Paste JSON array for rapid testing
3. **Task Management**: View, edit, remove tasks before analysis

### Strategy Toggle
Switch between 4 sorting strategies:
- 🎯 Smart Balance (Recommended)
- ⚡ Fastest Wins
- 🎖️ High Impact
- ⏰ Deadline Driven

### Visual Output
- **Color-coded priorities**: Red (High), Orange (Medium), Green (Low)
- **Score display**: Large numeric score (0-100)
- **Explanations**: Why each task received its score
- **Warnings**: Circular dependencies, missing data, etc.
- **Top 3 Suggestions**: Dedicated section with confidence levels

### Responsive Design
- Mobile-friendly grid layout
- Adaptive forms for different screen sizes
- Touch-friendly buttons and controls

## 🧪 Testing

### Sample Data

Use the provided sample data in `samples/tasks.json`:

```json
[
  {
    "id": "t1",
    "title": "Fix critical login bug",
    "due_date": "2025-11-28",
    "estimated_hours": 3,
    "importance": 9,
    "dependencies": []
  },
  {
    "id": "t2",
    "title": "Code review",
    "due_date": "2025-12-01",
    "estimated_hours": 1,
    "importance": 6,
    "dependencies": []
  }
]
```

### Test Scenarios

1. **Normal Priority**:
   - Mix of urgency and importance
   - Expected: Balanced scoring

2. **Overdue Task**:
   - Set `due_date` to past date
   - Expected: High score with "OVERDUE" warning

3. **Circular Dependency**:
   ```json
   [
     {"id": "t1", "dependencies": ["t2"]},
     {"id": "t2", "dependencies": ["t1"]}
   ]
   ```
   - Expected: Warning with cycle path

4. **Missing Data**:
   - Omit `due_date` or `importance`
   - Expected: Defaults applied, analysis continues

5. **Quick Win**:
   - `estimated_hours: 0.5`, `importance: 5`
   - Use "Fastest Wins" strategy
   - Expected: High priority despite medium importance

### Manual API Testing

Using curl:
```bash
curl -X POST http://localhost:8000/api/tasks/analyze/ \
  -H "Content-Type: application/json" \
  -d @samples/tasks.json
```

## 🔧 Configuration

### Custom Weights

Override strategy weights via API:

```json
{
  "weights": {
    "u": 0.5,
    "i": 0.3,
    "e": 0.1,
    "d": 0.1
  },
  "tasks": [...]
}
```

**Note**: Weights don't need to sum to 1.0 (normalization happens internally), but should be between 0-1.

## 📈 Design Decisions & Trade-offs

### 1. **In-Memory Processing vs Database**
**Decision**: Process tasks in-memory (no Django models/database)

**Rationale**:
- ✅ Faster development for assessment
- ✅ Simpler deployment (no migrations)
- ✅ Stateless API (RESTful)
- ❌ No persistence (acceptable for demo)

### 2. **Logarithmic Effort Scaling**
**Decision**: Use `log(hours)` instead of linear `1/hours`

**Rationale**:
- ✅ Prevents extreme bias toward 0.1hr tasks
- ✅ More realistic "diminishing returns" for larger tasks
- ✅ Avoids division by zero naturally

**Alternative Considered**: Linear scaling (`1 - hours/max`) - too aggressive on small tasks

### 3. **Urgency Bonus for Overdue**
**Decision**: Allow urgency >1.0 (up to 2.0)

**Rationale**:
- ✅ Ensures overdue tasks remain visible
- ✅ Bounded growth prevents ancient tasks from dominating
- ❌ Could mask low-importance old tasks

**Alternative Considered**: Cap at 1.0 - overdue tasks got lost with low importance

### 4. **Circular Dependency Non-Blocking**
**Decision**: Detect and warn, but continue analysis

**Rationale**:
- ✅ User can still see prioritization
- ✅ Warnings clearly indicate the issue
- ❌ Doesn't prevent invalid dependency chains

**Alternative Considered**: Fail analysis - too restrictive for exploratory use

### 5. **Four Fixed Strategies**
**Decision**: Predefined strategy presets vs full custom weights

**Rationale**:
- ✅ Easier UX for non-technical users
- ✅ Still allows advanced users to send custom weights via API
- ✅ Clear semantic meaning (Deadline Driven vs manual `{u:0.6, ...}`)

## 🚀 Future Enhancements

If more time were available:

1. **Dependency Graph Visualization** (Bonus)
   - D3.js or vis.js network diagram
   - Visual cycle highlighting
   - Interactive task exploration

2. **Date Intelligence** (Bonus)
   - Business day calculations (skip weekends)
   - Holiday awareness
   - Work-hour normalization (8hr/day)

3. **Eisenhower Matrix** (Bonus)
   - 2D grid: Urgent (Y) vs Important (X)
   - Drag-and-drop task repositioning
   - Quadrant-based filtering

4. **Learning System** (Bonus)
   - Thumbs up/down on suggestions
   - ML model to adjust weights per user
   - Historical accuracy tracking

5. **Unit Tests** (Bonus)
   - Pytest for scoring functions
   - DRF test client for API endpoints
   - Edge case coverage (see `tests/` if implemented)

6. **Database Persistence**
   - Store user task lists
   - Historical analysis tracking
   - Multi-user support with authentication

## 🎓 Learning Outcomes

This project demonstrates:

- ✅ **Algorithm Design**: Multi-factor weighted scoring with clear justifications
- ✅ **Clean Code**: Modular functions, separation of concerns (scoring.py, serializers, views)
- ✅ **Edge Case Handling**: Comprehensive validation and graceful degradation
- ✅ **API Design**: RESTful endpoints with clear request/response contracts
- ✅ **Frontend Integration**: Vanilla JS with modern UX patterns
- ✅ **Documentation**: This README with rationale for every decision

## 📝 Commit History

The Git history follows a structured progression:

1. Initial setup (Django project, gitignore)
2. Backend core (scoring algorithm)
3. API endpoints (analyze, suggest)
4. Frontend UI (forms, results display)
5. Edge case handling (circular deps, validation)
6. Polish (README, sample data, styling)

## 👨‍💻 Author

**Technical Assessment Submission**  
Software Development Intern Position  
Duration: ~3.5 hours  
Date: November 2025

---

## 📄 License

This is an assessment project and not intended for production use.

