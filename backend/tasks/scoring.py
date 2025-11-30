"""
Priority Scoring Algorithm for Task Analyzer

This module implements the core scoring logic that evaluates tasks based on:
- Urgency (due date)
- Importance (user rating)
- Effort (estimated hours)
- Dependencies (tasks blocking others)
"""

from datetime import datetime, date
from typing import List, Dict, Any, Tuple
import math


# Predefined strategy weights
STRATEGIES = {
    'smart_balance': {'u': 0.35, 'i': 0.35, 'e': 0.15, 'd': 0.15},
    'fastest': {'u': 0.15, 'i': 0.20, 'e': 0.50, 'd': 0.15},
    'high_impact': {'u': 0.15, 'i': 0.60, 'e': 0.10, 'd': 0.15},
    'deadline': {'u': 0.60, 'i': 0.25, 'e': 0.05, 'd': 0.10},
}


def normalize_importance(importance: int) -> float:
    """
    Normalize importance from 1-10 scale to 0-1 scale.
    """
    return max(0.0, min(1.0, (importance - 1) / 9))


def calculate_urgency_score(due_date_str: str, now: datetime) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate urgency score based on due date.
    
    Returns:
        Tuple of (score, metadata) where metadata contains explanation details
    """
    if not due_date_str:
        return 0.5, {'status': 'no_due_date', 'days_left': None}
    
    try:
        # Parse date
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = now.date()
        days_left = (due_date - today).days
        
        if days_left < 0:
            # Past due - max urgency with lateness bonus
            late_by = abs(days_left)
            lateness_bonus = min(late_by / 7, 1.0)  # Up to +1 bonus
            score = 1.0 + lateness_bonus
            return score, {
                'status': 'overdue',
                'days_left': days_left,
                'late_by': late_by,
                'score': score
            }
        elif days_left == 0:
            return 1.0, {'status': 'due_today', 'days_left': 0}
        elif days_left <= 3:
            # Very urgent
            score = 0.9 + (3 - days_left) * 0.033  # 0.9 to 1.0
            return score, {'status': 'urgent', 'days_left': days_left}
        else:
            # Normal urgency decay over 30 days
            score = max(0.0, min(1.0, 1 - days_left / 30))
            return score, {'status': 'normal', 'days_left': days_left}
            
    except (ValueError, TypeError):
        return 0.5, {'status': 'invalid_date', 'days_left': None}


def calculate_effort_score(estimated_hours: float, max_hours: float = 40) -> float:
    """
    Calculate effort score - lower hours = higher score (quick wins).
    
    Uses logarithmic scale to avoid extreme values for very small tasks.
    """
    if estimated_hours <= 0:
        return 1.0  # Instant task
    
    # Logarithmic scaling: quick tasks get high scores
    score = 1 - (math.log(estimated_hours + 1) / math.log(max_hours + 1))
    return max(0.0, min(1.0, score))


def calculate_dependency_score(task_id: str, dependency_map: Dict[str, int], 
                                max_dependents: int) -> float:
    """
    Calculate dependency score based on how many tasks depend on this one.
    Higher score means more tasks are blocked by this task.
    """
    if max_dependents == 0:
        return 0.0
    
    num_dependents = dependency_map.get(task_id, 0)
    return min(1.0, num_dependents / max_dependents)


def detect_circular_dependencies(tasks: List[Dict]) -> Tuple[List[List[str]], List[str]]:
    """
    Detect circular dependencies using DFS.
    
    Returns:
        Tuple of (cycles, all_task_ids_in_cycles)
    """
    # Build adjacency list: task_id -> list of tasks it depends on
    graph = {}
    all_task_ids = set()
    
    for task in tasks:
        task_id = task.get('id')
        if task_id:
            all_task_ids.add(task_id)
            graph[task_id] = task.get('dependencies', [])
    
    # DFS to find cycles
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {task_id: WHITE for task_id in all_task_ids}
    parent = {}
    cycles = []
    
    def dfs(node, path):
        if color[node] == BLACK:
            return
        if color[node] == GRAY:
            # Found cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:]
            cycles.append(cycle)
            return
        
        color[node] = GRAY
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor in all_task_ids:  # Only follow valid dependencies
                dfs(neighbor, path[:])
        
        color[node] = BLACK
    
    for task_id in all_task_ids:
        if color[task_id] == WHITE:
            dfs(task_id, [])
    
    # Flatten cycles to get all affected task IDs
    tasks_in_cycles = set()
    for cycle in cycles:
        tasks_in_cycles.update(cycle)
    
    return cycles, list(tasks_in_cycles)


def build_dependency_map(tasks: List[Dict]) -> Tuple[Dict[str, int], int, List[str]]:
    """
    Build a map of how many tasks depend on each task.
    
    Returns:
        Tuple of (dependency_map, max_dependents, missing_dependencies)
    """
    dependency_map = {}
    all_task_ids = {task.get('id') for task in tasks if task.get('id')}
    missing_deps = set()
    
    for task in tasks:
        task_id = task.get('id')
        dependencies = task.get('dependencies', [])
        
        for dep_id in dependencies:
            if dep_id not in all_task_ids:
                missing_deps.add(dep_id)
            else:
                # dep_id is depended on by task_id
                dependency_map[dep_id] = dependency_map.get(dep_id, 0) + 1
    
    max_dependents = max(dependency_map.values()) if dependency_map else 1
    
    return dependency_map, max_dependents, list(missing_deps)


def compute_task_score(task: Dict, weights: Dict[str, float], 
                       dependency_map: Dict[str, int], max_dependents: int,
                       now: datetime) -> Tuple[float, str, Dict[str, Any]]:
    """
    Compute priority score for a single task.
    
    Returns:
        Tuple of (score, priority_label, details)
    """
    task_id = task.get('id', '')
    
    # Calculate component scores
    u_score, urgency_meta = calculate_urgency_score(task.get('due_date'), now)
    i_score = normalize_importance(task.get('importance', 5))
    e_score = calculate_effort_score(task.get('estimated_hours', 1))
    d_score = calculate_dependency_score(task_id, dependency_map, max_dependents)
    
    # Weighted combination
    raw_score = (
        weights['u'] * u_score +
        weights['i'] * i_score +
        weights['e'] * e_score +
        weights['d'] * d_score
    )
    
    # Normalize to 0-100 for display
    final_score = raw_score * 100
    
    # Determine priority label
    if final_score >= 75:
        priority_label = 'High'
    elif final_score >= 50:
        priority_label = 'Medium'
    else:
        priority_label = 'Low'
    
    # Build explanation
    explanation_parts = []
    
    if urgency_meta['status'] == 'overdue':
        explanation_parts.append(f"⚠️ OVERDUE by {urgency_meta['late_by']} days")
    elif urgency_meta['status'] == 'due_today':
        explanation_parts.append("🔥 Due TODAY")
    elif urgency_meta['status'] == 'urgent':
        explanation_parts.append(f"Due in {urgency_meta['days_left']} days")
    
    importance_val = task.get('importance', 5)
    if importance_val >= 8:
        explanation_parts.append(f"High importance ({importance_val}/10)")
    elif importance_val >= 6:
        explanation_parts.append(f"Medium importance ({importance_val}/10)")
    
    hours = task.get('estimated_hours', 0)
    if hours <= 2:
        explanation_parts.append(f"Quick win ({hours}h)")
    
    num_dependents = dependency_map.get(task_id, 0)
    if num_dependents > 0:
        explanation_parts.append(f"Blocks {num_dependents} task{'s' if num_dependents > 1 else ''}")
    
    explanation = '. '.join(explanation_parts) if explanation_parts else "Standard priority task"
    
    details = {
        'urgency_score': round(u_score, 3),
        'importance_score': round(i_score, 3),
        'effort_score': round(e_score, 3),
        'dependency_score': round(d_score, 3),
        'urgency_meta': urgency_meta,
        'num_dependents': num_dependents,
    }
    
    return final_score, priority_label, explanation, details


def analyze_tasks(tasks: List[Dict], strategy: str = 'smart_balance', 
                  custom_weights: Dict = None) -> Dict[str, Any]:
    """
    Main function to analyze and score all tasks.
    
    Returns:
        Dictionary with sorted tasks, warnings, and metadata
    """
    if not tasks:
        return {
            'analyzed': [],
            'warnings': [],
            'strategy': strategy,
            'weights': STRATEGIES.get(strategy, STRATEGIES['smart_balance'])
        }
    
    # Validate and get weights
    weights = custom_weights if custom_weights else STRATEGIES.get(strategy, STRATEGIES['smart_balance'])
    
    warnings = []
    now = datetime.now()
    
    # Validate tasks and collect issues
    valid_tasks = []
    for idx, task in enumerate(tasks):
        if not task.get('id'):
            warnings.append(f"Task at index {idx} missing 'id' field - skipped")
            continue
        if not task.get('title'):
            warnings.append(f"Task '{task.get('id')}' missing 'title' - using default")
            task['title'] = f"Task {task.get('id')}"
        
        # Set defaults for missing fields
        if task.get('importance') is None:
            task['importance'] = 5
        if task.get('estimated_hours') is None:
            task['estimated_hours'] = 1
        
        # Validate ranges
        task['importance'] = max(1, min(10, int(task.get('importance', 5))))
        task['estimated_hours'] = max(0, float(task.get('estimated_hours', 1)))
        
        if not isinstance(task.get('dependencies'), list):
            task['dependencies'] = []
        
        valid_tasks.append(task)
    
    if not valid_tasks:
        return {
            'analyzed': [],
            'warnings': warnings + ['No valid tasks to analyze'],
            'strategy': strategy,
            'weights': weights
        }
    
    # Detect circular dependencies
    cycles, tasks_in_cycles = detect_circular_dependencies(valid_tasks)
    if cycles:
        warnings.append(f"⚠️ Circular dependency detected: {' -> '.join(cycles[0] + [cycles[0][0]])}")
    
    # Build dependency map
    dependency_map, max_dependents, missing_deps = build_dependency_map(valid_tasks)
    if missing_deps:
        warnings.append(f"Missing dependency IDs referenced: {', '.join(missing_deps)}")
    
    # Score all tasks
    analyzed_tasks = []
    for task in valid_tasks:
        score, priority_label, explanation, details = compute_task_score(
            task, weights, dependency_map, max_dependents, now
        )
        
        analyzed_task = {
            'id': task['id'],
            'title': task['title'],
            'due_date': task.get('due_date'),
            'estimated_hours': task['estimated_hours'],
            'importance': task['importance'],
            'dependencies': task['dependencies'],
            'score': round(score, 2),
            'priority_label': priority_label,
            'explanation': explanation,
            'in_circular_dependency': task['id'] in tasks_in_cycles,
        }
        
        analyzed_tasks.append(analyzed_task)
    
    # Sort by score (descending), then by dependency count, then by hours (ascending)
    analyzed_tasks.sort(
        key=lambda t: (
            -t['score'],  # Higher score first
            -dependency_map.get(t['id'], 0),  # More dependents first
            t['estimated_hours']  # Fewer hours first
        )
    )
    
    return {
        'analyzed': analyzed_tasks,
        'warnings': warnings,
        'strategy': strategy,
        'weights': weights,
        'cycles': cycles if cycles else None,
    }


def get_top_suggestions(analyzed_result: Dict, count: int = 3) -> List[Dict]:
    """
    Get top N task suggestions with enhanced explanations.
    """
    tasks = analyzed_result.get('analyzed', [])[:count]
    
    suggestions = []
    for idx, task in enumerate(tasks):
        confidence = 'High' if task['score'] >= 75 else 'Medium' if task['score'] >= 50 else 'Moderate'
        
        suggestion = {
            **task,
            'rank': idx + 1,
            'confidence': confidence,
            'recommendation': f"Rank #{idx + 1}: {task['explanation']}"
        }
        suggestions.append(suggestion)
    
    return suggestions

