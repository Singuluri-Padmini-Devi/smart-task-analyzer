"""
Unit Tests for Smart Task Analyzer
Tests the core scoring algorithm and edge case handling
"""

from django.test import TestCase
from datetime import datetime, timedelta
from tasks.scoring import (
    normalize_importance,
    calculate_urgency_score,
    calculate_effort_score,
    calculate_dependency_score,
    detect_circular_dependencies,
    build_dependency_map,
    compute_task_score,
    analyze_tasks,
    STRATEGIES
)


class ImportanceNormalizationTests(TestCase):
    """Test importance score normalization (1-10 scale to 0-1)"""
    
    def test_minimum_importance(self):
        """Test importance 1 normalizes to 0"""
        score = normalize_importance(1)
        self.assertEqual(score, 0.0)
    
    def test_maximum_importance(self):
        """Test importance 10 normalizes to 1"""
        score = normalize_importance(10)
        self.assertEqual(score, 1.0)
    
    def test_middle_importance(self):
        """Test importance 5 normalizes to ~0.44"""
        score = normalize_importance(5)
        self.assertAlmostEqual(score, 0.444, places=2)
    
    def test_importance_8(self):
        """Test importance 8 normalizes correctly"""
        score = normalize_importance(8)
        self.assertAlmostEqual(score, 0.777, places=2)


class UrgencyScoreTests(TestCase):
    """Test urgency calculation based on due dates"""
    
    def setUp(self):
        self.now = datetime(2025, 11, 30)
    
    def test_overdue_task(self):
        """Test overdue task gets bonus urgency score"""
        due_date = "2025-11-20"  # 10 days overdue
        score, meta = calculate_urgency_score(due_date, self.now)
        
        self.assertGreater(score, 1.0, "Overdue tasks should have score > 1.0")
        self.assertEqual(meta['status'], 'overdue')
        self.assertEqual(meta['late_by'], 10)
    
    def test_due_today(self):
        """Test task due today has maximum normal urgency"""
        due_date = "2025-11-30"
        score, meta = calculate_urgency_score(due_date, self.now)
        
        self.assertEqual(score, 1.0)
        self.assertEqual(meta['status'], 'due_today')
    
    def test_due_in_three_days(self):
        """Test task due in 3 days is very urgent"""
        due_date = "2025-12-03"
        score, meta = calculate_urgency_score(due_date, self.now)
        
        self.assertGreater(score, 0.8)
        self.assertEqual(meta['status'], 'urgent')
        self.assertEqual(meta['days_left'], 3)
    
    def test_due_in_future(self):
        """Test task due far in future has lower urgency"""
        due_date = "2025-12-30"  # 30 days away
        score, meta = calculate_urgency_score(due_date, self.now)
        
        self.assertLess(score, 0.5)
        self.assertEqual(meta['status'], 'normal')
    
    def test_no_due_date(self):
        """Test missing due date gets neutral urgency"""
        score, meta = calculate_urgency_score(None, self.now)
        
        self.assertEqual(score, 0.5)
        self.assertEqual(meta['status'], 'no_due_date')
    
    def test_invalid_date_format(self):
        """Test invalid date format is handled gracefully"""
        score, meta = calculate_urgency_score("invalid-date", self.now)
        
        self.assertEqual(score, 0.5)
        self.assertEqual(meta['status'], 'invalid_date')
    
    def test_lateness_bonus_bounded(self):
        """Test overdue bonus is capped (doesn't grow infinitely)"""
        due_date = "2024-11-30"  # 365 days overdue
        score, meta = calculate_urgency_score(due_date, self.now)
        
        # Bonus should be capped at +1.0, so max score is 2.0
        self.assertLessEqual(score, 2.0)


class EffortScoreTests(TestCase):
    """Test effort scoring (quick wins logic)"""
    
    def test_zero_hours_task(self):
        """Test zero-hour task gets maximum effort score"""
        score = calculate_effort_score(0)
        self.assertEqual(score, 1.0)
    
    def test_one_hour_task(self):
        """Test 1-hour task gets high effort score"""
        score = calculate_effort_score(1)
        self.assertGreater(score, 0.8)
    
    def test_long_task(self):
        """Test long task gets lower effort score"""
        score = calculate_effort_score(40)
        self.assertLess(score, 0.3)
    
    def test_logarithmic_scaling(self):
        """Test effort uses logarithmic scaling (not linear)"""
        score_2h = calculate_effort_score(2)
        score_4h = calculate_effort_score(4)
        
        # Logarithmic: difference between 2h and 4h should be less than 2x
        self.assertLess(score_2h - score_4h, 0.5)


class DependencyScoreTests(TestCase):
    """Test dependency scoring"""
    
    def test_no_dependents(self):
        """Test task with no dependents gets 0 dependency score"""
        dependency_map = {'t1': 0, 't2': 2}
        score = calculate_dependency_score('t1', dependency_map, 2)
        self.assertEqual(score, 0.0)
    
    def test_max_dependents(self):
        """Test task with max dependents gets 1.0 score"""
        dependency_map = {'t1': 5, 't2': 2}
        score = calculate_dependency_score('t1', dependency_map, 5)
        self.assertEqual(score, 1.0)
    
    def test_partial_dependents(self):
        """Test task with partial dependents gets proportional score"""
        dependency_map = {'t1': 2, 't2': 4}
        score = calculate_dependency_score('t1', dependency_map, 4)
        self.assertEqual(score, 0.5)
    
    def test_task_not_in_map(self):
        """Test task not depended on by others gets 0"""
        dependency_map = {'t1': 3}
        score = calculate_dependency_score('t2', dependency_map, 3)
        self.assertEqual(score, 0.0)


class CircularDependencyTests(TestCase):
    """Test circular dependency detection using DFS"""
    
    def test_no_cycle(self):
        """Test linear dependencies have no cycle"""
        tasks = [
            {'id': 't1', 'dependencies': []},
            {'id': 't2', 'dependencies': ['t1']},
            {'id': 't3', 'dependencies': ['t2']}
        ]
        cycles, tasks_in_cycles = detect_circular_dependencies(tasks)
        
        self.assertEqual(len(cycles), 0)
        self.assertEqual(len(tasks_in_cycles), 0)
    
    def test_simple_cycle(self):
        """Test simple A->B->A cycle is detected"""
        tasks = [
            {'id': 't1', 'dependencies': ['t2']},
            {'id': 't2', 'dependencies': ['t1']}
        ]
        cycles, tasks_in_cycles = detect_circular_dependencies(tasks)
        
        self.assertGreater(len(cycles), 0, "Should detect cycle")
        self.assertIn('t1', tasks_in_cycles)
        self.assertIn('t2', tasks_in_cycles)
    
    def test_three_node_cycle(self):
        """Test A->B->C->A cycle is detected"""
        tasks = [
            {'id': 't1', 'dependencies': ['t2']},
            {'id': 't2', 'dependencies': ['t3']},
            {'id': 't3', 'dependencies': ['t1']}
        ]
        cycles, tasks_in_cycles = detect_circular_dependencies(tasks)
        
        self.assertGreater(len(cycles), 0)
        self.assertEqual(len(tasks_in_cycles), 3)
    
    def test_cycle_with_independent_task(self):
        """Test cycle detection doesn't affect independent tasks"""
        tasks = [
            {'id': 't1', 'dependencies': ['t2']},
            {'id': 't2', 'dependencies': ['t1']},
            {'id': 't3', 'dependencies': []}
        ]
        cycles, tasks_in_cycles = detect_circular_dependencies(tasks)
        
        self.assertNotIn('t3', tasks_in_cycles, "Independent task should not be flagged")


class DependencyMapTests(TestCase):
    """Test dependency map building"""
    
    def test_build_simple_map(self):
        """Test building dependency map for simple dependencies"""
        tasks = [
            {'id': 't1', 'dependencies': []},
            {'id': 't2', 'dependencies': ['t1']},
            {'id': 't3', 'dependencies': ['t1']}
        ]
        dep_map, max_deps, missing = build_dependency_map(tasks)
        
        self.assertEqual(dep_map['t1'], 2, "t1 is depended on by 2 tasks")
        self.assertEqual(max_deps, 2)
        self.assertEqual(len(missing), 0)
    
    def test_missing_dependencies(self):
        """Test detection of missing dependency IDs"""
        tasks = [
            {'id': 't1', 'dependencies': ['t999']},
            {'id': 't2', 'dependencies': ['t1']}
        ]
        dep_map, max_deps, missing = build_dependency_map(tasks)
        
        self.assertIn('t999', missing)
        self.assertEqual(len(missing), 1)
    
    def test_no_dependencies(self):
        """Test tasks with no dependencies"""
        tasks = [
            {'id': 't1', 'dependencies': []},
            {'id': 't2', 'dependencies': []}
        ]
        dep_map, max_deps, missing = build_dependency_map(tasks)
        
        self.assertEqual(len(dep_map), 0)
        self.assertEqual(max_deps, 1)  # Default to 1 to avoid division by zero


class TaskScoreComputationTests(TestCase):
    """Test complete task score computation"""
    
    def setUp(self):
        self.now = datetime(2025, 11, 30)
        self.weights = STRATEGIES['smart_balance']
        self.dependency_map = {}
        self.max_dependents = 1
    
    def test_high_priority_task(self):
        """Test high importance, urgent task gets high score"""
        task = {
            'id': 't1',
            'title': 'Critical bug',
            'due_date': '2025-12-01',  # Tomorrow
            'estimated_hours': 2,
            'importance': 10,
            'dependencies': []
        }
        
        score, priority, explanation, details = compute_task_score(
            task, self.weights, self.dependency_map, self.max_dependents, self.now
        )
        
        self.assertGreater(score, 75, "Should be high priority")
        self.assertEqual(priority, 'High')
    
    def test_low_priority_task(self):
        """Test low importance, distant task gets low score"""
        task = {
            'id': 't1',
            'title': 'Nice to have',
            'due_date': '2025-12-30',  # 30 days away
            'estimated_hours': 10,
            'importance': 3,
            'dependencies': []
        }
        
        score, priority, explanation, details = compute_task_score(
            task, self.weights, self.dependency_map, self.max_dependents, self.now
        )
        
        self.assertLess(score, 50, "Should be low priority")
        self.assertEqual(priority, 'Low')
    
    def test_overdue_task_high_score(self):
        """Test overdue task gets very high score"""
        task = {
            'id': 't1',
            'title': 'Overdue task',
            'due_date': '2025-11-20',  # 10 days overdue
            'estimated_hours': 3,
            'importance': 8,
            'dependencies': []
        }
        
        score, priority, explanation, details = compute_task_score(
            task, self.weights, self.dependency_map, self.max_dependents, self.now
        )
        
        self.assertGreater(score, 90, "Overdue task should have very high score")
        self.assertIn('OVERDUE', explanation)


class AnalyzeTasksIntegrationTests(TestCase):
    """Integration tests for full task analysis"""
    
    def test_analyze_empty_list(self):
        """Test analyzing empty task list"""
        result = analyze_tasks([])
        
        self.assertEqual(len(result['analyzed']), 0)
        self.assertEqual(len(result['warnings']), 0)
    
    def test_analyze_basic_tasks(self):
        """Test analyzing basic task list"""
        tasks = [
            {
                'id': 't1',
                'title': 'Task 1',
                'due_date': '2025-12-01',
                'estimated_hours': 2,
                'importance': 8,
                'dependencies': []
            },
            {
                'id': 't2',
                'title': 'Task 2',
                'due_date': '2025-12-10',
                'estimated_hours': 5,
                'importance': 5,
                'dependencies': []
            }
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertEqual(len(result['analyzed']), 2)
        self.assertGreater(result['analyzed'][0]['score'], 
                          result['analyzed'][1]['score'],
                          "Higher priority task should be first")
    
    def test_analyze_with_circular_dependency(self):
        """Test analysis with circular dependency"""
        tasks = [
            {'id': 't1', 'title': 'Task 1', 'due_date': '2025-12-05',
             'estimated_hours': 2, 'importance': 7, 'dependencies': ['t2']},
            {'id': 't2', 'title': 'Task 2', 'due_date': '2025-12-06',
             'estimated_hours': 3, 'importance': 6, 'dependencies': ['t1']}
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertGreater(len(result['warnings']), 0, "Should have warnings")
        self.assertTrue(result['analyzed'][0]['in_circular_dependency'])
        self.assertTrue(result['analyzed'][1]['in_circular_dependency'])
    
    def test_analyze_with_missing_dependencies(self):
        """Test analysis with missing dependencies"""
        tasks = [
            {'id': 't1', 'title': 'Task 1', 'due_date': '2025-12-05',
             'estimated_hours': 2, 'importance': 7, 'dependencies': ['t999']}
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertIn('t999', str(result['warnings']))
    
    def test_different_strategies(self):
        """Test all four strategies produce different results"""
        tasks = [
            {'id': 't1', 'title': 'Quick task', 'due_date': '2025-12-10',
             'estimated_hours': 1, 'importance': 5, 'dependencies': []},
            {'id': 't2', 'title': 'Important task', 'due_date': '2025-12-10',
             'estimated_hours': 5, 'importance': 10, 'dependencies': []}
        ]
        
        # Test with different strategies
        result_fastest = analyze_tasks(tasks, strategy='fastest')
        result_impact = analyze_tasks(tasks, strategy='high_impact')
        
        # Fastest should favor t1 (1 hour)
        # High impact should favor t2 (importance 10)
        self.assertEqual(result_fastest['analyzed'][0]['id'], 't1')
        self.assertEqual(result_impact['analyzed'][0]['id'], 't2')
    
    def test_missing_fields_get_defaults(self):
        """Test tasks with missing fields get default values"""
        tasks = [
            {
                'id': 't1',
                'title': 'Minimal task'
                # Missing: due_date, estimated_hours, importance, dependencies
            }
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertEqual(len(result['analyzed']), 1)
        analyzed = result['analyzed'][0]
        self.assertEqual(analyzed['importance'], 5)  # Default
        self.assertEqual(analyzed['estimated_hours'], 1)  # Default


class StrategyTests(TestCase):
    """Test predefined strategy configurations"""
    
    def test_all_strategies_exist(self):
        """Test all required strategies are defined"""
        required_strategies = ['smart_balance', 'fastest', 'high_impact', 'deadline']
        
        for strategy in required_strategies:
            self.assertIn(strategy, STRATEGIES)
    
    def test_strategy_weights_valid(self):
        """Test all strategy weights are between 0 and 1"""
        for strategy_name, weights in STRATEGIES.items():
            for weight_key, weight_val in weights.items():
                self.assertGreaterEqual(weight_val, 0.0,
                    f"{strategy_name}.{weight_key} should be >= 0")
                self.assertLessEqual(weight_val, 1.0,
                    f"{strategy_name}.{weight_key} should be <= 1")
    
    def test_strategy_has_all_weights(self):
        """Test each strategy has all required weight keys"""
        required_keys = {'u', 'i', 'e', 'd'}
        
        for strategy_name, weights in STRATEGIES.items():
            self.assertEqual(set(weights.keys()), required_keys,
                f"{strategy_name} should have all weight keys")


class EdgeCaseTests(TestCase):
    """Test various edge cases"""
    
    def test_task_missing_id(self):
        """Test task without ID is skipped"""
        tasks = [
            {'title': 'No ID task', 'due_date': '2025-12-05',
             'estimated_hours': 2, 'importance': 7, 'dependencies': []}
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertEqual(len(result['analyzed']), 0)
        self.assertGreater(len(result['warnings']), 0)
    
    def test_task_with_extreme_values(self):
        """Test task with extreme values is clamped"""
        tasks = [
            {'id': 't1', 'title': 'Extreme task', 'due_date': '2025-12-05',
             'estimated_hours': -5, 'importance': 999, 'dependencies': []}
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertEqual(len(result['analyzed']), 1)
        analyzed = result['analyzed'][0]
        self.assertGreaterEqual(analyzed['estimated_hours'], 0)
        self.assertLessEqual(analyzed['importance'], 10)
        self.assertGreaterEqual(analyzed['importance'], 1)
    
    def test_very_long_task_list(self):
        """Test analyzing many tasks doesn't crash"""
        tasks = [
            {
                'id': f't{i}',
                'title': f'Task {i}',
                'due_date': '2025-12-10',
                'estimated_hours': i % 10 + 1,
                'importance': i % 10 + 1,
                'dependencies': []
            }
            for i in range(100)
        ]
        
        result = analyze_tasks(tasks)
        
        self.assertEqual(len(result['analyzed']), 100)

