"""Strategy performance tracker with real-time monitoring."""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
import time


class StrategyTracker:
    """Track and monitor strategy performance in real-time."""
    
    def __init__(self):
        self.history: Dict[str, list] = defaultdict(list)
        self.start_time = datetime.now()
        self.metrics_history: list = []
    
    def record(
        self,
        strategy_name: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """Record strategy metrics."""
        if timestamp is None:
            timestamp = datetime.now()
        
        record = {
            "timestamp": timestamp,
            "strategy": strategy_name,
            **metrics
        }
        
        self.history[strategy_name].append(record)
        self.metrics_history.append(record)
    
    def get_latest(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """Get latest metrics for a strategy."""
        if strategy_name in self.history and len(self.history[strategy_name]) > 0:
            return self.history[strategy_name][-1]
        return None
    
    def get_series(self, strategy_name: str, metric: str) -> pd.Series:
        """Get time series of a specific metric."""
        if strategy_name not in self.history:
            return pd.Series()
        
        series = pd.DataFrame(self.history[strategy_name])
        if metric in series.columns:
            return series.set_index('timestamp')[metric]
        return pd.Series()
    
    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all strategies."""
        summary = {}
        
        for strategy_name, records in self.history.items():
            if records:
                latest = records[-1]
                df = pd.DataFrame(records)
                
                summary[strategy_name] = {
                    "latest": latest,
                    "count": len(records),
                    "start_time": records[0]['timestamp'],
                    "last_update": latest['timestamp'],
                }
                
                # Calculate changes
                if len(records) > 1:
                    first = records[0]
                    summary[strategy_name]['total_change'] = (
                        latest.get('total_return', 0) - first.get('total_return', 0)
                    )
        
        return summary
    
    def export_csv(self, filepath: str):
        """Export all history to CSV."""
        all_records = []
        for strategy_name, records in self.history.items():
            for record in records:
                all_records.append(record)
        
        if all_records:
            df = pd.DataFrame(all_records)
            df.to_csv(filepath, index=False)
    
    def reset(self):
        """Reset all tracking data."""
        self.history.clear()
        self.metrics_history.clear()
        self.start_time = datetime.now()


class PerformanceMonitor:
    """Monitor multiple strategies and generate reports."""
    
    def __init__(self):
        self.trackers: Dict[str, StrategyTracker] = {}
        self.alert_manager = None
    
    def register(self, strategy_name: str):
        """Register a strategy for monitoring."""
        self.trackers[strategy_name] = StrategyTracker()
        return self.trackers[strategy_name]
    
    def get_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "strategies": {},
            "overall": {
                "total_return": 0,
                "active_strategies": 0,
            }
        }
        
        total_equity = 0
        total_initial = 0
        
        for name, tracker in self.trackers.items():
            latest = tracker.get_latest(name)
            if latest:
                report["strategies"][name] = {
                    "latest_metrics": latest,
                    "records_count": len(tracker.history[name]),
                }
                report["overall"]["active_strategies"] += 1
                
                if 'final_equity' in latest:
                    total_equity += latest['final_equity']
                    total_initial += 10000  # Assuming $10k initial
        
        if total_initial > 0:
            report["overall"]["total_return"] = (total_equity - total_initial) / total_initial
        
        return report
