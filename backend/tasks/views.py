"""
API Views for task analysis and suggestions.
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import AnalyzeRequestSerializer
from .scoring import analyze_tasks, get_top_suggestions, STRATEGIES


@api_view(['POST'])
def analyze_tasks_view(request):
    """
    POST /api/tasks/analyze/
    
    Accept a list of tasks and return them sorted by priority score.
    
    Request body:
    {
        "strategy": "smart_balance",  // optional
        "weights": {...},              // optional
        "tasks": [...]
    }
    
    Response:
    {
        "analyzed": [...],
        "warnings": [...],
        "strategy": "...",
        "weights": {...}
    }
    """
    serializer = AnalyzeRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    tasks = validated_data['tasks']
    strategy = validated_data.get('strategy', 'smart_balance')
    custom_weights = validated_data.get('weights')
    
    # Analyze tasks
    result = analyze_tasks(tasks, strategy=strategy, custom_weights=custom_weights)
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def suggest_tasks_view(request):
    """
    GET/POST /api/tasks/suggest/
    
    Return the top 3 tasks to work on with explanations.
    
    For POST, accepts same body as analyze endpoint.
    For GET, expects tasks and strategy as query params (limited functionality).
    """
    if request.method == 'POST':
        # Use POST body
        serializer = AnalyzeRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        tasks = validated_data['tasks']
        strategy = validated_data.get('strategy', 'smart_balance')
        custom_weights = validated_data.get('weights')
        
    else:
        # GET method - expect minimal query params
        strategy = request.query_params.get('strategy', 'smart_balance')
        
        # For GET, we need tasks to be provided somehow
        # This is a simplified version - typically you'd store tasks server-side
        return Response({
            'error': 'Please use POST method with tasks in request body',
            'example': {
                'tasks': [],
                'strategy': 'smart_balance'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Analyze and get suggestions
    result = analyze_tasks(tasks, strategy=strategy, custom_weights=custom_weights)
    suggestions = get_top_suggestions(result, count=3)
    
    return Response({
        'suggestions': suggestions,
        'total_tasks': len(result['analyzed']),
        'strategy': result['strategy'],
        'warnings': result['warnings'],
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def strategies_view(request):
    """
    GET /api/strategies/
    
    Return available strategies and their weights.
    """
    return Response({
        'strategies': STRATEGIES,
        'descriptions': {
            'smart_balance': 'Balanced approach considering all factors equally',
            'fastest': 'Prioritizes quick wins - tasks that take less time',
            'high_impact': 'Prioritizes importance over other factors',
            'deadline': 'Prioritizes urgent tasks based on due dates',
        }
    }, status=status.HTTP_200_OK)

