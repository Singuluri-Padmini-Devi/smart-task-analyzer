"""
Serializers for task validation and data processing.
"""

from rest_framework import serializers


class TaskSerializer(serializers.Serializer):
    """Serializer for individual task validation."""
    
    id = serializers.CharField(required=True, max_length=100)
    title = serializers.CharField(required=True, max_length=500)
    due_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    estimated_hours = serializers.FloatField(required=False, default=1, min_value=0)
    importance = serializers.IntegerField(required=False, default=5, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        allow_empty=True
    )
    
    def validate_due_date(self, value):
        """Validate date format if provided."""
        if value and value.strip():
            from datetime import datetime
            try:
                datetime.strptime(value, '%Y-%m-%d')
                return value
            except ValueError:
                raise serializers.ValidationError(
                    "Date must be in YYYY-MM-DD format"
                )
        return value


class AnalyzeRequestSerializer(serializers.Serializer):
    """Serializer for analyze endpoint request."""
    
    tasks = TaskSerializer(many=True, required=True)
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest', 'high_impact', 'deadline'],
        required=False,
        default='smart_balance'
    )
    weights = serializers.DictField(
        child=serializers.FloatField(),
        required=False,
        allow_null=True
    )
    
    def validate_tasks(self, value):
        """Ensure at least one task is provided."""
        if not value:
            raise serializers.ValidationError("At least one task is required")
        return value
    
    def validate_weights(self, value):
        """Validate custom weights if provided."""
        if value:
            required_keys = {'u', 'i', 'e', 'd'}
            if not required_keys.issubset(value.keys()):
                raise serializers.ValidationError(
                    f"Weights must include all keys: {required_keys}"
                )
            
            # Check all values are between 0 and 1
            for key, val in value.items():
                if not (0 <= val <= 1):
                    raise serializers.ValidationError(
                        f"Weight '{key}' must be between 0 and 1"
                    )
        
        return value

