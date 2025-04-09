"""
Usage tracker service for API key consumption.

This module provides functionality to track API key usage by users,
which will be used for the future credit system.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

# In-memory storage for usage data (to be replaced with database in production)
_usage_records: List[Dict[str, Any]] = []
_usage_summary: Dict[str, Dict[str, int]] = {}  # user_id -> {key_type -> count}

class UsageTracker:
    """
    API usage tracking system for the future credit/quota implementation.
    
    This is a simple implementation that will be expanded with:
    - Database integration
    - Credit allocation and consumption
    - Usage limits and quota management
    """
    
    @staticmethod
    async def record_usage(
        user_id: Optional[str], 
        key_type: str, 
        is_server_key: bool,
        operation: str = "api_call",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an API key usage event.
        
        Args:
            user_id: User identifier (can be None for anonymous usage)
            key_type: Type of API key ('google' or 'perplexity')
            is_server_key: Whether this is a server-provided key
            operation: The operation being performed (e.g., 'generate_learning_path')
            metadata: Additional information about the usage
        """
        # Create usage record
        usage_record = {
            "user_id": user_id or "anonymous",
            "key_type": key_type,
            "is_server_key": is_server_key,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Add to in-memory storage (would be database in production)
        _usage_records.append(usage_record)
        
        # Update usage summary
        user_key = user_id or "anonymous"
        if user_key not in _usage_summary:
            _usage_summary[user_key] = {}
            
        if key_type not in _usage_summary[user_key]:
            _usage_summary[user_key][key_type] = 0
            
        _usage_summary[user_key][key_type] += 1
        
        logger.debug(f"Recorded usage: {user_id or 'anonymous'} used {key_type} API for {operation}")
    
    @staticmethod
    async def get_user_usage(user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for a user.
        
        Args:
            user_id: User identifier (if None, returns summary for all users)
            
        Returns:
            Dict with usage statistics
        """
        if user_id:
            user_key = user_id
            if user_key not in _usage_summary:
                return {"user_id": user_id, "usage": {}, "total_calls": 0}
                
            total_calls = sum(_usage_summary[user_key].values())
            return {
                "user_id": user_id,
                "usage": _usage_summary[user_key],
                "total_calls": total_calls
            }
        else:
            # Summary for all users
            return {
                "user_count": len(_usage_summary),
                "total_usage": {
                    "google": sum(u.get("google", 0) for u in _usage_summary.values()),
                    "perplexity": sum(u.get("perplexity", 0) for u in _usage_summary.values())
                }
            }
    
    @staticmethod
    async def get_usage_summary() -> Dict[str, Any]:
        """
        Get a summary of overall API usage.
        
        Returns:
            Dict with usage summary statistics
        """
        total_google = 0
        total_perplexity = 0
        
        for user_stats in _usage_summary.values():
            total_google += user_stats.get("google", 0)
            total_perplexity += user_stats.get("perplexity", 0)
        
        return {
            "total_requests": len(_usage_records),
            "total_google_calls": total_google,
            "total_perplexity_calls": total_perplexity,
            "unique_users": len(_usage_summary)
        } 