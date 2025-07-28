"""
Main Job Application Agent class.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from .config import config
from .database import db
from .scheduler import JobScheduler
from .notifications import NotificationManager
from ..scrapers.scraper_manager import ScraperManager
from ..ai.cover_letter_generator import CoverLetterGenerator
from ..automation.application_handler import ApplicationHandler

logger = logging.getLogger(__name__)

class JobApplicationAgent:
    """Main agent class that orchestrates the job application process."""

    def __init__(self):
        self.config = config
        self.db = db
        self.scheduler = JobScheduler()
        self.notifications = NotificationManager()
        self.scraper_manager = ScraperManager()
        self.cover_letter_generator = CoverLetterGenerator()
        self.application_handler = ApplicationHandler()

        self.is_running = False
        self.stats = {
            'jobs_found_today': 0,
            'applications_sent_today': 0,
            'total_jobs': 0,
            'total_applications': 0
        }

    async def start(self):
        """Start the job application agent."""
        logger.info("Starting Job Application Agent...")
        self.is_running = True

        # Schedule periodic tasks
        await self._schedule_tasks()

        # Send startup notification
        await self.notifications.send_notification(
            "Job Agent Started",
            "Your job application agent is now running and searching for opportunities.",
            "startup"
        )

        # Start the main event loop
        await self._run_main_loop()

    async def stop(self):
        """Stop the job application agent."""
        logger.info("Stopping Job Application Agent...")
        self.is_running = False

        await self.notifications.send_notification(
            "Job Agent Stopped",
            "Your job application agent has been stopped.",
            "shutdown"
        )

    async def _schedule_tasks(self):
        """Schedule periodic tasks."""
        # Schedule job search every 30 minutes
        self.scheduler.schedule_periodic_task(
            "job_search",
            self._search_jobs,
            interval_minutes=30
        )

        # Schedule application processing every 5 minutes
        self.scheduler.schedule_periodic_task(
            "process_applications",
            self._process_pending_applications,
            interval_minutes=5
        )

        # Schedule daily stats update
        self.scheduler.schedule_daily_task(
            "daily_stats",
            self._update_daily_stats,
            hour=23, minute=59
        )

    async def _run_main_loop(self):
        """Main event loop."""
        while self.is_running:
            try:
                # Process scheduled tasks
                await self.scheduler.process_tasks()

                # Small delay to prevent busy waiting
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _search_jobs(self):
        """Search for new jobs across all platforms."""
        logger.info("Starting job search...")

        try:
            # Get jobs from all scrapers
            all_jobs = await self.scraper_manager.search_all_platforms()

            new_jobs_count = 0
            for job in all_jobs:
                # Calculate match score
                match_score = self._calculate_match_score(job)
                job['match_score'] = match_score

                # Save to database if match score is good
                if match_score >= 0.6:  # 60% match threshold
                    saved = await self.db.save_job(job)
                    if saved:
                        new_jobs_count += 1

            self.stats['jobs_found_today'] += new_jobs_count

            if new_jobs_count > 0:
                await self.notifications.send_notification(
                    f"Found {new_jobs_count} New Jobs",
                    f"Discovered {new_jobs_count} matching job opportunities.",
                    "new_jobs"
                )

            logger.info(f"Job search completed. Found {new_jobs_count} new matching jobs.")

        except Exception as e:
            logger.error(f"Error during job search: {e}")

    async def _process_pending_applications(self):
        """Process pending job applications."""
        logger.info("Processing pending applications...")

        try:
            # Get jobs that need applications
            pending_jobs = await self.db.get_jobs(status='discovered', limit=5)

            for job in pending_jobs:
                if self.stats['applications_sent_today'] >= self.config.job_search.max_applications_per_day:
                    logger.info("Daily application limit reached")
                    break

                # Generate cover letter
                cover_letter = await self.cover_letter_generator.generate_cover_letter(job)

                if cover_letter:
                    # Attempt to apply
                    success = await self.application_handler.apply_to_job(job, cover_letter)

                    if success:
                        self.stats['applications_sent_today'] += 1

                        # Update job status
                        job['status'] = 'applied'
                        await self.db.save_job(job)

                        # Save application record
                        await self.db.save_application({
                            'job_id': job['job_id'],
                            'status': 'submitted',
                            'cover_letter_path': cover_letter.get('file_path')
                        })

                        await self.notifications.send_notification(
                            "Application Submitted",
                            f"Successfully applied to {job['title']} at {job['company']}",
                            "application_success"
                        )
                    else:
                        # Mark for manual review
                        job['status'] = 'manual_review'
                        await self.db.save_job(job)

                        await self.notifications.send_notification(
                            "Manual Review Required",
                            f"Could not auto-apply to {job['title']} at {job['company']}",
                            "application_failure"
                        )

                # Add delay between applications
                await asyncio.sleep(self.config.job_search.application_delay_min * 60)

        except Exception as e:
            logger.error(f"Error processing applications: {e}")

    def _calculate_match_score(self, job: Dict[str, Any]) -> float:
        """Calculate how well a job matches the user profile."""
        score = 0.0

        # Check title match
        title = job.get('title', '').lower()
        for keyword in self.config.job_search.keywords:
            if keyword.lower() in title:
                score += 0.3
                break

        # Check skills match
        description = (job.get('description', '') + ' ' + job.get('requirements', '')).lower()
        skill_matches = 0
        for skill in self.config.user_profile.skills:
            if skill.lower() in description:
                skill_matches += 1

        if skill_matches > 0:
            score += min(0.5, skill_matches * 0.1)

        # Check experience requirements
        exp_text = job.get('experience_required', '').lower()
        if any(term in exp_text for term in ['0-2', '0 to 2', 'fresher', 'entry level']):
            score += 0.2

        return min(1.0, score)

    async def _update_daily_stats(self):
        """Update daily statistics."""
        await self.db.update_daily_stats(
            jobs_found=self.stats['jobs_found_today'],
            applications_sent=self.stats['applications_sent_today']
        )

        # Reset daily counters
        self.stats['jobs_found_today'] = 0
        self.stats['applications_sent_today'] = 0

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for the dashboard."""
        recent_jobs = await self.db.get_jobs(limit=10)
        stats = await self.db.get_stats(days=7)

        return {
            'stats': self.stats,
            'recent_jobs': recent_jobs,
            'weekly_stats': stats,
            'is_running': self.is_running
        }
