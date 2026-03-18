"""Alert management for quant strategies."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import dataclasses


@dataclasses.dataclass
class Alert:
    """Alert for strategy events."""
    id: str
    type: str  # "performance", "drawdown", "trade", "system"
    severity: str  # "info", "warning", "critical"
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)
    acknowledged: bool = False


class AlertManager:
    """Manages strategy alerts and notifications."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.max_alerts = 1000
    
    def create(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new alert."""
        from uuid import uuid4
        
        alert = Alert(
            id=str(uuid4()),
            type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {},
            acknowledged=False
        )
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        return alert
    
    def get_critical(self) -> List[Alert]:
        """Get all critical alerts."""
        return [a for a in self.alerts if a.severity == "critical" and not a.acknowledged]
    
    def get_warning(self) -> List[Alert]:
        """Get all warning alerts."""
        return [a for a in self.alerts if a.severity == "warning" and not a.acknowledged]
    
    def acknowledge(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def clear_acknowledged(self) -> int:
        """Clear acknowledged alerts."""
        count = len([a for a in self.alerts if a.acknowledged])
        self.alerts = [a for a in self.alerts if not a.acknowledged]
        return count
    
    def get_summary(self) -> Dict[str, int]:
        """Get alert summary."""
        return {
            "total": len(self.alerts),
            "critical": len([a for a in self.alerts if a.severity == "critical"]),
            "warning": len([a for a in self.alerts if a.severity == "warning"]),
            "info": len([a for a in self.alerts if a.severity == "info"]),
            "unacknowledged": len([a for a in self.alerts if not a.acknowledged]),
        }


class AlertRules:
    """Pre-defined alert rules."""
    
    @staticmethod
    def check_drawdown(alert_manager: AlertManager, equity: float, peak: float, threshold: float = 0.10):
        """Check if drawdown exceeds threshold."""
        if peak > 0:
            drawdown = (peak - equity) / peak
            if drawdown >= threshold:
                alert_manager.create(
                    alert_type="drawdown",
                    severity="critical" if drawdown >= 0.20 else "warning",
                    message=f"Drawdown alert: {drawdown*100:.2f}% (threshold: {threshold*100:.0f}%)",
                    metadata={"drawdown": drawdown, "equity": equity, "peak": peak}
                )
    
    @staticmethod
    def check_performance_degradation(
        alert_manager: AlertManager,
        current_return: float,
        historical_return: float,
        threshold: float = 0.5
    ):
        """Check if performance degraded significantly."""
        if historical_return > 0:
            degradation = (current_return - historical_return) / historical_return
            if degradation <= -threshold:
                alert_manager.create(
                    alert_type="performance",
                    severity="warning",
                    message=f"Performance degradation: {degradation*100:.2f}% vs historical",
                    metadata={"current_return": current_return, "historical_return": historical_return}
                )
    
    @staticmethod
    def check_high_volatility(
        alert_manager: AlertManager,
        volatility: float,
        threshold: float = 0.05
    ):
        """Check if volatility exceeds threshold."""
        if volatility >= threshold:
            alert_manager.create(
                alert_type="volatility",
                severity="warning",
                message=f"High volatility detected: {volatility*100:.2f}%",
                metadata={"volatility": volatility}
            )
