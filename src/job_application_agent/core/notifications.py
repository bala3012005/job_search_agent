"""
Desktop notification system for the job application agent.
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    logging.warning("plyer not available - desktop notifications disabled")

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages desktop notifications and alerts."""

    def __init__(self) -> None:
        """Initialize notification manager."""
        self.enabled = PLYER_AVAILABLE
        self.notification_history: List[Dict[str, Any]] = []

    async def send_notification(
        self, 
        title: str, 
        message: str, 
        notification_type: str = "info", 
        timeout: int = 10
    ) -> None:
        """
        Send a desktop notification.
        
        Args:
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (info, warning, error)
            timeout: How long notification should display in seconds
        """
        if not self.enabled:
            logger.info(f"Notification: {title} - {message}")
            return

        try:
            # Create notification
            if self.enabled and PLYER_AVAILABLE and plyer_notification is not None:
                if hasattr(plyer_notification, "notify") and callable(plyer_notification.notify):
                    plyer_notification.notify(
                        title=title,
                        message=message,
                        app_name="Job Application Agent",
                        timeout=timeout
                    )

            # Store in history
            self.notification_history.append({
                'title': title,
                'message': message,
                'type': notification_type,
                'timestamp': datetime.now().isoformat()
            })

            # Keep only last 100 notifications
            if len(self.notification_history) > 100:
                self.notification_history = self.notification_history[-100:]

            logger.info(f"Notification sent: {title}")

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def get_notification_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent notifications.
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of recent notifications
        """
        return self.notification_history[-limit:]

    def clear_history(self) -> None:
        """Clear all notification history."""
        self.notification_history.clear()