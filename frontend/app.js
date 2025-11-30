/**
 * Smart Task Analyzer - Frontend JavaScript
 * Handles task input, API communication, and results display
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State
let tasks = [];
let currentResults = null;

// DOM Elements
const taskForm = document.getElementById('task-form');
const bulkJsonTextarea = document.getElementById('bulk-json');
const loadJsonBtn = document.getElementById('load-json');
const taskList = document.getElementById('task-list');
const taskCount = document.getElementById('task-count');
const clearTasksBtn = document.getElementById('clear-tasks');
const strategySelect = document.getElementById('strategy-select');
const analyzeBtn = document.getElementById('analyze-btn');
const analyzeText = document.getElementById('analyze-text');
const analyzeLoader = document.getElementById('analyze-loader');
const outputSection = document.getElementById('output-section');
const warningsContainer = document.getElementById('warnings-container');
const warningsList = document.getElementById('warnings-list');
const currentStrategySpan = document.getElementById('current-strategy');
const resultsList = document.getElementById('results-list');
const getSuggestionsBtn = document.getElementById('get-suggestions');
const suggestionsList = document.getElementById('suggestions-list');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateTaskList();
});

// Event Listeners
function setupEventListeners() {
    taskForm.addEventListener('submit', handleAddTask);
    loadJsonBtn.addEventListener('click', handleLoadJson);
    clearTasksBtn.addEventListener('click', handleClearTasks);
    analyzeBtn.addEventListener('click', handleAnalyze);
    getSuggestionsBtn.addEventListener('click', handleGetSuggestions);
}

// Add single task from form
function handleAddTask(e) {
    e.preventDefault();
    
    const taskId = document.getElementById('task-id').value.trim();
    const title = document.getElementById('task-title').value.trim();
    const dueDate = document.getElementById('task-due').value;
    const hours = parseFloat(document.getElementById('task-hours').value);
    const importance = parseInt(document.getElementById('task-importance').value);
    const depsInput = document.getElementById('task-deps').value.trim();
    
    // Validate
    if (!taskId || !title) {
        alert('Task ID and Title are required!');
        return;
    }
    
    // Check for duplicate ID
    if (tasks.find(t => t.id === taskId)) {
        alert(`Task with ID '${taskId}' already exists!`);
        return;
    }
    
    // Parse dependencies
    const dependencies = depsInput
        ? depsInput.split(',').map(d => d.trim()).filter(d => d)
        : [];
    
    // Create task object
    const task = {
        id: taskId,
        title: title,
        due_date: dueDate || null,
        estimated_hours: hours,
        importance: importance,
        dependencies: dependencies
    };
    
    // Add to tasks array
    tasks.push(task);
    updateTaskList();
    
    // Reset form
    taskForm.reset();
    document.getElementById('task-hours').value = 1;
    document.getElementById('task-importance').value = 5;
    
    // Show success feedback
    showToast('Task added successfully!', 'success');
}

// Load tasks from JSON
function handleLoadJson() {
    const jsonText = bulkJsonTextarea.value.trim();
    
    if (!jsonText) {
        alert('Please paste JSON data first!');
        return;
    }
    
    try {
        const parsedTasks = JSON.parse(jsonText);
        
        if (!Array.isArray(parsedTasks)) {
            throw new Error('JSON must be an array of tasks');
        }
        
        // Validate each task has required fields
        for (const task of parsedTasks) {
            if (!task.id || !task.title) {
                throw new Error('Each task must have an "id" and "title"');
            }
        }
        
        // Add tasks (check for duplicates)
        let added = 0;
        let skipped = 0;
        
        for (const task of parsedTasks) {
            if (!tasks.find(t => t.id === task.id)) {
                tasks.push(task);
                added++;
            } else {
                skipped++;
            }
        }
        
        updateTaskList();
        bulkJsonTextarea.value = '';
        
        showToast(`Added ${added} tasks${skipped > 0 ? `, skipped ${skipped} duplicates` : ''}`, 'success');
        
    } catch (error) {
        alert(`Invalid JSON: ${error.message}`);
    }
}

// Clear all tasks
function handleClearTasks() {
    if (tasks.length === 0) return;
    
    if (confirm('Are you sure you want to clear all tasks?')) {
        tasks = [];
        updateTaskList();
        outputSection.style.display = 'none';
        showToast('All tasks cleared', 'info');
    }
}

// Update task list display
function updateTaskList() {
    taskCount.textContent = tasks.length;
    
    if (tasks.length === 0) {
        taskList.innerHTML = '<div class="empty-state"><p>No tasks added yet. Add tasks using the form above or paste JSON.</p></div>';
        analyzeBtn.disabled = true;
        return;
    }
    
    analyzeBtn.disabled = false;
    
    taskList.innerHTML = tasks.map((task, index) => `
        <div class="task-item">
            <div class="task-item-info">
                <div class="task-item-title">${task.id}: ${task.title}</div>
                <div class="task-item-details">
                    Due: ${task.due_date || 'N/A'} | 
                    Hours: ${task.estimated_hours} | 
                    Importance: ${task.importance}/10
                    ${task.dependencies.length > 0 ? ` | Deps: ${task.dependencies.join(', ')}` : ''}
                </div>
            </div>
            <button class="task-item-remove" onclick="removeTask(${index})">Remove</button>
        </div>
    `).join('');
}

// Remove task by index
function removeTask(index) {
    tasks.splice(index, 1);
    updateTaskList();
}

// Analyze tasks
async function handleAnalyze() {
    if (tasks.length === 0) {
        alert('Please add tasks first!');
        return;
    }
    
    const strategy = strategySelect.value;
    
    // Show loading state
    analyzeBtn.disabled = true;
    analyzeText.textContent = 'Analyzing...';
    analyzeLoader.style.display = 'inline-block';
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Analysis failed');
        }
        
        const result = await response.json();
        currentResults = result;
        
        displayResults(result);
        
    } catch (error) {
        alert(`Error: ${error.message}`);
        console.error('Analysis error:', error);
    } finally {
        // Reset button state
        analyzeBtn.disabled = false;
        analyzeText.textContent = 'Analyze Tasks';
        analyzeLoader.style.display = 'none';
    }
}

// Display analysis results
function displayResults(result) {
    outputSection.style.display = 'block';
    
    // Scroll to results
    outputSection.scrollIntoView({ behavior: 'smooth' });
    
    // Display warnings
    if (result.warnings && result.warnings.length > 0) {
        warningsContainer.style.display = 'block';
        warningsList.innerHTML = result.warnings.map(w => `<li>${w}</li>`).join('');
    } else {
        warningsContainer.style.display = 'none';
    }
    
    // Display strategy info
    const strategyNames = {
        'smart_balance': '🎯 Smart Balance',
        'fastest': '⚡ Fastest Wins',
        'high_impact': '🎖️ High Impact',
        'deadline': '⏰ Deadline Driven'
    };
    
    currentStrategySpan.textContent = strategyNames[result.strategy] || result.strategy;
    
    // Display weights
    const weights = result.weights;
    document.getElementById('weight-u').textContent = weights.u.toFixed(2);
    document.getElementById('weight-i').textContent = weights.i.toFixed(2);
    document.getElementById('weight-e').textContent = weights.e.toFixed(2);
    document.getElementById('weight-d').textContent = weights.d.toFixed(2);
    
    // Display all results
    if (result.analyzed.length === 0) {
        resultsList.innerHTML = '<div class="empty-state"><p>No tasks to display.</p></div>';
        return;
    }
    
    resultsList.innerHTML = result.analyzed.map(task => `
        <div class="result-card priority-${task.priority_label.toLowerCase()}">
            <div class="result-header">
                <div class="result-title">${task.title}</div>
                <span class="priority-badge priority-${task.priority_label.toLowerCase()}">
                    ${task.priority_label}
                </span>
            </div>
            
            <div class="result-score">${task.score}</div>
            
            <div class="result-details">
                <div class="detail-item">
                    <div class="detail-label">ID:</div>
                    <div class="detail-value">${task.id}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Due:</div>
                    <div class="detail-value">${task.due_date || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Hours:</div>
                    <div class="detail-value">${task.estimated_hours}h</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Importance:</div>
                    <div class="detail-value">${task.importance}/10</div>
                </div>
            </div>
            
            <div class="result-explanation">
                ${task.explanation}
            </div>
            
            ${task.in_circular_dependency ? '<div class="circular-dep-badge">⚠️ Circular Dependency</div>' : ''}
        </div>
    `).join('');
}

// Get top suggestions
async function handleGetSuggestions() {
    if (!currentResults) {
        alert('Please analyze tasks first!');
        return;
    }
    
    const strategy = strategySelect.value;
    
    getSuggestionsBtn.disabled = true;
    getSuggestionsBtn.textContent = 'Loading...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/suggest/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get suggestions');
        }
        
        const result = await response.json();
        displaySuggestions(result.suggestions);
        
    } catch (error) {
        alert(`Error: ${error.message}`);
        console.error('Suggestions error:', error);
    } finally {
        getSuggestionsBtn.disabled = false;
        getSuggestionsBtn.textContent = 'Get Top 3 Suggestions';
    }
}

// Display suggestions
function displaySuggestions(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        suggestionsList.innerHTML = '<div class="empty-state"><p>No suggestions available.</p></div>';
        return;
    }
    
    suggestionsList.innerHTML = suggestions.map(task => `
        <div class="suggestion-card">
            <div class="suggestion-rank">#${task.rank}</div>
            <div class="suggestion-title">${task.title}</div>
            <div class="suggestion-details">
                <strong>Score:</strong> ${task.score} | 
                <strong>Confidence:</strong> ${task.confidence}
            </div>
            <div class="suggestion-details">
                <strong>Due:</strong> ${task.due_date || 'N/A'} | 
                <strong>Hours:</strong> ${task.estimated_hours}h | 
                <strong>Importance:</strong> ${task.importance}/10
            </div>
            <div class="suggestion-explanation">
                💡 ${task.recommendation}
            </div>
        </div>
    `).join('');
}

// Toast notification
function showToast(message, type = 'info') {
    // Simple implementation - you could enhance this with a proper toast library
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Could add a visual toast here
}

// Sample data for testing
function loadSampleData() {
    const sample = [
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
            "title": "Update documentation",
            "due_date": "2025-12-10",
            "estimated_hours": 2,
            "importance": 5,
            "dependencies": []
        },
        {
            "id": "t3",
            "title": "Implement new feature",
            "due_date": "2025-12-05",
            "estimated_hours": 8,
            "importance": 7,
            "dependencies": ["t1"]
        },
        {
            "id": "t4",
            "title": "Code review",
            "due_date": "2025-12-01",
            "estimated_hours": 1,
            "importance": 6,
            "dependencies": []
        },
        {
            "id": "t5",
            "title": "Deploy to production",
            "due_date": "2025-12-08",
            "estimated_hours": 2,
            "importance": 8,
            "dependencies": ["t1", "t3"]
        }
    ];
    
    bulkJsonTextarea.value = JSON.stringify(sample, null, 2);
}

// Expose functions for HTML onclick handlers
window.removeTask = removeTask;
window.loadSampleData = loadSampleData;

