"""
Task scheduling system for the job application agent.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Callable, Any
import schedule

logger = logging.getLogger(__name__)

class JobScheduler:
    """Handles scheduling of periodic and one-time tasks."""

    def __init__(self):
        self.tasks = {}
        self.running_tasks = set()

    def schedule_periodic_task(self, task_id: str, task_func: Callable, interval_minutes: int):
        """Schedule a task to run periodically."""
        self.tasks[task_id] = {
            'func': task_func,
            'type': 'periodic',
            'interval': interval_minutes,
            'next_run': datetime.now() + timedelta(minutes=interval_minutes),
            'last_run': None
        }
        logger.info(f"Scheduled periodic task '{task_id}' every {interval_minutes} minutes")

    def schedule_daily_task(self, task_id: str, task_func: Callable, hour: int, minute: int = 0):
        """Schedule a task to run daily at a specific time."""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        self.tasks[task_id] = {
            'func': task_func,
            'type': 'daily',
            'hour': hour,
            'minute': minute,
            'next_run': next_run,
            'last_run': None
        }
        logger.info(f"Scheduled daily task '{task_id}' at {hour:02d}:{minute:02d}")

    async def process_tasks(self):
        """Process all scheduled tasks."""
        now = datetime.now()

        for task_id, task_info in self.tasks.items():
            if task_id in self.running_tasks:
                continue  # Task is already running

            if now >= task_info['next_run']:
                logger.info(f"Executing scheduled task: {task_id}")
                self.running_tasks.add(task_id)

                try:
                    # Run the task
                    await task_info['func']()
                    task_info['last_run'] = now

                    # Schedule next run
                    if task_info['type'] == 'periodic':
                        task_info['next_run'] = now + timedelta(minutes=task_info['interval'])
                    elif task_info['type'] == 'daily':
                        task_info['next_run'] = now + timedelta(days=1)

                    logger.info(f"Task '{task_id}' completed successfully")

                except Exception as e:
                    logger.error(f"Task '{task_id}' failed: {e}")
                    # Schedule retry in 5 minutes
                    task_info['next_run'] = now + timedelta(minutes=5)

                finally:
                    self.running_tasks.discard(task_id)

    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all scheduled tasks."""
        now = datetime.now()
        status = {}

        for task_id, task_info in self.tasks.items():
            status[task_id] = {
                'type': task_info['type'],
                'next_run': task_info['next_run'].isoformat(),
                'last_run': task_info['last_run'].isoformat() if task_info['last_run'] else None,
                'is_running': task_id in self.running_tasks,
                'time_until_next_run': str(task_info['next_run'] - now)
            }

        return status
