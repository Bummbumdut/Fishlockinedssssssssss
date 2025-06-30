import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

class AIUsageManager:
    """
    Manages AI API usage to stay within free tier limits
    Google AI Studio Free Tier: 15 requests/minute, 1,500 requests/day
    """
    
    def __init__(self, usage_file="ai_usage.json"):
        self.usage_file = usage_file
        self.daily_limit = 1500  # Google AI Studio daily limit
        self.minute_limit = 15   # Google AI Studio per-minute limit
        self.usage_data = self._load_usage_data()
    
    def _load_usage_data(self) -> Dict:
        """Load usage data from file"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self._create_empty_usage()
        return self._create_empty_usage()
    
    def _create_empty_usage(self) -> Dict:
        """Create empty usage structure"""
        return {
            "daily_usage": {},
            "minute_usage": {},
            "last_reset": datetime.now().isoformat()
        }
    
    def _save_usage_data(self):
        """Save usage data to file"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def _get_today_key(self) -> str:
        """Get today's date key"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_minute_key(self) -> str:
        """Get current minute key"""
        return datetime.now().strftime("%Y-%m-%d-%H-%M")
    
    def _cleanup_old_data(self):
        """Remove old usage data to keep file size manageable"""
        today = datetime.now()
        cutoff_date = today - timedelta(days=7)  # Keep 7 days of data
        
        # Clean daily usage
        keys_to_remove = []
        for date_key in self.usage_data["daily_usage"]:
            try:
                date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                if date_obj < cutoff_date:
                    keys_to_remove.append(date_key)
            except ValueError:
                keys_to_remove.append(date_key)
        
        for key in keys_to_remove:
            del self.usage_data["daily_usage"][key]
        
        # Clean minute usage (keep only last 2 hours)
        cutoff_minute = today - timedelta(hours=2)
        keys_to_remove = []
        for minute_key in self.usage_data["minute_usage"]:
            try:
                minute_obj = datetime.strptime(minute_key, "%Y-%m-%d-%H-%M")
                if minute_obj < cutoff_minute:
                    keys_to_remove.append(minute_key)
            except ValueError:
                keys_to_remove.append(minute_key)
        
        for key in keys_to_remove:
            del self.usage_data["minute_usage"][key]
    
    def can_make_request(self) -> tuple[bool, str]:
        """
        Check if we can make a request within limits
        Returns: (can_make_request, reason_if_not)
        """
        today_key = self._get_today_key()
        minute_key = self._get_minute_key()
        
        # Check daily limit
        daily_usage = self.usage_data["daily_usage"].get(today_key, 0)
        if daily_usage >= self.daily_limit:
            return False, f"Daily limit reached ({daily_usage}/{self.daily_limit}). Resets at midnight."
        
        # Check minute limit
        minute_usage = self.usage_data["minute_usage"].get(minute_key, 0)
        if minute_usage >= self.minute_limit:
            return False, f"Rate limit reached ({minute_usage}/{self.minute_limit}). Wait 1 minute."
        
        return True, ""
    
    def record_request(self):
        """Record a successful API request"""
        today_key = self._get_today_key()
        minute_key = self._get_minute_key()
        
        # Update daily usage
        self.usage_data["daily_usage"][today_key] = self.usage_data["daily_usage"].get(today_key, 0) + 1
        
        # Update minute usage
        self.usage_data["minute_usage"][minute_key] = self.usage_data["minute_usage"].get(minute_key, 0) + 1
        
        # Cleanup old data
        self._cleanup_old_data()
        
        # Save to file
        self._save_usage_data()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        today_key = self._get_today_key()
        minute_key = self._get_minute_key()
        
        daily_used = self.usage_data["daily_usage"].get(today_key, 0)
        minute_used = self.usage_data["minute_usage"].get(minute_key, 0)
        
        return {
            "daily": {
                "used": daily_used,
                "limit": self.daily_limit,
                "remaining": self.daily_limit - daily_used,
                "percentage": (daily_used / self.daily_limit) * 100
            },
            "minute": {
                "used": minute_used,
                "limit": self.minute_limit,
                "remaining": self.minute_limit - minute_used,
                "percentage": (minute_used / self.minute_limit) * 100
            }
        }
    
    def wait_if_needed(self) -> Optional[int]:
        """
        Wait if we're hitting rate limits
        Returns: seconds waited (None if no wait needed)
        """
        can_request, reason = self.can_make_request()
        if can_request:
            return None
        
        if "Rate limit" in reason:
            # Wait until next minute
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            wait_seconds = (next_minute - now).total_seconds()
            print(f"Rate limit hit. Waiting {wait_seconds:.1f} seconds...")
            time.sleep(wait_seconds)
            return int(wait_seconds)
        
        return None